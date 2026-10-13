# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "pydantic",
#     "pydantic-settings>=2.15.0",
# ]
# ///
"""
Script CLI Manajemen Retensi File NusaKlim (Model Bundles & Run Logs).

Menjalankan pembersihan berkas versi model lama di folder models/
dan berkas log eksekusi pipeline lama di folder logs/runs/ sesuai
dengan batas kebijakan retensi.

Proteksi Integritas:
- weather_model_latest.joblib dan *.backup.joblib TIDAK AKAN PERNAH dihapus.

Contoh Penggunaan:
    # Periksa status file dan potensi penghematan ruang disk:
    uv run python scripts/cleanup_retention.py --status

    # Simulasi pembersihan tanpa menghapus file (dry-run):
    uv run python scripts/cleanup_retention.py --dry-run

    # Jalankan pembersihan nyata dengan batas default (Settings):
    uv run python scripts/cleanup_retention.py

    # Jalankan pembersihan dengan batas retensi khusus:
    uv run python scripts/cleanup_retention.py --max-bundles 5 --max-logs 15
"""

import argparse
from pathlib import Path
import sys

# Pastikan root proyek ada di sys.path agar dapat mengimpor package `api`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.config import settings
from api.retention import (
    format_size,
    get_retention_status,
    run_all_retention,
)


def print_status(status: dict) -> None:
    """Cetak status retensi file ke terminal."""
    m_info = status["models"]
    l_info = status["logs"]

    print("=" * 72)
    print(" " * 18 + "NUSAKLIM FILE RETENTION STATUS")
    print("=" * 72)

    print("\n[1] MODEL BUNDLES (models/)")
    print(f"  Direktori           : {m_info['dir']}")
    print(f"  Total Bundle Versi  : {m_info['bundle_count']} file ({format_size(m_info['total_bytes'])})")
    print(f"  Batas Retensi       : {m_info['limit']} file")
    print(f"  File Berlebih       : {m_info['excess_count']} file (Potensi hemat: {format_size(m_info['excess_bytes'])})")
    print(f"  File Terlindungi    : {m_info['protected_count']} file ({', '.join(m_info['protected_files'])})")
    if m_info["newest_bundle"]:
        print(f"  Bundle Terbaru      : {m_info['newest_bundle']}")
        print(f"  Bundle Tertua       : {m_info['oldest_bundle']}")

    print("\n[2] RUN LOGS (logs/runs/)")
    print(f"  Direktori           : {l_info['dir']}")
    print(f"  Total File Log      : {l_info['log_count']} file ({format_size(l_info['total_bytes'])})")
    print(f"  Batas Retensi       : {l_info['limit']} file")
    print(f"  File Berlebih       : {l_info['excess_count']} file (Potensi hemat: {format_size(l_info['excess_bytes'])})")
    if l_info["newest_log"]:
        print(f"  Log Terbaru         : {l_info['newest_log']}")
        print(f"  Log Tertua          : {l_info['oldest_log']}")

    print("\n" + "-" * 72)
    print(f"TOTAL POTENSI RUANG DISK DIBEBASKAN : {format_size(status['total_excess_bytes'])}")
    print("=" * 72)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Manajemen Retensi File Model Bundles dan Pipeline Run Logs NusaKlim",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Cek status ukuran direktori, jumlah file, dan potensi pembersihan",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulasi pembersihan tanpa menghapus berkas apapun dari disk",
    )
    parser.add_argument(
        "--max-bundles",
        type=int,
        default=None,
        help=f"Maksimum bundle model berstempel waktu yang dipertahankan (default: {settings.max_model_bundles})",
    )
    parser.add_argument(
        "--max-logs",
        type=int,
        default=None,
        help=f"Maksimum file log eksekusi yang dipertahankan (default: {settings.max_run_logs})",
    )

    args = parser.parse_args(argv)

    if args.status:
        status = get_retention_status(
            max_bundles=args.max_bundles,
            max_logs=args.max_logs,
        )
        print_status(status)
        return

    mode_label = "[DRY-RUN / SIMULASI]" if args.dry_run else "[EKSEKUSI RETENSI]"
    print("=" * 72)
    print(f"  NUSAKLIM FILE RETENTION CLEANUP {mode_label}")
    print("=" * 72)

    result = run_all_retention(
        dry_run=args.dry_run,
        max_bundles=args.max_bundles,
        max_logs=args.max_logs,
    )

    m_res = result["models"]
    l_res = result["logs"]

    print("\n[1] MODEL BUNDLES:")
    print(f"  Dipertahankan ({len(m_res['kept'])}):")
    for fname in m_res["kept"][:5]:
        print(f"    - {fname}")
    if len(m_res["kept"]) > 5:
        print(f"    ... dan {len(m_res['kept']) - 5} lainnya")

    action_word = "Akan dihapus" if args.dry_run else "Berhasil dihapus"
    print(f"  {action_word} ({len(m_res['deleted'])}):")
    if m_res["deleted"]:
        for fname in m_res["deleted"]:
            print(f"    - {fname}")
    else:
        print("    (tidak ada - jumlah file masih di bawah batas retensi)")
    print(f"  Ruang dibebaskan: {format_size(m_res['freed_bytes'])}")

    print("\n[2] RUN LOGS:")
    print(f"  Dipertahankan ({len(l_res['kept'])}):")
    for fname in l_res["kept"][:5]:
        print(f"    - {fname}")
    if len(l_res["kept"]) > 5:
        print(f"    ... dan {len(l_res['kept']) - 5} lainnya")

    print(f"  {action_word} ({len(l_res['deleted'])}):")
    if l_res["deleted"]:
        for fname in l_res["deleted"]:
            print(f"    - {fname}")
    else:
        print("    (tidak ada - jumlah file masih di bawah batas retensi)")
    print(f"  Ruang dibebaskan: {format_size(l_res['freed_bytes'])}")

    print("\n" + "=" * 72)
    final_status = "Simulasi selesai (tidak ada file yang diubah)." if args.dry_run else "Pembersihan retensi selesai."
    print(f"Status: {final_status}")
    print(f"Total Ruang Dibebaskan: {format_size(result['freed_bytes'])}")
    print("=" * 72)


if __name__ == "__main__":
    main()
