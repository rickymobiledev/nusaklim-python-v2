# ==============================================================================
# MANAJEMEN RETENSI FILE (MODEL BUNDLES & RUN LOGS) NUSAKLIM
# ==============================================================================
# Modul ini mengelola kebijakan retensi otomatis untuk model machine learning
# dan log eksekusi pipeline pada NusaKlim:
#   1. weather_model_bundle_*.joblib di folder models/
#   2. *.log di folder logs/runs/
#
# Proteksi:
#   File 'weather_model_latest.joblib' dan '*.backup.joblib' TIDAK AKAN PERNAH
#   dihapus oleh modul ini.
# ==============================================================================

import logging
import os
from pathlib import Path
from typing import Any

from api.config import settings

logger = logging.getLogger(__name__)


def format_size(size_bytes: int | float) -> str:
    """Konversi ukuran bytes ke string yang mudah dibaca pengguna (B, KB, MB, GB, TB)."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0 or unit == "TB":
            return f"{size:3.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024.0
    return f"{size:.1f} PB"


def is_protected_bundle(path: Path | str) -> bool:
    """Cek apakah file bundle model dilindungi dan tidak boleh dihapus."""
    name = Path(path).name.lower()
    if name == "weather_model_latest.joblib":
        return True
    if "backup" in name and name.endswith(".joblib"):
        return True
    if name.endswith(".backup.joblib") or ".backup." in name:
        return True
    return False


def cleanup_model_bundles(
    models_dir: str | Path | None = None,
    keep_count: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Mencari file weather_model_bundle_*.joblib di folder models.

    Urutkan berdasarkan mtime/nama terbaru.
    Pertahankan `keep_count` file terbaru, hapus sisanya.
    PENTING: JANGAN PERNAH menghapus weather_model_latest.joblib atau *.backup.joblib!

    Returns:
        dict: {"deleted": [...], "kept": [...], "freed_bytes": ...}
    """
    if models_dir is None:
        target_dir = Path(settings.model_bundle_path).parent if settings.model_bundle_path else Path(settings.base_dir) / "models"
    else:
        target_dir = Path(models_dir)

    if keep_count is None:
        keep_count = settings.max_model_bundles
    keep_count = max(0, int(keep_count))

    if not target_dir.exists() or not target_dir.is_dir():
        logger.warning(f"Direktori models tidak ditemukan: {target_dir}")
        return {"deleted": [], "kept": [], "freed_bytes": 0}

    # Cari file yang sesuai pola weather_model_bundle_*.joblib
    raw_files = [p for p in target_dir.glob("weather_model_bundle_*.joblib") if p.is_file()]

    # Filter proteksi file
    candidates = [p for p in raw_files if not is_protected_bundle(p)]

    # Urutkan berdasarkan mtime dan nama terbaru (reverse=True)
    candidates.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0, p.name), reverse=True)

    kept_files = candidates[:keep_count]
    to_delete = candidates[keep_count:]

    deleted: list[str] = []
    freed_bytes = 0

    for file_path in to_delete:
        try:
            file_size = file_path.stat().st_size
        except OSError:
            file_size = 0

        if dry_run:
            deleted.append(file_path.name)
            freed_bytes += file_size
        else:
            try:
                file_path.unlink()
                deleted.append(file_path.name)
                freed_bytes += file_size
                logger.info(f"Model bundle dihapus: {file_path.name} ({format_size(file_size)})")
            except OSError as e:
                logger.warning(f"Gagal menghapus bundle {file_path.name}: {e}")

    return {
        "deleted": deleted,
        "kept": [f.name for f in kept_files],
        "freed_bytes": freed_bytes,
    }


def cleanup_run_logs(
    runs_dir: str | Path | None = None,
    keep_count: int | None = None,
    dry_run: bool = False,
    exclude_files: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    """Mencari file *.log di logs/runs/.

    Urutkan berdasarkan mtime/nama terbaru.
    Pertahankan `keep_count` file terbaru, hapus sisanya.

    Returns:
        dict: {"deleted": [...], "kept": [...], "freed_bytes": ...}
    """
    if runs_dir is None:
        target_dir = Path(settings.log_dir) / "runs"
    else:
        target_dir = Path(runs_dir)

    if keep_count is None:
        keep_count = settings.max_run_logs
    keep_count = max(0, int(keep_count))

    if not target_dir.exists() or not target_dir.is_dir():
        logger.warning(f"Direktori logs/runs tidak ditemukan: {target_dir}")
        return {"deleted": [], "kept": [], "freed_bytes": 0}

    excluded = set(exclude_files or [])
    raw_files = [
        p for p in target_dir.glob("*.log")
        if p.is_file() and p.name not in excluded and str(p) not in excluded
    ]

    # Urutkan berdasarkan mtime dan nama terbaru (reverse=True)
    raw_files.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0, p.name), reverse=True)

    kept_files = raw_files[:keep_count]
    to_delete = raw_files[keep_count:]

    deleted: list[str] = []
    freed_bytes = 0

    for file_path in to_delete:
        try:
            file_size = file_path.stat().st_size
        except OSError:
            file_size = 0

        if dry_run:
            deleted.append(file_path.name)
            freed_bytes += file_size
        else:
            try:
                file_path.unlink()
                deleted.append(file_path.name)
                freed_bytes += file_size
                logger.info(f"Run log dihapus: {file_path.name} ({format_size(file_size)})")
            except OSError as e:
                logger.warning(f"Gagal menghapus log {file_path.name}: {e}")

    return {
        "deleted": deleted,
        "kept": [f.name for f in kept_files],
        "freed_bytes": freed_bytes,
    }


def run_all_retention(
    dry_run: bool = False,
    models_dir: str | Path | None = None,
    runs_dir: str | Path | None = None,
    max_bundles: int | None = None,
    max_logs: int | None = None,
    exclude_logs: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    """Menjalankan kedua pembersihan retensi: model bundles dan pipeline run logs."""
    models_res = cleanup_model_bundles(
        models_dir=models_dir,
        keep_count=max_bundles,
        dry_run=dry_run,
    )
    logs_res = cleanup_run_logs(
        runs_dir=runs_dir,
        keep_count=max_logs,
        dry_run=dry_run,
        exclude_files=exclude_logs,
    )
    return {
        "models": models_res,
        "logs": logs_res,
        "freed_bytes": models_res["freed_bytes"] + logs_res["freed_bytes"],
    }


def get_retention_status(
    models_dir: str | Path | None = None,
    runs_dir: str | Path | None = None,
    max_bundles: int | None = None,
    max_logs: int | None = None,
) -> dict[str, Any]:
    """Mengambil status pemakaian disk dan jumlah file retensi saat ini."""
    if models_dir is None:
        m_dir = Path(settings.model_bundle_path).parent if settings.model_bundle_path else Path(settings.base_dir) / "models"
    else:
        m_dir = Path(models_dir)

    if runs_dir is None:
        l_dir = Path(settings.log_dir) / "runs"
    else:
        l_dir = Path(runs_dir)

    mb_limit = settings.max_model_bundles if max_bundles is None else max(0, int(max_bundles))
    rl_limit = settings.max_run_logs if max_logs is None else max(0, int(max_logs))

    # Model bundles
    bundle_files = [p for p in m_dir.glob("weather_model_bundle_*.joblib") if p.is_file() and not is_protected_bundle(p)] if m_dir.is_dir() else []
    bundle_files.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0, p.name), reverse=True)
    bundles_total_bytes = sum(p.stat().st_size for p in bundle_files if p.exists())
    excess_bundles = bundle_files[mb_limit:]
    excess_bundles_bytes = sum(p.stat().st_size for p in excess_bundles if p.exists())

    # Protected models
    protected_files = [p for p in m_dir.glob("*.joblib") if p.is_file() and (p.name == "weather_model_latest.joblib" or is_protected_bundle(p))] if m_dir.is_dir() else []
    protected_total_bytes = sum(p.stat().st_size for p in protected_files if p.exists())

    # Run logs
    log_files = [p for p in l_dir.glob("*.log") if p.is_file()] if l_dir.is_dir() else []
    log_files.sort(key=lambda p: (p.stat().st_mtime if p.exists() else 0, p.name), reverse=True)
    logs_total_bytes = sum(p.stat().st_size for p in log_files if p.exists())
    excess_logs = log_files[rl_limit:]
    excess_logs_bytes = sum(p.stat().st_size for p in excess_logs if p.exists())

    return {
        "models": {
            "dir": str(m_dir),
            "bundle_count": len(bundle_files),
            "limit": mb_limit,
            "excess_count": len(excess_bundles),
            "total_bytes": bundles_total_bytes,
            "excess_bytes": excess_bundles_bytes,
            "protected_count": len(protected_files),
            "protected_bytes": protected_total_bytes,
            "protected_files": [p.name for p in protected_files],
            "newest_bundle": bundle_files[0].name if bundle_files else None,
            "oldest_bundle": bundle_files[-1].name if bundle_files else None,
        },
        "logs": {
            "dir": str(l_dir),
            "log_count": len(log_files),
            "limit": rl_limit,
            "excess_count": len(excess_logs),
            "total_bytes": logs_total_bytes,
            "excess_bytes": excess_logs_bytes,
            "newest_log": log_files[0].name if log_files else None,
            "oldest_log": log_files[-1].name if log_files else None,
        },
        "total_excess_bytes": excess_bundles_bytes + excess_logs_bytes,
    }
