import os, pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

pptx_path = r"d:\Downloads\nusaklim\Presentasi_Eksekutif_NusaKlim_Weather_AI_PPKS.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

C_NAVY = RGBColor(30, 58, 138)
C_TEAL = RGBColor(13, 148, 136)
C_DARK = RGBColor(15, 23, 42)
C_BODY = RGBColor(51, 65, 85)
C_MUTED = RGBColor(100, 116, 139)
C_LIGHT_BG = RGBColor(248, 250, 252)
C_ACCENT_BG = RGBColor(239, 246, 255)
C_BORDER = RGBColor(226, 232, 240)
C_WHITE = RGBColor(255, 255, 255)
C_GREEN = RGBColor(5, 150, 105)
C_RED = RGBColor(220, 38, 38)
C_GOLD = RGBColor(217, 119, 6)

blank_layout = prs.slide_layouts[6]

def add_header(slide, title_text, category_text="PUSAT PENELITIAN KELAPA SAWIT (PPKS) - NUSAKLIM WEATHER AI"):
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.4), Inches(11.733), Inches(0.9))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = C_ACCENT_BG
    top_bar.line.color.rgb = C_BORDER
    top_bar.line.width = Pt(1)
    tf = top_bar.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_top = Inches(0.08)
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(9.5)
    p_cat.font.bold = True
    p_cat.font.color.rgb = C_TEAL
    p_tit = tf.add_paragraph()
    p_tit.text = title_text
    p_tit.font.size = Pt(16)
    p_tit.font.bold = True
    p_tit.font.color.rgb = C_NAVY

def add_card(slide, left, top, width, height, bg_color=C_LIGHT_BG, border_color=C_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)
    return card

# ==================== SLIDE 1 ====================
slide1 = prs.slides.add_slide(blank_layout)
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = C_ACCENT_BG
bg1.line.fill.background()

c1 = add_card(slide1, Inches(1.2), Inches(1.2), Inches(10.933), Inches(5.1), bg_color=C_WHITE, border_color=C_NAVY)
tf1 = c1.text_frame
tf1.word_wrap = True
tf1.margin_left = Inches(0.6)
tf1.margin_top = Inches(0.4)

p0 = tf1.paragraphs[0]
p0.text = "PUSAT PENELITIAN KELAPA SAWIT (PPKS)"
p0.font.size = Pt(12)
p0.font.bold = True
p0.font.color.rgb = C_TEAL
p0.alignment = PP_ALIGN.CENTER

p1 = tf1.add_paragraph()
p1.text = "SISTEM PREDIKSI CUACA 7 HARI\nBERBASIS MACHINE LEARNING NUSAKLIM"
p1.font.size = Pt(25)
p1.font.bold = True
p1.font.color.rgb = C_NAVY
p1.alignment = PP_ALIGN.CENTER
p1.space_before = Pt(10)
p1.space_after = Pt(10)

p2 = tf1.add_paragraph()
p2.text = "Dokumentasi Lengkap: Data Preprocessing, Benchmarking 8 Model AI, Audit Celah Data, dan Panduan Keputusan Klien"
p2.font.size = Pt(11.5)
p2.font.color.rgb = C_BODY
p2.alignment = PP_ALIGN.CENTER

p3 = tf1.add_paragraph()
p3.text = "\n? Populasi Data: 14,8 Juta Baris Observasi | 184 Stasiun AWS Perkebunan Sawit\n? Model Champion: LightGBM Multi-Horizon (Akurasi MAE ?0.80?C | Retraining 61 Detik)"
p3.font.size = Pt(10.5)
p3.font.color.rgb = C_MUTED
p3.alignment = PP_ALIGN.CENTER

p4 = tf1.add_paragraph()
p4.text = "\nTim Data Analyst & AI Engineering PPKS | September 2026"
p4.font.size = Pt(9.5)
p4.font.bold = True
p4.font.color.rgb = C_NAVY
p4.alignment = PP_ALIGN.CENTER

slide1.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 1 - PEMBUKA):\n"
    "1. Sapa audiens dan pimpinan: 'Selamat pagi/siang Bapak/Ibu sekalian. Hari ini saya akan mempresentasikan Sistem AI Prediksi Cuaca 7 Hari untuk jaringan AWS NusaKlim PPKS.'\n"
    "2. Visi proyek: 'Tujuan kita adalah mengubah 14,8 juta data mentah sensor menjadi informasi ramalan cuaca 7 hari yang presisi, cepat, dan otomatis guna mendukung efisiensi kebun sawit.'\n"
    "3. Seluruh tahap telah selesai: data cleaning, uji 8 model AI, audit celah data, hingga kesiapan operasional.'"
)

# ==================== SLIDE 2 ====================
slide2 = prs.slides.add_slide(blank_layout)
add_header(slide2, "1. Latar Belakang: Dari Data Mentah Lapangan Menuju Solusi Agroklimat Cerdas")

c2_l = add_card(slide2, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
tf2_l = c2_l.text_frame
tf2_l.word_wrap = True
tf2_l.margin_left = Inches(0.3)
tf2_l.margin_top = Inches(0.3)
p = tf2_l.paragraphs[0]
p.text = "TANTANGAN DATA SENSOR LAPANGAN"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_RED

pts2_l = [
    ("Volume Raksasa:", "14.827.287 baris data interval mentah (1,37 GB) dari 184 stasiun AWS di pelosok kebun."),
    ("Gangguan Hardware:", "Sensor lepas menghasilkan kode aneh (-90?F / -67?C) dan counter loop hujan puluhan ribu mm."),
    ("Data Eror RTC 2000:", "Alat pertama kali dipasang merekam timestamp default tahun 1970/2000 yang belum terkalibrasi."),
    ("Intermitensi Lapangan:", "Sinyal GSM putus-putus dan solar panel drop memicu celah data (missing days).")
]
for t, d in pts2_l:
    p = tf2_l.add_paragraph()
    p.text = f"? {t} {d}"
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(8)

c2_r = add_card(slide2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_NAVY)
tf2_r = c2_r.text_frame
tf2_r.word_wrap = True
tf2_r.margin_left = Inches(0.3)
tf2_r.margin_top = Inches(0.3)
p = tf2_r.paragraphs[0]
p.text = "KEBUTUHAN STRATEGIS PERKEBUNAN SAWIT"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_NAVY

pts2_r = [
    ("Presisi Pemupukan:", "Mengetahui peluang hujan 1?3 hari ke depan agar pupuk mahal tidak hanyut terbawa erosi air."),
    ("Jadwal Panen & Angkut TBS:", "Mengantisipasi jalan kebun licin/banjir saat hujan lebat untuk kelancaran truk ke pabrik (PKS)."),
    ("Aplikasi Pestisida & Herbisida:", "Penyemprotan gulma hanya efektif jika tidak ada hujan 4?6 jam setelah aplikasi."),
    ("Otomatisasi Penuh:", "Sistem harus bisa mengupdate ramalan 7 hari setiap hari tanpa intervensi manual tim IT.")
]
for t, d in pts2_r:
    p = tf2_r.add_paragraph()
    p.text = f"? {t} {d}"
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(8)

slide2.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 2 - MASALAH & KEBUTUHAN):\n"
    "1. Bahasa awam: 'Bapak/Ibu, data sensor kebun kita sangat besar (14,8 juta baris), tapi kotor karena banyak kabel copot atau sensor rusak.'\n"
    "2. Kaitan bisnis: 'Perkebunan sawit sangat bergantung pada cuaca. Memupuk sebelum hujan lebat membuat pupuk hanyut terbuang sia-sia. Begitu juga panen TBS dan truk pengangkut butuh kepastian cuaca.'\n"
    "3. Poin kunci: 'Kita butuh data yang bersih dan model AI yang bisa meramal 7 hari ke depan secara otomatis.'"
)

# ==================== SLIDE 3 ====================
slide3 = prs.slides.add_slide(blank_layout)
add_header(slide3, "2. Data Preprocessing: Standarisasi Kualitas & Kepatuhan Penuh Notulen PPKS")

c3_1 = add_card(slide3, Inches(0.8), Inches(1.5), Inches(3.7), Inches(5.4))
tf3_1 = c3_1.text_frame
tf3_1.word_wrap = True
tf3_1.margin_left = Inches(0.2)
tf3_1.margin_top = Inches(0.2)
p = tf3_1.paragraphs[0]
p.text = "1. FORMULA NOTULEN"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_NAVY
f_list = [
    ("Suhu (?C):", "(tempout - 32) * 5/9"),
    ("Tekanan (hPa):", "bar * 33.864"),
    ("Hujan (mm):", "rain15 * 12.70"),
    ("Agregasi SUM:", "Hujan & Solar"),
    ("Agregasi MEAN:", "Suhu, RH, Barometer, Angin")
]
for k, v in f_list:
    p = tf3_1.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

c3_2 = add_card(slide3, Inches(4.8), Inches(1.5), Inches(3.7), Inches(5.4))
tf3_2 = c3_2.text_frame
tf3_2.word_wrap = True
tf3_2.margin_left = Inches(0.2)
tf3_2.margin_top = Inches(0.2)
p = tf3_2.paragraphs[0]
p.text = "2. FILTER KETAT & ANOMALI"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_TEAL
f_list2 = [
    ("Filter Tahun 2000:", "3.567 baris RTC default < 2022 dibersihkan total (Notulen Poin 5)."),
    ("Filter ID Bengkel:", "Tag WiFiLogger dan 9991?9995 disaring bersih."),
    ("Isolasi Sentinel:", "Kode 3276.7, 32767, 255, dan -1 otomatis diubah ke NaN."),
    ("Batas Fisis Realistis:", "Suhu 12?45?C, Barometer 920?1040 hPa, Hujan <=300 mm/hari.")
]
for k, v in f_list2:
    p = tf3_2.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

c3_3 = add_card(slide3, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_NAVY)
tf3_3 = c3_3.text_frame
tf3_3.word_wrap = True
tf3_3.margin_left = Inches(0.2)
tf3_3.margin_top = Inches(0.2)
p = tf3_3.paragraphs[0]
p.text = "3. ARAH MATA ANGIN (NOTULEN POIN 4)"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_NAVY
f_list3 = [
    ("Utara:", "> 315? s/d <= 45?"),
    ("Timur:", "> 45? s/d <= 135?"),
    ("Selatan:", "> 135? s/d <= 225?"),
    ("Barat:", "> 225? s/d <= 315?"),
    ("Hasil Akhir:", "114.651 Baris Data Harian Bersih Siap Pakai (Golden Dataset).")
]
for k, v in f_list3:
    p = tf3_3.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

slide3.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 3 - PREPROCESSING & NOTULEN):\n"
    "1. Tekankan kepatuhan: 'Seluruh proses preprocessing 100% mematuhi Notulen Rapat PPKS 20 Agustus 2026.'\n"
    "2. Jelaskan poinnya:\n"
    "   - Mengonversi satuan (?F ke ?C, bar ke hPa, rain15 ke mm).\n"
    "   - Menghapus data sampah tahun 2000 dan tag pengujian teknisi.\n"
    "   - Mengonversi arah angin derajat ke 4 mata angin kardinal (Utara, Barat, Selatan, Timur).\n"
    "3. Hasil akhir: Dataset Bersih Harian 114.651 baris data siap pakai.'"
)

# ==================== SLIDE 4 ====================
slide4 = prs.slides.add_slide(blank_layout)
add_header(slide4, "3. Arsitektur Tiga Tingkat Dataset NusaKlim yang Tersedia")

c4_1 = add_card(slide4, Inches(0.8), Inches(1.5), Inches(3.7), Inches(5.4))
tf4_1 = c4_1.text_frame
tf4_1.word_wrap = True
tf4_1.margin_left = Inches(0.25)
tf4_1.margin_top = Inches(0.25)
p = tf4_1.paragraphs[0]
p.text = "LEVEL 1: RAW DATASET"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_MUTED
t1_desc = [
    ("File:", "nusaklim-aws-reduce.csv"),
    ("Ukuran:", "1,37 GB (14,8 Juta Baris)"),
    ("Format:", "Interval 10?15 Menitan"),
    ("Kondisi:", "Data mentah asli langsung dari server logger lapangan."),
    ("Peran:", "Arsip historis cadangan (backup).")
]
for k, v in t1_desc:
    p = tf4_1.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

c4_2 = add_card(slide4, Inches(4.8), Inches(1.5), Inches(3.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_TEAL)
tf4_2 = c4_2.text_frame
tf4_2.word_wrap = True
tf4_2.margin_left = Inches(0.25)
tf4_2.margin_top = Inches(0.25)
p = tf4_2.paragraphs[0]
p.text = "LEVEL 2: CLEANED INTERVAL"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_TEAL
t2_desc = [
    ("File:", "nusaklim_cleaned_interval.csv"),
    ("Ukuran:", "969,45 MB (14,8 Juta Baris)"),
    ("Format:", "Interval Bersih 10?15 Menitan"),
    ("Kondisi:", "Bebas error, satuan baku (?C, hPa, mm), waktu lokal WIB."),
    ("Peran:", "Riset Deep Learning LSTM per jam, Analisis Diurnal 24-Jam, dan Deteksi Badai Menit-ke-Menit.")
]
for k, v in t2_desc:
    p = tf4_2.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

c4_3 = add_card(slide4, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.4), bg_color=C_WHITE, border_color=C_NAVY)
tf4_3 = c4_3.text_frame
tf4_3.word_wrap = True
tf4_3.margin_left = Inches(0.25)
tf4_3.margin_top = Inches(0.25)
p = tf4_3.paragraphs[0]
p.text = "LEVEL 3: DAILY AGGREGATED"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_NAVY
t3_desc = [
    ("File:", "nusaklim_daily_aggregated.csv"),
    ("Ukuran:", "10,12 MB (114.651 Baris)"),
    ("Format:", "Agregasi Harian (1 Baris / Hari)"),
    ("Kondisi:", "Lengkap dengan Suhu Min/Max, RH Min/Max, dan Mata Angin."),
    ("Peran:", "Mesin Utama Model Prediksi 7-Hari di Website & Dashboard Kebun PPKS.")
]
for k, v in t3_desc:
    p = tf4_3.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

slide4.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 4 - TIGA TINGKAT DATASET):\n"
    "1. Jelaskan 3 file yang kita hasilkan:\n"
    "   - File 1 (1.37 GB): Arsip mentah asli.\n"
    "   - File 2 (969 MB): Data interval 15 menitan yang sudah bersih. Dipakai jika tim riset ingin meneliti fluktuasi cuaca per jam atau badai mendadak.\n"
    "   - File 3 (10 MB): Data harian ringkas yang menjadi bahan bakar utama website ramalan cuaca 7 hari agar cepat dan hemat memori server.\n"
    "2. Poin penting: Ukuran 10 MB bukan karena data hilang, melainkan 96 catatan per hari diringkas rapi menjadi 1 baris harian.'"
)

# ==================== SLIDE 5 ====================
slide5 = prs.slides.add_slide(blank_layout)
add_header(slide5, "4. Audit Celah Data (Data Gaps) & Ketahanan Sistem di Lapangan")

c5_1 = add_card(slide5, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
tf5_1 = c5_1.text_frame
tf5_1.word_wrap = True
tf5_1.margin_left = Inches(0.3)
tf5_1.margin_top = Inches(0.3)
p = tf5_1.paragraphs[0]
p.text = "FAKTA KELENGKAPAN DATA JARINGAN AWS"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_NAVY

g_stats = [
    ("Rata-rata Kelengkapan:", "84.47 % (Median: 92.50 %)"),
    ("Stasiun Sangat Lengkap (>=90%):", "101 Stasiun (55.2% dari jaringan)"),
    ("Stasiun Lengkap (80% - 89%):", "20 Stasiun (10.9%)"),
    ("Stasiun Cukup (50% - 79%):", "50 Stasiun (27.3%)"),
    ("Durasi Gap:", "55.9% jeda hanya 1?3 hari akibat sinyal GSM atau solar panel drop saat mendung tebal.")
]
for k, v in g_stats:
    p = tf5_1.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9.5)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

c5_2 = add_card(slide5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_TEAL)
tf5_2 = c5_2.text_frame
tf5_2.word_wrap = True
tf5_2.margin_left = Inches(0.3)
tf5_2.margin_top = Inches(0.3)
p = tf5_2.paragraphs[0]
p.text = "MENGAPA MODEL TETAP AKURAT & ANTI-CRASH?"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_TEAL

g_reasons = [
    ("1. Global Model Pooling:", "Pola cuaca dari 101 stasiun yang sangat lengkap mentransfer ilmunya (knowledge transfer) ke stasiun yang ber-gap."),
    ("2. Native Missing Handling:", "LightGBM memiliki percabangan otomatis jika ada sensor NaN tanpa membuat sistem crash."),
    ("3. Kalender Musiman Astronomis:", "Siklus monsun sin/cos aktif 100% dari kalender bumi tanpa butuh sinyal AWS."),
    ("4. Hasil Uji Stress-Test:", "Bahkan saat 10% data sengaja dihilangkan, error suhu hanya naik tipis +0.26?C (Sangat Tangguh!).")
]
for k, v in g_reasons:
    p = tf5_2.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

slide5.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 5 - AUDIT CELAH DATA):\n"
    "1. Jawab pertanyaan gap: 'Rata-rata kelengkapan data kita 84,5% (median 92,5%), yang merupakan angka sangat baik di kebun terpencil.'\n"
    "2. Berikan keyakinan: 'Sistem kita dilatih secara Global, sehingga stasiun yang lengkap otomatis menutupi stasiun yang sempat hilang sinyal. LightGBM juga punya jalur cabang otomatis jika ada data kosong sehingga tidak akan pernah error/hang.'\n"
    "3. Uji stress-test membuktikan model tetap akurat walau kehilangan data.'"
)

# ==================== SLIDE 6 ====================
slide6 = prs.slides.add_slide(blank_layout)
add_header(slide6, "5. Langkah 1: Pengembangan Model Prediksi Cuaca Multi-Horizon (H+1 s/d H+7)")

c6_1 = add_card(slide6, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
tf6_1 = c6_1.text_frame
tf6_1.word_wrap = True
tf6_1.margin_left = Inches(0.3)
tf6_1.margin_top = Inches(0.3)
p = tf6_1.paragraphs[0]
p.text = "DESAIN REKAYASA FITUR (37 FITUR FISIS)"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_NAVY

f_eng = [
    ("Fitur Lag Historis:", "t-1, t-2, t-3, t-7 hari untuk Suhu, Kelembapan, Tekanan, Hujan, Solar, dan Angin."),
    ("Rata-rata Bergerak:", "Rolling Mean 3 hari dan 7 hari untuk menangkap tren mingguan."),
    ("Dinamika Atmosfer:", "Beda tekanan 1 hari (?P) sebagai indikator badai mendadak & defisit kelembapan (100 - RH)."),
    ("Siklus Musiman:", "sin/cos Day-of-Year dan Bulan untuk menangkap peralihan Monsun Barat/Timur."),
    ("Identitas Stasiun:", "Categorical embedding untuk 184 stasiun AWS.")
]
for k, v in f_eng:
    p = tf6_1.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

c6_2 = add_card(slide6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_GOLD)
tf6_2 = c6_2.text_frame
tf6_2.word_wrap = True
tf6_2.margin_left = Inches(0.3)
tf6_2.margin_top = Inches(0.3)
p = tf6_2.paragraphs[0]
p.text = "OUTPUT PREDIKSI 7-HARI YANG DIHASILKAN"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_GOLD

out_desc = [
    ("1. Suhu Rata-rata (?C):", "Estimasi suhu harian untuk H+1 hingga H+7."),
    ("2. Suhu Ekstrem (?C):", "Estimasi Suhu Minimum (malam) & Suhu Maksimum (siang)."),
    ("3. Kelembapan Relatif (%):", "Estimasi RH harian untuk menghitung evaporasi tanah."),
    ("4. Akumulasi Hujan (mm):", "Estimasi volume air hujan harian kuantitatif."),
    ("5. Peluang Kejadian Hujan (%):", "Probabilitas terjadinya hujan (0% s/d 100%)"),
    ("6. Klasifikasi Cuaca:", "Cerah Berawan, Hujan Ringan, Hujan Sedang, Hujan Lebat.")
]
for k, v in out_desc:
    p = tf6_2.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(5)

slide6.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 6 - DESAIN MODEL 7 HARI):\n"
    "1. Jelaskan cara kerja model: 'Model AI kita melihat tren kemarin, pergerakan barometer udara, dan kalender musim monsun.'\n"
    "2. Hasil output: 'Setiap stasiun akan mendapatkan 6 output lengkap: Suhu Avg, Suhu Min/Max, Kelembapan, Curah Hujan dalam mm, Peluang Hujan %, dan Kategori Cuaca.'"
)

# ==================== SLIDE 7 ====================
slide7 = prs.slides.add_slide(blank_layout)
add_header(slide7, "6. Bukti Akurasi Validasi Lapangan pada Data Observasi Aktual (30 Hari Uji)")

tbl_shape = slide7.shapes.add_table(8, 7, Inches(0.8), Inches(1.5), Inches(11.733), Inches(4.2))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(2.133)
tbl.columns[1].width = Inches(1.6)
tbl.columns[2].width = Inches(1.6)
tbl.columns[3].width = Inches(1.6)
tbl.columns[4].width = Inches(1.6)
tbl.columns[5].width = Inches(1.6)
tbl.columns[6].width = Inches(1.6)

headers_m = ["Horizon Waktu", "Suhu MAE (?C)", "Suhu RMSE", "Suhu R?", "RH MAE (%)", "Hujan MAE (mm)", "Akurasi Hujan (%)"]
for c_idx, h in enumerate(headers_m):
    cell = tbl.cell(0, c_idx)
    cell.text = h
    cell.fill.solid()
    cell.fill.fore_color.rgb = C_NAVY
    p = cell.text_frame.paragraphs[0]
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

m_rows = [
    ["H+1 (Besok)", "0.80 ?C", "1.05 ?C", "0.666", "2.73 %", "6.93 mm", "75.1 %"],
    ["H+2 (Hari ke-2)", "0.86 ?C", "1.12 ?C", "0.621", "3.23 %", "7.25 mm", "74.8 %"],
    ["H+3 (Hari ke-3)", "0.88 ?C", "1.15 ?C", "0.594", "3.53 %", "7.34 mm", "75.2 %"],
    ["H+4 (Hari ke-4)", "0.92 ?C", "1.19 ?C", "0.567", "3.66 %", "7.60 mm", "74.4 %"],
    ["H+5 (Hari ke-5)", "0.97 ?C", "1.25 ?C", "0.522", "3.67 %", "7.74 mm", "74.8 %"],
    ["H+6 (Hari ke-6)", "0.99 ?C", "1.29 ?C", "0.501", "3.66 %", "7.83 mm", "73.6 %"],
    ["H+7 (Hari ke-7)", "1.01 ?C", "1.31 ?C", "0.493", "3.73 %", "7.84 mm", "73.3 %"],
]

for r_idx, row in enumerate(m_rows):
    for c_idx, val in enumerate(row):
        cell = tbl.cell(r_idx + 1, c_idx)
        cell.text = val
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_ACCENT_BG if (r_idx % 2 == 0) else C_WHITE
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(9)
        p.font.color.rgb = C_DARK
        p.alignment = PP_ALIGN.CENTER
        if c_idx == 0 or c_idx == 1:
            p.font.bold = True

c7_b = add_card(slide7, Inches(0.8), Inches(5.9), Inches(11.733), Inches(1.1), bg_color=C_WHITE, border_color=C_GREEN)
tf7_b = c7_b.text_frame
tf7_b.word_wrap = True
tf7_b.margin_left = Inches(0.2)
tf7_b.margin_top = Inches(0.12)
p = tf7_b.paragraphs[0]
p.text = "KESIMPULAN AKURASI: Error Suhu rata-rata hanya ?0.80?C pada H+1 dan tetap stabil di ?1.01?C pada H+7. Akurasi kejadian hujan konsisten 73.3% ? 75.2% di seluruh horizon 7 hari!"
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = C_GREEN

slide7.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 7 - BUKTI AKURASI):\n"
    "1. Jelaskan angka akurasi secara santai: 'MAE 0.80?C pada H+1 artinya prediksi suhu kita rata-rata hanya meleset di bawah 1 derajat Celcius, sangat presisi.'\n"
    "2. Peluruhan error: 'Error naik perlahan dari 0.80?C ke 1.01?C di hari ke-7, yang membuktikan model sangat stabil.'\n"
    "3. Akurasi hujan: 'Mampu mendeteksi apakah hari itu akan hujan atau kering dengan ketepatan 73% sampai 75%.'"
)

# ==================== SLIDE 8 ====================
slide8 = prs.slides.add_slide(blank_layout)
add_header(slide8, "7. Benchmarking Komparatif: Machine Learning vs Deep Learning (8 Algoritma)")

tbl_shape8 = slide8.shapes.add_table(9, 7, Inches(0.8), Inches(1.5), Inches(11.733), Inches(4.3))
tbl8 = tbl_shape8.table
tbl8.columns[0].width = Inches(1.6)
tbl8.columns[1].width = Inches(2.333)
tbl8.columns[2].width = Inches(1.5)
tbl8.columns[3].width = Inches(1.5)
tbl8.columns[4].width = Inches(1.6)
tbl8.columns[5].width = Inches(1.6)
tbl8.columns[6].width = Inches(1.6)

headers8 = ["Kategori", "Nama Algoritma", "Suhu MAE", "Suhu R?", "Waktu Train", "RAM Server", "Status Produksi"]
for c_idx, h in enumerate(headers8):
    cell = tbl8.cell(0, c_idx)
    cell.text = h
    cell.fill.solid()
    cell.fill.fore_color.rgb = C_NAVY
    p = cell.text_frame.paragraphs[0]
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

rows8 = [
    ["Machine Learning", "LightGBM (Champion)", "0.766 ?C", "0.687", "3.38 detik", "220 MB", "PILIHAN UTAMA"],
    ["Machine Learning", "CatBoost", "0.756 ?C", "0.688", "5.93 detik", "380 MB", "Sangat Bagus"],
    ["Machine Learning", "XGBoost", "0.760 ?C", "0.689", "5.63 detik", "450 MB", "Sangat Bagus"],
    ["Machine Learning", "Random Forest", "0.755 ?C", "0.692", "135.91 detik", "1.200 MB", "Boros RAM"],
    ["Machine Learning", "Ridge Regression", "0.756 ?C", "0.666", "0.13 detik", "110 MB", "Baseline"],
    ["Deep Learning", "LSTM (2-Layer)", "0.712 ?C", "0.848", "328.36 detik", "850 MB", "Pilihan Riset"],
    ["Deep Learning", "GRU (2-Layer)", "0.727 ?C", "0.833", "537.23 detik", "720 MB", "Pilihan Riset"],
    ["Deep Learning", "Deep MLP (Dense)", "0.756 ?C", "0.641", "90.96 detik", "510 MB", "Standar"],
]

for r_idx, row in enumerate(rows8):
    for c_idx, val in enumerate(row):
        cell = tbl8.cell(r_idx + 1, c_idx)
        cell.text = val
        cell.fill.solid()
        if r_idx == 0:
            cell.fill.fore_color.rgb = C_ACCENT_BG
        elif r_idx == 5:
            cell.fill.fore_color.rgb = RGBColor(254, 243, 199)
        else:
            cell.fill.fore_color.rgb = C_WHITE if (r_idx % 2 == 1) else C_LIGHT_BG
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(9)
        p.font.color.rgb = C_DARK
        p.alignment = PP_ALIGN.CENTER
        if c_idx == 1:
            p.font.bold = True

c8_b = add_card(slide8, Inches(0.8), Inches(6.0), Inches(11.733), Inches(1.0), bg_color=C_WHITE, border_color=C_NAVY)
tf8_b = c8_b.text_frame
tf8_b.word_wrap = True
tf8_b.margin_left = Inches(0.2)
tf8_b.margin_top = Inches(0.1)
p = tf8_b.paragraphs[0]
p.text = "INSIGHT UTAMA: LightGBM 100x LEBIH CEPAT (3.3s vs 328s) dan hemat RAM tanpa perlu sewa GPU, dengan akurasi yang hampir identik dengan Deep Learning. Sangat ideal untuk website operasional!"
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = C_NAVY

slide8.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 8 - ML VS DEEP LEARNING):\n"
    "1. Perbandingan 8 model: 'LSTM unggul tipis di akurasi (0.71?C vs 0.76?C), TETAPI waktu trainingnya 5,5 menit dan butuh GPU mahal.'\n"
    "2. Keunggulan LightGBM: 'LightGBM hanya butuh 3,3 detik di CPU biasa, hemat RAM, dan otomatis menangani sensor yang sempat mati.'\n"
    "3. Pemenang operasional: 'LightGBM adalah pilihan paling rasional untuk sistem website.'"
)

# ==================== SLIDE 9 ====================
slide9 = prs.slides.add_slide(blank_layout)
add_header(slide9, "8. Panduan Pengambilan Keputusan Klien (Decision Framework)")

c9_1 = add_card(slide9, Inches(0.8), Inches(1.5), Inches(3.7), Inches(5.4), bg_color=C_WHITE, border_color=C_NAVY)
tf9_1 = c9_1.text_frame
tf9_1.word_wrap = True
tf9_1.margin_left = Inches(0.25)
tf9_1.margin_top = Inches(0.25)
p = tf9_1.paragraphs[0]
p.text = "SKENARIO A: OPERASIONAL WEB"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_NAVY
p1 = tf9_1.add_paragraph()
p1.text = "PILIHAN: LightGBM / CatBoost"
p1.font.size = Pt(10)
p1.font.bold = True
p1.font.color.rgb = C_TEAL
p1.space_before = Pt(4)

s_a = [
    ("Prioritas:", "Kecepatan, hemat biaya server, stabil, auto-retrain malam hari."),
    ("Keunggulan:", "Training cuma 3?5 detik di CPU biasa. Tidak butuh sewa GPU."),
    ("Ketahanan:", "Otomatis menangani sensor lapangan yang sempat NaN."),
    ("Rekomendasi:", "SANGAT DISARANKAN untuk website NusaKlim.")
]
for k, v in s_a:
    p = tf9_1.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

c9_2 = add_card(slide9, Inches(4.8), Inches(1.5), Inches(3.7), Inches(5.4))
tf9_2 = c9_2.text_frame
tf9_2.word_wrap = True
tf9_2.margin_left = Inches(0.25)
tf9_2.margin_top = Inches(0.25)
p = tf9_2.paragraphs[0]
p.text = "SKENARIO B: RISET & JURNAL"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_GOLD
p1 = tf9_2.add_paragraph()
p1.text = "PILIHAN: LSTM / GRU Neural Net"
p1.font.size = Pt(10)
p1.font.bold = True
p1.font.color.rgb = C_GOLD
p1.space_before = Pt(4)

s_b = [
    ("Prioritas:", "Akurasi sekuensial tertinggi, eksplorasi Deep Learning."),
    ("Keunggulan:", "Menghasilkan R? tertinggi (0.848) pada sekuens 14 hari."),
    ("Konsekuensi:", "Memerlukan server GPU dan waktu training lebih lama (5?9 menit)."),
    ("Rekomendasi:", "Sangat baik untuk bahan publikasi ilmiah PPKS.")
]
for k, v in s_b:
    p = tf9_2.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

c9_3 = add_card(slide9, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_GREEN)
tf9_3 = c9_3.text_frame
tf9_3.word_wrap = True
tf9_3.margin_left = Inches(0.25)
tf9_3.margin_top = Inches(0.25)
p = tf9_3.paragraphs[0]
p.text = "SKENARIO C: HYBRID TERBAIK"
p.font.size = Pt(11.5)
p.font.bold = True
p.font.color.rgb = C_GREEN
p1 = tf9_3.add_paragraph()
p1.text = "REKOMENDASI TIM AI PPKS"
p1.font.size = Pt(10)
p1.font.bold = True
p1.font.color.rgb = C_GREEN
p1.space_before = Pt(4)

s_c = [
    ("Konsep:", "Dual-Engine Architecture (Kombinasi Terbaik)."),
    ("Engine 1:", "LightGBM melayani peramalan real-time di website operasional."),
    ("Engine 2:", "LSTM berjalan di background sebagai benchmark/shadow evaluasi berkala."),
    ("Manfaat:", "Operasional kebun super cepat, riset ilmiah tetap terdepan.")
]
for k, v in s_c:
    p = tf9_3.add_paragraph()
    p.text = f"? {k} {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

slide9.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 9 - MATRIKS KEPUTUSAN):\n"
    "1. Berikan 3 opsi jelas bagi pimpinan:\n"
    "   - 'Opsi A (Website Operasional): LightGBM (Cepat, stabil, tanpa GPU).'\n"
    "   - 'Opsi B (Riset Akademis): LSTM (Akurasi sekuensial tinggi).'\n"
    "   - 'Opsi C (Solusi Ideal Hybrid): LightGBM sebagai mesin utama di website, LSTM sebagai shadow model di laboratorium riset.'\n"
    "2. Pesan kunci: Opsi C memberikan manfaat operasional sekaligus riset.'"
)

# ==================== SLIDE 10 ====================
slide10 = prs.slides.add_slide(blank_layout)
add_header(slide10, "9. Contoh Simulasi Ramalan 7 Hari & Rekomendasi Agronomi Kebun (Stasiun 227)")

tbl_shape10 = slide10.shapes.add_table(8, 7, Inches(0.8), Inches(1.5), Inches(11.733), Inches(4.3))
tbl10 = tbl_shape10.table
tbl10.columns[0].width = Inches(1.8)
tbl10.columns[1].width = Inches(1.6)
tbl10.columns[2].width = Inches(1.4)
tbl10.columns[3].width = Inches(1.4)
tbl10.columns[4].width = Inches(1.4)
tbl10.columns[5].width = Inches(1.4)
tbl10.columns[6].width = Inches(2.733)

headers10 = ["Horizon / Hari", "Kondisi Cuaca", "Suhu (?C)", "Kelembapan", "Curah Hujan", "Peluang Hujan", "Rekomendasi Agronomi Kebun Sawit"]
for c_idx, h in enumerate(headers10):
    cell = tbl10.cell(0, c_idx)
    cell.text = h
    cell.fill.solid()
    cell.fill.fore_color.rgb = C_NAVY
    p = cell.text_frame.paragraphs[0]
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

sim_rows = [
    ["H+1 (Kamis, 20 Ags)", "Hujan Ringan", "23.3 ?C", "85.9 %", "1.4 mm", "55 %", "Aman untuk panen TBS & penyerbukan."],
    ["H+2 (Jumat, 21 Ags)", "Hujan Sedang", "23.7 ?C", "84.2 %", "13.6 mm", "70 %", "Tunda pemupukan sore hari (rawan hanyut)."],
    ["H+3 (Sabtu, 22 Ags)", "Hujan Ringan", "24.4 ?C", "84.0 %", "3.9 mm", "55 %", "Aplikasi pupuk pagi hari aman dilakukan."],
    ["H+4 (Minggu, 23 Ags)", "Hujan Ringan", "24.0 ?C", "83.9 %", "7.8 mm", "61 %", "Monitoring saluran drainase blok rendah."],
    ["H+5 (Senin, 24 Ags)", "Hujan Ringan", "24.0 ?C", "83.8 %", "5.0 mm", "57 %", "Jalur transportasi angkut TBS normal."],
    ["H+6 (Selasa, 25 Ags)", "Hujan Ringan", "24.0 ?C", "83.0 %", "2.2 mm", "55 %", "Optimal untuk pembersihan piringan sawit."],
    ["H+7 (Rabu, 26 Ags)", "Hujan Ringan", "24.1 ?C", "82.1 %", "3.3 mm", "55 %", "Kondisi lapangan stabil untuk operasional."],
]

for r_idx, row in enumerate(sim_rows):
    for c_idx, val in enumerate(row):
        cell = tbl10.cell(r_idx + 1, c_idx)
        cell.text = val
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_ACCENT_BG if (r_idx % 2 == 0) else C_WHITE
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(9)
        p.font.color.rgb = C_DARK
        p.alignment = PP_ALIGN.CENTER if c_idx < 6 else PP_ALIGN.LEFT
        if c_idx == 0:
            p.font.bold = True

c10_b = add_card(slide10, Inches(0.8), Inches(6.0), Inches(11.733), Inches(1.0), bg_color=C_WHITE, border_color=C_TEAL)
tf10_b = c10_b.text_frame
tf10_b.word_wrap = True
tf10_b.margin_left = Inches(0.2)
tf10_b.margin_top = Inches(0.1)
p = tf10_b.paragraphs[0]
p.text = "NILAI BISNIS LANGSUNG: Mandor dan Manajer Kebun tidak hanya melihat angka cuaca, tetapi langsung mendapatkan panduan tindakan agronomi harian untuk efisiensi biaya pemupukan dan keselamatan panen!"
p.font.size = Pt(10)
p.font.bold = True
p.font.color.rgb = C_TEAL

slide10.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 10 - DEMO OUTPUT NYATA):\n"
    "1. Tunjukkan manfaat praktis: 'Bapak/Ibu, sistem kita langsung menerjemahkan angka cuaca menjadi Rekomendasi Agronomi bagi mandor kebun.'\n"
    "2. Contoh: 'Di hari Jumat diprediksi hujan 13.6 mm, sistem otomatis memberi alert: Tunda pemupukan sore hari agar pupuk tidak hanyut terbawa air.'\n"
    "3. Manfaat: 'Sangat menghemat biaya pupuk dan mengoptimalkan jadwal panen TBS.'"
)

# ==================== SLIDE 11 ====================
slide11 = prs.slides.add_slide(blank_layout)
add_header(slide11, "10. Otomatisasi Training Ulang (Continuous Retraining MLOps Pipeline)")

c11_1 = add_card(slide11, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
tf11_1 = c11_1.text_frame
tf11_1.word_wrap = True
tf11_1.margin_left = Inches(0.3)
tf11_1.margin_top = Inches(0.3)
p = tf11_1.paragraphs[0]
p.text = "TIGA PEMICU (TRIGGER) RETRAINING"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_NAVY

tr_list = [
    ("1. Pemicu Waktu Terjadwal (Time-Based):", "Berjalan otomatis setiap Minggu malam pk 23:00 WIB untuk memperbarui pola cuaca terbaru."),
    ("2. Pemicu Volume Data (Data-Volume-Based):", "Otomatis aktif saat ada batch upload data baru >= 10.000 baris atau penambahan stasiun baru."),
    ("3. Pemicu Penurunan Akurasi (Drift-Based):", "Aktif jika error MAE pada data aktual harian melebihi batas toleransi (anomali El Nino mendadak).")
]
for k, v in tr_list:
    p = tf11_1.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(8)

c11_2 = add_card(slide11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_GREEN)
tf11_2 = c11_2.text_frame
tf11_2.word_wrap = True
tf11_2.margin_left = Inches(0.3)
tf11_2.margin_top = Inches(0.3)
p = tf11_2.paragraphs[0]
p.text = "KEUNGGULAN OPERASIONAL RETRAINING"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_GREEN

op_list = [
    ("Kecepatan Komputasi Kilat:", "Hanya butuh ~61 detik untuk melatih ulang seluruh model 7-hari pada 184 stasiun."),
    ("Validasi Otomatis (Champion vs Challenger):", "Model baru hanya akan menggantikan model lama jika performa MAE/RMSE terbukti lebih baik."),
    ("Manajemen Versi Aman (Versioning):", "Setiap model disimpan dengan timestamp (models/weather_model_bundle_YYYYMMDD.joblib) sehingga aman untuk rollback."),
    ("Skrip Siap Pakai:", "retrain_pipeline.py dapat langsung dipasang di Windows Task Scheduler / Linux Cron.")
]
for k, v in op_list:
    p = tf11_2.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

slide11.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 11 - RETRAINING OTOMATIS):\n"
    "1. Jelaskan bagaimana sistem terus belajar: 'Jika ada data baru masuk, sistem otomatis melatih ulang modelnya hanya dalam 61 DETIK.'\n"
    "2. Skema pengamanan: 'Model baru akan diadu dulu dengan model lama (Champion vs Challenger). Jika performanya lebih baik, barulah sistem mempromosikannya ke website operasional.'"
)

# ==================== SLIDE 12 ====================
slide12 = prs.slides.add_slide(blank_layout)
add_header(slide12, "11. Kesimpulan Akhir & Rencana Tindak Lanjut (Next Steps)")

c12_1 = add_card(slide12, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.4))
tf12_1 = c12_1.text_frame
tf12_1.word_wrap = True
tf12_1.margin_left = Inches(0.3)
tf12_1.margin_top = Inches(0.3)
p = tf12_1.paragraphs[0]
p.text = "PENCAPAIAN TAHAP LANGKAH 1"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_NAVY

p_done = [
    ("1. Data Preprocessing & Cleaning 100%:", "14.8M baris mentah dibersihkan, 114k baris harian siap pakai, 5 dokumen PDF resmi selesai dibuat."),
    ("2. Model AI 7-Hari Terlatih & Tervalidasi:", "LightGBM Champion beroperasi dengan akurasi MAE ?0.80?C dan akurasi hujan 75.1%."),
    ("3. Benchmarking 8 Algoritma Tuntas:", "Panduan keputusan klien telah terdokumentasi lengkap berbasis bukti empiris."),
    ("4. Resiliensi Teruji:", "Sistem terbukti kebal terhadap celah data (missing days) di kebun.")
]
for k, v in p_done:
    p = tf12_1.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(7)

c12_2 = add_card(slide12, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), bg_color=C_ACCENT_BG, border_color=C_NAVY)
tf12_2 = c12_2.text_frame
tf12_2.word_wrap = True
tf12_2.margin_left = Inches(0.3)
tf12_2.margin_top = Inches(0.3)
p = tf12_2.paragraphs[0]
p.text = "RENCANA LANGKAH BERIKUTNYA"
p.font.size = Pt(12.5)
p.font.bold = True
p.font.color.rgb = C_NAVY

p_next = [
    ("Langkah 2: Komparasi API Open-Meteo (Notulen Poin 9):", "Menarik data ramalan dari Open-Meteo API dan membandingkannya dengan model internal PPKS."),
    ("Langkah 3: Pembuatan REST API Backend (FastAPI):", "Membangun endpoint API /forecast/{stn_id} untuk integrasi ke website & aplikasi mobile."),
    ("Langkah 4: Integrasi Dashboard UI/UX (Notulen Poin 10):", "Menyajikan tampilan Dual-View (Mode Tabel Cepat untuk Lapangan + Mode Visual Interaktif untuk Manajemen)."),
    ("Langkah 5: Deployment Server & Cron Scheduling:", "Menjadwalkan inferensi otomatis harian di server produksi PPKS.")
]
for k, v in p_next:
    p = tf12_2.add_paragraph()
    p.text = f"? {k}\n  {v}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_BODY
    p.space_before = Pt(6)

slide12.notes_slide.notes_text_frame.text = (
    "PETUNJUK PRESENTASI (SLIDE 12 - PENUTUP & NEXT STEPS):\n"
    "1. Rangkum pencapaian: 'Seluruh fondasi data dan Model AI 7-Hari telah selesai 100% dan terbukti sangat akurat serta stabil.'\n"
    "2. Arahkan ke tahap berikutnya: 'Kita siap melangkah ke Langkah 2 (komparasi Open-Meteo) dan Langkah 3-4 (pembuatan API Backend dan Dashboard Website).'\n"
    "3. Tutup dengan apresiasi dan buka sesi tanya jawab.'"
)

# Save Presentation
prs.save(pptx_path)
print(f"SUCCESS: PowerPoint Presentation saved to: {pptx_path}")
print(f"Total Slides: {len(prs.slides)} slides with complete embedded Speaker Notes!")
