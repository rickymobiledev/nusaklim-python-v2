"""PostgreSQL storage for raw observations and the cleaned daily dataset.

Raw sensor values stay as text to preserve historical error markers for QC.
The observation key is (stnname, utctime); append preserves the first reading.
"""
from decimal import Decimal, InvalidOperation

import pandas as pd
import psycopg

from api.config import settings
from api.ingest_upload import REQUIRED_COLUMNS, UploadValidationError, validate_csv_header

RAW_COLUMNS = REQUIRED_COLUMNS + ["created_at", "updated_at"]
DAILY_COLUMNS = [
    "stnname", "date", "temp_avg", "temp_min", "temp_max", "humidity_avg",
    "humidity_min", "humidity_max", "pressure_avg_hpa", "rainfall_total_mm",
    "solar_radiation_avg", "wind_speed_avg", "wind_speed_max", "wind_direction_deg",
    "wind_direction_name", "records_count",
]
RAW_NAMES = ", ".join(RAW_COLUMNS)
DAILY_NAMES = ", ".join(DAILY_COLUMNS)


def connect():
    if not settings.database_url:
        raise ValueError("NUSAKLIM_DATABASE_URL belum diisi")
    return psycopg.connect(settings.database_url, connect_timeout=10)


def initialize(conn):
    from api.db_migrations import apply_migrations
    return apply_migrations(conn)


def _raw_row(record):
    row = [None if record.get(c) is None or pd.isna(record.get(c)) else str(record[c]).strip()
           for c in RAW_COLUMNS]
    # Match CSV epochs such as "1787136600.0" to the JSON integer epoch.
    row[0] = row[0] or ""
    row[1] = row[1] or ""
    try:
        epoch = Decimal(row[1])
        if epoch.is_finite():
            epoch_text = format(epoch, "f")
            row[1] = epoch_text.rstrip("0").rstrip(".") if "." in epoch_text else epoch_text
    except InvalidOperation:
        pass  # Historical malformed epochs are preserved; cleaning drops them.
    return row


def _ingest_batches(batches, mode="append"):
    if mode != "append":
        raise UploadValidationError("PostgreSQL hanya mendukung mode append; replace seluruh riwayat tidak didukung.")
    total = added = 0
    # One transaction per request/file: a bad later batch rolls back the entire import.
    with connect() as conn:
        initialize(conn)
        conn.execute("SELECT pg_advisory_xact_lock(72410612)")
        conn.execute("CREATE TEMP TABLE incoming_weather (LIKE weather_raw) ON COMMIT DROP")
        for records in batches:
            with conn.cursor() as cur:
                with cur.copy(f"COPY incoming_weather ({RAW_NAMES}) FROM STDIN") as copy:
                    for record in records:
                        copy.write_row(_raw_row(record))
                        total += 1
                cur.execute(f"INSERT INTO weather_raw ({RAW_NAMES}) SELECT {RAW_NAMES} FROM incoming_weather ON CONFLICT (stnname, utctime) DO NOTHING")
                added += cur.rowcount
                cur.execute("TRUNCATE incoming_weather")
    return {"mode": mode, "rows_in_upload": total, "rows_added": added, "rows_skipped": total - added}


def ingest_records(records, mode="append"):
    return _ingest_batches([records], mode)


def import_raw_csv(path, mode="append", chunk_size=100_000):
    validate_csv_header(path)
    def batches():
        for frame in pd.read_csv(path, dtype=str, chunksize=chunk_size, low_memory=False):
            frame.columns = frame.columns.str.strip()
            yield frame.to_dict("records")
    return _ingest_batches(batches(), mode)


def iter_raw_chunks(chunk_size=500_000):
    # Server cursor prevents loading millions of observations into RAM at once.
    with connect() as conn:
        with conn.cursor(name="weather_raw_chunks") as cur:
            cur.execute(f"SELECT {RAW_NAMES} FROM weather_raw ORDER BY stnname, utctime")
            while rows := cur.fetchmany(chunk_size):
                yield pd.DataFrame.from_records(rows, columns=RAW_COLUMNS)


def save_daily(frame):
    if frame.empty:
        raise ValueError("Hasil cleaning kosong; data harian lama tetap disimpan")
    with connect() as conn:
        initialize(conn)
        # DELETE + COPY in one transaction: readers see the complete old or new dataset.
        conn.execute("SELECT pg_advisory_xact_lock(72410613)")
        conn.execute("DELETE FROM weather_daily")
        with conn.cursor() as cur:
            with cur.copy(f"COPY weather_daily ({DAILY_NAMES}) FROM STDIN") as copy:
                for row in frame[DAILY_COLUMNS].itertuples(index=False, name=None):
                    values = [None if pd.isna(v) else v for v in row]
                    values[0] = str(values[0])
                    values[1] = pd.Timestamp(values[1]).date()
                    values[-1] = int(values[-1]) if values[-1] is not None else None
                    copy.write_row(values)


def load_daily():
    if settings.storage_backend == "csv":
        return pd.read_csv(settings.daily_csv_path, dtype={"stnname": str})
    with connect() as conn:
        rows = conn.execute(f"SELECT {DAILY_NAMES} FROM weather_daily ORDER BY stnname, date").fetchall()
    frame = pd.DataFrame.from_records(rows, columns=DAILY_COLUMNS)
    if frame.empty:
        raise ValueError("weather_daily kosong; jalankan cleaning atau impor CSV harian terlebih dahulu")
    # Keep the same date representation as CSV, including feature engineering callers.
    frame["date"] = frame["date"].astype(str)
    return frame


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Inisialisasi PostgreSQL / impor riwayat cuaca")
    parser.add_argument("--raw-csv", help="Impor CSV mentah lama; aman diulang, duplikat diabaikan")
    parser.add_argument("--daily-csv", help="Impor snapshot CSV harian untuk training/forecast")
    args = parser.parse_args()
    with connect() as conn:
        initialize(conn)
    if args.raw_csv:
        print(import_raw_csv(args.raw_csv))
    if args.daily_csv:
        frame = pd.read_csv(args.daily_csv, dtype={"stnname": str})
        save_daily(frame)
        print(f"Imported {len(frame):,} station-days")


if __name__ == "__main__":
    main()
