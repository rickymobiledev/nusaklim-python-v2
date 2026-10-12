# NusaKlim Python v2

Proyek ini menggunakan **uv** untuk mengelola Python 3.13, virtual environment,
dan dependensi. Versi dependensi dari `requirements.txt` dipertahankan saat
migrasi; konfigurasi aktif ada di `pyproject.toml` dan `uv.lock`.
PyTorch menggunakan build CPU dari indeks resmi PyTorch.

## Persiapan

Pasang [uv](https://docs.astral.sh/uv/getting-started/installation/) bila belum
tersedia, lalu jalankan dari direktori proyek:

```powershell
uv sync --locked
Copy-Item .env.example .env
```

uv membuat `.venv` dan menggunakan Python 3.13 sesuai `.python-version`.
Jika Python tersebut belum tersedia, uv mengunduhnya secara otomatis.
Tidak perlu mengaktifkan virtual environment secara manual.
Isi `NUSAKLIM_WEATHER_API_KEY` di `.env` dengan key milik Anda sebelum
menjalankan API. `.env` diabaikan oleh Git.

## Menjalankan proyek

```powershell
# Server API (host/port dibaca dari env; URL Swagger dicetak saat startup)
uv run python -m api.serve

# Demo cepat
uv run python demo_performa_model.py --cepat

# Script Python lainnya
uv run python nama_script.py
```

Launcher berada di folder `scripts/`, tersedia sebagai `.bat` untuk Windows
dan `.sh` untuk Bash (Linux, macOS, atau Git Bash). Semuanya menggunakan uv
dan otomatis berpindah ke root proyek:

```powershell
# Windows
.\scripts\run_demo.bat
.\scripts\scratch_pipeline.bat
.\scripts\scratch_pipeline_2.bat
```

```bash
# Bash
bash scripts/run_demo.sh
bash scripts/scratch_pipeline.sh
bash scripts/scratch_pipeline_2.sh
```

Launcher scratch menjalankan pipeline training dan pembuatan artefak.

## Konfigurasi environment

`api/config.py` membaca `.env` di root checkout. Environment proses memiliki
prioritas lebih tinggi daripada `.env`. Semua field dapat diatur dengan
prefix `NUSAKLIM_`; lihat daftar lengkap di `.env.example`.

```dotenv
NUSAKLIM_WEATHER_API_KEY=isi-key-anda
NUSAKLIM_HOST=127.0.0.1
NUSAKLIM_PORT=9000
NUSAKLIM_RELOAD=false
NUSAKLIM_CORS_ORIGINS='["http://localhost:3000"]'
```

`PORT` juga diterima jika `NUSAKLIM_PORT` tidak disetel. Untuk mengubah port
langsung dari terminal PowerShell:

```powershell
$env:NUSAKLIM_PORT = "9000"
uv run python -m api.serve
```

Root proyek bisa diatur lewat `NUSAKLIM_PROJECT_ROOT` di `.env`, misalnya
`NUSAKLIM_PROJECT_ROOT=E:/Projects/nusaklim-python-v2`. `PROJECT_ROOT` juga
diterima jika `NUSAKLIM_PROJECT_ROOT` tidak disetel. Path relatif dihitung dari
root checkout; `.env` tetap dibaca dari root checkout.

Default lokasi data/model mengikuti project root tersebut, atau `NUSAKLIM_BASE_DIR`
jika diatur (path relatif dihitung dari project root). Lokasi raw CSV, incoming, archive, rejected, dan staging mengikuti
`NUSAKLIM_RAW_DATA_DIR`. Semua path dapat diganti dengan path absolut.
Siapkan CSV yang diperlukan sebelum menjalankan forecast atau training.
Beberapa script analisis/training di luar `api/config.py` masih memiliki path
mesin asal yang perlu disesuaikan jika digunakan.

Perubahan `.env` dibaca saat proses dimulai; restart server setelah mengubahnya.

## Mengelola dependensi

```powershell
uv add nama_paket
uv remove nama_paket
uv sync --locked
```

Sertakan `pyproject.toml`, `uv.lock`, dan `.python-version` di Git.
`.venv` sudah diabaikan oleh `.gitignore`.

## Pengujian

```powershell
uv run python -m unittest discover -s tests -p test_config.py
```

`tests/test_api.py` berisi pemeriksaan endpoint sekaligus pemicu retrain/ingest.
Menjalankan file tersebut secara penuh dapat memproses data dan memperbarui
model; pemeriksaan forecast juga memerlukan data dan konfigurasi path yang benar.
