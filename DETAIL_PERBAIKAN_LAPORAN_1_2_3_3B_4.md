# Detail Perbaikan Laporan NusaKlim (Laporan 1, 2, 3, 3b, dan 4)

Dokumen ini merinci perubahan pada setiap laporan berdasarkan pengecekan langsung ke kode/skrip pembuat PDF-nya (`git diff` untuk file yang sudah ada sebelumnya, atau pembacaan isi file untuk skrip yang baru dibuat). Setiap laporan dikelompokkan menjadi 4 kategori: **Bug teknis**, **Koreksi angka & fakta**, **Perapian bahasa**, dan **Perubahan isi/metodologi**.

---

## Laporan 1 — Data Cleaning Tingkat Interval
*(skrip: `generate_interval_pdf.py`)*

### Bug teknis yang diperbaiki
- **File laporan tidak bisa dibuat ulang**: alamat filenya masih menunjuk ke `d:\Downloads\nusaklim\...` (komputer lama), sudah diarahkan ke folder proyek yang sekarang (`D:\Projects\Kodepanda\Nusaklim\nusaklim`).
- **Simbol rusak (°, ², dll muncul jadi "?")**: font PDF diganti dari Helvetica ke Arial (didaftarkan dari file TTF asli) supaya simbol derajat, pangkat dua, dsb tampil normal.
- **Bug tanda bintang**: tulisan gaya `*Deep Learning RNN/LSTM*`, `*input*`, `*output*`, `*Data Dictionary*`, `*gust*`, dll yang niatnya jadi huruf miring, malah muncul apa adanya dengan tanda bintangnya di PDF. Sudah dihapus/diganti bahasa Indonesia biasa.

### Koreksi angka & fakta
- **Jumlah stasiun AWS**: 184 → **183** (dicek ulang dari data asli).
- **Ukuran dataset**: 969,45 MB → **970,97 MB** (angka lama sudah kadaluarsa, diperbarui sesuai data terkini).
- **Jumlah baris data harian (referensi silang ke dataset harian)**: 114.651 → **114.507** baris.
- **Batas kewajaran nilai sensor diperlebar dan dirapikan**:
  - Suhu: 12°C–45°C → **0°C–100°C**
  - Tekanan udara: 920–1040 hPa → **500–1200 hPa**
  - Curah hujan: dulu dibuang jika >60 mm/15 menit → sekarang batas **0–1000 mm**
  - Angin: 0–150 km/jam → **0–100 km/jam**
  - **Aturan baru ditambahkan untuk Kelembapan** (sebelumnya belum ada penyaringan kode eror sensor untuk kelembapan): nilai eror -1 dan 255 sekarang dibuang, batas 0–100%.
- Referensi ke "notulen rapat PPKS 20 Agustus 2026" (sumber tidak jelas/tidak bisa diverifikasi) dihapus, diganti penjelasan aturan kewajaran fisik yang lebih netral.

### Perapian bahasa
- Judul disederhanakan: "...Tingkat Interval **Telemetri**" → "...Tingkat Interval" (kata "Telemetri" dihapus).
- "Siklus Diurnal" → "Siklus Harian (24 Jam)".
- Istilah teknis berlebihan disederhanakan (mis. "Sentinel hardware" → "Kode eror sensor", "isolasi ke NaN" → "diubah jadi kosong").

### Perubahan isi/metodologi
- Ditambahkan catatan kejujuran: peramalan resolusi tinggi (per jam) dijelaskan sebagai **rencana riset ke depan**, belum diimplementasikan di model produksi 7-hari yang berjalan sekarang.
- Tabel tanda tangan pengesahan ditambah kolom baru "Diverifikasi Oleh" (Cut Mardiana, Asisten TI), jadi 3 kolom (Disiapkan/Diverifikasi/Disetujui) dari sebelumnya 2 kolom.

---

## Laporan 2 — Preprocessing & EDA (Exploratory Data Analysis)
*(skrip: `generate_pdf.py`)*

### Bug teknis yang diperbaiki
- **Font simbol rusak**: Helvetica diganti ke Arial TTF asli — memperbaiki simbol seperti °, ±, →, ², − yang sebelumnya bisa tampil rusak.
- **Path file output & folder gambar salah**: dari `d:\Downloads\nusaklim\...` diperbaiki ke lokasi proyek yang benar.
- **Ukuran gambar disesuaikan** agar tidak distorsi/terpotong (mis. grafik distribusi dan siklus harian yang kini menampilkan lebih banyak variabel).
- **Lampiran baru ditambahkan dengan pengecekan file aman**: kode untuk Lampiran A (Daftar Stasiun AWS) memuat pengecekan keberadaan file dengan teks cadangan bila file tidak ditemukan, supaya skrip tidak gagal total.

### Koreksi angka & fakta
- **Jumlah stasiun AWS**: 184 → **183**.
- **Jumlah baris data harian**: 114.651 → **114.507** baris.
- **Batas kewajaran fisik direvisi**: Suhu 12–45°C → **0–100°C**; Tekanan 920–1040 hPa → **500–1200 hPa**; Curah hujan (anomali >60 mm/15 menit) → batas **0–1000 mm**; Angin >80 km/jam → **>100 km/jam**; Radiasi solar >1500 W/m² → **>2000 W/m²**.
- **Tabel jumlah error sensor dihitung ulang total** (semua angka berubah signifikan), termasuk baris baru untuk Tekanan dan Curah Hujan yang sebelumnya tidak ada di tabel ini.
- **Statistik deskriptif harian dihitung ulang total** dengan N Valid baru 98.911 baris (konsisten untuk semua variabel, bukan berbeda-beda seperti sebelumnya). Baris "Suhu Minimum" dan "Suhu Maksimum" terpisah dihapus dari tabel (disederhanakan menjadi Suhu Rata-rata saja).
- **Koreksi besar pada koefisien korelasi** — angka lama ternyata keliru:
  - Suhu vs Kelembapan: r = -0,74 ("sangat kuat") → **r = -0,28 ("lemah")**
  - Radiasi Solar vs Suhu: r = +0,62 → **r = +0,37**
  - Curah Hujan vs berbagai variabel: semua angka dikoreksi, ditambah korelasi baru vs Kecepatan Angin (r = +0,45)
  - Catatan: nilai +0,62 yang lama ternyata salah tempat — itu sebenarnya korelasi Suhu Maksimum vs Suhu Rata-rata, bukan Radiasi vs Suhu.
- **Klasifikasi intensitas curah hujan BMKG dihitung ulang**, misalnya kategori "Tidak Hujan" dari 55,7% → **50,7%**, "Hujan Ringan" dari 31,4% → **38,6%**.

### Perapian bahasa
- "feature engineering" → "pemilihan variabel cuaca yang akan diikutsertakan sebagai input".
- Semua rujukan "Notulen Rapat" / "sesuai arahan Notulen Rapat Butir X" **dihapus** dari judul dan teks laporan.
- "sentinel" (istilah hardware) → "kode eror".
- "raw dataset" → "data mentah"; "station-days" → "baris (kombinasi stasiun & hari)".
- "siklus diurnal" → "siklus harian (24 jam)".
- Nama teknis model disederhanakan, mis. "Model 3: Deep Sequence (TFT/PatchTST)" → "Model 3: Deep Learning Sekuensial Lanjutan" (nama arsitektur spesifik dihapus).
- Metrik evaluasi hujan yang terlalu teknis (CSI, HSS, Brier Score) diganti metrik yang konsisten dengan laporan lain (MAE/RMSE/R², Accuracy/F1 untuk arah angin).

### Perubahan isi/metodologi
- **Lampiran A baru**: "Daftar Lengkap Stasiun AWS NusaKlim" (ID, lokasi, perusahaan pengelola, koordinat) — konten yang sebelumnya tidak ada.
- **Penjelasan baru** kenapa N Valid (98.911) lebih kecil dari total baris (114.507) — karena hanya baris dengan semua 8 variabel lengkap yang dipakai.
- **Bagian baru "Penjelasan Siklus Harian (24 Jam)"**: analisis naratif per variabel dengan jam puncak/lembah, yang sebelumnya hanya berupa gambar tanpa penjelasan teks.
- **Temuan baru**: 2 stasiun (2134 dan 2140) diduga bermasalah karena mencapai batas maksimum curah hujan harian pada 48–65% dari total hari pengamatan — dikeluarkan dari peringkat "10 stasiun akumulasi hujan tertinggi" dan ditandai untuk pemeriksaan lapangan.
- Baris "Dasar Rapat Notulen" dihapus sepenuhnya dari tabel info sampul; klaim "memenuhi mandat Notulen Rapat 20 Agustus 2026" dihapus dari kesimpulan.

---

## Laporan 3 — Pengembangan & Evaluasi Model Prediksi Cuaca 7 Hari
*(skrip: `generate_model_pdf.py`)*

### Bug teknis yang diperbaiki
- **Font & path diperbaiki** dengan pola yang sama seperti laporan lain (Arial TTF, path proyek yang benar).
- **Bug tanda bintang** pada judul dan kalimat (mis. "Metodologi Rekayasa Fitur (*Feature Engineering*)") — dihapus, istilah asingnya sekaligus dibuang.
- **Tabel "champion" algoritma dulu tidak konsisten dengan datanya sendiri**: LightGBM diberi label "CHAMPION (Dipilih)" padahal MAE dan R²-nya lebih buruk dari Ridge/Random Forest di tabel yang sama. Sekarang pemenang ditentukan otomatis dari data benchmark, dan laporan mengakui secara eksplisit bila LightGBM bukan yang terbaik.
- **Daftar gambar di kesimpulan tidak sinkron** dengan gambar yang benar-benar dipakai (disebut "4 grafik" padahal cuma 3 dipakai) — diperbaiki jadi "6 gambar" sesuai gambar yang benar-benar disisipkan.
- **Angka-angka kunci dulu di-hardcode, sekarang dihitung langsung dari model & data riil** — dijamin selalu sinkron setiap kali model dilatih ulang.

### Koreksi angka & fakta
- **Jumlah stasiun AWS**: 184 → **183**.
- **Jumlah fitur prediktor**: 37 → **36** (24 Lag + 6 Rolling + 3 Tekanan/Termal + 2 Kalender + 1 Arah Angin).
- **Jumlah sub-model**: 21 → **49** (42 regresi + 7 klasifikasi arah angin) — konsekuensi penambahan target dari ~3 variabel menjadi 7 variabel × 7 horizon.
- **Perbandingan kecepatan training LightGBM vs Random Forest**: "12x lebih cepat" → **"60–150x lebih cepat"** (karena benchmark diperluas ke H+1 & H+7 dengan target Curah Hujan, bukan Suhu).
- **Seluruh tabel metrik performa H+1–H+7 diganti total**: dari fokus 3 variabel (Suhu/RH/Hujan) menjadi 7 indikator, dengan angka lama (mis. Suhu MAE H+1 0,80 / Hujan MAE 6,93) tidak dipakai lagi — diganti angka yang dihitung otomatis dari model aktual.
- **Contoh stasiun demo forecast diganti**: AWS 227 (Sumut – Sei Pancur) → **AWS 222 (Rambutan)**, dengan nilai ramalan yang tidak lagi hardcode melainkan dihasilkan langsung dari fungsi peramalan.

### Perapian bahasa
- "Automatic Weather Station (AWS)" → "Stasiun Cuaca Otomatis (AWS)".
- Nama kelompok fitur disederhanakan: "Temporal Lag Features" → "Lag Temporal"; "Moving Aggregations" → "Rolling Mean 7-Hari"; "Identitas Stasiun" dihapus dari daftar fitur, diganti "Arah Angin Hari Ini".
- "Meredam fluktuasi noise sensor harian" → "Meredam derau harian".
- Kalimat teknis berlebihan ("prekursor terbentuknya badai konvektif") disederhanakan jadi "biasanya menjadi tanda awal badai & hujan lebat yang datang tiba-tiba".
- Label internal seperti "Langkah 1 (Model Training)" diganti "Tahap Pelatihan Model" — penomoran jargon internal dihapus dari penutup laporan.

### Perubahan isi/metodologi
- **Target prediksi disederhanakan sekaligus diperluas**: Suhu cukup rata-rata (Min/Max dihapus), "Peluang Hujan %" dihapus sebagai target; ditambahkan 3 target numerik baru (Radiasi Matahari, Tekanan Udara, Kecepatan Angin) plus target klasifikasi baru (Arah Mata Angin, 4 kategori).
- **Fitur "Identitas Stasiun" dihapus total dari prediktor** — ditambahkan subbab baru yang menjelaskan alasannya (mencegah model "menghafal" pola per stasiun).
- **Benchmark algoritma diperluas**: dari hanya H+1 dengan target Suhu, menjadi H+1 dan H+7 dengan target Curah Hujan — kesimpulan diubah dari "LightGBM unggul" menjadi pengakuan transparan bahwa Ridge/Random Forest bisa menyamai atau mengungguli LightGBM untuk target hujan.
- **2 grafik baru ditambahkan**: performa klasifikasi arah angin, dan matriks kebingungan arah angin.
- **Tabel "Rekomendasi Agronomi" dihapus total** dari tabel ramalan 7 hari — kolom teks contoh tanpa dasar ilmiah (mis. "Aman untuk panen TBS", "Tunda pemupukan sore hari") dibuang, diganti kolom nilai prediksi murni.

---

## Laporan 3b — Analisis Model Per-Stasiun (Lokal) vs Global
*(skrip: `generate_per_station_pdf.py` — file baru, tidak ada versi lama di git untuk dibandingkan)*

### Status file ini
Skrip ini **ditulis ulang dari nol** pada sesi revisi ini (statusnya "untracked" di git, tidak ada histori versi lama). Bergantung pada data baru `local_benchmark_v2.json`, `global_benchmark_v2.json`, dan `station_sampling.json`.

### Bukti sudah bersih dari angka lama/usang
- Dicek langsung: **tidak ditemukan** lagi kutipan angka lama dari Laporan 4 versi Suhu (R² LSTM = 0,848, MAE Deep MLP = 0,756°C) yang sempat dikutip di versi sebelumnya.
- Semua angka MAE dan jumlah stasiun dihitung dinamis dari file data JSON saat laporan dibuat, bukan angka yang ditulis manual — sehingga otomatis ikut data terbaru dan tidak akan basi lagi.

### Kondisi teknis
- Font Arial TTF, path proyek, dan penulisan simbol (°, ², ×, −) sudah mengikuti pola yang benar seperti laporan lain.
- Jumlah stasiun sampel uji lokal: **30 stasiun** (dicek konsisten dengan data). Jumlah stasiun total training model global: **183** (bukan 184) — sudah benar.
- Tidak ditemukan bug tanda bintang markdown atau path folder rusak di file ini.

### Isi utama laporan
Membandingkan, untuk 7 indikator cuaca di 30 stasiun sampel acak: **Model Lokal** (dilatih ulang khusus per stasiun) vs **Model Global** (model yang sama dari Laporan 4, dilatih dari gabungan 183 stasiun). Hanya algoritma Machine Learning (Ridge & Random Forest) yang diuji ulang secara lokal — Deep Learning sengaja tidak diuji ulang karena data per-stasiun terlalu sedikit untuknya. Kesimpulannya tidak tunggal: sebagian indikator lebih baik pakai Model Lokal, sebagian tetap lebih baik pakai Model Global — dengan rekomendasi arsitektur hibrida untuk produksi.

---

## Laporan 4 — Komparasi Machine Learning vs Deep Learning
*(skrip: `generate_benchmark_pdf.py`)*

### Bug teknis yang diperbaiki
- **Path hardcoded milik komputer lama dihapus**, diganti path proyek yang benar.
- **Simbol rusak (° dan R² jadi "?")** diperbaiki dengan mendaftarkan font Arial asli.
- **Bug tanda bintang** (`*evidence-based*`, `*black-box*`, `*Decision Matrix*`, dll) yang tidak diproses jadi huruf miring — dihapus/ditulis ulang sebagai kalimat biasa.
- **Sumber angka**: sebelumnya semua angka hasil benchmark ditulis manual (rawan salah ketik) — sekarang dibaca otomatis dari file data JSON terbaru.

### Koreksi angka & fakta
- **Jumlah baris data mentah**: 114.651 → **114.507**.
- **Jumlah stasiun**: 184 → **183**.
- **Jumlah data uji dirinci per model** (sebelumnya satu angka generik "4.458" untuk semua model): sekitar 3.989–3.996 baris untuk model ML dan 2.159–2.243 baris untuk LSTM/GRU (berbeda karena kebutuhan jendela waktu berbeda).
- **Jumlah algoritma dipangkas**: dari 8 model (LightGBM, XGBoost, CatBoost, Random Forest, Ridge, LSTM, GRU, Deep MLP) menjadi **5 model** (3 ML + 2 DL) — XGBoost, CatBoost, dan Deep MLP dihapus dari cakupan laporan agar tetap ringkas.
- **Indikator yang diuji**: dari 1 indikator (Suhu) menjadi **7 indikator** — kelima model dilatih ulang dari nol untuk masing-masing indikator.
- **Semua angka MAE berubah** karena pelatihan ulang dari nol (bukan sekadar revisi angka lama), misalnya MAE Suhu LSTM 0,712°C → 0,7114°C.
- **Untuk Curah Hujan (fokus utama proyek)**: LSTM (MAE 6,06 mm) mengungguli algoritma ML terbaik Random Forest (MAE 7,28 mm) — mengonfirmasi temuan "LSTM sedikit lebih unggul dari ML".
- **Kesimpulan pemenang berubah total**: versi lama merekomendasikan **LightGBM** sebagai model produksi utama. Versi baru menghitung rata-rata peringkat MAE di 6 indikator regresi — hasilnya LightGBM justru menjadi yang **terburuk** (rata-rata peringkat 4,33), sementara kategori pemenang menjadi **Deep Learning** dan algoritma tunggal terbaik menjadi **Ridge**.
- **Skema pembagian data dibuat eksplisit**: latih sampai 20 Juli 2026, uji 20 Juli–19 Agustus 2026 (30 hari) — sebelumnya cuma disebut istilah teknis tanpa tanggal konkret.

### Perapian bahasa
- Judul diubah dari "...(Panduan Keputusan Klien)" → "Laporan Benchmark Model Global: 3 ML vs 2 DL, 7 Indikator Cuaca PPKS" — menghapus kesan "menjual" ke klien.
- Box klaim "REPRODUSIBILITAS RISET & STANDAR KUALITAS" (soal skrip lama yang sudah tidak dipakai) dihapus seluruhnya.
- Istilah asing dengan tanda bintang (`*evidence-based*`, `*feature engineering*`, `*black-box*`, `*Decision Matrix*`) dihapus/disederhanakan ke Bahasa Indonesia.
- Bab lama "Panduan Pengambilan Keputusan Klien (Decision Matrix)" dengan bahasa pemasaran ("PILIHAN UTAMA", "Hybrid Dual-Engine Architecture") dihapus total, diganti bab baru berbasis tabel angka rata-rata peringkat dengan bahasa lebih sederhana.
- Tabel "Taksonomi 8 Algoritma" penuh istilah teknis (Leaf-wise GBDT, oblivious trees, Tikhonov) dihapus, diganti penjelasan metodologi dengan bahasa lugas dan analogi konkret (mis. kenapa arah angin tidak boleh dirata-ratakan langsung).

### Perubahan isi/metodologi
- **Perluasan cakupan indikator**: dari 1 (Suhu) menjadi 7 (6 regresi + 1 klasifikasi Arah Angin) — seluruh 5 algoritma dilatih ulang dari nol untuk tiap indikator.
- **Arah Angin dipindah dari regresi ke klasifikasi 4 kelas** — perbaikan metodologis karena derajat arah angin bersifat sirkuler (350° dan 10° itu berdekatan, bukan jauh, sehingga tidak boleh dirata-ratakan langsung sebagai angka).
- **Grafik Pareto Frontier diperbaiki**: fokus dipindah ke Curah Hujan, dengan kriteria dominasi dua sisi (lebih cepat DAN lebih akurat) yang dijelaskan eksplisit — versi lama hanya disebut "Trade-off" tanpa kriteria jelas.
- **Bab baru "Showcase: Ramalan 7 Hari pada 10 Stasiun"**: menampilkan ramalan nyata dari model produksi (bukan simulasi) pada 10 stasiun yang dipilih acak.
- **Referensi silang ditambahkan** ke Laporan 3 (model produksi) dan Laporan 3b (lanjutan langsung dari laporan ini).

---

## Ringkasan Pola Umum di Semua Laporan
- **Bug font**: Helvetica → Arial TTF (memperbaiki simbol °, ², ±, → yang rusak).
- **Bug path**: `d:\Downloads\nusaklim\...` (komputer lama, tidak ada lagi) → path proyek yang benar.
- **Bug tanda bintang**: gaya markdown `*miring*` tidak diproses PDF-nya, tampil apa adanya — dihapus/ditulis ulang sebagai kalimat biasa.
- **Jumlah stasiun**: 184 → 183 di semua laporan, dicek ulang langsung dari data mentah.
- **Angka dihitung otomatis dari data/model**, bukan ditulis manual — supaya tidak ada lagi angka basi ketika data/model diperbarui.
- **Bahasa disederhanakan**: istilah asing yang tidak perlu dihapus, referensi ke "notulen rapat" internal dihapus, klaim yang berlebihan/tidak didukung data diluruskan.
