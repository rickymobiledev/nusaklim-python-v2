"""Versioned PostgreSQL migrations; the caller owns commit/rollback."""
import hashlib
from pathlib import Path
import re

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations" / "postgres"
MIGRATION_LOCK = 72410614


def _files(directory=None):
    directory = Path(directory) if directory is not None else MIGRATIONS_DIR
    if not directory.is_dir():
        raise ValueError(f"Folder migrasi tidak ditemukan: {directory}")
    result = []
    versions = set()
    for path in sorted(directory.glob("*.sql")):
        match = re.fullmatch(r"(\d+)_[a-zA-Z0-9_]+\.sql", path.name)
        if not match:
            raise ValueError(f"Nama file migrasi tidak valid: {path.name}")
        version = match[1]
        number = int(version)
        if number in versions:
            raise ValueError(f"Versi migrasi duplikat: {version}")
        versions.add(number)
        script = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        result.append((version, path.name, hashlib.sha256(script.encode()).hexdigest(), script))
    if not result:
        raise ValueError("Tidak ada file migrasi SQL")
    return sorted(result, key=lambda item: int(item[0]))


def _applied(conn):
    if conn.execute("SELECT to_regclass('nusaklim_schema_migrations')").fetchone()[0] is None:
        return {}
    return {version: (filename, checksum) for version, filename, checksum in
            conn.execute("SELECT version, filename, checksum FROM nusaklim_schema_migrations").fetchall()}


def migration_status(conn, directory=None):
    files = _files(directory)
    applied = _applied(conn)
    result = []
    for version, filename, checksum, _ in files:
        previous = applied.get(version)
        state = "pending" if previous is None else ("applied" if previous == (filename, checksum) else "modified")
        result.append({"version": version, "filename": filename, "status": state})
    known = {item[0] for item in files}
    for version, (filename, _) in applied.items():
        if version not in known:
            result.append({"version": version, "filename": filename, "status": "missing"})
    return result


def apply_migrations(conn, directory=None):
    files = _files(directory)
    # Serialize schema changes across API workers and migration commands.
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK,))
    status = migration_status(conn, directory)
    invalid = [item for item in status if item["status"] in ("modified", "missing")]
    if invalid:
        raise ValueError("Migrasi yang sudah diterapkan diubah/hilang: " + ", ".join(item["filename"] for item in invalid))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nusaklim_schema_migrations (
            version text PRIMARY KEY,
            filename text NOT NULL,
            checksum text NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    applied = _applied(conn)
    completed = []
    for version, filename, checksum, script in files:
        if version in applied:
            continue
        conn.execute(script)
        conn.execute("INSERT INTO nusaklim_schema_migrations (version, filename, checksum) VALUES (%s, %s, %s)",
                     (version, filename, checksum))
        completed.append(version)
    return completed
