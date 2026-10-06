# ==============================================================================
# UPLOAD DATA MENTAH BARU (CSV) -> MERGE KE nusaklim-aws-reduce.csv
# Dipakai oleh POST /ingest/upload. Merge dilakukan streaming (chunk) karena file
# raw berukuran > 1 GB / belasan juta baris.
# ==============================================================================

import os
import shutil
import pandas as pd

REQUIRED_COLUMNS = ["stnname", "utctime", "tempout", "humout", "windspd", "winddir", "bar", "solar", "rain15"]
CHUNK_ROWS = 500_000


class UploadValidationError(ValueError):
    pass


def validate_csv_header(path: str) -> list[str]:
    """Pastikan baris pertama adalah header CSV dengan semua kolom wajib. Return daftar kolom."""
    try:
        header = pd.read_csv(path, nrows=0).columns.tolist()
    except Exception as e:
        raise UploadValidationError(f"File bukan CSV yang valid: {e}")
    header = [c.strip() for c in header]
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        raise UploadValidationError(
            f"Kolom wajib tidak ada di header CSV: {missing}. Header yang diterima: {header}"
        )
    return header


def _station_max_utctime(raw_path: str) -> pd.Series:
    """Epoch (detik) terbaru per stasiun yang sudah ada di file raw."""
    partial = []
    for chunk in pd.read_csv(raw_path, usecols=["stnname", "utctime"], chunksize=CHUNK_ROWS, low_memory=False):
        chunk["stnname"] = chunk["stnname"].astype(str).str.strip()
        chunk["utctime"] = pd.to_numeric(chunk["utctime"], errors="coerce")
        partial.append(chunk.dropna(subset=["utctime"]).groupby("stnname")["utctime"].max())
    if not partial:
        return pd.Series(dtype="float64")
    return pd.concat(partial).groupby(level=0).max()


def merge_upload(staging_path: str, raw_path: str, mode: str, keep_source: bool = False) -> dict:
    """Gabungkan file upload ke file raw.

    mode="replace": file upload menggantikan seluruh file raw (raw lama disimpan sebagai .bak).
    mode="append" : hanya baris yang lebih baru dari data terakhir tiap stasiun yang ditambahkan,
                    sehingga upload ulang / data yang tumpang tindih tidak menggandakan baris.
    keep_source   : True = file sumber tidak dihapus/dipindah (pemanggil yang mengarsipkan).
    """
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    if mode == "replace" or not os.path.exists(raw_path):
        if os.path.exists(raw_path):
            os.replace(raw_path, raw_path + ".bak")
        if keep_source:
            shutil.copyfile(staging_path, raw_path)
        else:
            os.replace(staging_path, raw_path)
        rows = sum(len(c) for c in pd.read_csv(raw_path, usecols=["stnname"], chunksize=CHUNK_ROWS))
        return {"mode": "replace", "rows_in_upload": rows, "rows_added": rows, "rows_skipped": 0}

    raw_header = [c.strip() for c in pd.read_csv(raw_path, nrows=0).columns]
    max_per_stn = _station_max_utctime(raw_path)

    filtered_path = staging_path + ".filtered"
    seen_in_upload = 0
    added = 0
    try:
        for chunk in pd.read_csv(staging_path, chunksize=CHUNK_ROWS, low_memory=False, dtype=str):
            chunk.columns = [c.strip() for c in chunk.columns]
            seen_in_upload += len(chunk)
            chunk["stnname"] = chunk["stnname"].astype(str).str.strip()
            utc = pd.to_numeric(chunk["utctime"], errors="coerce")
            keep = utc.notna() & (utc > chunk["stnname"].map(max_per_stn).fillna(-1))
            chunk = chunk[keep].drop_duplicates(subset=["stnname", "utctime"])
            if chunk.empty:
                continue
            chunk = chunk.reindex(columns=raw_header)
            chunk.to_csv(filtered_path, mode="a", header=False, index=False)
            added += len(chunk)

        if added:
            with open(raw_path, "rb+") as f:
                f.seek(-1, os.SEEK_END)
                needs_newline = f.read(1) not in (b"\n", b"\r")
            with open(raw_path, "ab") as dst, open(filtered_path, "rb") as src:
                if needs_newline:
                    dst.write(b"\n")
                shutil.copyfileobj(src, dst, length=1024 * 1024)
    finally:
        for p in (filtered_path,) if keep_source else (filtered_path, staging_path):
            if os.path.exists(p):
                os.remove(p)

    return {"mode": "append", "rows_in_upload": seen_in_upload, "rows_added": added,
            "rows_skipped": seen_in_upload - added}
