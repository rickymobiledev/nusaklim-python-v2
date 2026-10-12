"""Apply schema migrations and optionally migrate historical CSV data."""
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from api import weather_store as store
from api.db_migrations import apply_migrations, migration_status


def verify(conn):
    raw_rows, raw_stations = conn.execute("SELECT count(*), count(DISTINCT stnname) FROM weather_raw").fetchone()
    daily_rows, daily_stations = conn.execute("SELECT count(*), count(DISTINCT stnname) FROM weather_daily").fetchone()
    return {"raw_rows": raw_rows, "daily_rows": daily_rows,
            "raw_stations": raw_stations, "daily_stations": daily_stations}


def migrate(raw_csv=None, daily_csv=None, chunk_size=100_000):
    if chunk_size < 1:
        raise ValueError("chunk_size harus lebih besar dari 0")
    # Validate inputs before making any database changes.
    if raw_csv is not None:
        store.validate_csv_header(str(Path(raw_csv).resolve(strict=True)))
    daily_frame = None
    if daily_csv is not None:
        daily_frame = pd.read_csv(Path(daily_csv).resolve(strict=True), dtype={"stnname": str})
        missing = set(store.DAILY_COLUMNS) - set(daily_frame.columns)
        if missing:
            raise ValueError("Kolom CSV harian tidak lengkap: " + ", ".join(sorted(missing)))
        if daily_frame.empty:
            raise ValueError("CSV harian kosong")
    with store.connect() as conn:
        completed = apply_migrations(conn)
    result = {"migrations": completed}
    if raw_csv is not None:
        print("Mengimpor riwayat mentah ke PostgreSQL...", flush=True)
        result["raw"] = store.import_raw_csv(str(raw_csv), chunk_size=chunk_size)
    if daily_frame is not None:
        store.save_daily(daily_frame)
        result["daily_rows"] = len(daily_frame)
    elif raw_csv is not None:
        from process_nusaklim import run_nusaklim_pipeline
        print("Membuat agregasi harian dari PostgreSQL...", flush=True)
        frame = run_nusaklim_pipeline(storage_backend="postgres", chunk_size=chunk_size)
        result["daily_rows"] = len(frame)
    with store.connect() as conn:
        result["verification"] = verify(conn)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Migrasi schema PostgreSQL dan data historis NusaKlim (tanpa retrain)")
    parser.add_argument("--status", action="store_true", help="Lihat status migrasi tanpa mengubah database")
    parser.add_argument("--raw-csv", help="Impor raw CSV lama lalu buat agregasi harian dari database")
    parser.add_argument("--daily-csv", help="Impor snapshot harian sebagai pengganti langkah cleaning")
    parser.add_argument("--chunk-size", type=int, default=100_000, help="Ukuran batch impor/cleaning, default 100000")
    args = parser.parse_args(argv)
    if args.chunk_size < 1:
        parser.error("--chunk-size harus lebih besar dari 0")
    if args.status and (args.raw_csv or args.daily_csv):
        parser.error("--status tidak dapat digabung dengan opsi impor")
    try:
        if args.status:
            with store.connect() as conn:
                result = migration_status(conn)
            print(json.dumps(result, indent=2))
            return 1 if any(item["status"] in ("modified", "missing") for item in result) else 0
        result = migrate(args.raw_csv, args.daily_csv, args.chunk_size)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as error:
        # Driver errors can contain connection details; don't print the configured URL.
        if isinstance(error, (ValueError, FileNotFoundError)):
            detail = str(error)
        else:
            detail = f"{type(error).__name__}: periksa koneksi, izin database, dan format CSV"
        print(f"Migrasi gagal: {detail}. Tahap yang selesai tetap tersimpan; perintah aman diulang.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
