# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "pandas",
#     "numpy",
#     "scikit-learn",
#     "lightgbm",
#     "joblib",
#     "psycopg[binary]>=3.2,<4",
#     "python-dotenv",
#     "pydantic",
#     "pydantic-settings>=2.15.0",
# ]
# ///
"""
Script Training Model NusaKlim Berdasarkan Data PostgreSQL.

Melakukan alur kerja lengkap (MLOps Pipeline) berbasis PostgreSQL:
1. Memeriksa ketersediaan dan integritas data di database PostgreSQL.
2. (Opsional / Otomatis jika kosong) Cleaning & Agregasi data mentah
   dari tabel `weather_raw` ke tabel `weather_daily`.
3. Feature Engineering (29 fitur fisis, lag, kalender, dan persistence).
4. Melatih 49 model prediksi cuaca (7 variabel x 7 horizon H+1 s/d H+7)
   menggunakan algoritma champion (LightGBM, Ridge, Random Forest).
5. Menyimpan model berstempel waktu (versioned) dan model produksi latest.
6. Menjalankan uji inferensi ramalan 7 hari untuk memverifikasi hasil.

Contoh Penggunaan:
    # Jalankan training dari PostgreSQL (otomatis agregasi jika daily kosong):
    uv run python scripts/train_postgres.py

    # Hanya jalankan cleaning & agregasi harian dari weather_raw:
    uv run python scripts/train_postgres.py --clean-only

    # Hanya jalankan training (menggunakan weather_daily yang sudah ada):
    uv run python scripts/train_postgres.py --train-only

    # Paksa agregasi ulang dari weather_raw lalu latih model:
    uv run python scripts/train_postgres.py --force-clean

    # Lihat status kesiapan data dan model saat ini:
    uv run python scripts/train_postgres.py --status
"""

import argparse
import os
from pathlib import Path
import re
import sys
import time

# Pastikan root proyek ada di sys.path agar modul `api`, `process_nusaklim`,
# dan `retrain_pipeline` dapat diimpor dengan benar
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import joblib
import pandas as pd

from api.config import settings
from api import weather_store as store


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


def get_db_stats() -> dict[str, int]:
    """Mengambil jumlah baris tabel PostgreSQL terkini."""
    with store.connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM weather_stations")
        stations = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM weather_raw")
        raw = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM weather_daily")
        daily = cur.fetchone()[0]
    return {"stations": stations, "raw": raw, "daily": daily}


def get_latest_model_info() -> dict | None:
    """Membaca metadata dari bundle model terkini jika file tersedia."""
    bundle_path = Path(settings.model_bundle_path)
    if not bundle_path.is_file():
        return None
    try:
        bundle = joblib.load(bundle_path)
        return {
            "path": str(bundle_path),
            "timestamp": bundle.get("timestamp", "unknown"),
            "models_count": len(bundle.get("models", {})),
            "train_samples": bundle.get("train_samples", 0),
            "max_train_date": bundle.get("max_train_date", "unknown"),
            "split_date": bundle.get("split_date", "unknown"),
            "metrics": bundle.get("metrics", {}),
        }
    except Exception as e:
        return {"path": str(bundle_path), "error": str(e)}


def update_env_storage_backend(env_path: Path) -> bool:
    """Memperbarui NUSAKLIM_STORAGE_BACKEND=postgres di file .env."""
    if not env_path.is_file():
        return False
    try:
        content = env_path.read_text(encoding="utf-8")
        if re.search(r"^NUSAKLIM_STORAGE_BACKEND\s*=.*$", content, flags=re.MULTILINE):
            new_content = re.sub(
                r"^NUSAKLIM_STORAGE_BACKEND\s*=.*$",
                "NUSAKLIM_STORAGE_BACKEND=postgres",
                content,
                flags=re.MULTILINE,
            )
        else:
            new_content = content + "\nNUSAKLIM_STORAGE_BACKEND=postgres\n"
        env_path.write_text(new_content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"[Warning] Gagal memperbarui .env: {e}", file=sys.stderr)
        return False


def run_cleaning_stage(chunk_size: int = 500_000) -> pd.DataFrame:
    """Menjalankan cleaning dan agregasi harian dari PostgreSQL weather_raw ke weather_daily."""
    print("=" * 70)
    print("TAHAP 1: CLEANING & AGREGASI HARIAN DARI POSTGRESQL (weather_raw -> weather_daily)")
    print("=" * 70)
    print(f"Sumber data : PostgreSQL weather_raw")
    print(f"Target data : PostgreSQL weather_daily")
    print(f"Batch chunk : {format_number(chunk_size)} baris per batch")
    print("-" * 70)

    start_time = time.time()
    from process_nusaklim import run_nusaklim_pipeline

    df_daily = run_nusaklim_pipeline(
        storage_backend="postgres",
        chunk_size=chunk_size,
    )
    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"[OK] Cleaning & agregasi selesai dalam {format_duration(elapsed)}.")
    print(f"     Total tersimpan di weather_daily: {format_number(len(df_daily))} stasiun-hari.")
    return df_daily


def run_training_stage(
    test_days: int = 30,
    station_test: str = "222",
) -> dict:
    """Menjalankan proses retraining machine learning dari tabel PostgreSQL weather_daily."""
    print("=" * 70)
    print("TAHAP 2: TRAINING MODEL MACHINE LEARNING DARI POSTGRESQL (weather_daily)")
    print("=" * 70)
    print(f"Evaluasi Out-of-Time: {test_days} hari terakhir")
    print(f"Stasiun Uji Inferensi: Stasiun {station_test}")
    print("-" * 70)

    start_time = time.time()
    settings.storage_backend = "postgres"
    os.environ["NUSAKLIM_STORAGE_BACKEND"] = "postgres"
    from retrain_pipeline import (
        build_features_and_targets,
        train_and_evaluate,
        generate_7day_forecast,
        load_daily,
    )

    df_daily = load_daily()
    total_days = len(df_daily)
    unique_stations = df_daily["stnname"].nunique()
    print(f"[Info] Berhasil memuat {format_number(total_days)} baris data harian dari {unique_stations} stasiun.")

    print("\n[MLOps] Membangun fitur (Feature Engineering)...")
    df_featured, feature_cols, target_cols, target_types = build_features_and_targets(df_daily)
    print(f"[MLOps] Fitur yang dihasilkan: {len(feature_cols)} fitur.")
    print(f"[MLOps] Target prediksi      : {len(target_cols)} target (7 variabel x 7 horizon H+1 s/d H+7).")

    print("\n[MLOps] Melatih model champion & evaluasi metrik...")
    model_bundle = train_and_evaluate(
        df_featured,
        feature_cols,
        target_cols,
        target_types,
        test_days=test_days,
    )

    # Uji inferensi 7-hari pada stasiun contoh
    try:
        available_stations = df_featured["stnname"].astype(str).unique().tolist()
        target_stn = station_test if station_test in available_stations else (available_stations[0] if available_stations else None)
        if target_stn:
            print(f"\n[MLOps] Pengujian inferensi 7 hari pada Stasiun {target_stn}:")
            generate_7day_forecast(station_id=target_stn, df_featured=df_featured)
    except Exception as e:
        print(f"[Warning] Gagal menjalankan uji inferensi stasiun {station_test}: {e}")

    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"[OK] Training model selesai dalam {format_duration(elapsed)}.")
    return model_bundle


def print_status():
    """Menampilkan status PostgreSQL dan info bundle model."""
    print("=" * 70)
    print("STATUS DATA POSTGRESQL & MODEL NUSAKLIM")
    print("=" * 70)
    try:
        stats = get_db_stats()
        print(f"Koneksi PostgreSQL: OK (Target: {settings.database_url.split('@')[-1] if '@' in settings.database_url else '(tersedia)'})")
        print(f"  - weather_stations : {format_number(stats['stations'])} stasiun")
        print(f"  - weather_raw      : {format_number(stats['raw'])} pembacaan sensor")
        print(f"  - weather_daily    : {format_number(stats['daily'])} stasiun-hari")
    except Exception as e:
        print(f"Koneksi PostgreSQL: GAGAL ({e})")
        stats = None

    print("-" * 70)
    model_info = get_latest_model_info()
    if model_info and "error" not in model_info:
        print("Model Produksi Terkini (weather_model_latest.joblib):")
        print(f"  - File Path       : {model_info['path']}")
        print(f"  - Versi Timestamp : {model_info['timestamp']}")
        print(f"  - Jumlah Submodel : {model_info['models_count']} model")
        print(f"  - Sampel Training : {format_number(model_info['train_samples'])} baris")
        print(f"  - Data Terakhir   : {model_info['max_train_date']}")
        print(f"  - Split Validasi  : {model_info['split_date']}")
        metrics = model_info.get("metrics", {})
        t1 = metrics.get("temp_avg_h1", {}).get("MAE")
        r7 = metrics.get("rainfall_total_mm_h7", {}).get("MAE")
        if t1 is not None:
            print(f"  - MAE Sampel      : Suhu H+1 = {t1:.2f}°C, Curah Hujan H+7 = {r7:.2f} mm")
    elif model_info and "error" in model_info:
        print(f"Model Produksi Terkini: Error saat membaca ({model_info['error']})")
    else:
        print("Model Produksi Terkini: Belum ada file model di models/weather_model_latest.joblib")

    print("-" * 70)
    print("Rekomendasi:")
    if stats:
        if stats["raw"] == 0:
            print("  [!] weather_raw kosong. Jalankan 'scripts/import_data.py' terlebih dahulu.")
        elif stats["daily"] == 0:
            print("  [!] weather_daily masih kosong. Jalankan 'scripts/train_postgres.py' (otomatis cleaning).")
        else:
            print("  [OK] Data PostgreSQL siap. Anda dapat langsung menjalankan training.")
    print("=" * 70)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="NusaKlim - Train Data Cuaca Machine Learning Berdasarkan PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  uv run python scripts/train_postgres.py
  uv run python scripts/train_postgres.py --train-only
  uv run python scripts/train_postgres.py --clean-only
  uv run python scripts/train_postgres.py --force-clean
  uv run python scripts/train_postgres.py --status
        """,
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Tampilkan status data PostgreSQL dan model terkini tanpa melatih",
    )
    parser.add_argument(
        "--train-only",
        action="store_true",
        help="Hanya jalankan training (menggunakan weather_daily yang sudah ada di PostgreSQL)",
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Hanya jalankan cleaning & agregasi harian (weather_raw -> weather_daily) tanpa training",
    )
    parser.add_argument(
        "--clean",
        "--force-clean",
        dest="force_clean",
        action="store_true",
        help="Paksa jalankan ulang cleaning & agregasi harian meskipun weather_daily sudah terisi",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500_000,
        help="Ukuran chunk pemrosesan saat membaca weather_raw (default: 500000 baris)",
    )
    parser.add_argument(
        "--test-days",
        type=int,
        default=30,
        help="Jumlah hari untuk split validasi out-of-time (default: 30 hari)",
    )
    parser.add_argument(
        "--station-test",
        type=str,
        default="222",
        help="ID stasiun untuk uji inferensi 7 hari setelah training selesai (default: 222)",
    )
    parser.add_argument(
        "--set-active",
        action="store_true",
        help="Otomatis aktifkan NUSAKLIM_STORAGE_BACKEND=postgres di file .env setelah sukses",
    )

    args = parser.parse_args(argv)

    if args.status:
        print_status()
        return 0

    if args.train_only and (args.clean_only or args.force_clean):
        parser.error("Tidak dapat menggabungkan --train-only dengan opsi cleaning.")

    if not settings.database_url:
        print("[ERROR] NUSAKLIM_DATABASE_URL belum dikonfigurasi di .env!", file=sys.stderr)
        return 1

    try:
        stats = get_db_stats()
    except Exception as e:
        print(f"[ERROR] Gagal terhubung ke PostgreSQL: {e}", file=sys.stderr)
        return 1

    print("=" * 70)
    print("NUSAKLIM POSTGRESQL MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 70)
    print(f"Root Proyek    : {PROJECT_ROOT}")
    print(f"Database Target: {settings.database_url.split('@')[-1] if '@' in settings.database_url else '(tersedia)'}")
    print(f"Data Mentah    : {format_number(stats['raw'])} baris di weather_raw")
    print(f"Data Harian    : {format_number(stats['daily'])} baris di weather_daily")
    print("=" * 70)

    if stats["raw"] == 0 and stats["daily"] == 0:
        print(
            "[ERROR] Tabel weather_raw dan weather_daily di PostgreSQL masih kosong!\n"
            "Silakan impor data mentah terlebih dahulu dengan:\n"
            "  uv run python scripts/import_data.py\n"
            "  atau: .\\scripts\\import_data.bat",
            file=sys.stderr,
        )
        return 1

    overall_start = time.time()

    # Tentukan apakah tahap cleaning perlu dijalankan
    need_cleaning = False
    if args.clean_only:
        need_cleaning = True
    elif args.force_clean:
        need_cleaning = True
    elif not args.train_only and stats["daily"] == 0:
        print("\n[INFO] Tabel weather_daily masih kosong (0 baris).")
        print("       Menjalankan cleaning dan agregasi harian otomatis dari weather_raw...")
        need_cleaning = True

    if args.train_only and stats["daily"] == 0:
        print(
            "[ERROR] Opsi --train-only dipilih tetapi weather_daily kosong!\n"
            "Jalankan tanpa flag --train-only agar tahap cleaning dijalankan terlebih dahulu.",
            file=sys.stderr,
        )
        return 1

    # 1. Jalankan tahap cleaning jika dibutuhkan
    if need_cleaning:
        if stats["raw"] == 0:
            print("[ERROR] weather_raw kosong, tidak bisa melakukan cleaning!", file=sys.stderr)
            return 1
        run_cleaning_stage(chunk_size=args.chunk_size)
        print()

    # Jika hanya ingin cleaning, selesai di sini
    if args.clean_only:
        print("=" * 70)
        print(f"[SELESAI] Tahap cleaning & agregasi harian selesai dalam {format_duration(time.time() - overall_start)}.")
        print("Anda sekarang dapat menjalankan training model dengan:")
        print("  uv run python scripts/train_postgres.py --train-only")
        print("=" * 70)
        return 0

    # 2. Jalankan tahap training model
    model_bundle = run_training_stage(
        test_days=args.test_days,
        station_test=args.station_test,
    )
    print()

    # 3. Opsi setel aktif di .env
    if args.set_active:
        env_file = PROJECT_ROOT / ".env"
        if update_env_storage_backend(env_file):
            print(f"[Konfigurasi] NUSAKLIM_STORAGE_BACKEND=postgres telah diaktifkan di {env_file.name}.")

    total_time = time.time() - overall_start
    final_stats = get_db_stats()

    print("=" * 70)
    print("RINGKASAN LENGKAP TRAINING MODEL POSTGRESQL")
    print("=" * 70)
    print(f"Total Waktu Pipeline: {format_duration(total_time)}")
    print(f"Status Data DB Saat Ini:")
    print(f"  - weather_stations: {format_number(final_stats['stations'])} stasiun")
    print(f"  - weather_raw     : {format_number(final_stats['raw'])} pembacaan mentah")
    print(f"  - weather_daily   : {format_number(final_stats['daily'])} baris harian aktif")
    print(f"Model Bundle:")
    print(f"  - Versi Baru      : weather_model_bundle_{model_bundle.get('timestamp')}.joblib")
    print(f"  - Model Produksi  : {settings.model_bundle_path}")
    print(f"  - Target Pelatihan: {len(model_bundle.get('models', {}))} model teroptimasi")
    print("=" * 70)
    print("[SELESAI] Model prediksi siap digunakan untuk forecasting!")
    print("Langkah selanjutnya:")
    print("  1. Pastikan 'NUSAKLIM_STORAGE_BACKEND=postgres' di file .env")
    print("  2. Jalankan server API: uv run python -m api.serve")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
