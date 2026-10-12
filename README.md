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

## Penyimpanan PostgreSQL

Backend PostgreSQL menyimpan data historis dan kiriman baru dalam `weather_raw`.
Hasil cleaning/agregasi disimpan dalam `weather_daily`; training dan forecast
membacanya langsung dari database. Model tetap disimpan sebagai `.joblib`.
Default backend masih `csv` sampai konfigurasi PostgreSQL diaktifkan.

Siapkan database dan user PostgreSQL terlebih dahulu; migrasi tidak membuat
database atau role. User perlu hak membuat tabel serta membaca/menulis data di
database tersebut. Isi `.env` (ganti host, user, password, dan nama database
sesuai server tim):

```dotenv
NUSAKLIM_DATABASE_URL=postgresql://nusaklim:password@127.0.0.1:5432/nusaklim
NUSAKLIM_RELOAD=false
```

Password yang mengandung karakter khusus dalam URL perlu di-percent-encode.
Jangan masukkan kredensial asli ke Git. Terapkan schema PostgreSQL sebelum
mengaktifkan backend atau menyalakan API:

```powershell
uv sync --locked
uv run python -m api.migrate_postgres
```

Perintah tanpa argumen menerapkan versi SQL dari `migrations/postgres` (termasuk pembuatan
tabel `weather_stations` beserta relasi foreign key dari `weather_raw` dan `weather_daily`
ke stasiun). Metadata stasiun dari `data/device_nusaklim.csv` otomatis diimpor/di-upsert ke tabel
`weather_stations`. Anda juga dapat menentukan file CSV device tertentu dengan opsi `--device-csv <path>`
atau melewati impor device dengan `--skip-device`. Versi dan checksum dicatat dalam ledger
`nusaklim_schema_migrations`; jalankan lagi untuk menerapkan migrasi yang belum tercatat. Periksa
hasilnya kapan saja dengan perintah read-only:

```powershell
uv run python -m api.migrate_postgres --status
```

Untuk impor satu kali seluruh sejarah raw dari `data/nusaklim-aws-reduce.csv`
sekaligus menjalankan cleaning ke database:

```powershell
uv run python -m api.migrate_postgres --raw-csv .\data\nusaklim-aws-reduce.csv
```

Raw CSV dibaca per chunk (default 100000 baris; ubah dengan
`--chunk-size 50000`, misalnya). Baris dengan pasangan station dan epoch yang
sudah ada diabaikan; format epoch ekuivalen seperti `1787136600.0` dan
`1787136600` diperlakukan sama. File CSV sumber tidak dihapus. CLI migrasi hanya
mengimpor dan membersihkan data; CLI ini tidak menjalankan retrain model.
Duplikat historis mempertahankan observasi pertama, sehingga agregasi dapat
berubah jika CSV lama memiliki pembacaan berulang. Schema, impor raw, dan
penyimpanan daily merupakan tahap transaksi terpisah; jika tahap berikutnya
gagal, tahap yang sudah selesai tetap tersimpan dan perintah dapat diulang.

Jika memiliki snapshot harian, impor dengan `--daily-csv`. Opsi ini dapat
digabung dengan raw; saat daily CSV diberikan, cleaning otomatis dilewati:

```powershell
uv run python -m api.migrate_postgres --raw-csv .\data\nusaklim-aws-reduce.csv --daily-csv .\nusaklim_daily_aggregated.csv
```

Impor snapshot daily mengganti seluruh isi `weather_daily` dalam satu transaksi,
sehingga pembaca melihat snapshot lama atau snapshot baru secara utuh. Launcher
tersedia dari root proyek maupun direktori lain:

```powershell
.\scripts\migrate_postgres.bat --status
```

```bash
bash scripts/migrate_postgres.sh --raw-csv ./data/nusaklim-aws-reduce.csv
```

Setelah migrasi dan impor selesai, aktifkan backend PostgreSQL di `.env`, lalu
jalankan API:

```dotenv
NUSAKLIM_STORAGE_BACKEND=postgres
```

```powershell
uv run python -m api.serve
```
Tim stasiun menggunakan endpoint yang sama:

```http
POST /api/v1/ingest/json
X-API-Key: <key>
Content-Type: application/json
```

```json
{
  "mode": "append",
  "records": [
    {"stnname": "227", "utctime": 1787136600, "tempout": 80.6, "humout": 75}
  ]
}
```

Pada PostgreSQL, data JSON langsung disimpan dan transaksi selesai sebelum
respons `Accepted`. Data terlambat dengan waktu yang belum ada juga diterima;
kiriman ulang diabaikan. `mode=replace` ditolak agar upload tidak menghapus
seluruh riwayat database. Endpoint upload CSV dan folder incoming juga
diimpor ke PostgreSQL saat backend ini aktif.

Setelah penyimpanan, API otomatis menjalankan cleaning dari `weather_raw`,
menyimpan ulang `weather_daily`, retrain, dan reload model di background.
Tidak perlu menjalankan `api.pipeline_runner` sebagai service terpisah.
Hasil proses ada di `logs/pipeline.log`, `logs/pipeline_history.jsonl`, dan
`logs/runs/<task_id>.log`. Jika retrain gagal, data mentah yang sudah diterima
tetap tersimpan dan proses bisa dipicu ulang dengan `POST /api/v1/ingest`.

Setiap request tetap memicu satu retrain; request ingest/retrain lain mendapat
409 selama job berjalan. Jalankan satu worker API dan jangan menjalankan
pipeline manual bersamaan karena kunci training masih berada dalam proses API.
Background task belum memakai antrean persisten: jika server berhenti,
data JSON yang sudah diterima tetap tersimpan, tetapi job perlu dipicu ulang.
Split validasi 30 hari terakhir tetap berlaku.

Pengujian PostgreSQL memakai schema sementara yang dihapus setelah pengujian;
URL test harus menunjuk database khusus pengujian dan user harus boleh membuat schema:

```powershell
$env:NUSAKLIM_TEST_DATABASE_URL = "postgresql://user:password@127.0.0.1:5432/nusaklim_test"
uv run python -m unittest discover -s tests -p test_weather_store.py
uv run python -m unittest discover -s tests -p test_db_migrations.py
```

Implementasi COPY dan cursor batch mengikuti
[dokumentasi Psycopg](https://www.psycopg.org/psycopg3/docs/basic/copy.html).
