# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "psycopg[binary]>=3.2,<4",
#     "python-dotenv",
#     "pydantic",
#     "pydantic-settings>=2.15.0",
# ]
# ///
"""
Script Backup Database PostgreSQL NusaKlim.

Membuat cadangan (backup) database PostgreSQL NusaKlim menggunakan pg_dump
dan menyimpannya ke folder data/ (atau lokasi yang ditentukan pengguna).

Contoh Penggunaan:
    # Backup database lengkap (format custom compressed .dump ke folder data/):
    uv run python scripts/backup_postgres.py

    # Backup dalam format plain SQL:
    uv run python scripts/backup_postgres.py --format sql

    # Tentukan nama / lokasi file output spesifik:
    uv run python scripts/backup_postgres.py -o data/my_backup.dump

    # Cek status database dan daftar file backup yang ada:
    uv run python scripts/backup_postgres.py --status

    # Backup schema saja (tanpa data tabel):
    uv run python scripts/backup_postgres.py --schema-only
"""

import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import unquote, urlparse

# Pastikan root proyek ada di sys.path agar dapat mengimpor `api`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.config import settings
import psycopg


def find_pg_dump() -> str | None:
    """Cari path pg_dump di PATH atau lokasi instalasi standar Windows / Scoop."""
    pg_dump = shutil.which("pg_dump")
    if pg_dump:
        return pg_dump

    # Cek direktori Scoop
    scoop_path = Path.home() / "scoop" / "apps" / "postgresql" / "current" / "bin" / "pg_dump.exe"
    if scoop_path.is_file():
        return str(scoop_path)

    # Cek Program Files Windows
    for pg_dir in Path(r"C:\Program Files\PostgreSQL").glob("*/bin/pg_dump.exe"):
        if pg_dir.is_file():
            return str(pg_dir)

    return None


def find_pg_restore() -> str | None:
    """Cari path pg_restore di PATH atau lokasi instalasi standar Windows / Scoop."""
    pg_restore = shutil.which("pg_restore")
    if pg_restore:
        return pg_restore

    scoop_path = Path.home() / "scoop" / "apps" / "postgresql" / "current" / "bin" / "pg_restore.exe"
    if scoop_path.is_file():
        return str(scoop_path)

    for pg_dir in Path(r"C:\Program Files\PostgreSQL").glob("*/bin/pg_restore.exe"):
        if pg_dir.is_file():
            return str(pg_dir)

    return None


def parse_db_url(url: str) -> dict[str, str | int]:
    """Ekstrak parameter koneksi database dari PostgreSQL URL."""
    parsed = urlparse(url)
    return {
        "user": unquote(parsed.username or "postgres"),
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/") or "nusaklim",
    }


def format_size(bytes_num: int) -> str:
    """Format ukuran byte ke bentuk yang mudah dibaca (KB, MB, GB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if bytes_num < 1024:
            return f"{bytes_num:.2f} {unit}"
        bytes_num /= 1024
    return f"{bytes_num:.2f} PB"


def print_status(db_params: dict[str, str | int], backup_dir: Path) -> None:
    """Cetak status koneksi, ukuran database, jumlah baris tabel, dan daftar backup."""
    print("=" * 70)
    print("STATUS DATABASE & DAFTAR BACKUP NUSAKLIM")
    print("=" * 70)
    print(f"Host     : {db_params['host']}:{db_params['port']}")
    print(f"Database : {db_params['dbname']}")
    print(f"User     : {db_params['user']}")

    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_size_pretty(pg_database_size(%s));",
                    (db_params["dbname"],),
                )
                db_size = cur.fetchone()[0]
                print(f"Ukuran DB: {db_size}")

                tables = ["weather_stations", "weather_raw", "weather_daily"]
                for tbl in tables:
                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = %s
                        );
                        """,
                        (tbl,),
                    )
                    exists = cur.fetchone()[0]
                    if exists:
                        cur.execute(f"SELECT COUNT(*) FROM public.{tbl};")
                        cnt = cur.fetchone()[0]
                        print(f"  - {tbl:<18}: {cnt:>12,d} baris")
                    else:
                        print(f"  - {tbl:<18}: (belum dibuat)")
    except Exception as exc:
        print(f"Gagal menghubungkan ke database: {exc}")

    print("\nFile Backup yang Tersedia di Folder:", backup_dir)
    if backup_dir.is_dir():
        backup_files = sorted(
            list(backup_dir.glob("*.dump")) + list(backup_dir.glob("*.sql")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if backup_files:
            for bf in backup_files:
                size_str = format_size(bf.stat().st_size)
                mtime_str = datetime.fromtimestamp(bf.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  - {bf.name:<40} ({size_str:>10}) [{mtime_str}]")
        else:
            print("  (Belum ada file backup .dump atau .sql di folder ini)")
    else:
        print("  (Folder tidak ditemukan)")
    print("=" * 70)


def run_backup(
    output_path: Path | None = None,
    dump_format: str = "custom",
    schema_only: bool = False,
    data_only: bool = False,
    clean: bool = False,
) -> Path:
    """Jalankan proses backup pg_dump."""
    if not settings.database_url:
        print("ERROR: NUSAKLIM_DATABASE_URL belum disetel di .env", file=sys.stderr)
        sys.exit(1)

    db_params = parse_db_url(settings.database_url)
    backup_dir = PROJECT_ROOT / "data"
    backup_dir.mkdir(parents=True, exist_ok=True)

    pg_dump_bin = find_pg_dump()
    if not pg_dump_bin:
        print(
            "ERROR: 'pg_dump' tidak ditemukan di PATH maupun instalasi standar PostgreSQL.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Tentukan nama file default jika output_path tidak diberikan
    ext = ".sql" if dump_format in ("sql", "plain") else ".dump"
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "nusaklim_schema" if schema_only else "nusaklim_backup"
        output_path = backup_dir / f"{prefix}_{timestamp}{ext}"
    else:
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        pg_dump_bin,
        "-h", str(db_params["host"]),
        "-p", str(db_params["port"]),
        "-U", str(db_params["user"]),
        "-d", str(db_params["dbname"]),
    ]

    if dump_format in ("custom", "c"):
        cmd.extend(["-Fc"])
    elif dump_format in ("tar", "t"):
        cmd.extend(["-Ft"])
    elif dump_format in ("directory", "d"):
        cmd.extend(["-Fd"])

    if schema_only:
        cmd.append("--schema-only")
    elif data_only:
        cmd.append("--data-only")

    if clean:
        cmd.append("--clean")

    cmd.extend(["-f", str(output_path)])

    env = os.environ.copy()
    if db_params["password"]:
        env["PGPASSWORD"] = str(db_params["password"])

    print("=" * 70)
    print("MEMULAI BACKUP POSTGRESQL NUSAKLIM")
    print("=" * 70)
    print(f"Database     : {db_params['dbname']} ({db_params['host']}:{db_params['port']})")
    print(f"Format       : {dump_format.upper()}")
    print(f"Target File  : {output_path}")
    print(f"Binary       : {pg_dump_bin}")
    print("=" * 70)
    print("Sedang mengekspor data...")

    t0 = time.time()
    result = subprocess.run(cmd, env=env)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"\n[GAGAL] pg_dump keluar dengan status kode {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    file_size = output_path.stat().st_size
    print("\n" + "=" * 70)
    print("[SUKSES] Backup database berhasil dibuat!")
    print(f"File Output : {output_path}")
    print(f"Ukuran File : {format_size(file_size)}")
    print(f"Waktu Backup: {elapsed:.2f} detik")
    print("=" * 70)

    # Cetak instruksi restore
    print("\nPetunjuk Pemulihan (Restore):")
    if dump_format in ("custom", "c"):
        print(f"  pg_restore -h {db_params['host']} -p {db_params['port']} -U {db_params['user']} -d {db_params['dbname']} --clean --if-exists {output_path}")
    else:
        print(f"  psql -h {db_params['host']} -p {db_params['port']} -U {db_params['user']} -d {db_params['dbname']} -f {output_path}")

    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Backup database PostgreSQL NusaKlim ke folder data/",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Path file output cadangan (default: data/nusaklim_backup_YYYYMMDD_HHMMSS.dump)",
    )
    parser.add_argument(
        "-F", "--format",
        choices=["custom", "sql", "tar"],
        default="custom",
        help="Format backup: 'custom' (default, terkompresi .dump), 'sql' (plain SQL), 'tar'",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Hanya backup skema DDL tanpa data",
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Hanya backup data isi tabel tanpa skema DDL",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Sertakan perintah DROP sebelum perintah CREATE saat restore",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Periksa ukuran database, jumlah data tabel, dan daftar backup yang tersedia",
    )

    args = parser.parse_args(argv)

    if args.schema_only and args.data_only:
        parser.error("Opsi --schema-only dan --data-only tidak dapat digunakan bersamaan.")

    backup_dir = PROJECT_ROOT / "data"
    db_params = parse_db_url(settings.database_url) if settings.database_url else {}

    if args.status:
        if not db_params:
            print("ERROR: NUSAKLIM_DATABASE_URL belum disetel di .env", file=sys.stderr)
            sys.exit(1)
        print_status(db_params, backup_dir)
        return

    run_backup(
        output_path=args.output,
        dump_format=args.format,
        schema_only=args.schema_only,
        data_only=args.data_only,
        clean=args.clean,
    )


if __name__ == "__main__":
    main()
