# Ringkasan Perbaikan Laporan NusaKlim (Berdasarkan Feedback Reviewer)

Dokumen ini merangkum semua perbaikan yang sudah dilakukan pada laporan-laporan NusaKlim PPKS, berdasarkan catatan/komentar yang diberikan reviewer di file PDF. Ditulis dengan bahasa sederhana supaya mudah dicek ulang.

---

## 1. Laporan 3 — Model Prediksi Cuaca 7 Hari

**Perbaikan yang sudah dikerjakan sebelumnya (sesi lalu):**
- Target prediksi disederhanakan: Suhu cukup rata-rata saja (tidak perlu Min/Max terpisah), dan "Peluang Hujan (%)" dihapus sebagai target sendiri — sekarang kondisi cuaca (Cerah/Hujan Ringan/dst) dihitung otomatis dari angka Curah Hujan (mm).
- Fitur "Identitas Stasiun" (nama stasiun) **dihapus** dari daftar fitur prediktor, karena itu cuma kode unik, bukan variabel cuaca — supaya model tidak "menghafal" per stasiun.
- Jumlah fitur dirapikan dari 37 menjadi 36, dengan penjelasan alasan ilmiahnya (biar tidak overfitting, merujuk penelitian kompetisi forecasting M5).
- Perbandingan algoritma (LightGBM vs Ridge vs Random Forest) sekarang dibuat untuk **H+1 DAN H+7** (sebelumnya cuma H+1), pakai indikator **Curah Hujan** karena itu fokus utama proyek.
- Evaluasi performa H+1 sampai H+7 sekarang mencakup **ketujuh indikator** (dulu cuma sebagian).
- Grafik "fitur paling berpengaruh" sekarang dijamin selalu sinkron dengan tulisan penjelasannya (dihitung otomatis dari model, bukan ditulis manual).
- Validasi hasil ramalan vs data asli sekarang dibuat untuk semua 6 target angka + 1 matriks kebingungan untuk arah angin.

**Perbaikan baru (sesi ini):**
- Tabel "Rekomendasi Agronomi" (contoh: "Aman untuk panen TBS", dll) yang isinya cuma teks contoh tanpa aturan/sumber yang jelas — **sudah dihapus total** dari tabel ramalan 7 hari.

---

## 2. Laporan 4 — Komparasi Machine Learning vs Deep Learning

**Perbaikan baru (sesi ini):**
- **Klarifikasi jumlah baris data**: sekarang dijelaskan jelas bahwa 114.651 baris itu data mentah (sebelum dipisah), bukan jumlah data training maupun data testing. Angka data training (±89 ribu baris) dan data testing (±3.836 baris, 30 hari terakhir) sekarang ditulis terpisah dan otomatis dihitung dari data asli.
- **Konfirmasi model global**: dijelaskan eksplisit bahwa ke-8 model ini masing-masing adalah **1 model global** (dilatih dari gabungan 184 stasiun sekaligus), bukan 8 model terpisah per stasiun.
- **Ganti indikator contoh dari Suhu ke Curah Hujan**: karena curah hujan adalah fokus utama proyek. Ini artinya seluruh 8 model (LightGBM, XGBoost, CatBoost, Random Forest, Ridge, LSTM, GRU, Deep MLP) **dilatih ulang dari nol** memakai target Curah Hujan (mm), bukan Suhu lagi. Semua tabel, grafik, dan kesimpulan di laporan diperbarui mengikuti hasil baru ini.
  - Hasil menarik: untuk indikator Curah Hujan, **LSTM justru sedikit lebih unggul** dibanding model Machine Learning — beda dengan hasil sebelumnya waktu pakai Suhu.
- **Grafik "Pareto Frontier" diperbaiki dan dijelaskan**: sekarang grafik ini benar-benar menandai model mana yang "tidak terkalahkan" di dua sisi sekaligus (cepat DAN akurat) dengan garis & lingkaran khusus. Ditambahkan juga penjelasan kenapa nama "Pareto" itu sudah benar secara istilah, dan kenapa grafik ini beda fungsinya dari grafik batang MAE biasa (bukan sekadar pengulangan).

---

## 3. Laporan 2 — Preprocessing & EDA (Exploratory Data Analysis)

Laporan ini juga sempat dapat banyak catatan reviewer sebelumnya. Hasil audit ulang (sesi ini) terhadap 17 poin catatan lama menunjukkan **15 poin sudah beres**, contohnya:
- Kata "Telemetri" dan "Insolasi" sudah diganti/dihapus sesuai istilah yang dipakai di web.
- Penjelasan statistik (curah hujan, kecepatan angin, tekanan udara, radiasi solar) sudah dibuat lebih informatif.
- Angka korelasi yang tadinya salah tulis (misal Suhu vs Kelembapan yang tadinya ditulis -0.74, padahal aslinya -0.41) sudah dikoreksi dan **dicek ulang langsung dari data asli**.
- Istilah "feature engineering" diganti jadi "feature selection" karena memang cuma memilih variabel yang sudah ada, bukan membuat variabel baru.
- Istilah "siklus diurnal" diganti jadi "siklus harian (24 jam)" di seluruh dokumen.
- Kalimat soal ENSO/IOD yang diminta dihapus, sudah dihapus.

**2 masalah baru yang ditemukan & diperbaiki (sesi ini):**
- **Simbol aneh "?"** yang harusnya derajat (°) atau pangkat dua (²) — muncul di 3 grafik (grafik ringkasan pembersihan data, grafik matriks korelasi, grafik tren waktu). Ini terjadi karena font yang dipakai untuk bikin grafik tidak mendukung simbol tersebut. **Sudah diperbaiki** dengan mengganti font grafik.
- **Angka korelasi curah hujan yang sudah kadaluarsa**: grafik matriks korelasi ternyata dibuat dari data lama (sebelum data terbaru diperbarui), jadi angkanya beda dengan data yang dipakai sekarang. **Sudah dihitung ulang dari data terbaru** dan tulisan di laporan disesuaikan supaya cocok dengan grafiknya.
- Bonus: ada garis aneh yang menyambung lurus di grafik tren waktu (melompati bagian data yang kosong tahun 2022-2023) — sekarang bagian kosong itu ditampilkan sebagai celah kosong yang sebenarnya, bukan disambung garis lurus yang menyesatkan.

---

## 4. Perapian Bahasa & Konsistensi di SEMUA Laporan (Laporan 1–7)

Setelah 3 laporan di atas selesai, dilakukan satu putaran perapian menyeluruh ke **seluruh 7 laporan** (termasuk Laporan 1 Data Cleaning Interval, Laporan 3b Model Per-Stasiun vs Global, Laporan 5 Audit Gap Data, Laporan 6 Komparasi vs Open-Meteo, dan Laporan 7 Dokumentasi Master), dengan permintaan: bahasa jangan berlebihan, istilah asing yang tidak perlu dijelaskan tidak usah ditulis, penamaan variabel diseragamkan, simbol yang salah tampil diperbaiki, dan grafik harus selalu cocok dengan tulisannya.

**Jumlah stasiun diperbaiki di SEMUA laporan (184 → 183):** dicek ulang langsung dari data (`nusaklim_daily_aggregated.csv` dan `nusaklim_cleaned_interval.csv`), keduanya konsisten menunjukkan **183 stasiun**, bukan 184 seperti yang tertulis di hampir semua laporan sebelumnya. Sudah diperbaiki di seluruh 7 laporan, termasuk yang muncul di judul, tabel ringkasan, dan grafik.

**Bug simbol "*" yang muncul apa adanya di PDF:** ditemukan bahwa penulisan gaya \*miring\* (dimaksudkan untuk jadi huruf miring) ternyata **tidak diproses** oleh program pembuat PDF-nya, sehingga tanda bintangnya justru muncul apa adanya di hasil cetak — misalnya pembaca akan melihat tulisan "(\*Decision Matrix\*)" lengkap dengan tanda bintangnya, bukan tulisan miring seperti yang dimaksud. Ini ditemukan dan diperbaiki di semua laporan yang terpengaruh (istilah asingnya sekalian disederhanakan jadi Bahasa Indonesia, bukan hanya diberi huruf miring).

**Path/alamat file yang rusak (laporan gagal dibuat ulang):** 6 dari 7 skrip pembuat laporan (Laporan 1, 3b, 5, 6, 7, dan skrip pendukung lain) ternyata masih menunjuk ke folder lama di komputer lain (`d:\Downloads\nusaklim\...`) yang tidak ada lagi di komputer ini — akibatnya laporan-laporan itu sebenarnya **tidak bisa dibuat ulang sama sekali** sebelum diperbaiki. Semua sudah diarahkan ke folder proyek yang benar.

**Istilah asing yang disederhanakan** (di berbagai laporan): "insolasi" → "radiasi solar", "siklus diurnal" → "siklus harian (24 jam)", "Pooled" → "Gabungan", "Ground-Truth" → "Data Aktual", "blind-test" → "data uji", "black-box" → "sulit ditelusuri logikanya", "Apple-to-Apple" (salah tulis dari "Apples-to-Apples") → "adil (kondisi sama)", nama teknik yang di-*namedrop* tanpa penjelasan (Tikhonov, oblivious trees, TFT/PatchTST, Quantile Loss, CSI/HSS/Brier Score) dihapus atau diganti penjelasan sederhana karena tidak pernah dipakai nyata di laporan manapun.

**Laporan 7 (Dokumentasi Master)** paling banyak berubah karena isinya rangkuman dari semua laporan lain, jadi ikut menjadi usang saat laporan 3 & 4 direvisi. Yang diperbaiki:
- Klaim "37 fitur termasuk kode ID stasiun" diganti jadi "36 fitur, TANPA kode ID stasiun" — menyesuaikan revisi Laporan 3.
- Tabel akurasi 8 algoritma (dulu pakai angka Suhu lama) diganti dengan angka Curah Hujan terbaru — menyesuaikan revisi Laporan 4.
- Klaim "NusaKlim 3x lebih akurat dari Open-Meteo" (berlebihan, tidak didukung datanya sendiri) diganti jadi penjelasan yang jujur: lebih akurat di Suhu & Kelembapan, masih kalah di Curah Hujan.
- Tabel daftar 7 laporan resmi: ditambahkan baris Laporan 3b yang sebelumnya tidak tercantum, dan diperbaiki 1 nama file yang salah ketik.
- Grafik alur kerja (flowchart) dibuat ulang — grafik lama memuat simbol rusak, angka yang sudah tidak berlaku, dan klaim "3x lebih akurat" yang sama.

**Laporan 3b** juga sempat mengutip angka lama dari Laporan 4 (R² LSTM = 0.848, MAE Deep MLP = 0.756°C) yang sudah tidak ada lagi setelah Laporan 4 diganti ke Curah Hujan — sudah diperbaiki agar tidak mengutip angka yang sudah tidak ada sumbernya.

Seluruh 7 laporan PDF (dan salinan bernomornya) sudah dibuat ulang dan dicek bersih dari simbol rusak, sisa tanda bintang, dan angka "184".
