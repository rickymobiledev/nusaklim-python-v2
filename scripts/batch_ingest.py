# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "pandas",
#     "python-dotenv",
#     "pydantic",
#     "pydantic-settings>=2.15.0",
#     "requests",
# ]
# ///
"""
NusaKlim Batch Ingestion CLI Utility.

Mempermudah pengiriman data sensor cuaca mentah dalam batch melalui REST API NusaKlim,
dengan dukungan fleksibel untuk pemilihan stasiun, penonaktifan retrain (batching ingest),
atau memicu retraining otomatis setelah seluruh batch selesai di-commit.

Contoh Penggunaan:
    # 1. Ingest batch dari file CSV tanpa memicu retrain (default untuk batching):
    uv run python scripts/batch_ingest.py --file data/incoming_weather.csv --no-retrain

    # 2. Ingest batch dan picu retrain otomatis di batch terakhir:
    uv run python scripts/batch_ingest.py --file data/incoming_weather.csv --trigger-retrain

    # 3. Ingest hanya data stasiun 227 dengan batasan maksimal 2.000 baris:
    uv run python scripts/batch_ingest.py --file data/nusaklim-aws-reduce.csv --station 227 --limit 2000 --no-retrain

    # 4. Atur ukuran per batch request (misal: 2.500 baris per request):
    uv run python scripts/batch_ingest.py --file data/incoming_weather.csv --batch-size 2500 --no-retrain
"""

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Generator, List, Dict, Any, Optional
import urllib.request
import urllib.error

# Pastikan root proyek ada di sys.path agar dapat membaca modul konfigurasi api
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from api.config import settings


def format_duration(seconds: float) -> str:
    """Format durasi detik ke bentuk 'Xm Ys' atau 'Xs'."""
    seconds = max(0.0, seconds)
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs:02d}s"


def format_number(val: int | float) -> str:
    """Format angka dengan pemisah ribuan."""
    return f"{int(val):,}"


def parse_int_epoch(val: Any) -> Optional[int]:
    """Parse utctime ke integer Unix epoch detik."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s == "---":
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def parse_float_val(val: Any) -> Optional[float]:
    """Parse nilai sensor ke float, abaikan nilai kosong atau '---'."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s == "---":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def parse_str_val(val: Any) -> Optional[str]:
    """Parse string atau tanggal, abaikan jika kosong atau '---'."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    return s if s and s != "---" else None


def row_to_record(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Konversi dictionary baris CSV/JSON ke format IngestRecord valid."""
    stnname = str(row.get("stnname", "")).strip()
    if not stnname or stnname == "---":
        return None

    utctime = parse_int_epoch(row.get("utctime"))
    if utctime is None:
        return None

    record = {
        "stnname": stnname,
        "utctime": utctime,
        "tempout": parse_float_val(row.get("tempout")),
        "humout": parse_float_val(row.get("humout")),
        "windspd": parse_float_val(row.get("windspd")),
        "winddir": parse_float_val(row.get("winddir")),
        "bar": parse_float_val(row.get("bar")),
        "solar": parse_float_val(row.get("solar")),
        "rain15": parse_float_val(row.get("rain15")),
        "created_at": parse_str_val(row.get("created_at")),
        "updated_at": parse_str_val(row.get("updated_at")),
    }
    return record


def stream_csv_records(
    file_path: Path,
    station_id: Optional[str] = None,
    limit: Optional[int] = None,
    chunk_size: int = 50_000,
) -> Generator[Dict[str, Any], None, None]:
    """Membaca CSV secara streaming dan menghasilkan dict IngestRecord satu per satu."""
    total_yielded = 0
    target_stn = str(station_id).strip() if station_id is not None else None

    reader = pd.read_csv(
        file_path,
        chunksize=chunk_size,
        dtype=str,
        low_memory=False,
    )

    for chunk in reader:
        chunk.columns = chunk.columns.str.strip()

        if target_stn is not None and "stnname" in chunk.columns:
            chunk = chunk[chunk["stnname"].astype(str).str.strip() == target_stn]

        if chunk.empty:
            continue

        for row in chunk.to_dict("records"):
            rec = row_to_record(row)
            if rec is not None:
                yield rec
                total_yielded += 1
                if limit is not None and total_yielded >= limit:
                    return


def load_json_records(
    file_path: Path,
    station_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Membaca file JSON (berupa list record atau object ber-field 'records')."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        raw_list = data.get("records", [])
    elif isinstance(data, list):
        raw_list = data
    else:
        raise ValueError(f"Format JSON tidak valid pada {file_path}")

    target_stn = str(station_id).strip() if station_id is not None else None
    valid_records = []
    for item in raw_list:
        rec = row_to_record(item)
        if rec is None:
            continue
        if target_stn is not None and rec["stnname"] != target_stn:
            continue
        valid_records.append(rec)
        if limit is not None and len(valid_records) >= limit:
            break

    return valid_records


def batch_generator(generator: Generator[Any, None, None], batch_size: int) -> Generator[List[Any], None, None]:
    """Mengelompokkan generator item menjadi list batch berukuran batch_size."""
    batch = []
    for item in generator:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def send_ingest_request(
    endpoint_url: str,
    api_key: str,
    records: List[Dict[str, Any]],
    mode: str = "append",
    trigger_retrain: bool = False,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Mengirim request HTTP POST /ingest/json ke REST API."""
    payload = {
        "mode": mode,
        "trigger_retrain": trigger_retrain,
        "records": records,
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint_url,
        data=body_bytes,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "User-Agent": "NusaKlim-Batch-Ingest/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            res_body = res.read().decode("utf-8")
            return {
                "status_code": res.status,
                "data": json.loads(res_body) if res_body else {},
                "error": None,
            }
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"detail": err_body}
        return {
            "status_code": e.code,
            "data": parsed,
            "error": parsed.get("detail", f"HTTP Error {e.code}"),
        }
    except Exception as e:
        return {
            "status_code": 0,
            "data": {},
            "error": str(e),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="NusaKlim Batch Ingestion CLI - Pengiriman Data Mentah dalam Batch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh Penggunaan:
  # Ingest batch tanpa memicu retrain (mode batching ingest):
  uv run python scripts/batch_ingest.py --file data/incoming_weather.csv --no-retrain

  # Ingest batch dan picu retrain otomatis di akhir batch:
  uv run python scripts/batch_ingest.py --file data/incoming_weather.csv --trigger-retrain

  # Ingest stasiun 227 saja dengan limit 5000 baris:
  uv run python scripts/batch_ingest.py --file data/nusaklim-aws-reduce.csv --station 227 --limit 5000 --no-retrain

  # Atur ukuran batch menjadi 2000 baris per request:
  uv run python scripts/batch_ingest.py --file data/incoming.csv --batch-size 2000 --no-retrain
        """,
    )

    parser.add_argument(
        "--file", "-f",
        type=Path,
        default=None,
        help="Jalur file CSV atau JSON yang berisi data sensor mentah.",
    )
    parser.add_argument(
        "--station", "-s",
        type=str,
        default=None,
        help="ID stasiun AWS (opsional, untuk memfilter hanya record stasiun tertentu).",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=5000,
        help="Jumlah record per batch HTTP request (default: 5000, maks: 100000).",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Batasi total record yang dikirim (berguna untuk pengujian cepat).",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["append", "replace"],
        default="append",
        help="Mode ingest ('append' atau 'replace', default: append).",
    )

    # Grup penentuan opsi retrain
    retrain_group = parser.add_mutually_exclusive_group()
    retrain_group.add_argument(
        "--no-retrain",
        dest="trigger_retrain",
        action="store_false",
        default=False,
        help="Jangan picu retrain model (data hanya disimpan ke storage, default untuk batch).",
    )
    retrain_group.add_argument(
        "--trigger-retrain",
        dest="trigger_retrain",
        action="store_true",
        help="Picu otomatis proses retrain di background pada batch terakhir.",
    )

    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help=f"URL endpoint ingest/json (default: http://{settings.host}:{settings.port}{settings.api_prefix}/ingest/json).",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API Key untuk autentikasi header X-API-Key (default: dari konfigurasi .env).",
    )

    args = parser.parse_args(argv)

    # Validasi file sumber
    file_path = args.file
    if file_path is None:
        # Coba cek default paths yang ada
        candidates = [
            PROJECT_ROOT / "data" / "nusaklim-aws-reduce.csv",
            PROJECT_ROOT / "data_raw" / "nusaklim-aws-reduce.csv",
        ]
        for c in candidates:
            if c.is_file():
                file_path = c
                break

    if file_path is None or not file_path.is_file():
        print(f"[ERROR] File sumber tidak ditemukan atau belum ditentukan!", file=sys.stderr)
        print("Gunakan opsi: --file <path/ke/file.csv>", file=sys.stderr)
        return 1

    if args.batch_size < 1:
        print("[ERROR] --batch-size harus lebih besar dari 0.", file=sys.stderr)
        return 1

    if args.batch_size > settings.max_ingest_records:
        print(
            f"[PERINGATAN] --batch-size ({args.batch_size:,}) melebihi batas server ({settings.max_ingest_records:,}). "
            f"Menyesuaikan ke {settings.max_ingest_records:,}...",
            file=sys.stderr,
        )
        args.batch_size = settings.max_ingest_records

    # Konfigurasi Endpoint & Autentikasi
    endpoint_url = args.endpoint or f"http://{settings.host}:{settings.port}{settings.api_prefix}/ingest/json"
    api_key = args.api_key or settings.weather_api_key

    print("=" * 75)
    print("NUSAKLIM BATCH INGESTION UTILITY")
    print("=" * 75)
    print(f"File Sumber       : {file_path}")
    print(f"Ukuran File       : {file_path.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"Filter Stasiun    : {args.station or '(Semua Stasiun)'}")
    print(f"Ukuran per Batch  : {format_number(args.batch_size)} baris / request")
    print(f"Limit Maksimal    : {format_number(args.limit) if args.limit else 'Tidak dibatasi'}")
    print(f"Mode Ingest       : {args.mode}")
    print(f"Trigger Retrain   : {'Aktif (pada batch terakhir)' if args.trigger_retrain else 'Nonaktif (--no-retrain)'}")
    print(f"Target API        : {endpoint_url}")
    print("=" * 75)

    is_json = file_path.suffix.lower() == ".json"

    # Siapkan batch iterator dengan mekanisme look-ahead untuk mendeteksi batch terakhir
    if is_json:
        print("Memuat dan memfilter data dari file JSON...")
        all_records = load_json_records(file_path, station_id=args.station, limit=args.limit)
        if not all_records:
            print("[INFO] Tidak ada record valid yang ditemukan untuk dikirim.")
            return 0
        print(f"Ditemukan {format_number(len(all_records))} record valid.")
        raw_batches = [all_records[i : i + args.batch_size] for i in range(0, len(all_records), args.batch_size)]
        batches_iter = iter(raw_batches)
        total_batches_est = len(raw_batches)
    else:
        print("Menyiapkan pembacaan streaming file CSV...")
        record_stream = stream_csv_records(file_path, station_id=args.station, limit=args.limit)
        batches_iter = batch_generator(record_stream, args.batch_size)
        total_batches_est = None

    # Look-ahead buffering untuk mengetahui apakah batch saat ini adalah batch terakhir
    try:
        current_batch = next(batches_iter)
    except StopIteration:
        print("[INFO] Tidak ada data valid yang cocok dengan kriteria filter.")
        return 0

    batch_idx = 0
    total_records_sent = 0
    total_rows_added = 0
    total_rows_skipped = 0
    t_start = time.time()
    retrain_triggered = False

    while current_batch is not None:
        batch_idx += 1
        # Intip batch berikutnya
        try:
            next_batch = next(batches_iter)
            is_last_batch = False
        except StopIteration:
            next_batch = None
            is_last_batch = True

        # Tentukan trigger_retrain untuk batch ini:
        # Hanya True jika user memilih --trigger-retrain DAN ini adalah batch terakhir
        should_retrain = bool(args.trigger_retrain and is_last_batch)

        batch_count = len(current_batch)
        batch_label = f"Batch {batch_idx}"
        if total_batches_est is not None:
            batch_label += f"/{total_batches_est}"

        retrain_tag = " [RETRAIN TRIGGER]" if should_retrain else " [NO-RETRAIN]"
        print(f"-> Mengirim {batch_label} ({format_number(batch_count)} baris){retrain_tag}...", end=" ", flush=True)

        t_batch_start = time.time()
        resp = send_ingest_request(
            endpoint_url=endpoint_url,
            api_key=api_key,
            records=current_batch,
            mode=args.mode,
            trigger_retrain=should_retrain,
        )
        t_batch_elapsed = time.time() - t_batch_start

        status_code = resp["status_code"]
        if status_code in (200, 202):
            data = resp["data"]
            msg = data.get("message", "Accepted")
            task_id = data.get("task_id", "-")
            total_records_sent += batch_count

            # Parsing info rows_added/skipped dari pesan respons jika tersedia
            print(f"[OK] {status_code} ({t_batch_elapsed:.2f}s)")
            print(f"   Task ID: {task_id}")
            print(f"   Pesan  : {msg}")

            if should_retrain:
                retrain_triggered = True
        else:
            print(f"[GAGAL] Status {status_code} ({t_batch_elapsed:.2f}s)")
            print(f"   Error: {resp.get('error')}", file=sys.stderr)
            if status_code == 409:
                print(
                    "   [INFO] Terjadi konflik 409: Proses retrain/ingest lain sedang berjalan di server. "
                    "Gunakan --no-retrain untuk commit tanpa retrain.",
                    file=sys.stderr,
                )
            # Hentikan atau tanyakan? Hentikan batch jika error fatal
            print("\n[ABORT] Pengiriman batch dihentikan karena respons error dari server.", file=sys.stderr)
            return 1

        current_batch = next_batch

    total_time = time.time() - t_start
    avg_speed = total_records_sent / total_time if total_time > 0 else 0

    print("\n" + "=" * 75)
    print("RINGKASAN SELESAI BATCH INGESTION")
    print("=" * 75)
    print(f"Total Batch Dikirim : {batch_idx}")
    print(f"Total Baris Dikirim : {format_number(total_records_sent)} baris")
    print(f"Total Waktu         : {format_duration(total_time)}")
    print(f"Kecepatan Rata-rata : {format_number(avg_speed)} baris/detik")
    if retrain_triggered:
        print("Status Retraining   : BERJALAN DI LATAR BELAKANG (estimasi ~24 menit)")
        print("                      Pantau log: logs/pipeline.log atau logs/runs/<task_id>.log")
    else:
        print("Status Retraining   : TIDAK DIPICU (data berhasil di-commit ke storage)")
    print("=" * 75)
    print("[SELESAI] Batch ingest berhasil diselesaikan!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
