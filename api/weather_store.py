"""PostgreSQL storage for raw observations and the cleaned daily dataset.

Raw sensor values stay as text to preserve historical error markers for QC.
The observation key is (stnname, utctime); append preserves the first reading.
"""
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

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
STATION_COLUMNS = [
    "id", "name", "brand", "latitude", "longitude", "created_at", "updated_at",
    "company_id", "company_code", "company_name", "company_image_url",
    "company_created_at", "company_updated_at",
]
RAW_NAMES = ", ".join(RAW_COLUMNS)
DAILY_NAMES = ", ".join(DAILY_COLUMNS)
STATION_NAMES = ", ".join(STATION_COLUMNS)


def connect():
    if not settings.database_url:
        raise ValueError("NUSAKLIM_DATABASE_URL belum diisi")
    return psycopg.connect(settings.database_url, connect_timeout=10)


def connect_with_retry():
    """connect() yang mengulang bila PostgreSQL/pgbouncer belum siap (mis. baru restart).

    Hanya error koneksi (OperationalError, termasuk ConnectionTimeout) yang diulang;
    delay berlipat ganda per percobaan.
    """
    attempts = max(1, settings.db_connect_retries)
    delay = settings.db_connect_retry_delay
    for attempt in range(1, attempts + 1):
        try:
            return connect()
        except psycopg.OperationalError as exc:
            if attempt == attempts:
                raise
            print(f"[DB] Koneksi gagal ({attempt}/{attempts}): {exc}. "
                  f"Ulangi dalam {delay:g}s...", flush=True)
            time.sleep(delay)
            delay *= 2


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


def _station_row(record):
    row = []
    for c in STATION_COLUMNS:
        val = record.get(c)
        if val is None or pd.isna(val):
            row.append(None)
        elif c in ("latitude", "longitude"):
            try:
                row.append(float(val))
            except (ValueError, TypeError):
                row.append(None)
        else:
            s = str(val).strip()
            row.append(s if s else None)
    if not row[0]:
        return None
    if not row[1]:
        row[1] = f"Station {row[0]}"
    return tuple(row)


def import_stations_csv(path=None):
    csv_path = Path(path if path is not None else settings.device_csv_path).resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"File CSV stasiun tidak ditemukan: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)
    df.columns = df.columns.str.strip()
    missing = {"id", "name"} - set(df.columns)
    if missing:
        raise ValueError("Kolom CSV stasiun tidak lengkap: " + ", ".join(sorted(missing)))

    rows = []
    for record in df.to_dict("records"):
        r = _station_row(record)
        if r is not None:
            rows.append(r)

    with connect() as conn:
        initialize(conn)
        conn.execute("SELECT pg_advisory_xact_lock(72410615)")
        query = f"""
            INSERT INTO weather_stations ({STATION_NAMES})
            VALUES ({', '.join(['%s'] * len(STATION_COLUMNS))})
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                updated_at = EXCLUDED.updated_at,
                company_id = EXCLUDED.company_id,
                company_code = EXCLUDED.company_code,
                company_name = EXCLUDED.company_name,
                company_image_url = EXCLUDED.company_image_url,
                company_created_at = EXCLUDED.company_created_at,
                company_updated_at = EXCLUDED.company_updated_at;
        """
        with conn.cursor() as cur:
            cur.executemany(query, rows)
    return {"rows_in_file": len(df), "stations_saved": len(rows)}


def ensure_stations_exist(conn, station_ids):
    if not station_ids:
        return
    cleaned = []
    seen = set()
    for sid in station_ids:
        if sid is None or pd.isna(sid):
            continue
        s = str(sid).strip()
        if s and s not in seen:
            seen.add(s)
            cleaned.append((s, f"Station {s}"))
    if not cleaned:
        return
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO weather_stations (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            cleaned,
        )


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
            station_ids = [r.get("stnname") if hasattr(r, "get") else getattr(r, "stnname", None)
                           for r in records]
            ensure_stations_exist(conn, station_ids)
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
        if "stnname" in frame.columns:
            ensure_stations_exist(conn, frame["stnname"].dropna().unique())
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
    with connect_with_retry() as conn:
        rows = conn.execute(f"SELECT {DAILY_NAMES} FROM weather_daily ORDER BY stnname, date").fetchall()
    frame = pd.DataFrame.from_records(rows, columns=DAILY_COLUMNS)
    if frame.empty:
        raise ValueError("weather_daily kosong; jalankan cleaning atau impor CSV harian terlebih dahulu")
    # Keep the same date representation as CSV, including feature engineering callers.
    frame["date"] = frame["date"].astype(str)
    return frame


def load_stations(conn=None):
    if conn is not None:
        rows = conn.execute(f"SELECT {STATION_NAMES} FROM weather_stations ORDER BY id").fetchall()
        return pd.DataFrame.from_records(rows, columns=STATION_COLUMNS)
    if settings.storage_backend == "csv":
        csv_path = Path(settings.device_csv_path)
        if not csv_path.is_file():
            return pd.DataFrame(columns=STATION_COLUMNS)
        df = pd.read_csv(csv_path, dtype=str)
        df.columns = df.columns.str.strip()
        for col in STATION_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[STATION_COLUMNS]
    with connect() as conn_obj:
        rows = conn_obj.execute(f"SELECT {STATION_NAMES} FROM weather_stations ORDER BY id").fetchall()
    return pd.DataFrame.from_records(rows, columns=STATION_COLUMNS)


EDITABLE_STATION_FIELDS = ("name", "brand", "latitude", "longitude", "company_code", "company_name")


class StationExistsError(Exception):
    pass


class StationNotFoundError(Exception):
    pass


def _now_text():
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _write_stations_csv(df):
    csv_path = Path(settings.device_csv_path)
    tmp = csv_path.with_suffix(".csv.tmp")
    df[STATION_COLUMNS].to_csv(tmp, index=False)
    tmp.replace(csv_path)


def create_station(station_id, fields):
    """Tambah stasiun baru. StationExistsError kalau id sudah terdaftar."""
    sid = str(station_id).strip()
    now = _now_text()
    record = {c: fields.get(c) for c in EDITABLE_STATION_FIELDS}
    record.update(id=sid, created_at=now, updated_at=now)
    row = _station_row(record)
    if settings.storage_backend == "csv":
        df = load_stations()
        if sid in set(df["id"].astype(str).str.strip()):
            raise StationExistsError(sid)
        new = pd.DataFrame([dict(zip(STATION_COLUMNS, row))])
        _write_stations_csv(pd.concat([df, new], ignore_index=True))
        return
    with connect() as conn:
        initialize(conn)
        cur = conn.execute(
            f"INSERT INTO weather_stations ({STATION_NAMES}) VALUES ({', '.join(['%s'] * len(STATION_COLUMNS))}) "
            "ON CONFLICT (id) DO NOTHING", row)
        if cur.rowcount == 0:
            raise StationExistsError(sid)


def update_station(station_id, changes):
    """Ubah sebagian field stasiun (hanya key di `changes`). StationNotFoundError kalau id tidak ada."""
    sid = str(station_id).strip()
    changes = {k: v for k, v in changes.items() if k in EDITABLE_STATION_FIELDS}
    now = _now_text()
    if settings.storage_backend == "csv":
        df = load_stations()
        mask = df["id"].astype(str).str.strip() == sid
        if not mask.any():
            raise StationNotFoundError(sid)
        for k, v in changes.items():
            df[k] = df[k].astype(object)
            df.loc[mask, k] = v
        df.loc[mask, "updated_at"] = now
        _write_stations_csv(df)
        return
    sets = ", ".join(f"{k} = %s" for k in changes) + (", " if changes else "") + "updated_at = %s"
    with connect() as conn:
        initialize(conn)
        cur = conn.execute(f"UPDATE weather_stations SET {sets} WHERE id = %s",
                           [*changes.values(), now, sid])
        if cur.rowcount == 0:
            raise StationNotFoundError(sid)


class StationInUseError(Exception):
    pass


def delete_station(station_id):
    """Hapus stasiun dari registry. Ditolak (StationInUseError) kalau stasiun masih punya data
    observasi, supaya riwayat cuaca tidak yatim/hilang. StationNotFoundError kalau id tidak ada."""
    sid = str(station_id).strip()
    if settings.storage_backend == "csv":
        df = load_stations()
        mask = df["id"].astype(str).str.strip() == sid
        if not mask.any():
            raise StationNotFoundError(sid)
        daily_path = Path(settings.daily_csv_path)
        if daily_path.is_file():
            stn = pd.read_csv(daily_path, usecols=["stnname"], dtype=str)["stnname"].str.strip()
            if (stn == sid).any():
                raise StationInUseError(sid)
        _write_stations_csv(df[~mask])
        return
    with connect() as conn:
        initialize(conn)
        try:
            cur = conn.execute("DELETE FROM weather_stations WHERE id = %s", [sid])
        except psycopg.errors.ForeignKeyViolation:
            raise StationInUseError(sid)
        if cur.rowcount == 0:
            raise StationNotFoundError(sid)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Inisialisasi PostgreSQL / impor riwayat cuaca")
    parser.add_argument("--device-csv", help="Impor CSV stasiun/device ke weather_stations")
    parser.add_argument("--raw-csv", help="Impor CSV mentah lama; aman diulang, duplikat diabaikan")
    parser.add_argument("--daily-csv", help="Impor snapshot CSV harian untuk training/forecast")
    args = parser.parse_args()
    with connect() as conn:
        initialize(conn)
    if args.device_csv:
        print(import_stations_csv(args.device_csv))
    if args.raw_csv:
        print(import_raw_csv(args.raw_csv))
    if args.daily_csv:
        frame = pd.read_csv(args.daily_csv, dtype={"stnname": str})
        save_daily(frame)
        print(f"Imported {len(frame):,} station-days")


if __name__ == "__main__":
    main()
