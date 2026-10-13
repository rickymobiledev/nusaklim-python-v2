# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "pandas",
#     "psycopg[binary]>=3.2,<4",
#     "python-dotenv",
#     "pydantic",
#     "pydantic-settings>=2.15.0",
# ]
# ///
"""
Script Impor Data PostgreSQL NusaKlim (Stasiun & Data Cuaca).

Mengimpor metadata stasiun AWS dan riwayat pembacaan sensor cuaca
dari direktori data/ ke database PostgreSQL dengan performa tinggi
menggunakan PostgreSQL streaming COPY dan penyelesaian konflik duplikasi.

Contoh Penggunaan:
    # Impor stasiun dan data cuaca sekaligus (default data/):
    uv run python scripts/import_data.py

    # Impor stasiun saja:
    uv run python scripts/import_data.py --stations-only

    # Impor cuaca saja:
    uv run python scripts/import_data.py --weather-only

    # Lihat status dan jumlah data di database saat ini:
    uv run python scripts/import_data.py --status

    # Pengujian cepat (hanya baca 50.000 baris pertama):
    uv run python scripts/import_data.py --weather-only --limit-rows 50000
"""

import argparse
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import sys
import time

# Pastikan root proyek ada di sys.path agar dapat mengimpor package `api`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import psycopg

from api.config import settings
from api import weather_store as store
from api.ingest_upload import validate_csv_header


def format_duration(seconds: float) -> str:
    """Format durasi detik ke bentuk 'Xm Ys' atau 'Xs'."""
    seconds = max(0.0, seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins:02d}m {secs:02d}s"


def format_number(val: int | float) -> str:
    """Format angka dengan pemisah ribuan."""
    return f"{int(val):,}"


def normalize_epoch(s: str | None) -> str:
    """Normalisasi epoch timestamp agar konsisten (misal '1787136600.0' -> '1787136600')."""
    if not s or s == "---":
        return s or ""
    s_clean = s.strip()
    if "." in s_clean:
        parts = s_clean.split(".", 1)
        if len(parts) == 2 and parts[1].replace("0", "") == "":
            return parts[0]
        try:
            d = Decimal(s_clean)
            if d.is_finite():
                formatted = format(d, "f")
                return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
        except InvalidOperation:
            pass
    return s_clean


def get_table_counts(conn) -> dict[str, int]:
    """Mengambil jumlah baris saat ini dari tabel stasiun dan data mentah."""
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM weather_stations")
    stations_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM weather_raw")
    raw_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM weather_daily")
    daily_count = cur.fetchone()[0]
    return {
        "stations": stations_count,
        "raw": raw_count,
        "daily": daily_count,
    }


def import_stations(csv_path: Path) -> dict:
    """Mengimpor metadata stasiun cuaca dari CSV ke weather_stations."""
    print("=" * 70)
    print("1. MEMULAI IMPOR METADATA STASIUN (weather_stations)")
    print("=" * 70)
    print(f"File sumber: {csv_path}")

    if not csv_path.is_file():
        raise FileNotFoundError(f"File stasiun tidak ditemukan: {csv_path}")

    start_time = time.time()
    result = store.import_stations_csv(str(csv_path))
    elapsed = time.time() - start_time

    print(f"[OK] Selesai impor stasiun dalam {elapsed:.2f}s:")
    print(f"     - Total stasiun di CSV : {result['rows_in_file']}")
    print(f"     - Tersimpan/diperbarui : {result['stations_saved']}")
    return result


def import_weather_raw(
    csv_path: Path,
    chunk_size: int = 100_000,
    limit_rows: int | None = None,
    commit_per_chunk: bool = True,
) -> dict:
    """Mengimpor riwayat data cuaca mentah dari CSV ke weather_raw via PostgreSQL streaming COPY."""
    print("=" * 70)
    print("2. MEMULAI IMPOR DATA CUACA MENTAH (weather_raw)")
    print("=" * 70)
    print(f"File sumber : {csv_path}")
    print(f"Ukuran chunk: {format_number(chunk_size)} baris per batch")
    if limit_rows:
        print(f"Batasan baris: Maksimal {format_number(limit_rows)} baris")

    if not csv_path.is_file():
        raise FileNotFoundError(f"File data cuaca tidak ditemukan: {csv_path}")

    file_size_bytes = csv_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"Ukuran file : {file_size_mb:.2f} MB")

    # Validasi header CSV
    validate_csv_header(str(csv_path))

    # Estimasi baris berdasarkan rata-rata ukuran per baris (~93 byte/baris)
    estimated_total_rows = int(file_size_bytes / 93)
    if limit_rows:
        estimated_total_rows = min(estimated_total_rows, limit_rows)

    start_time = time.time()
    total_processed = 0
    total_added = 0
    total_skipped = 0
    chunk_index = 0

    with store.connect() as conn:
        store.initialize(conn)

        # Cache stasiun yang sudah terdaftar di database untuk menghindari foreign key violation
        cur = conn.cursor()
        cur.execute("SELECT id FROM weather_stations")
        known_stations = {row[0] for row in cur.fetchall()}
        print(f"Stasiun terdaftar di database saat ini: {len(known_stations)} stasiun")

        # Buat tabel temporary untuk batch staging (preservasi baris selama koneksi aktif)
        cur.execute(
            "CREATE TEMP TABLE IF NOT EXISTS incoming_weather (LIKE weather_raw) ON COMMIT PRESERVE ROWS"
        )
        cur.execute("TRUNCATE incoming_weather")
        if commit_per_chunk:
            conn.commit()

        print("-" * 70)
        print(f"Memproses batch streaming ke PostgreSQL...")

        try:
            reader = pd.read_csv(
                csv_path,
                chunksize=chunk_size,
                dtype=str,
                low_memory=False,
            )

            for chunk in reader:
                chunk_index += 1
                chunk.columns = chunk.columns.str.strip()

                if limit_rows and total_processed + len(chunk) > limit_rows:
                    chunk = chunk.iloc[: limit_rows - total_processed]

                chunk_len = len(chunk)
                if chunk_len == 0:
                    break

                # 1. Pastikan setiap stasiun di chunk ini sudah ada di tabel weather_stations
                station_ids = chunk["stnname"].dropna().unique()
                missing_stations = [s.strip() for s in station_ids if s and s.strip() not in known_stations]
                if missing_stations:
                    cur.executemany(
                        "INSERT INTO weather_stations (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                        [(s, f"Station {s}") for s in missing_stations],
                    )
                    known_stations.update(missing_stations)

                # 2. Siapkan data baris untuk streaming COPY
                rows_to_copy = []
                for row in chunk[store.RAW_COLUMNS].itertuples(index=False, name=None):
                    cleaned_row = []
                    for idx, val in enumerate(row):
                        if val is None or pd.isna(val):
                            cleaned_row.append(None)
                        else:
                            s_val = str(val).strip()
                            cleaned_row.append(s_val if s_val != "" else None)

                    # Pastikan stnname dan utctime tidak None (NOT NULL di Postgres)
                    cleaned_row[0] = cleaned_row[0] or ""
                    cleaned_row[1] = normalize_epoch(cleaned_row[1])
                    rows_to_copy.append(tuple(cleaned_row))

                # 3. Fast COPY ke temporary table
                with cur.copy(f"COPY incoming_weather ({store.RAW_NAMES}) FROM STDIN") as copy:
                    for r in rows_to_copy:
                        copy.write_row(r)

                # 4. Upsert / Konflik DO NOTHING ke weather_raw
                cur.execute(
                    f"""
                    INSERT INTO weather_raw ({store.RAW_NAMES})
                    SELECT {store.RAW_NAMES} FROM incoming_weather
                    ON CONFLICT (stnname, utctime) DO NOTHING
                    """
                )
                added_in_chunk = cur.rowcount
                skipped_in_chunk = chunk_len - added_in_chunk

                total_processed += chunk_len
                total_added += added_in_chunk
                total_skipped += skipped_in_chunk

                # 5. Kosongkan temporary table untuk chunk berikutnya
                cur.execute("TRUNCATE incoming_weather")

                if commit_per_chunk:
                    conn.commit()

                # Hitung metrik progres
                elapsed = time.time() - start_time
                speed = total_processed / elapsed if elapsed > 0 else 0
                pct = min(100.0, (total_processed / estimated_total_rows) * 100) if estimated_total_rows else 0
                remaining_rows = max(0, estimated_total_rows - total_processed)
                eta_seconds = remaining_rows / speed if speed > 0 else 0
                eta_str = format_duration(eta_seconds)

                print(
                    f"[{chunk_index:03d}] {format_number(total_processed):>11} baris "
                    f"({pct:5.1f}%) | "
                    f"+{format_number(added_in_chunk):>6} baru | "
                    f"Kecepatan: {format_number(speed):>6} baris/s | "
                    f"Waktu: {format_duration(elapsed):>7} | ETA: {eta_str:>7}",
                    flush=True,
                )

                if limit_rows and total_processed >= limit_rows:
                    print(f"\n[INFO] Batasan limit {format_number(limit_rows)} baris telah tercapai.")
                    break

        except KeyboardInterrupt:
            print("\n" + "!" * 70)
            print("[PERINGATAN] Proses dihentikan oleh pengguna (Ctrl+C).")
            if commit_per_chunk:
                print(f"Data hingga baris ke-{format_number(total_processed)} telah tersimpan aman di database.")
            else:
                conn.rollback()
                print("Seluruh batch transaksi dibatalkan (rollback).")
            print("!" * 70)
            raise

        if not commit_per_chunk:
            conn.commit()

    total_time = time.time() - start_time
    avg_speed = total_processed / total_time if total_time > 0 else 0

    return {
        "total_processed": total_processed,
        "total_added": total_added,
        "total_skipped": total_skipped,
        "chunks": chunk_index,
        "total_time_seconds": total_time,
        "avg_speed_rows_per_sec": avg_speed,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="NusaKlim - Impor Data CSV (Stasiun & Cuaca) ke PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  uv run python scripts/import_data.py
  uv run python scripts/import_data.py --stations-only
  uv run python scripts/import_data.py --weather-only
  uv run python scripts/import_data.py --chunk-size 200000
  uv run python scripts/import_data.py --status
        """,
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Tampilkan status koneksi database dan jumlah data saat ini",
    )
    parser.add_argument(
        "--stations-only",
        action="store_true",
        help="Hanya impor data stasiun (device_nusaklim.csv)",
    )
    parser.add_argument(
        "--weather-only",
        action="store_true",
        help="Hanya impor data cuaca mentah (nusaklim-aws-reduce.csv)",
    )
    parser.add_argument(
        "--stations-file",
        type=Path,
        default=PROJECT_ROOT / "data" / "device_nusaklim.csv",
        help="Jalur file CSV stasiun (default: data/device_nusaklim.csv)",
    )
    parser.add_argument(
        "--weather-file",
        type=Path,
        default=PROJECT_ROOT / "data" / "nusaklim-aws-reduce.csv",
        help="Jalur file CSV data cuaca (default: data/nusaklim-aws-reduce.csv)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100_000,
        help="Ukuran chunk pemrosesan per batch (default: 100000 baris)",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        default=None,
        help="Batasi jumlah baris yang diimpor (berguna untuk testing)",
    )
    parser.add_argument(
        "--single-transaction",
        action="store_true",
        help="Gunakan 1 transaksi tunggal (rollback seluruhnya jika terjadi error)",
    )

    args = parser.parse_args(argv)

    if args.stations_only and args.weather_only:
        parser.error("Tidak dapat memilih --stations-only dan --weather-only secara bersamaan.")

    if args.chunk_size < 1:
        parser.error("--chunk-size harus lebih besar dari 0.")

    # Cek konfigurasi database
    db_url = settings.database_url
    if not db_url:
        print("[ERROR] NUSAKLIM_DATABASE_URL belum dikonfigurasi di .env!", file=sys.stderr)
        print("Silakan buka file .env dan pastikan baris berikut sudah aktif:", file=sys.stderr)
        print("  NUSAKLIM_DATABASE_URL=postgresql://user:password@host:port/dbname", file=sys.stderr)
        return 1

    # Cek koneksi ke database
    try:
        with store.connect() as conn:
            counts_before = get_table_counts(conn)
    except Exception as e:
        print(f"[ERROR] Gagal terhubung ke PostgreSQL: {e}", file=sys.stderr)
        print("Pastikan PostgreSQL service berjalan dan kredensial di .env sudah sesuai.", file=sys.stderr)
        return 1

    # Jika hanya mengecek status
    if args.status:
        print("=" * 70)
        print("STATUS DATABASE POSTGRESQL NUSAKLIM")
        print("=" * 70)
        print(f"URL Database : {settings.database_url.split('@')[-1] if '@' in settings.database_url else '(tersedia)'}")
        print(f"weather_stations : {format_number(counts_before['stations'])} baris")
        print(f"weather_raw      : {format_number(counts_before['raw'])} baris")
        print(f"weather_daily    : {format_number(counts_before['daily'])} baris")
        print("=" * 70)
        return 0

    print("=" * 70)
    print("NUSAKLIM POSTGRESQL DATA IMPORTER")
    print("=" * 70)
    print(f"Root Proyek    : {PROJECT_ROOT}")
    print(f"Database Target: {settings.database_url.split('@')[-1] if '@' in settings.database_url else '(lokal)'}")
    print(f"Status Awal DB : {format_number(counts_before['stations'])} stasiun, {format_number(counts_before['raw'])} data cuaca")
    print("=" * 70)

    # Tentukan apakah impor stasiun
    run_stations = not args.weather_only
    # Tentukan apakah impor data cuaca
    run_weather = not args.stations_only

    stations_result = None
    weather_result = None

    try:
        # 1. Impor data stasiun terlebih dahulu
        if run_stations:
            stations_result = import_stations(args.stations_file)
            print()

        # 2. Impor riwayat cuaca mentah
        if run_weather:
            weather_result = import_weather_raw(
                args.weather_file,
                chunk_size=args.chunk_size,
                limit_rows=args.limit_rows,
                commit_per_chunk=not args.single_transaction,
            )
            print()

    except Exception as e:
        print(f"\n[ERROR] Impor gagal: {e}", file=sys.stderr)
        return 1

    # Verifikasi akhir
    with store.connect() as conn:
        counts_after = get_table_counts(conn)

    print("=" * 70)
    print("RINGKASAN HASIL IMPOR DATA")
    print("=" * 70)
    if stations_result:
        print(f"Stasiun (weather_stations):")
        print(f"  - Dibaca dari CSV    : {format_number(stations_result['rows_in_file'])}")
        print(f"  - Tersimpan di DB    : {format_number(stations_result['stations_saved'])}")
    if weather_result:
        print(f"Data Cuaca (weather_raw):")
        print(f"  - Total diproses     : {format_number(weather_result['total_processed'])} baris")
        print(f"  - Baris baru masuk   : {format_number(weather_result['total_added'])} baris")
        print(f"  - Duplikat dilewati  : {format_number(weather_result['total_skipped'])} baris")
        print(f"  - Total waktu        : {format_duration(weather_result['total_time_seconds'])}")
        print(f"  - Kecepatan rata-rata: {format_number(weather_result['avg_speed_rows_per_sec'])} baris/detik")

    print("-" * 70)
    print(f"Total baris akhir di database:")
    print(f"  - weather_stations : {format_number(counts_after['stations'])} stasiun (+{format_number(counts_after['stations'] - counts_before['stations'])})")
    print(f"  - weather_raw      : {format_number(counts_after['raw'])} baris (+{format_number(counts_after['raw'] - counts_before['raw'])})")
    print("=" * 70)
    print("[SELESAI] Semua proses impor telah berhasil diselesaikan!")
    print("Catatan: Anda sekarang dapat mengaktifkan 'NUSAKLIM_STORAGE_BACKEND=postgres' di .env")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
