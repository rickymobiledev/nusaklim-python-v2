@echo off
setlocal
cd /d "%~dp0.."
where uv >nul 2>nul
if errorlevel 1 (
    echo uv belum terpasang atau tidak ada di PATH. 1>&2
    exit /b 1
)
uv run python scripts/backup_postgres.py %*
exit /b %errorlevel%
