# ==============================================================================
# ORKESTRATOR PIPELINE DATA BARU -> CLEANING -> AGREGASI -> RETRAIN (+ LOG)
# Dipakai oleh POST /ingest, /ingest/upload, /retrain, dan CLI:
#     python -m api.pipeline_runner            (proses semua file di data_raw/incoming/)
#
# Struktur folder (lihat api/config.py):
#   data_raw/nusaklim-aws-reduce.csv   master (gabungan seluruh data mentah)
#   data_raw/incoming/                 TARUH FILE BARU DI SINI
#   data_raw/archive/                  file yang sudah sukses di-merge (dipindah otomatis)
#   data_raw/rejected/                 file yang gagal validasi / merge (dipindah otomatis)
#   logs/pipeline.log                  ringkasan 1 baris per proses: SUKSES / GAGAL + penyebab
#   logs/pipeline_history.jsonl        versi mesin-terbaca dari log di atas
#   logs/runs/<task_id>.log            output lengkap proses cleaning & retrain (untuk debugging)
#
# Format nama file baru: nusaklim-aws-reduce_YYYYMMDD-YYYYMMDD.csv
#   (tanggal data pertama - terakhir di dalam file). Nama tidak dipakai untuk logika;
#   file apa pun berekstensi .csv di incoming/ diproses, nama di atas hanya konvensi agar
#   riwayat arsip mudah dibaca.
# ==============================================================================

import json
import os
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime

import joblib

from api.config import settings
from api.ingest_upload import merge_upload, validate_csv_header, UploadValidationError

NAME_PATTERN = re.compile(r"^nusaklim-aws-reduce_\d{8}-\d{8}\.csv$")
TAIL_LINES = 25

STAGE_HINTS = {
    "validasi": "Header/kolom CSV tidak sesuai format nusaklim-aws-reduce.csv. File dipindah ke data_raw/rejected/. "
                "Perbaiki file lalu taruh lagi di data_raw/incoming/.",
    "merge": "Gagal menggabungkan file ke master CSV. Master tidak diubah (merge baru ditulis di akhir). "
             "Cek disk penuh / file master sedang terbuka di program lain.",
    "cleaning": "process_nusaklim.py gagal (cleaning & agregasi harian). Retrain DIBATALKAN, model produksi lama tetap dipakai. "
                "Biasanya: data mentah rusak/format kolom berubah, atau RAM habis.",
    "retrain": "retrain_pipeline.py gagal. Model produksi lama (weather_model_latest.joblib) tetap dipakai. "
               "Biasanya: data harian terlalu sedikit, kolom hilang, atau RAM habis.",
    "verifikasi": "Retrain selesai tanpa error tetapi file model tidak diperbarui / tidak bisa dibaca. Model lama tetap dipakai.",
    "reload": "Model baru sudah tersimpan tetapi gagal dimuat ulang ke memori API. Restart service API.",
}


class StageError(Exception):
    def __init__(self, stage: str, reason: str, detail: str = ""):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.detail = detail


def _paths():
    return {
        "incoming": settings.incoming_dir,
        "archive": settings.archive_dir,
        "rejected": settings.rejected_dir,
        "logs": settings.log_dir,
        "runs": os.path.join(settings.log_dir, "runs"),
    }


def _ensure_dirs():
    for p in _paths().values():
        os.makedirs(p, exist_ok=True)


def _write_log(entry: dict):
    """1 baris ringkas di pipeline.log + 1 baris JSON di pipeline_history.jsonl."""
    log_dir = _paths()["logs"]
    ts = entry["timestamp"]
    if entry["status"] == "SUKSES":
        extra = (f"file={entry.get('files') or '-'} | +{entry.get('rows_added', 0):,} baris raw | "
                 f"data harian s/d {entry.get('max_train_date', '?')} | {entry.get('duration_sec', 0):.0f}s")
        if entry.get("metrics_note"):
            extra += f" | {entry['metrics_note']}"
    else:
        extra = (f"tahap={entry['stage']} | penyebab={entry['reason']} | {entry['hint']} | "
                 f"detail lengkap: {entry.get('run_log', '-')}")
    line = f"{ts} | {entry['task_id']} | {entry['status']:<6} | {extra}\n"
    with open(os.path.join(log_dir, "pipeline.log"), "a", encoding="utf-8") as f:
        f.write(line)
    with open(os.path.join(log_dir, "pipeline_history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[MLOps] {line.strip()}")


def _tail(path: str, n: int = TAIL_LINES) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return "".join(f.readlines()[-n:]).strip()
    except OSError:
        return ""


def _run_script(stage: str, script: str, run_log: str):
    """Jalankan script Python sebagai subprocess, output ditulis ke run_log, cek exit code."""
    if not os.path.exists(script):
        raise StageError(stage, f"script tidak ditemukan: {script}")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    with open(run_log, "ab") as out:
        out.write(f"\n===== [{stage}] {datetime.now():%Y-%m-%d %H:%M:%S} python {script} =====\n".encode("utf-8"))
        out.flush()
        ret = subprocess.run([sys.executable, script], cwd=settings.base_dir, stdout=out,
                             stderr=subprocess.STDOUT, env=env).returncode
    if ret != 0:
        tail = _tail(run_log)
        last_line = tail.splitlines()[-1] if tail else f"exit code {ret}"
        raise StageError(stage, f"exit code {ret}: {last_line}", tail)


def _archive_name(src: str, task_id: str) -> str:
    base = os.path.basename(src)
    if NAME_PATTERN.match(base):
        return base
    return f"nusaklim-aws-reduce_{task_id}.csv"


def _move_unique(src: str, dest_dir: str, name: str) -> str:
    dest = os.path.join(dest_dir, name)
    if os.path.exists(dest):
        stem, ext = os.path.splitext(name)
        dest = os.path.join(dest_dir, f"{stem}__{datetime.now():%H%M%S}{ext}")
    os.replace(src, dest)
    return dest


def _collect_sources(extra_files: list[tuple[str, str]] | None):
    """Daftar (path, mode) yang akan di-merge: file upload API + semua .csv di incoming/."""
    sources = list(extra_files or [])
    incoming = _paths()["incoming"]
    for name in sorted(os.listdir(incoming)):
        if name.lower().endswith(".csv"):
            sources.append((os.path.join(incoming, name), "append"))
    return sources


def _verify_new_bundle(started_at: float) -> dict:
    path = settings.model_bundle_path
    if not os.path.exists(path) or os.path.getmtime(path) < started_at:
        raise StageError("verifikasi", "weather_model_latest.joblib tidak diperbarui oleh retrain")
    try:
        bundle = joblib.load(path)
        metrics = bundle["metrics"]
        max_date = bundle["max_train_date"]
    except Exception as e:
        raise StageError("verifikasi", f"model baru tidak bisa dibaca: {e}")
    t1 = metrics.get("temp_avg_h1", {}).get("MAE")
    r7 = metrics.get("rainfall_total_mm_h7", {}).get("MAE")
    note = f"MAE suhu H+1={t1}, hujan H+7={r7}" if t1 is not None else ""
    return {"max_train_date": max_date, "metrics_note": note, "metrics": {
        "temp_avg_h1_MAE": t1, "rainfall_total_mm_h7_MAE": r7, "n_models": len(bundle.get("models", {}))}}


def run_pipeline(task_id: str, trigger: str, extra_files: list[tuple[str, str]] | None = None,
                 retrain_only: bool = False, on_success=None) -> bool:
    """Jalankan tahap: merge file baru -> cleaning+agregasi -> retrain -> verifikasi -> reload.
    Selalu menulis 1 entri SUKSES/GAGAL ke logs/pipeline.log. Return True kalau sukses."""
    _ensure_dirs()
    run_log = os.path.join(_paths()["runs"], f"{task_id}.log")
    started = time.time()
    entry = {"task_id": task_id, "trigger": trigger, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "run_log": run_log, "files": "", "rows_added": 0}
    archived: list[str] = []
    try:
        if not retrain_only:
            sources = _collect_sources(extra_files)
            for path, mode in sources:
                base = os.path.basename(path)
                try:
                    validate_csv_header(path)
                except UploadValidationError as e:
                    _move_unique(path, _paths()["rejected"], base)
                    raise StageError("validasi", f"{base}: {e}")
                try:
                    stats = merge_upload(path, settings.raw_csv_path, mode, keep_source=True)
                except Exception as e:
                    _move_unique(path, _paths()["rejected"], base)
                    raise StageError("merge", f"{base}: {e}", traceback.format_exc())
                entry["rows_added"] += stats["rows_added"]
                archived.append(os.path.basename(_move_unique(path, _paths()["archive"], _archive_name(path, task_id))))
                with open(run_log, "a", encoding="utf-8") as f:
                    f.write(f"[merge] {base}: {stats}\n")
            entry["files"] = ", ".join(archived) or "(tidak ada file baru - proses ulang master)"
            _run_script("cleaning", os.path.join(settings.base_dir, "process_nusaklim.py"), run_log)
        else:
            entry["files"] = "(retrain dari data harian yang sudah ada)"

        t_retrain = time.time()
        _run_script("retrain", os.path.join(settings.base_dir, "retrain_pipeline.py"), run_log)
        entry.update(_verify_new_bundle(t_retrain))

        if on_success:
            try:
                on_success()
            except Exception as e:
                raise StageError("reload", str(e), traceback.format_exc())

        entry.update(status="SUKSES", duration_sec=time.time() - started)
        _write_log(entry)
        return True
    except StageError as e:
        entry.update(status="GAGAL", stage=e.stage, reason=e.reason, hint=STAGE_HINTS.get(e.stage, ""),
                     error_tail=e.detail, duration_sec=time.time() - started)
    except Exception as e:  # kegagalan tak terduga
        entry.update(status="GAGAL", stage="tak-terduga", reason=f"{type(e).__name__}: {e}",
                     hint="Error tidak terduga di orkestrator pipeline.", error_tail=traceback.format_exc(),
                     duration_sec=time.time() - started)
    with open(run_log, "a", encoding="utf-8") as f:
        f.write(f"\n===== GAGAL di tahap {entry['stage']} =====\n{entry['reason']}\n{entry.get('error_tail', '')}\n")
    _write_log(entry)
    return False


if __name__ == "__main__":
    ok = run_pipeline(f"ingest-cli-{datetime.now():%Y%m%d%H%M%S}", trigger="cli")
    sys.exit(0 if ok else 1)
