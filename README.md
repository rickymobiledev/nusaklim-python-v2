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

## Migrasi Database & Impor Data (PostgreSQL)

NusaKlim menggunakan PostgreSQL untuk menyimpan metadata stasiun AWS (`weather_stations`),
data observasi mentah sensor 10-menitan (`weather_raw`), dan dataset ringkasan harian
teragregasi (`weather_daily`) yang digunakan untuk melatih model AI.

### 1. Konfigurasi Koneksi Database
Siapkan database dan user PostgreSQL terlebih dahulu. User memerlukan hak untuk
membuat tabel serta membaca/menulis data di database tersebut.
Buka file `.env` di root proyek dan isi URL koneksi database:

```dotenv
NUSAKLIM_DATABASE_URL=postgresql://user:password@127.0.0.1:5432/nusaklim
```

Password yang mengandung karakter khusus dalam URL perlu di-percent-encode.

### 2. Terapkan Migrasi Schema Database
Terapkan migrasi DDL dari `migrations/postgres` (termasuk pembuatan tabel `weather_stations`,
`weather_raw`, `weather_daily`, index, serta relasi foreign key):

```powershell
# Windows PowerShell / CMD:
uv run python -m api.migrate_postgres
# atau launcher:
.\scripts\migrate_postgres.bat
```

```bash
# Bash (Linux / macOS / Git Bash):
bash scripts/migrate_postgres.sh
```

Periksa status penerapan versi migrasi kapan saja dengan perintah read-only:

```powershell
uv run python -m api.migrate_postgres --status
```

### 3. Impor Data Stasiun & Data Cuaca Mentah
Setelah skema tabel terbentuk, impor metadata stasiun dari `data/device_nusaklim.csv`
dan data sensor mentah historis dari `data/nusaklim-aws-reduce.csv` (~14,7 juta baris)
menggunakan script streaming COPY berkecepatan tinggi:

```powershell
# Windows PowerShell / CMD:
uv run python scripts/import_data.py
# atau launcher:
.\scripts\import_data.bat
```

```bash
# Bash (Linux / macOS / Git Bash):
./scripts/import_data.sh
```

**Fitur & Opsi Impor:**
- **Streaming COPY berkecepatan tinggi**: Kecepatan mencapai ~20.000–40.000 baris/detik.
- **Idempoten & Resumable**: Setiap chunk di-commit bertahap. Jika terputus (Ctrl+C), data yang tersimpan tetap aman dan saat diulang baris duplikat otomatis dilewati (`ON CONFLICT DO NOTHING`).
- **Auto-Resolve Relasi**: Otomatis mendaftarkan stasiun yang belum ada di `weather_stations` agar tidak melanggar foreign key constraint.

```powershell
# Opsi khusus:
uv run python scripts/import_data.py --status              # Cek status & jumlah baris DB
uv run python scripts/import_data.py --stations-only       # Hanya impor stasiun (device_nusaklim.csv)
uv run python scripts/import_data.py --weather-only        # Hanya impor data cuaca (nusaklim-aws-reduce.csv)
uv run python scripts/import_data.py --chunk-size 200000   # Mengatur ukuran batch chunk
uv run python scripts/import_data.py --limit-rows 50000    # Uji coba cepat dengan limit baris
```

### 4. Backup & Restore Database
Buat salinan cadangan (backup) database PostgreSQL kapan saja dan simpan ke folder `data/`:

```powershell
# Windows PowerShell / CMD:
uv run python scripts/backup_postgres.py
# atau launcher:
.\scripts\backup_postgres.bat
```

```bash
# Bash (Linux / macOS / Git Bash):
bash scripts/backup_postgres.sh
```

**Opsi Backup:**
```powershell
uv run python scripts/backup_postgres.py --status           # Cek ukuran database & file backup di folder data/
uv run python scripts/backup_postgres.py --format sql       # Backup dalam format teks SQL mentah
uv run python scripts/backup_postgres.py --schema-only      # Hanya backup skema DDL (tanpa data)
uv run python scripts/backup_postgres.py -o data/my.dump    # Menentukan nama file keluaran khusus
```

**Restore Database dari Backup:**
```powershell
# Restore dari file custom .dump:
pg_restore -h 127.0.0.1 -p 5432 -U postgres -d nusaklim --clean --if-exists data\nusaklim_backup_YYYYMMDD_HHMMSS.dump

# Atau restore dari format plain SQL:
psql -h 127.0.0.1 -p 5432 -U postgres -d nusaklim -f data\nusaklim_backup_YYYYMMDD_HHMMSS.sql
```

## Pelatihan Model (Training) dari Database PostgreSQL


Setelah data mentah tersimpan di PostgreSQL, latih model prediksi cuaca 7 hari secara langsung dari database:

```powershell
# Windows PowerShell / CMD:
uv run python scripts/train_postgres.py
# atau launcher:
.\scripts\train_postgres.bat
```

```bash
# Bash (Linux / macOS / Git Bash):
./scripts/train_postgres.sh
```

### Alur yang Berjalan Otomatis:
1. **Cleaning & Agregasi Harian**: Script otomatis mendeteksi jika tabel `weather_daily` masih kosong (0 baris), membersihkan anomali/outlier sensor dari `weather_raw`, dan menyimpan ringkasan harian bersih ke `weather_daily` (~3 menit).
2. **Feature Engineering**: Membangun 29 fitur fisis (lag 1, 3, 7 hari, rolling 7 hari, kalender sin/cos DOY, dan persistensi arah angin).
3. **Multi-Model Training**: Melatih 49 model champion (kombinasi LightGBM, Ridge Regression, Random Forest) untuk seluruh 7 horizon (H+1 s/d H+7) pada 7 variabel cuaca.
4. **Penyimpanan Versioned Bundle**: Menyimpan model berstempel waktu (`models/weather_model_bundle_YYYYMMDD_HHMMSS.joblib`) dan memperbarui model produksi aktif (`models/weather_model_latest.joblib`).
5. **Uji Inferensi**: Menjalankan simulasi prediksi 7 hari untuk memverifikasi model.

**Opsi Khusus Training:**
```powershell
uv run python scripts/train_postgres.py --status        # Cek kesiapan data DB & model terkini
uv run python scripts/train_postgres.py --clean-only    # Hanya agregasi weather_raw -> weather_daily
uv run python scripts/train_postgres.py --train-only    # Langsung latih model dari weather_daily yang sudah ada
uv run python scripts/train_postgres.py --force-clean   # Paksa agregasi ulang dari data mentah weather_raw
uv run python scripts/train_postgres.py --set-active    # Otomatis aktifkan backend postgres di .env
```

Setelah pelatihan selesai, aktifkan backend PostgreSQL di `.env`:
```dotenv
NUSAKLIM_STORAGE_BACKEND=postgres
```

## Menjalankan Proyek

Setelah database siap dan model selesai dilatih, jalankan API dan demo:

```powershell
# Server API (host/port dibaca dari env; URL Swagger dicetak saat startup)
uv run python -m api.serve

# Demo cepat performa model
uv run python demo_performa_model.py --cepat

# Script Python lainnya
uv run python nama_script.py
```

Launcher berada di folder `scripts/`, tersedia sebagai `.bat` untuk Windows
dan `.sh` untuk Bash (Linux, macOS, atau Git Bash):

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

## Konfigurasi Environment

`api/config.py` membaca `.env` di root checkout. Environment proses memiliki
prioritas lebih tinggi daripada `.env`. Semua field dapat diatur dengan
prefix `NUSAKLIM_`; lihat daftar lengkap di `.env.example`.

```dotenv
NUSAKLIM_WEATHER_API_KEY=isi-key-anda
NUSAKLIM_HOST=127.0.0.1
NUSAKLIM_PORT=9000
NUSAKLIM_RELOAD=false
NUSAKLIM_CORS_ORIGINS='["http://localhost:3000"]'
NUSAKLIM_STORAGE_BACKEND=postgres
NUSAKLIM_DATABASE_URL=postgresql://user:password@127.0.0.1:5432/nusaklim
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

### Beralih Versi Model (Switch Back)
Setiap training menyimpan bundle model berstempel waktu di folder `models/`.
Untuk beralih kembali ke versi model sebelumnya:
```dotenv
NUSAKLIM_MODEL_BUNDLE_PATH=models/weather_model_bundle_20261012_141427.joblib
```
Atau salin kembali file bundle lama menimpa `models/weather_model_latest.joblib`.

## Mengelola Dependensi

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
uv run python -m unittest discover -s tests -p test_import_data.py
uv run python -m unittest discover -s tests -p test_train_postgres.py
```

`tests/test_api.py` berisi pemeriksaan endpoint sekaligus pemicu retrain/ingest.
Pemeriksaan forecast memerlukan data dan model yang valid.

Pengujian PostgreSQL memakai schema sementara yang dihapus setelah pengujian;
URL test harus menunjuk database khusus pengujian dan user harus boleh membuat schema:

```powershell
$env:NUSAKLIM_TEST_DATABASE_URL = "postgresql://user:password@127.0.0.1:5432/nusaklim_test"
uv run python -m unittest discover -s tests -p test_weather_store.py
uv run python -m unittest discover -s tests -p test_db_migrations.py
```

## Operasional Ingest Data Baru & Background Retrain

Saat backend PostgreSQL aktif (`NUSAKLIM_STORAGE_BACKEND=postgres`), data observasi
baru dapat dikirim lewat API:

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
seluruh riwayat database. Endpoint upload CSV dan folder `data_raw/incoming/` juga
diimpor ke PostgreSQL saat backend ini aktif.

Setelah penyimpanan, API otomatis menjalankan cleaning dari `weather_raw`,
menyimpan ulang `weather_daily`, retrain, dan reload model di background.
Hasil proses ada di `logs/pipeline.log`, `logs/pipeline_history.jsonl`, dan
`logs/runs/<task_id>.log`. Jika retrain gagal, data mentah yang sudah diterima
tetap tersimpan dan proses bisa dipicu ulang dengan `POST /api/v1/ingest`.

Setiap request memicu satu retrain; request ingest/retrain lain mendapat
409 selama job berjalan. Jalankan satu worker API karena kunci training berada
dalam proses API.
