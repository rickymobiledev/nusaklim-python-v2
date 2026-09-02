# PANDUAN LENGKAP & NASKAH PRESENTASI EKSEKUTIF (SLIDE-BY-SLIDE)
**Proyek:** Sistem Prediksi Cuaca 7 Hari Berbasis Machine Learning NusaKlim AWS  
**Institusi:** Pusat Penelitian Kelapa Sawit (PPKS)  
**File Presentasi PPTX:** `Presentasi_Eksekutif_NusaKlim_Weather_AI_PPKS.pptx` (12 Slide Widescreen 16:9)

---

## ?? Tips Presentasi di Depan Klien & Pimpinan:
1. **Gunakan Analogi Sehari-hari:** Jangan terlalu banyak menggunakan rumus teknis matematika yang rumit; analogikan dengan kegiatan kebun sawit (seperti pemupukan, panen TBS, dan jalan licin).
2. **Fokus pada Nilai Bisnis (ROI):** Tekankan bahwa model ini menghemat biaya operasional kebun (mencegah pupuk hanyut ratusan juta rupiah) dan menghemat biaya IT server (karena LightGBM tidak butuh sewa GPU).
3. **Bawakan dengan Tenang & Percaya Diri:** Seluruh data, bukti empiris, dan 5 dokumen PDF pendukung sudah lengkap di workspace.

---

## ?? Naskah Presentasi per Slide:

### SLIDE 1: Judul & Pembuka
* **Judul Slide:** SISTEM PREDIKSI CUACA 7 HARI BERBASIS MACHINE LEARNING NUSAKLIM
* **Pesan Utama:** Solusi AI & Agroklimat Cerdas Berbasis 184 Stasiun Cuaca Perkebunan PPKS.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Selamat pagi/siang Bapak/Ibu pimpinan dan rekan-rekan sekalian. Hari ini saya akan mempresentasikan hasil pengembangan Sistem Kecerdasan Buatan (AI) Prediksi Cuaca 7 Hari untuk jaringan stasiun cuaca NusaKlim PPKS.*  
  > *Tujuan utama kita adalah mengubah 14,8 juta baris data mentah sensor di kebun kelapa sawit menjadi informasi ramalan cuaca 7 hari ke depan yang presisi, cepat, dan otomatis guna mendukung efisiensi operasional kebun."*

---

### SLIDE 2: Latar Belakang & Masalah Data Lapangan
* **Judul Slide:** 1. Latar Belakang: Dari Data Mentah Lapangan Menuju Solusi Agroklimat Cerdas
* **Poin Kunci:** Tantangan Data Kotor vs Kebutuhan Strategis Perkebunan Sawit.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Bapak/Ibu, stasiun cuaca AWS kita di kebun merekam data setiap 10-15 menit, totalnya mencapai 14,8 juta baris. Namun, data mentah ini sangat kotor karena ada sensor yang kabelnya copot sehingga membaca suhu minus -67?C seperti di Kutub, atau penakar hujan yang rusak sehingga mencatat hujan ratusan meter.*  
  > *Kenapa kita butuh sistem ini? Karena perkebunan kelapa sawit sangat bergantung pada cuaca. Jika kita memupuk saat besoknya hujan lebat, pupuk bernilai ratusan juta rupiah akan hanyut terbuang sia-sia. Begitu juga panen TBS dan transportasi truk akan terhambat jika jalan kebun berlumpur. Kita butuh data yang bersih dan model AI yang bisa meramal 7 hari ke depan secara otomatis."*

---

### SLIDE 3: Data Preprocessing & Kepatuhan Notulen Rapat
* **Judul Slide:** 2. Data Preprocessing: Standarisasi Kualitas & Kepatuhan Penuh Notulen PPKS
* **Poin Kunci:** Formula Notulen, Filter RTC 2000, Isolasi Sentinel, dan Arah Mata Angin Kardinal.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Seluruh proses pembersihan data dilakukan dengan 100% mematuhi Notulen Rapat PPKS tanggal 20 Agustus 2026.  
  > Pertama, kita mengonversi semua satuan ke standar internasional (?C, hPa, mm).  
  > Kedua, kita membuang data sampah pengujian tahun 2000 dan tag bengkel, serta menetapkan batas fisis yang wajar di iklim tropis.  
  > Ketiga, sesuai notulen, derajat arah angin telah kita kelompokkan ke 4 arah mata angin utama (Utara, Barat, Selatan, Timur). Hasilnya adalah dataset bersih harian (Golden Dataset) sebanyak 114.651 baris data yang siap diolah model AI."*

---

### SLIDE 4: Tiga Tingkat Dataset NusaKlim
* **Judul Slide:** 3. Arsitektur Tiga Tingkat Dataset NusaKlim yang Tersedia
* **Poin Kunci:** Raw (1.37 GB) vs Cleaned Interval (969 MB) vs Daily Aggregated (10 MB).
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Sekarang kita memiliki 3 file data yang rapi dan masing-masing punya fungsi spesifik:  
  > - File 1 (1.37 GB): Ini arsip mentah asli dari lapangan.  
  > - File 2 (969 MB): Ini data interval 15 menitan yang sudah bersih total. Sangat cocok untuk tim riset jika ingin meneliti pola cuaca per jam atau deteksi badai mendadak.  
  > - File 3 (10 MB): Ini data harian yang sudah diringkas (96 baris per hari menjadi 1 baris harian). File inilah yang dipakai oleh website untuk meramal cuaca 7 hari secara super cepat dan hemat memori server.  
  > Jadi, ukuran 10 MB bukan berarti data hilang, melainkan diringkas secara cerdas sesuai kebutuhan peramalan harian."*

---

### SLIDE 5: Audit Celah Data & Ketahanan Sistem
* **Judul Slide:** 4. Audit Celah Data (Data Gaps) & Ketahanan Sistem di Lapangan
* **Poin Kunci:** Kelengkapan 84.5% (Median 92.5%), 55.9% gap 1-3 hari, 4 Pilar Resiliensi AI.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Apakah ada stasiun yang sempat mati atau datanya bolong di kebun? Ada, rata-rata kelengkapan data kita 84,5% (median 92,5%), yang merupakan angka sangat wajar di perkebunan sawit terpencil karena kendala sinyal GSM atau mendung tebal.  
  > Kenapa sistem kita tetap bisa bekerja dengan sangat andal? Karena kita melatih 1 Model Global bersama-sama, sehingga stasiun yang datanya lengkap otomatis membantu stasiun yang sinyalnya sempat hilang. Model LightGBM kita juga pintar; jika ada sensor yang mati, dia otomatis mencari jalur alternatif dan tidak akan pernah error/hang. Kita sudah uji stres dengan sengaja membuang 10% data, akurasi model tetap sangat baik di angka MAE 1.2?C."*

---

### SLIDE 6: Langkah 1 - Model Prediksi Cuaca 7 Hari
* **Judul Slide:** 5. Langkah 1: Pengembangan Model Prediksi Cuaca Multi-Horizon (H+1 s/d H+7)
* **Poin Kunci:** 37 Fitur Rekayasa Fisis & 6 Output Parameter Cuaca Lengkap.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Untuk menghasilkan ramalan 7 hari, kita membangun 37 fitur prediktor pintar. Model melihat apa yang terjadi kemarin, memantau tren mingguan, membaca penurunan barometer udara sebagai tanda badai, dan selalu mencocokkan dengan kalender musiman monsun.  
  > Setiap stasiun akan mendapatkan 6 output lengkap: Suhu Rata-rata, Suhu Min/Max, Kelembapan, Curah Hujan dalam mm, Peluang Hujan %, dan Kategori Cuaca."*

---

### SLIDE 7: Bukti Akurasi Nyata (30 Hari Uji Lapangan)
* **Judul Slide:** 6. Bukti Akurasi Validasi Lapangan pada Data Observasi Aktual (30 Hari Uji)
* **Poin Kunci:** Suhu MAE 0.80?C (H+1) s/d 1.01?C (H+7), Kelembapan 2.7%, Akurasi Hujan 75.1%.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Bapak/Ibu, mari kita lihat bukti akurasinya yang diuji secara buta (blind test) pada 30 hari data aktual terakhir:  
  > - Angka MAE 0.80?C pada H+1 artinya: jika model memprediksi besok suhu 28.0?C, maka suhu asli lapangan hanya bergeser tipis di kisaran 27.2?C atau 28.8?C. Ini adalah standar akurasi yang sangat tinggi.  
  > - Error suhu naik sangat wajar dan stabil, dari 0.80?C ke 1.01?C pada hari ke-7.  
  > - Untuk kelembapan udara, errornya hanya 2.7% sampai 3.7%.  
  > - Dan untuk deteksi apakah hari itu akan hujan atau tidak, akurasinya stabil di angka 73% sampai 75%."*

---

### SLIDE 8: Benchmarking 8 Algoritma (ML vs Deep Learning)
* **Judul Slide:** 7. Benchmarking Komparatif: Machine Learning vs Deep Learning (8 Algoritma)
* **Poin Kunci:** LightGBM 100x Lebih Cepat (3.3s vs 328s) & Hemat Biaya Server dibanding LSTM.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Kita menguji 8 algoritma sekaligus (LightGBM, XGBoost, CatBoost, Random Forest, Ridge, LSTM, GRU, dan Deep MLP) agar keputusan kita berbasis bukti nyata.  
  > Dari segi akurasi murni, LSTM (Deep Learning) memang sedikit lebih presisi (MAE 0.71?C vs 0.76?C). TETAPI, perhatikan waktu pelatihannya: LightGBM hanya butuh 3,38 DETIK di komputer biasa, sedangkan LSTM butuh 328 DETIK (5,5 menit) dan wajib menggunakan kartu grafis GPU yang mahal.  
  > Untuk kebutuhan operasional harian website, LightGBM adalah pemenang mutlak karena cepat, murah, dan stabil."*

---

### SLIDE 9: Panduan Keputusan Klien (Decision Matrix)
* **Judul Slide:** 8. Panduan Pengambilan Keputusan Klien (Decision Framework)
* **Poin Kunci:** Skenario A (Operasional Web: LightGBM), Skenario B (Riset Jurnal: LSTM), Skenario C (Hybrid Dual-Engine).
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Kami menyajikan 3 opsi jelas bagi pimpinan/klien:  
  > - Opsi A: Jika fokus kita adalah meluncurkan website ramalan cuaca kebun yang murah, cepat, dan otomatis tanpa biaya sewa GPU, pilihlah LightGBM.  
  > - Opsi B: Jika fokus kita adalah menulis jurnal ilmiah atau riset akademis agroklimat mutakhir, LSTM adalah pilihan tepat.  
  > - Opsi C (Rekomendasi Terbaik Kita): Kita gunakan arsitektur Hybrid. LightGBM dipakai untuk website sehari-hari, sementara LSTM disimpan sebagai model pembanding di laboratorium riset."*

---

### SLIDE 10: Contoh Hasil Nyata Ramalan 7 Hari & Rekomendasi Agronomi
* **Judul Slide:** 9. Contoh Simulasi Ramalan 7 Hari & Rekomendasi Agronomi Kebun (Stasiun 227)
* **Poin Kunci:** Tampilan Simulasi Harian + Rekomendasi Tindakan Mandor Kebun (TBS / Pupuk).
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Ini adalah contoh tampilan nyata pada Stasiun 227 (Kebun Sei Pancur, Sumatera Utara).  
  > Sistem tidak hanya mengeluarkan angka teknis, tapi otomatis menerjemahkannya menjadi Rekomendasi Agronomi.  
  > Contoh pada hari Jumat: Model memprediksi Hujan Sedang 13.6 mm dengan peluang 70%. Sistem langsung memberi peringatan: 'Tunda pemupukan sore hari agar pupuk tidak hanyut'. Sebaliknya pada hari Sabtu: Hujan ringan hanya 3.9 mm, sistem memberitahu: 'Pemupukan pagi hari aman dilakukan'. Inilah yang membuat sistem ini sangat bernilai tinggi bagi manajemen kebun di lapangan."*

---

### SLIDE 11: Pipeline Otomatisasi Training Ulang (MLOps)
* **Judul Slide:** 10. Otomatisasi Training Ulang (Continuous Retraining MLOps Pipeline)
* **Poin Kunci:** 3 Trigger (Waktu, Volume Data, Drift), Waktu Training Ulang Cuma 61 Detik.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Jika ada penambahan data baru di masa depan, kita tidak perlu repot melatih model secara manual.  
  > Sistem bisa kita jadwalkan berjalan otomatis setiap Minggu malam, atau langsung jalan otomatis saat tim lapangan mengunggah file CSV baru, dan proses training ulang seluruh model 184 stasiun ini hanya memakan waktu 61 DETIK!  
  > Model baru akan diadu dulu dengan model lama (Champion vs Challenger). Jika model baru lebih pintar, barulah sistem mempromosikannya ke website operasional."*

---

### SLIDE 12: Kesimpulan & Rencana Langkah Selanjutnya
* **Judul Slide:** 11. Kesimpulan Akhir & Rencana Tindak Lanjut (Next Steps)
* **Poin Kunci:** Langkah 1 Selesai 100%, 5 Dokumen PDF Siap, Siap Masuk ke Langkah 2 & 3-4.
* **Naskah yang Anda Ucapkan (Speaker Script):**
  > *"Bapak/Ibu, tahap fondasi dan pengembangan Model AI 7-Hari (Langkah 1) telah selesai 100% dan terbukti sangat akurat, tangguh, serta siap pakai.  
  > Langkah berikutnya yang siap kita kerjakan adalah Langkah 2: Menghubungkan dan membandingkan model kita dengan API Open-Meteo sesuai arahan rapat, lalu membangun API Backend dan menghubungkannya ke Tampilan Website NusaKlim (Tabel Cepat dan Visual Dashboard).  
  > Terima kasih atas perhatian Bapak/Ibu sekalian. Saya membuka sesi tanya jawab jika ada hal yang ingin didiskusikan lebih lanjut."*
