import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

pptx_path = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\report\Presentasi_Data_Cleaning_Preprocessing_EDA_NusaKlim_PPKS.pptx"
fig_dir = r"D:\Projects\Kodepanda\Nusaklim\nusaklim\figures"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ==================== COLOR PALETTE (konsisten dgn presentasi eksekutif) ====================
C_NAVY_DARK = RGBColor(15, 32, 66)
C_NAVY_PRI  = RGBColor(30, 58, 138)
C_TEAL_PRI  = RGBColor(13, 148, 136)
C_TEAL_DARK = RGBColor(15, 118, 110)
C_GREEN_ACC = RGBColor(5, 150, 105)
C_GOLD_ACC  = RGBColor(217, 119, 6)
C_RED_ACC   = RGBColor(220, 38, 38)
C_DARK_TXT  = RGBColor(15, 23, 42)
C_BODY_TXT  = RGBColor(51, 65, 85)
C_MUTED_TXT = RGBColor(100, 116, 139)
C_WHITE     = RGBColor(255, 255, 255)
C_CARD_BG   = RGBColor(248, 250, 252)
C_ACCENT_BG = RGBColor(239, 246, 255)
C_BORDER    = RGBColor(226, 232, 240)
C_BORDER_HI = RGBColor(147, 197, 253)

blank_layout = prs.slide_layouts[6]

# ==================== HELPERS ====================

def new_slide():
    return prs.slides.add_slide(blank_layout)

def set_notes(slide, text):
    notes_tf = slide.notes_slide.notes_text_frame
    notes_tf.text = text

def draw_header(slide, title_text, category_text, badge_color=C_TEAL_PRI):
    top_bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.95))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = C_NAVY_DARK
    top_bar.line.fill.background()
    tf = top_bar.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_top = Inches(0.07)
    p0 = tf.paragraphs[0]
    p0.text = category_text.upper()
    p0.font.size = Pt(10)
    p0.font.bold = True
    p0.font.color.rgb = RGBColor(45, 212, 191)
    p1 = tf.add_paragraph()
    p1.text = title_text
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

def draw_card(slide, left, top, width, height, bg_color=C_WHITE, border_color=C_BORDER, line_width=1.2):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(line_width)
    return card

def add_textbox(slide, left, top, width, height, lines, base_size=13, color=C_BODY_TXT, bold_first=False, align=PP_ALIGN.LEFT, bullet=True, line_spacing=1.12):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(lines):
        if isinstance(item, tuple):
            text, opts = item
        else:
            text, opts = item, {}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        prefix = "\u2022  " if (bullet and opts.get("bullet", True) and opts.get("level", 0) == 0) else ("   \u2013  " if bullet and opts.get("level", 0) == 1 else "")
        p.text = prefix + text
        p.font.size = Pt(opts.get("size", base_size))
        p.font.bold = opts.get("bold", False)
        p.font.italic = opts.get("italic", False)
        p.font.color.rgb = opts.get("color", color)
        p.alignment = opts.get("align", align)
        p.line_spacing = opts.get("line_spacing", line_spacing)
        p.space_after = Pt(opts.get("space_after", 6))
    return box

def add_footer(slide, num):
    box = slide.shapes.add_textbox(Inches(0.5), Inches(7.12), Inches(12.333), Inches(0.3))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = f"PPKS \u2013 NusaKlim Weather AI  |  Data Cleaning & Preprocessing/EDA  |  Slide {num}"
    p.font.size = Pt(9)
    p.font.color.rgb = C_MUTED_TXT
    p.alignment = PP_ALIGN.CENTER

def add_table(slide, left, top, width, height, data, col_widths=None, header_bg=C_NAVY_PRI, font_size=10.5, header_font_size=11):
    rows = len(data)
    cols = len(data[0])
    gtable = slide.shapes.add_table(rows, cols, left, top, width, height).table
    if col_widths:
        for i, w in enumerate(col_widths):
            gtable.columns[i].width = w
    for r in range(rows):
        for c in range(cols):
            cell = gtable.cell(r, c)
            cell.text = str(data[r][c])
            para = cell.text_frame.paragraphs[0]
            para.font.size = Pt(header_font_size if r == 0 else font_size)
            para.font.bold = (r == 0)
            para.font.color.rgb = C_WHITE if r == 0 else C_DARK_TXT
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_bg if r == 0 else (C_CARD_BG if r % 2 == 0 else C_WHITE)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.07)
            cell.margin_right = Inches(0.07)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
    return gtable

def add_image(slide, path, left, top, width=None, height=None):
    if os.path.exists(path):
        slide.shapes.add_picture(path, left, top, width=width, height=height)
    else:
        box = draw_card(slide, left, top, width or Inches(6), height or Inches(3), bg_color=C_CARD_BG)
        tf = box.text_frame
        tf.text = f"[Gambar tidak ditemukan: {os.path.basename(path)}]"
        tf.paragraphs[0].font.size = Pt(10)
        tf.paragraphs[0].font.color.rgb = C_MUTED_TXT

def add_kicker_number(slide, n_str, top=Inches(1.4)):
    box = slide.shapes.add_textbox(Inches(0.5), top, Inches(1.0), Inches(0.6))
    p = box.text_frame.paragraphs[0]
    p.text = n_str
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = C_TEAL_DARK

SLIDE_NUM = [0]
def track(slide):
    SLIDE_NUM[0] += 1
    add_footer(slide, SLIDE_NUM[0])
    return SLIDE_NUM[0]

CAT1 = "LAPORAN 1 \u2013 DATA CLEANING TINGKAT INTERVAL"
CAT2 = "LAPORAN 2 \u2013 PREPROCESSING & EXPLORATORY DATA ANALYSIS (EDA)"

# ============================================================================
# SLIDE 1: COVER
# ============================================================================
s = new_slide()
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg.fill.solid(); bg.fill.fore_color.rgb = C_NAVY_DARK; bg.line.fill.background()
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
band.fill.solid(); band.fill.fore_color.rgb = C_TEAL_PRI; band.line.fill.background()

card = draw_card(s, Inches(1.0), Inches(1.15), Inches(11.333), Inches(5.2), bg_color=C_WHITE, border_color=C_TEAL_PRI, line_width=2.0)
tf = card.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.6)
tf.margin_top = Inches(0.45)
p0 = tf.paragraphs[0]
p0.text = "PUSAT PENELITIAN KELAPA SAWIT (PPKS)"
p0.font.size = Pt(13); p0.font.bold = True; p0.font.color.rgb = C_TEAL_PRI
p0.alignment = PP_ALIGN.CENTER

p1 = tf.add_paragraph()
p1.text = "DATA CLEANING, PREPROCESSING & EXPLORATORY\nDATA ANALYSIS (EDA) \u2013 NUSAKLIM WEATHER AI"
p1.font.size = Pt(26); p1.font.bold = True; p1.font.color.rgb = C_NAVY_PRI
p1.alignment = PP_ALIGN.CENTER
p1.space_before = Pt(10); p1.space_after = Pt(10)

p2 = tf.add_paragraph()
p2.text = "Ringkasan Dua Laporan Teknis: (1) Data Cleaning Tingkat Interval Telemetri, dan\n(2) Preprocessing Data & Exploratory Data Analysis Cuaca AWS"
p2.font.size = Pt(13); p2.font.color.rgb = C_BODY_TXT
p2.alignment = PP_ALIGN.CENTER
p2.space_after = Pt(18)

badges = [
    ("14,8 JUTA", "Baris Data Mentah"),
    ("184", "Stasiun AWS PPKS"),
    ("114.651", "Baris Data Harian Bersih"),
    ("100%", "Sesuai Notulen Rapat"),
]
bw, bh, gap = Inches(2.5), Inches(1.05), Inches(0.15)
total_w = bw * 4 + gap * 3
start_x = Inches(1.0) + (Inches(11.333) - total_w) / 2
for i, (num, label) in enumerate(badges):
    bx = start_x + i * (bw + gap)
    bcard = draw_card(s, bx, Inches(5.15), bw, bh, bg_color=C_ACCENT_BG, border_color=C_BORDER_HI, line_width=1.3)
    btf = bcard.text_frame
    btf.word_wrap = True
    bp0 = btf.paragraphs[0]
    bp0.text = num
    bp0.font.size = Pt(17); bp0.font.bold = True; bp0.font.color.rgb = C_NAVY_PRI
    bp0.alignment = PP_ALIGN.CENTER
    bp1 = btf.add_paragraph()
    bp1.text = label
    bp1.font.size = Pt(9.5); bp1.font.color.rgb = C_BODY_TXT
    bp1.alignment = PP_ALIGN.CENTER

meta = s.shapes.add_textbox(Inches(1.0), Inches(6.55), Inches(11.333), Inches(0.6))
mp = meta.text_frame.paragraphs[0]
mp.text = "Disusun oleh Tim Data Analyst & AI Engineering PPKS  |  September 2026"
mp.font.size = Pt(11); mp.font.color.rgb = RGBColor(203, 213, 225)
mp.alignment = PP_ALIGN.CENTER

track(s)
set_notes(s, (
    "Selamat pagi/siang Bapak/Ibu sekalian. Pada kesempatan ini saya akan mempresentasikan secara khusus dua laporan "
    "fondasi dari proyek NusaKlim Weather AI, yaitu: pertama, Laporan Data Cleaning Tingkat Interval Telemetri, dan kedua, "
    "Laporan Preprocessing Data dan Exploratory Data Analysis (EDA).\n\n"
    "Presentasi kali ini SENGAJA hanya berfokus pada tahap pembersihan dan eksplorasi data \u2014 belum masuk ke pembahasan "
    "model prediksi cuaca, benchmarking algoritma, atau audit ketahanan model, karena itu adalah topik laporan berikutnya.\n\n"
    "Sebagai gambaran umum: kita mengolah 14,8 juta baris data mentah dari 184 stasiun cuaca otomatis (AWS) yang tersebar "
    "di seluruh perkebunan kelapa sawit PPKS, sejak Januari 2022 hingga Agustus 2026. Seluruh proses pembersihan dan "
    "standarisasi 100% mengacu pada Notulen Rapat Tim Data Analyst dan Peneliti PPKS tanggal 20 Agustus 2026. "
    "Hasil akhirnya adalah dataset harian bersih sebanyak 114.651 baris yang siap dipakai untuk riset dan pengembangan model."
))

# ============================================================================
# SLIDE 2: AGENDA / RUANG LINGKUP
# ============================================================================
s = new_slide()
draw_header(s, "Ruang Lingkup & Agenda Presentasi", "Pembuka")
add_textbox(s, Inches(0.6), Inches(1.5), Inches(11.5), Inches(0.7), [
    ("Presentasi ini merangkum 2 dari 5 dokumen teknis proyek NusaKlim, yaitu dokumen fondasi kualitas data:", {"size": 14, "bold": True, "color": C_DARK_TXT, "bullet": False}),
], bullet=False)

col_w = Inches(5.55)
c1 = draw_card(s, Inches(0.6), Inches(2.3), col_w, Inches(3.9), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.5)
tf1 = c1.text_frame; tf1.word_wrap = True; tf1.margin_left = Inches(0.25); tf1.margin_top = Inches(0.2)
p = tf1.paragraphs[0]; p.text = "LAPORAN 1"; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = C_NAVY_PRI
p = tf1.add_paragraph(); p.text = "Data Cleaning Tingkat Interval Telemetri"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = C_DARK_TXT; p.space_after = Pt(8)
for line in [
    "Pembersihan 14,8 juta baris data interval 10-15 menit",
    "Konversi satuan ke standar metrik (\u00b0C, hPa, mm)",
    "Isolasi nilai sentinel error hardware sensor",
    "Menghasilkan file nusaklim_cleaned_interval.csv (969 MB)",
]:
    p = tf1.add_paragraph(); p.text = "\u2022  " + line; p.font.size = Pt(12.5); p.font.color.rgb = C_BODY_TXT; p.space_after = Pt(6)

c2 = draw_card(s, Inches(6.35), Inches(2.3), col_w, Inches(3.9), bg_color=C_ACCENT_BG, border_color=C_TEAL_PRI, line_width=1.5)
tf2 = c2.text_frame; tf2.word_wrap = True; tf2.margin_left = Inches(0.25); tf2.margin_top = Inches(0.2)
p = tf2.paragraphs[0]; p.text = "LAPORAN 2"; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = C_TEAL_DARK
p = tf2.add_paragraph(); p.text = "Preprocessing Data & Exploratory Data Analysis (EDA)"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = C_DARK_TXT; p.space_after = Pt(8)
for line in [
    "Audit kualitas & Quality Control (QC) data mentah",
    "Agregasi 15-menit menjadi 1 baris harian per stasiun",
    "Statistik deskriptif, korelasi, dan pola musiman cuaca",
    "Menghasilkan file nusaklim_daily_aggregated.csv (10,1 MB)",
]:
    p = tf2.add_paragraph(); p.text = "\u2022  " + line; p.font.size = Pt(12.5); p.font.color.rgb = C_BODY_TXT; p.space_after = Pt(6)

track(s)
set_notes(s, (
    "Sebelum masuk ke detail, saya ingin menyamakan konteks dulu. Proyek NusaKlim ini sebenarnya punya 5 dokumen laporan "
    "resmi, tapi hari ini kita HANYA membahas dua yang paling fondasional.\n\n"
    "Laporan pertama adalah Data Cleaning Tingkat Interval \u2014 ini adalah pembersihan data pada level paling mentah, "
    "yaitu data yang direkam sensor setiap 10 sampai 15 menit sekali, tanpa diringkas dulu. Outputnya adalah file "
    "nusaklim_cleaned_interval.csv.\n\n"
    "Laporan kedua adalah Preprocessing dan EDA \u2014 ini menjelaskan bagaimana data interval tadi diagregasi/diringkas "
    "menjadi 1 baris per hari per stasiun, plus hasil analisis eksploratif (statistik, korelasi, pola musiman) untuk "
    "memahami karakteristik cuaca di kebun. Outputnya adalah file nusaklim_daily_aggregated.csv yang nantinya dipakai "
    "untuk model prediksi 7 hari (dibahas di laporan terpisah).\n\n"
    "Jadi alurnya: Data Mentah \u2192 (Laporan 1) Dibersihkan di level interval \u2192 (Laporan 2) Diagregasi harian + dianalisis \u2192 "
    "baru siap masuk ke pemodelan AI."
))

# ============================================================================
# SLIDE 3: RINGKASAN EKSEKUTIF DATASET INTERVAL
# ============================================================================
s = new_slide()
draw_header(s, "Ringkasan Eksekutif & Tujuan Dataset Interval Bersih", CAT1)
add_textbox(s, Inches(0.6), Inches(1.5), Inches(11.9), Inches(1.3), [
    ("Untuk kebutuhan riset agroklimat presisi tinggi dan pemodelan Deep Learning (LSTM/RNN), diekstrak dataset bersih tingkat interval 10\u201315 menit: nusaklim_cleaned_interval.csv.", {"size": 13.5}),
    ("Berbeda dari nusaklim_daily_aggregated.csv (1 baris/hari untuk model tabular), file ini mempertahankan SELURUH titik pencatatan resolusi tinggi dalam keadaan bersih, terkalibrasi, dan bebas eror hardware.", {"size": 13.5}),
])

kpis = [
    ("969,45 MB", "Ukuran File Bersih", "dari 1,37 GB mentah (turun 30,9%)"),
    ("14.823.713", "Baris Valid", "dari 14.827.287 baris mentah"),
    ("184", "Stasiun AWS", "seluruh kebun sawit PPKS"),
    ("2022\u20132026", "Cakupan Waktu", "01 Jan 2022 s/d 19 Agu 2026 (WIB)"),
]
kw, kh, kgap = Inches(2.85), Inches(1.7), Inches(0.15)
kx0 = Inches(0.6)
for i, (num, label, sub) in enumerate(kpis):
    kx = kx0 + i * (kw + kgap)
    kcard = draw_card(s, kx, Inches(3.1), kw, kh, bg_color=C_WHITE, border_color=C_BORDER_HI, line_width=1.5)
    stripe = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, kx, Inches(3.1), kw, Inches(0.08))
    stripe.fill.solid(); stripe.fill.fore_color.rgb = C_NAVY_PRI; stripe.line.fill.background()
    ktf = kcard.text_frame; ktf.word_wrap = True; ktf.margin_top = Inches(0.18)
    kp0 = ktf.paragraphs[0]; kp0.text = num; kp0.font.size = Pt(20); kp0.font.bold = True; kp0.font.color.rgb = C_NAVY_PRI; kp0.alignment = PP_ALIGN.CENTER
    kp1 = ktf.add_paragraph(); kp1.text = label; kp1.font.size = Pt(11); kp1.font.bold = True; kp1.font.color.rgb = C_DARK_TXT; kp1.alignment = PP_ALIGN.CENTER
    kp2 = ktf.add_paragraph(); kp2.text = sub; kp2.font.size = Pt(9); kp2.font.color.rgb = C_MUTED_TXT; kp2.alignment = PP_ALIGN.CENTER

box = draw_card(s, Inches(0.6), Inches(5.1), Inches(12.1), Inches(1.35), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.12)
bp = btf.paragraphs[0]; bp.text = "KEGUNAAN KHUSUS"; bp.font.size = Pt(10); bp.font.bold = True; bp.font.color.rgb = C_NAVY_PRI
bp2 = btf.add_paragraph(); bp2.text = "Riset Deep Learning sekuensial (LSTM/GRU), analisis siklus diurnal 24 jam, dan deteksi badai/nowcasting menit-ke-menit \u2014 kebutuhan yang tidak bisa dipenuhi oleh data harian yang sudah diringkas."
bp2.font.size = Pt(12.5); bp2.font.color.rgb = C_BODY_TXT

track(s)
set_notes(s, (
    "Slide ini adalah ringkasan eksekutif dari Laporan Data Cleaning Interval. Poin pentingnya: kita TIDAK membuang data "
    "resolusi tinggi. File nusaklim_cleaned_interval.csv ini mempertahankan seluruh 14.823.713 baris pencatatan asli "
    "per 10-15 menit, hanya saja sudah dibersihkan dan dikonversi ke satuan standar.\n\n"
    "Empat angka kunci yang perlu diingat: ukuran file turun dari 1,37 GB menjadi 969,45 MB \u2014 penurunan 30,9% ini murni "
    "karena optimasi format string dan tipe data, BUKAN karena data hilang. Baris valid 14.823.713 dari 14.827.287 baris "
    "mentah \u2014 artinya hanya sekitar 3.574 baris sampah yang dibuang (kurang dari 0,03%). Cakupan mencapai 184 stasiun "
    "AWS otentik di seluruh kebun PPKS, dari Januari 2022 sampai Agustus 2026.\n\n"
    "Mengapa kita masih perlu menyimpan data seresolusi tinggi ini, padahal sudah ada versi harian yang lebih ringkas? "
    "Karena untuk riset lanjutan seperti model Deep Learning LSTM, analisis pola pemanasan/pendinginan sepanjang hari "
    "(siklus diurnal), atau sistem peringatan dini badai mendadak, kita butuh detail per menit \u2014 bukan rata-rata harian."
))

# ============================================================================
# SLIDE 4: METODOLOGI PEMBERSIHAN - BAGIAN 1
# ============================================================================
s = new_slide()
draw_header(s, "Metodologi Pembersihan Data Interval (1/2): Filter & Waktu", CAT1)
add_textbox(s, Inches(0.6), Inches(1.45), Inches(11.9), Inches(0.55), [
    ("Diproses menggunakan algoritma streaming chunk (500.000 baris/batch), mengikuti aturan fisis & Notulen Rapat PPKS 20 Agustus 2026:", {"size": 13, "bullet": False}),
], bullet=False)

data1 = [
    ["Tahapan", "Operasi / Formula", "Kriteria Eliminasi"],
    ["1. Filter Stasiun Non-AWS", "Eliminasi ID pengujian bengkel: WiFiLogger, 9991\u20139995", "Memastikan hanya 184 stasiun AWS otentik yang diproses"],
    ["2. Filter RTC Reset (<2022)", "Filter utctime < 1640995200 (sebelum 1 Jan 2022)", "Menghapus 3.567 baris artefak instalasi awal tahun 2000"],
    ["3. Konversi Waktu ke WIB", "datetime_wib = utctime + 7 jam", "Format YYYY-MM-DD HH:MM:SS, siap dibaca manusia & sistem"],
]
add_table(s, Inches(0.6), Inches(2.15), Inches(12.1), Inches(2.3), data1, col_widths=[Inches(3.2), Inches(4.4), Inches(4.5)], font_size=11.5, header_font_size=12)

add_textbox(s, Inches(0.6), Inches(4.75), Inches(12.1), Inches(1.7), [
    ("Kenapa 3 langkah ini harus di awal?", {"size": 13, "bold": True, "color": C_NAVY_PRI, "bullet": False}),
    ("Data lapangan bercampur dengan tag pengujian pabrik/bengkel dan sisa kalibrasi RTC (real-time clock) yang belum di-setting saat instalasi \u2014 kalau tidak difilter dulu, baris-baris ini akan merusak semua statistik dan agregasi di tahap berikutnya.", {"size": 13, "level": 1}),
    ("Standarisasi ke WIB (UTC+7) sejak awal memastikan seluruh proses agregasi harian berikutnya konsisten dengan hari kalender operasional kebun, bukan hari kalender UTC yang bergeser.", {"size": 13, "level": 1}),
])

track(s)
set_notes(s, (
    "Ini adalah bagian pertama dari metodologi pembersihan level interval \u2014 tiga langkah paling awal sebelum data "
    "disentuh secara fisis.\n\n"
    "Langkah 1, Filter Stasiun Non-AWS: di lapangan, ada beberapa ID yang sebenarnya bukan stasiun cuaca sungguhan, "
    "melainkan tag pengujian dari bengkel/pabrik seperti 'WiFiLogger' atau ID 9991 sampai 9995. Ini kita buang supaya "
    "hanya 184 stasiun AWS otentik yang diproses.\n\n"
    "Langkah 2, Filter RTC Reset: setiap alat punya jam internal (Real-Time Clock). Saat baru dipasang sebelum "
    "disinkronkan, jam ini defaultnya menunjukkan tahun 2000 atau bahkan 1970. Baris dengan timestamp sebelum "
    "1 Januari 2022 kita anggap sampah instalasi dan kita buang \u2014 totalnya 3.567 baris.\n\n"
    "Langkah 3, Konversi Waktu ke WIB: seluruh data awalnya dalam format Unix timestamp UTC. Kita tambahkan 7 jam agar "
    "sesuai zona waktu Indonesia Barat, dan formatnya diubah jadi tanggal-jam yang mudah dibaca. Ini penting supaya "
    "nanti saat kita agregasi jadi data harian, pembagian 'hari'-nya sesuai dengan hari kalender kebun di lapangan, "
    "bukan hari UTC yang bisa bergeser beberapa jam."
))

# ============================================================================
# SLIDE 5: METODOLOGI PEMBERSIHAN - BAGIAN 2
# ============================================================================
s = new_slide()
draw_header(s, "Metodologi Pembersihan Data Interval (2/2): Konversi Satuan Meteorologi", CAT1)

data2 = [
    ["Parameter", "Formula Konversi", "Batas Fisis / Sentinel yang Dihapus"],
    ["Suhu (temp_c)", "temp_c = (tempout - 32.0) \u00d7 (5/9)", "Sentinel 3276.7\u00b0F & -90\u00b0F di-NaN; batas valid 12\u201345\u00b0C"],
    ["Tekanan (pressure_hpa)", "pressure_hpa = bar \u00d7 33.864", "inHg \u2192 hPa; di luar 920\u20131040 hPa diisolasi ke NaN"],
    ["Curah Hujan (rainfall_mm)", "rainfall_mm = rain15 \u00d7 12.70", "Tipping bucket \u2192 mm; >60 mm/15-menit diisolasi ke NaN"],
    ["Radiasi & Angin", "Sentinel solar=32767, windspd=255, winddir=32767 \u2192 NaN", "Batas solar 0\u20132000 W/m\u00b2; angin 0\u2013150 km/jam; arah 0\u2013360\u00b0"],
]
add_table(s, Inches(0.6), Inches(1.55), Inches(12.1), Inches(3.1), data2, col_widths=[Inches(2.9), Inches(4.4), Inches(4.8)], font_size=11.5, header_font_size=12)

box = draw_card(s, Inches(0.6), Inches(4.95), Inches(12.1), Inches(1.55), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.12)
bp = btf.paragraphs[0]; bp.text = "CATATAN PENTING DATA INTERVAL"; bp.font.size = Pt(10.5); bp.font.bold = True; bp.font.color.rgb = C_NAVY_PRI
bp2 = btf.add_paragraph()
bp2.text = "Semua nilai di luar batas fisis tropis TIDAK dihapus barisnya, melainkan diisolasi/di-masking menjadi NaN pada kolom terkait \u2014 baris tetap dipertahankan untuk kolom lain yang masih valid, sesuai standar WMO No. 8."
bp2.font.size = Pt(12.5); bp2.font.color.rgb = C_BODY_TXT

track(s)
set_notes(s, (
    "Ini bagian kedua metodologi \u2014 konversi satuan pengukuran dari satuan bawaan alat (Amerika/Imperial) ke satuan "
    "metrik internasional yang baku, sekaligus penyaringan nilai eror sensor.\n\n"
    "Suhu: alat mencatat dalam Fahrenheit, kita konversi ke Celsius dengan rumus standar. Nilai sentinel 3276.7 derajat "
    "Fahrenheit itu bukan suhu asli \u2014 itu adalah kode eror hardware saat sensor terputus, jadi kita ubah jadi kosong (NaN).\n\n"
    "Tekanan: dari inHg (inch of mercury) dikonversi ke hPa (hektopascal) dengan faktor kali 33.864, sesuai notulen rapat.\n\n"
    "Curah hujan: sensor tipping bucket mencatat jumlah 'ketukan', dikonversi ke milimeter dengan faktor kali 12.70.\n\n"
    "Radiasi matahari dan angin: sama-sama punya kode sentinel hardware seperti 32767 atau 255 yang menandakan sensor "
    "error atau kabel putus \u2014 semua ini di-masking jadi NaN.\n\n"
    "Poin yang perlu saya tekankan ke Bapak/Ibu: kita TIDAK menghapus seluruh barisnya hanya karena satu sensor error. "
    "Kalau sensor suhu di satu baris rusak tapi sensor kelembapan dan tekanan di baris yang sama masih bagus, baris itu "
    "tetap kita simpan \u2014 hanya kolom suhu-nya saja yang dikosongkan. Ini menjaga data tetap maksimal dipakai."
))

# ============================================================================
# SLIDE 6: STATISTIK TRANSFORMASI & VOLUME DATA
# ============================================================================
s = new_slide()
draw_header(s, "Ringkasan Transformasi & Statistik Volume Data", CAT1)

data3 = [
    ["Komponen", "Dataset Mentah (Raw)", "Dataset Bersih Interval", "Tindakan"],
    ["Ukuran File", "1,37 GB (1.472.934.120 bytes)", "969,45 MB (1.016.543.935 bytes)", "Reduksi 30,9% (optimasi string)"],
    ["Total Baris", "14.827.287 baris", "14.823.713 baris valid", "3.574 baris sampah disaring"],
    ["Satuan Suhu", "Fahrenheit (\u00b0F)", "Celsius (\u00b0C)", "Formula Notulen Rapat PPKS"],
    ["Satuan Tekanan", "inHg", "hPa (Hektopaskal)", "Faktor kali 33.864"],
    ["Satuan Hujan", "Tipping bucket raw", "Milimeter (mm)", "Faktor kali 12.70 + isolasi loop"],
    ["Representasi Waktu", "utctime (Unix integer)", "datetime_wib (string terbaca)", "WIB siap dibaca manusia & sistem"],
]
add_table(s, Inches(0.6), Inches(1.55), Inches(12.1), Inches(4.7), data3, col_widths=[Inches(2.6), Inches(3.3), Inches(3.3), Inches(2.9)], font_size=11.5, header_font_size=12)

track(s)
set_notes(s, (
    "Slide ini adalah tabel ringkasan 'before-after' yang sangat berguna untuk audiens yang ingin melihat perbandingan "
    "cepat antara data mentah dan data bersih.\n\n"
    "Highlight utama: ukuran file mengecil 30,9% (dari 1,37 GB menjadi 969,45 MB) walaupun jumlah baris hampir tidak "
    "berkurang (99,98% baris dipertahankan). Ini murni efisiensi teknis penyimpanan, bukan kehilangan data.\n\n"
    "Semua satuan sekarang konsisten dengan standar internasional: Celsius untuk suhu, hPa untuk tekanan, dan milimeter "
    "untuk curah hujan \u2014 ini penting supaya kalau nanti dibandingkan dengan sumber data lain seperti API Open-Meteo, "
    "satuannya sudah apple-to-apple dan tidak perlu konversi ulang.\n\n"
    "Representasi waktu juga sudah berubah dari angka Unix timestamp yang sulit dibaca manusia (misalnya angka "
    "1640995200) menjadi format tanggal-jam yang langsung bisa dibaca siapa saja, dalam zona waktu Indonesia Barat."
))

# ============================================================================
# SLIDE 7: KAMUS DATA INTERVAL
# ============================================================================
s = new_slide()
draw_header(s, "Kamus Data (Data Dictionary): nusaklim_cleaned_interval.csv", CAT1)

data4 = [
    ["Kolom", "Satuan", "Rentang Fisis Valid", "Deskripsi"],
    ["stnname", "-", "ID Stasiun 7 s/d 2244", "Kode identifikasi unik stasiun AWS kebun sawit"],
    ["datetime_wib", "WIB (UTC+7)", "2022-01-01 s/d 2026-08-19", "Waktu pencatatan lokal, format YYYY-MM-DD HH:MM:SS"],
    ["temp_c", "Celsius (\u00b0C)", "12,0 \u2013 45,0 \u00b0C", "Suhu udara ambien bersih per interval"],
    ["humidity_pct", "Persen (%)", "0,0 \u2013 100,0 %", "Kelembapan relatif udara (Relative Humidity)"],
    ["pressure_hpa", "hPa (mbar)", "920,0 \u2013 1040,0 hPa", "Tekanan udara barometrik permukaan tanah"],
    ["rainfall_mm", "Milimeter (mm)", "0,0 \u2013 60,0 mm", "Akumulasi curah hujan per interval 15 menit"],
    ["solar_radiation_wm2", "W/m\u00b2", "0,0 \u2013 2000,0 W/m\u00b2", "Intensitas radiasi flux penyinaran matahari"],
    ["wind_speed_kmh", "km/jam", "0,0 \u2013 150,0 km/h", "Kecepatan angin permukaan"],
    ["wind_direction_deg", "Derajat (\u00b0)", "0,0\u00b0 \u2013 360,0\u00b0", "Arah datangnya angin (0\u00b0/360\u00b0=Utara, 90\u00b0=Timur)"],
]
add_table(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(5.4), data4, col_widths=[Inches(2.5), Inches(1.9), Inches(2.6), Inches(5.3)], font_size=10.5, header_font_size=11.5)

track(s)
set_notes(s, (
    "Ini adalah kamus data lengkap dari file nusaklim_cleaned_interval.csv \u2014 saya tunjukkan supaya tim yang nanti mau "
    "memakai file ini untuk riset tahu persis apa arti tiap kolom, satuannya apa, dan rentang nilai yang dianggap wajar.\n\n"
    "Sembilan kolom utama: identitas stasiun (stnname), waktu (datetime_wib), lalu enam parameter cuaca inti \u2014 suhu, "
    "kelembapan, tekanan, curah hujan, radiasi solar, kecepatan angin, dan arah angin dalam derajat.\n\n"
    "Yang perlu dicatat: pada level interval ini, arah angin MASIH dalam bentuk derajat mentah (0-360 derajat), belum "
    "dikategorikan ke 4 arah mata angin seperti Utara/Selatan/Timur/Barat. Pengelompokan ke 4 arah mata angin itu baru "
    "dilakukan di tahap agregasi harian, yang akan saya bahas di Laporan 2 nanti.\n\n"
    "Tabel ini juga berguna sebagai referensi cepat kalau ada yang bertanya 'kenapa suhu di bawah 12 derajat dianggap "
    "tidak valid?' \u2014 jawabannya karena itu di luar rentang fisis wajar untuk iklim tropis dataran perkebunan sawit."
))

# ============================================================================
# SLIDE 8: PERBANDINGAN 3 LEVEL DATASET
# ============================================================================
s = new_slide()
draw_header(s, "Perbandingan Tiga Level Dataset NusaKlim", CAT1)

data5 = [
    ["Kriteria", "1. Raw Input", "2. Cleaned Interval (Baru)", "3. Daily Aggregated"],
    ["Level Waktu", "Interval 10\u201315 menit", "Interval 10\u201315 menit", "Agregasi harian (1 hari/baris)"],
    ["Jumlah Baris", "14.827.287", "14.823.713 valid", "114.651 ringkasan"],
    ["Ukuran File", "1,37 GB", "969,45 MB", "10,12 MB"],
    ["Status Kualitas", "Mentah (ada eror hardware)", "Bersih & terkalibrasi (\u00b0C, hPa, mm)", "Bersih + ekstrem harian + arah kardinal"],
    ["Peruntukan Utama", "Sumber arsip mentah asli", "Riset Deep Learning LSTM, siklus diurnal, deteksi badai konvektif", "Model prediksi cuaca 7-hari produksi di website & dashboard kebun"],
]
add_table(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(4.3), data5, col_widths=[Inches(2.2), Inches(2.9), Inches(3.6), Inches(3.6)], font_size=11, header_font_size=12)

box = draw_card(s, Inches(0.5), Inches(5.95), Inches(12.3), Inches(1.05), bg_color=C_ACCENT_BG, border_color=C_TEAL_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.1)
bp = btf.paragraphs[0]
bp.text = "Ukuran 10 MB pada dataset harian BUKAN berarti data hilang \u2014 ini adalah hasil peringkasan cerdas (96 baris/hari menjadi 1 baris) sesuai kebutuhan peramalan harian."
bp.font.size = Pt(12.5); bp.font.bold = True; bp.font.color.rgb = C_NAVY_PRI

track(s)
set_notes(s, (
    "Slide ini menjawab pertanyaan yang paling sering muncul: 'Kita punya berapa banyak versi data, dan masing-masing "
    "buat apa?' Jawabannya, ada 3 tingkatan.\n\n"
    "Level 1, Raw Input: arsip mentah asli, 1,37 GB, 14,8 juta baris, apa adanya dari lapangan termasuk eror sensornya.\n\n"
    "Level 2, Cleaned Interval \u2014 ini yang jadi fokus utama Laporan 1 hari ini: masih di level 10-15 menitan, tapi sudah "
    "bersih dan terkalibrasi. Ini yang cocok untuk riset Deep Learning yang butuh detail per menit, seperti mendeteksi "
    "lonjakan angin sebelum badai.\n\n"
    "Level 3, Daily Aggregated: ini yang jadi fokus Laporan 2 nanti \u2014 diringkas jadi 1 baris per hari per stasiun, "
    "totalnya 114.651 baris, hanya 10 MB. File inilah yang dipakai website untuk meramal cuaca 7 hari secara cepat dan "
    "hemat memori server.\n\n"
    "Saya tekankan poin terakhir: ukuran 10 MB itu bukan berarti kita kehilangan informasi. sekitar 144 baris data per 10 menit "
    "dalam sehari diringkas jadi 1 baris ringkasan harian (dengan rata-rata, min, max, total) \u2014 itu penyusutan yang "
    "disengaja dan sesuai kebutuhan, bukan kebocoran data."
))

# ============================================================================
# SLIDE 9: REKOMENDASI PENGGUNAAN DATASET INTERVAL
# ============================================================================
s = new_slide()
draw_header(s, "Rekomendasi Penggunaan Dataset Interval Bersih untuk Riset", CAT1)

recs = [
    ("1", "Pemodelan Deep Learning Beresolusi Tinggi", "Pelatihan LSTM/GRU/Transformer untuk meramal fluktuasi cuaca per jam atau per 15 menit ke depan (sub-daily forecasting)."),
    ("2", "Analisis Siklus Diurnal Mikroklimat Kebun", "Mempelajari kurva pemanasan tanah pagi-sore, jam puncak radiasi matahari, dan waktu presipitasi konvektif lokal."),
    ("3", "Sistem Peringatan Dini Badai Mendadak", "Mendeteksi lonjakan kecepatan angin (gust) atau penurunan tekanan barometrik mendadak dalam hitungan menit sebelum badai."),
]
top = Inches(1.7)
for i, (num, title, desc) in enumerate(recs):
    card = draw_card(s, Inches(0.6), top, Inches(12.1), Inches(1.35), bg_color=C_WHITE, border_color=C_BORDER_HI, line_width=1.3)
    numbox = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.85), top + Inches(0.28), Inches(0.8), Inches(0.8))
    numbox.fill.solid(); numbox.fill.fore_color.rgb = C_NAVY_PRI; numbox.line.fill.background()
    ntf = numbox.text_frame; ntf.word_wrap = True
    npar = ntf.paragraphs[0]; npar.text = num; npar.font.size = Pt(20); npar.font.bold = True; npar.font.color.rgb = C_WHITE; npar.alignment = PP_ALIGN.CENTER
    ttf = card.text_frame; ttf.word_wrap = True; ttf.margin_left = Inches(2.0); ttf.margin_top = Inches(0.15)
    tp = ttf.paragraphs[0]; tp.text = title; tp.font.size = Pt(14.5); tp.font.bold = True; tp.font.color.rgb = C_DARK_TXT
    dp = ttf.add_paragraph(); dp.text = desc; dp.font.size = Pt(12); dp.font.color.rgb = C_BODY_TXT
    top += Inches(1.5)

box = draw_card(s, Inches(0.6), Inches(6.3), Inches(12.1), Inches(0.75), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.08)
bp = btf.paragraphs[0]
bp.text = "Lokasi file: d:\\Downloads\\nusaklim\\nusaklim_cleaned_interval.csv (969,45 MB) \u2014 siap diakses seluruh peneliti & tim AI PPKS."
bp.font.size = Pt(11.5); bp.font.italic = True; bp.font.color.rgb = C_NAVY_PRI

track(s)
set_notes(s, (
    "Ini adalah slide penutup untuk Laporan 1. Saya ingin sampaikan tiga rekomendasi konkret pemanfaatan dataset "
    "interval bersih ini untuk riset lanjutan di PPKS.\n\n"
    "Pertama, untuk tim yang tertarik pada Deep Learning \u2014 dataset ini siap dipakai melatih model sekuensial seperti "
    "LSTM atau GRU untuk meramal cuaca dalam skala sub-harian, misalnya per jam.\n\n"
    "Kedua, untuk riset agroklimat murni \u2014 data ini bisa dipakai mempelajari siklus diurnal, yaitu pola naik-turun suhu "
    "dan radiasi matahari sepanjang 24 jam, yang berguna untuk memahami mikroklimat di sekitar tanaman sawit.\n\n"
    "Ketiga, dan ini yang paling bernilai praktis \u2014 potensi membangun sistem peringatan dini badai mendadak. Karena "
    "resolusinya per 15 menit, kita bisa mendeteksi tanda-tanda awal badai (lonjakan angin, penurunan tekanan tiba-tiba) "
    "jauh lebih cepat dibanding kalau kita hanya punya data harian.\n\n"
    "File ini sudah tersimpan di workspace kita dan siap diakses oleh seluruh tim peneliti dan AI Engineering PPKS. "
    "Dengan ini, Laporan 1 selesai kita bahas \u2014 selanjutnya kita masuk ke Laporan 2: Preprocessing dan EDA."
))

# ============================================================================
# SLIDE 10: PENDAHULUAN LAPORAN 2
# ============================================================================
s = new_slide()
draw_header(s, "Pendahuluan & Dasar Notulen Rapat", CAT2)
add_textbox(s, Inches(0.6), Inches(1.6), Inches(12.1), Inches(2.3), [
    ("PPKS mengoperasikan jaringan Automatic Weather Station (AWS) NusaKlim di berbagai perkebunan kelapa sawit di Indonesia. Informasi agroklimat yang presisi, kontinu, dan reliabel adalah fondasi penting untuk:", {"size": 14, "bullet": False}),
    ("Penentuan jadwal agronomi (pemupukan, penyerbukan, pengendalian hama/penyakit, panen)", {"size": 13.5}),
    ("Analisis neraca air tanah dan mitigasi defisit air", {"size": 13.5}),
    ("Prediksi hasil produksi kelapa sawit", {"size": 13.5}),
])

box = draw_card(s, Inches(0.6), Inches(4.15), Inches(12.1), Inches(2.1), bg_color=C_ACCENT_BG, border_color=C_TEAL_PRI, line_width=1.5)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.25); btf.margin_top = Inches(0.2)
bp = btf.paragraphs[0]; bp.text = "DASAR ACUAN RESMI"; bp.font.size = Pt(11); bp.font.bold = True; bp.font.color.rgb = C_TEAL_DARK
bp2 = btf.add_paragraph()
bp2.text = "Seluruh tahapan preprocessing dan EDA dalam laporan ini dikembangkan secara ketat mengacu pada Notulen Rapat Pembahasan Data Cuaca dan Pengembangan Model Prediksi Cuaca, tertanggal 20 Agustus 2026, yang melibatkan Tim Data Analyst dan Peneliti PPKS."
bp2.font.size = Pt(14); bp2.font.color.rgb = C_DARK_TXT; bp2.space_before = Pt(8)
bp3 = btf.add_paragraph()
bp3.text = "Sumber data: raw dataset telemetri AWS NusaKlim berukuran 1,37 GB (14.827.287 baris pencatatan)."
bp3.font.size = Pt(13); bp3.font.italic = True; bp3.font.color.rgb = C_BODY_TXT; bp3.space_before = Pt(8)

track(s)
set_notes(s, (
    "Kita masuk ke Laporan 2: Preprocessing Data dan Exploratory Data Analysis (EDA). Sebelum ke detail teknis, penting "
    "untuk memahami KENAPA laporan ini dibuat.\n\n"
    "PPKS mengoperasikan jaringan stasiun cuaca otomatis NusaKlim di berbagai kebun sawit di Indonesia. Data cuaca yang "
    "presisi dan kontinu bukan sekadar angka statistik \u2014 ini adalah dasar pengambilan keputusan operasional sehari-hari "
    "di kebun: kapan waktu tepat memupuk, kapan menyerbukkan bunga, bagaimana mengendalikan hama sesuai kelembapan, "
    "kapan waktu aman untuk panen, sampai memperkirakan neraca air tanah dan bahkan memprediksi hasil produksi TBS.\n\n"
    "Poin yang ingin saya tekankan: seluruh proses yang akan saya jelaskan bukan keputusan sepihak tim data, melainkan "
    "hasil kesepakatan resmi dalam Notulen Rapat tanggal 20 Agustus 2026 yang melibatkan Tim Data Analyst dan Peneliti "
    "PPKS. Jadi setiap formula konversi, setiap aturan agregasi, itu semua traceable ke keputusan rapat tersebut \u2014 "
    "bukan asumsi sepihak dari programmer."
))

# ============================================================================
# SLIDE 11: MATRIKS NOTULEN RAPAT - BAGIAN 1
# ============================================================================
s = new_slide()
draw_header(s, "Matriks Kesepakatan Notulen Rapat (1/2): Konversi & Agregasi", CAT2)

data6 = [
    ["Poin Notulen", "Arahan & Kesepakatan", "Implementasi Teknis"],
    ["1. Konversi Suhu", "Suhu dari alat masih Fahrenheit, harus dikonversi ke Celsius", "T_C = (tempout-32)\u00d75/9; validasi 12\u201345\u00b0C; kode eror 3276.7\u00b0F & 0\u00b0F disaring"],
    ["2. Konversi Tekanan", "Tekanan barometer dikoreksi dengan faktor kalibrasi", "P_hPa = bar\u00d733.864; filter ambang fisik 920\u20131040 hPa"],
    ["3. Konversi Curah Hujan", "Data rain15 dikoreksi faktor 12.70 untuk mm", "Rain_mm = rain15\u00d712.70; filter anomali >60 mm/15-menit"],
    ["4. Aturan Agregasi Harian", "Dijumlahkan: curah hujan. Dirata-ratakan: suhu, tekanan, kelembapan, radiasi solar, angin, arah angin", "Agregasi per stasiun per tanggal lokal WIB; dilengkapi nilai Min & Max harian"],
]
add_table(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(4.9), data6, col_widths=[Inches(2.3), Inches(4.5), Inches(5.5)], font_size=11.5, header_font_size=12)

track(s)
set_notes(s, (
    "Slide ini menampilkan 4 poin pertama dari 7 poin kesepakatan Notulen Rapat yang menjadi 'undang-undang' preprocessing "
    "kita. Ini sengaja saya tampilkan dalam bentuk tabel supaya terlihat jelas: kolom kiri itu keputusan rapat, kolom "
    "kanan itu bagaimana kita mengimplementasikannya secara teknis.\n\n"
    "Poin 1-3 sebenarnya sama dengan yang sudah kita bahas di Laporan 1 tadi \u2014 konversi suhu, tekanan, dan curah hujan "
    "ke satuan metrik. Saya ulang di sini karena laporan ini (Laporan 2) juga menerapkan aturan yang sama persis pada "
    "level data harian, jadi konsistensinya terjaga dari level interval sampai level harian.\n\n"
    "Yang baru di sini adalah Poin 4, Aturan Agregasi Harian \u2014 ini keputusan penting yang menentukan bagaimana 96 baris "
    "data per 15 menit dalam sehari dirangkum jadi 1 baris. Aturannya: untuk curah hujan, kita JUMLAHKAN "
    "(karena ini besaran akumulatif \u2014 total hujan sehari). Sedangkan untuk suhu, tekanan, radiasi solar, "
    "kelembapan, dan angin, kita RATA-RATAKAN (karena ini besaran kondisi sesaat, bukan akumulasi; radiasi sengaja dirata-ratakan agar tidak bergantung pada jumlah pembacaan sensor per hari). Ini prinsip fisis "
    "yang penting supaya angka hasil agregasi punya makna yang benar secara meteorologi."
))

# ============================================================================
# SLIDE 12: MATRIKS NOTULEN RAPAT - BAGIAN 2
# ============================================================================
s = new_slide()
draw_header(s, "Matriks Kesepakatan Notulen Rapat (2/2): Arah Angin, Setup Awal & Missing Data", CAT2)

data7 = [
    ["Poin Notulen", "Arahan & Kesepakatan", "Implementasi Teknis"],
    ["5. Kategorisasi Arah Angin", "Derajat harian dirata-rata dulu, lalu diklasifikasi ke 4 arah mata angin", "Logika bertingkat pada rata-rata harian (0\u2013360\u00b0), hasilkan kolom wind_direction_name"],
    ["6. Penanganan Setup Awal", "Data instalasi awal (~9 ribuan baris tes pabrik/RTC default 2000/1970) harus dihapus", "Penyaringan timestamp < 2022-01-01 dan ID non-stasiun (WiFiLogger, 9991-9995)"],
    ["7. Data Hilang & Target Prediksi", "Evaluasi dampak missing data; target peramalan 7 hari; perbandingan dgn Open-Meteo", "Audit missingness per variabel/stasiun, korelasi fitur, rekomendasi model ML/DL time series"],
]
add_table(s, Inches(0.5), Inches(1.55), Inches(12.3), Inches(3.7), data7, col_widths=[Inches(2.3), Inches(4.5), Inches(5.5)], font_size=11.5, header_font_size=12)

box = draw_card(s, Inches(0.5), Inches(5.55), Inches(12.3), Inches(1.35), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.1)
bp = btf.paragraphs[0]; bp.text = "LANDASAN FISIS PENGOLAHAN AGROKLIMAT"; bp.font.size = Pt(10.5); bp.font.bold = True; bp.font.color.rgb = C_NAVY_PRI
bp2 = btf.add_paragraph()
bp2.text = "Setiap parameter meteorologi punya karakteristik instrumen tersendiri. Penerapan konversi satuan dan aturan agregasi yang tepat mencegah distorsi kalkulasi neraca air dan memastikan fitur model prediksi 7-hari punya signifikansi fisis yang valid."
bp2.font.size = Pt(12); bp2.font.color.rgb = C_BODY_TXT

track(s)
set_notes(s, (
    "Ini tiga poin terakhir dari Notulen Rapat, Poin 5 sampai 7.\n\n"
    "Poin 5, Kategorisasi Arah Angin: berbeda dengan data interval yang masih dalam derajat mentah, di level harian ini "
    "kita rata-ratakan dulu derajatnya dalam satu hari, baru diklasifikasikan ke 4 arah mata angin \u2014 Utara, Timur, "
    "Selatan, Barat. Ini memudahkan mandor kebun atau pengguna awam membaca laporan tanpa perlu paham angka derajat.\n\n"
    "Poin 6, Penanganan Setup Awal: ini penegasan ulang dari yang sudah kita lakukan di level interval \u2014 sekitar 9 "
    "ribuan baris data bawaan tes pabrik atau RTC yang belum di-setting harus dibuang, supaya tidak mencemari hasil "
    "agregasi harian.\n\n"
    "Poin 7, ini poin yang paling strategis: evaluasi dampak data yang hilang (missing data), dan target akhir dari "
    "semua ini adalah membangun model peramalan cuaca 7 hari ke depan, serta membandingkannya dengan layanan API "
    "eksternal Open-Meteo. Poin ini menjadi jembatan menuju laporan-laporan berikutnya tentang pemodelan AI.\n\n"
    "Intinya, setiap keputusan teknis yang kita ambil selalu berlandaskan pemahaman fisis meteorologi yang benar \u2014 "
    "bukan sekadar 'auto-generate' angka, supaya nanti model AI yang dilatih di atasnya juga punya dasar yang solid."
))

# ============================================================================
# SLIDE 13: AUDIT MUTU RAW DATA & QC
# ============================================================================
s = new_slide()
draw_header(s, "Audit Mutu Raw Data & Prosedur Quality Control (QC)", CAT2)

data8 = [
    ["Kategori", "Jumlah Baris", "Persentase", "Tindakan"],
    ["Total Raw Input", "14.827.287", "100,0%", "Read in chunks (500k)"],
    ["ID Non-Stasiun (tes)", "7", "<0,001%", "Dihapus permanen"],
    ["Timestamp Rusak/Null", "1", "<0,001%", "Dihapus permanen"],
    ["Setup Epoch (<2022)", "3.566", "0,024%", "Dihapus (Notulen Poin 5)"],
    ["Valid Interval Records", "14.823.713", "99,976%", "Diproses ke tahap QC fisis"],
    ["Error Sensor Suhu", "114.232", "0,77%", "Masking \u2192 NaN"],
    ["Error Sensor Solar", "110.050", "0,74%", "Masking \u2192 NaN"],
    ["Error Sensor Arah Angin", "138.268", "0,93%", "Masking \u2192 NaN"],
    ["Error Sensor Kelembapan", "114.928", "0,78%", "Masking \u2192 NaN"],
    ["Error Sensor Kec. Angin", "104.167", "0,70%", "Masking \u2192 NaN"],
]
add_table(s, Inches(0.5), Inches(1.5), Inches(6.9), Inches(5.4), data8, col_widths=[Inches(2.6), Inches(1.6), Inches(1.3), Inches(1.4)], font_size=10.5, header_font_size=11)
add_image(s, os.path.join(fig_dir, "fig1_cleaning_summary.png"), Inches(7.55), Inches(1.65), width=Inches(5.25))
cap = s.shapes.add_textbox(Inches(7.55), Inches(4.35), Inches(5.25), Inches(0.5))
cp = cap.text_frame.paragraphs[0]; cp.text = "Gambar 1: Alur Pembersihan & Frekuensi Eror Hardware Sensor"; cp.font.size = Pt(9.5); cp.font.italic = True; cp.font.color.rgb = C_MUTED_TXT; cp.alignment = PP_ALIGN.CENTER

track(s)
set_notes(s, (
    "Slide ini menampilkan hasil audit menyeluruh terhadap seluruh 14,8 juta baris raw data, sebelum masuk ke agregasi "
    "harian \u2014 ibaratnya ini 'rontgen kesehatan data' kita.\n\n"
    "Bacaannya dari atas: dari 14.827.287 baris total, hanya 7 baris ID non-stasiun dan 1 baris timestamp rusak yang "
    "dihapus \u2014 sangat kecil. Kemudian 3.566 baris setup epoch (sisa instalasi awal) juga dihapus sesuai notulen. "
    "Hasilnya, 14.823.713 baris atau 99,976% dinyatakan valid dan lanjut ke tahap QC fisis berikutnya.\n\n"
    "Di tahap QC fisis, kita cek per sensor: eror sensor suhu ada di 0,77% baris, solar 0,74%, arah angin 0,93%, "
    "kelembapan 0,78%, dan kecepatan angin 0,70%. Semua angka ini di bawah 1% \u2014 menunjukkan kualitas hardware AWS "
    "kita di lapangan secara keseluruhan cukup baik, meski wajar ada sensor yang sesekali bermasalah karena kondisi "
    "cuaca ekstrem atau usia alat.\n\n"
    "Grafik di sebelah kanan memvisualisasikan alur ini secara keseluruhan sehingga mudah dipahami bahkan oleh audiens "
    "non-teknis. Yang penting digarisbawahi: semua persentase eror ini di-masking per kolom, TIDAK menyebabkan baris "
    "datanya hilang seluruhnya."
))

# ============================================================================
# SLIDE 14: RASIONAL SENTINEL HARDWARE
# ============================================================================
s = new_slide()
draw_header(s, "Mengapa Sentinel Hardware Harus Diubah Menjadi NaN?", CAT2)

add_textbox(s, Inches(0.6), Inches(1.7), Inches(11.9), Inches(2.2), [
    ("Pada stasiun cuaca digital berbasis mikroprosesor (seperti Davis Vantage Pro2), saat terjadi:", {"size": 14, "bullet": False}),
    ("Kabel sensor terputus", {"size": 13.5}),
    ("Korosi akibat kelembapan tinggi di kebun sawit", {"size": 13.5}),
    ("Tegangan baterai solar drop", {"size": 13.5}),
    ("...modul ADC (Analog-to-Digital Converter) mengirimkan nilai biner maksimum sebagai kode eror.", {"size": 14, "bullet": False}),
])

data9 = [
    ["Kode Sentinel", "Arti Teknis", "Contoh Nilai Terbaca"],
    ["0x7FFF = 32767", "Nilai maksimum 16-bit bertanda (signed)", "Suhu 3276.7\u00b0F, Solar 32767 W/m\u00b2, Arah Angin 32767\u00b0"],
    ["0xFF = 255", "Nilai maksimum 8-bit", "Kecepatan Angin 255, Kelembapan 255"],
]
add_table(s, Inches(0.6), Inches(4.0), Inches(11.9), Inches(1.5), data9, col_widths=[Inches(2.5), Inches(4.4), Inches(5.0)], font_size=12, header_font_size=12.5)

box = draw_card(s, Inches(0.6), Inches(5.75), Inches(11.9), Inches(0.95), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.08)
bp = btf.paragraphs[0]
bp.text = "Isolasi sentinel menjadi NaN mencegah distorsi perhitungan rata-rata iklim, sesuai standar World Meteorological Organization (WMO No. 8)."
bp.font.size = Pt(12.5); bp.font.bold = True; bp.font.color.rgb = C_NAVY_PRI

track(s)
set_notes(s, (
    "Slide ini menjawab pertanyaan teknis yang sering ditanyakan: 'Kenapa ada angka aneh seperti 3276 derajat "
    "Fahrenheit di data mentah, dan kenapa itu bukan cuma dianggap typo?'\n\n"
    "Jawabannya ada di cara kerja hardware. Stasiun cuaca digital kita, seperti Davis Vantage Pro2, punya komponen "
    "bernama ADC (Analog-to-Digital Converter) yang mengubah sinyal listrik dari sensor jadi angka digital. Kalau kabel "
    "sensornya putus, korosi karena kelembapan tinggi di kebun sawit, atau baterai solar-nya lemah, ADC ini tidak bisa "
    "membaca sinyal dengan benar dan otomatis mengirim nilai maksimum yang bisa dia simpan \u2014 ini disebut sentinel value.\n\n"
    "Contohnya, untuk data 16-bit, nilai maksimumnya adalah 32767 dalam heksadesimal 0x7FFF. Ini muncul sebagai suhu "
    "3276.7 derajat Fahrenheit, radiasi solar 32767 watt per meter persegi, atau arah angin 32767 derajat \u2014 yang "
    "semuanya jelas mustahil secara fisis. Untuk data 8-bit, nilai maksimumnya 255.\n\n"
    "Kenapa ini penting dijelaskan ke Bapak/Ibu? Karena ini membuktikan bahwa penyaringan data kita bukan tebak-tebakan "
    "sembarangan, melainkan berbasis pemahaman mendalam tentang cara kerja hardware sensor itu sendiri. Dengan mengubah "
    "nilai sentinel ini jadi kosong (NaN) alih-alih membiarkannya ikut dihitung rata-rata, kita menjaga integritas "
    "statistik iklim sesuai standar organisasi meteorologi dunia, WMO."
))

# ============================================================================
# SLIDE 15: FORMULA AGREGASI HARIAN
# ============================================================================
s = new_slide()
draw_header(s, "Formula Agregasi Harian: Sum vs Mean", CAT2)
add_textbox(s, Inches(0.6), Inches(1.45), Inches(11.9), Inches(0.5), [
    ("114.651 station-days dihasilkan dari agregasi data 15-menitan per stasiun per hari lokal (WIB):", {"size": 13, "bullet": False}),
], bullet=False)

data10 = [
    ["Variabel", "Satuan Target", "Metode Agregasi", "Keterangan"],
    ["Curah Hujan", "mm/hari", "PENJUMLAHAN (SUM)", "Akumulasi presipitasi total dalam 24 jam"],
    ["Radiasi Solar", "W/m\u00b2 (rata-rata harian)", "RATA-RATA (MEAN)", "Rata-rata radiasi matahari harian"],
    ["Suhu Udara", "\u00b0C", "RATA-RATA (MEAN) + Min/Max", "Dilengkapi pencatatan T_min dan T_max"],
    ["Tekanan Barometer", "hPa (mbar)", "RATA-RATA (MEAN)", "Rata-rata tekanan permukaan per stasiun"],
    ["Kelembapan (RH)", "%", "RATA-RATA (MEAN) + Min/Max", "Dilengkapi pencatatan RH_min dan RH_max"],
    ["Kecepatan Angin", "km/h", "RATA-RATA (MEAN) + Max", "Dilengkapi V_max (gust/kec. maksimum)"],
    ["Arah Angin (Derajat)", "Derajat & Kategori", "RATA-RATA \u2192 Kategori", "Dilanjutkan konversi ke nama mata angin"],
]
add_table(s, Inches(0.5), Inches(2.05), Inches(12.3), Inches(4.9), data10, col_widths=[Inches(2.6), Inches(2.2), Inches(3.0), Inches(4.5)], font_size=11, header_font_size=12)

track(s)
set_notes(s, (
    "Sekarang kita bahas detail teknis bagaimana sekitar 144 baris data per 10 menit dalam sehari diringkas jadi 1 baris "
    "ringkasan harian \u2014 total hasilnya 114.507 'station-days' (kombinasi stasiun dan tanggal).\n\n"
    "Prinsip yang saya tekankan lagi: ada dua kelompok metode agregasi. Kelompok pertama, PENJUMLAHAN, dipakai untuk "
    "besaran yang sifatnya akumulatif \u2014 curah hujan. Kenapa dijumlahkan? Karena yang kita ingin tahu "
    "adalah TOTAL hujan sehari, bukan rata-rata hujan per 15 menit yang tidak ada artinya secara praktis.\n\n"
    "Kelompok kedua, RATA-RATA, dipakai untuk besaran kondisi sesaat \u2014 suhu, tekanan, kelembapan, radiasi solar, dan kecepatan angin. Radiasi dulu dijumlahkan, tapi itu keliru karena totalnya ikut berubah mengikuti jumlah pembacaan sensor per hari, jadi sekarang dirata-ratakan. "
    "Untuk suhu dan kelembapan, kita tidak hanya simpan rata-rata, tapi juga nilai minimum dan maksimum harian \u2014 ini "
    "penting untuk analisis ekstrem cuaca, misalnya suhu terpanas siang hari atau suhu terdingin dini hari.\n\n"
    "Untuk kecepatan angin, selain rata-rata kita juga simpan nilai maksimum (istilahnya 'gust' atau hembusan angin "
    "terkuat) \u2014 ini indikator penting untuk potensi kerusakan tanaman atau bahaya bagi pekerja kebun.\n\n"
    "Arah angin diproses dua tahap: dirata-ratakan dulu dalam derajat, baru kemudian dikonversi jadi kategori mata "
    "angin \u2014 yang akan saya jelaskan detail di slide berikutnya."
))

# ============================================================================
# SLIDE 16: KLASIFIKASI ARAH MATA ANGIN
# ============================================================================
s = new_slide()
draw_header(s, "Klasifikasi Arah Mata Angin (Notulen Poin 4)", CAT2)

data11 = [
    ["Rentang Derajat", "Kategori", "Kode Output"],
    ["> 315\u00b0 atau \u2264 45\u00b0", "Utara", "'Utara'"],
    ["> 225\u00b0 s.d. 315\u00b0", "Barat", "'Barat'"],
    ["> 135\u00b0 s.d. 225\u00b0", "Selatan", "'Selatan'"],
    ["> 45\u00b0 s.d. 135\u00b0", "Timur", "'Timur'"],
    ["Nilai hilang/sensor rusak", "Tidak Tersedia", "'---'"],
]
add_table(s, Inches(0.5), Inches(1.5), Inches(5.6), Inches(3.4), data11, col_widths=[Inches(2.5), Inches(1.8), Inches(1.3)], font_size=11.5, header_font_size=12, header_bg=C_TEAL_PRI)
add_image(s, os.path.join(fig_dir, "fig5_wind_analysis.png"), Inches(6.35), Inches(1.5), width=Inches(6.4))
cap = s.shapes.add_textbox(Inches(6.35), Inches(5.0), Inches(6.4), Inches(0.5))
cp = cap.text_frame.paragraphs[0]; cp.text = "Gambar 2: Proporsi Arah Angin & Boxplot Kecepatan per Kategori"; cp.font.size = Pt(9.5); cp.font.italic = True; cp.font.color.rgb = C_MUTED_TXT; cp.alignment = PP_ALIGN.CENTER

track(s)
set_notes(s, (
    "Slide ini menjelaskan logika di balik konversi derajat arah angin menjadi 4 kategori mata angin sederhana yang "
    "mudah dibaca semua orang.\n\n"
    "Logikanya bertingkat: kalau derajat rata-rata harian lebih dari 315 derajat ATAU kurang dari sama dengan 45 "
    "derajat, itu dikategorikan Utara. Antara 45 sampai 135 derajat itu Timur. Antara 135 sampai 225 derajat itu "
    "Selatan. Dan antara 225 sampai 315 derajat itu Barat. Kalau datanya hilang atau sensor rusak, kita beri tanda "
    "strip tiga ('---') sebagai penanda 'tidak tersedia', bukan angka yang menyesatkan.\n\n"
    "Grafik di sebelah kanan menunjukkan dua hal: proporsi seberapa sering angin datang dari tiap arah sepanjang "
    "periode observasi, dan boxplot yang menunjukkan sebaran kecepatan angin untuk masing-masing kategori arah \u2014 ini "
    "berguna misalnya untuk mengetahui apakah angin dari arah tertentu cenderung lebih kencang, yang relevan untuk "
    "perencanaan penanaman atau perlindungan tanaman muda dari angin kencang."
))

# ============================================================================
# SLIDE 17: STATISTIK DESKRIPTIF EDA
# ============================================================================
s = new_slide()
draw_header(s, "Statistik Deskriptif Agregasi Harian (Complete Cases: 97.031 Station-Days)", CAT2)
data12 = [
    ["Variabel Cuaca", "N Valid", "Mean \u00b1 Std", "Min", "Q1 (25%)", "Median", "Q3 (75%)", "P99", "Max"],
    ["Suhu Rata-rata (\u00b0C)", "97.031", "26,98 \u00b1 1,63", "13,68", "26,11", "26,98", "27,87", "31,35", "36,44"],
    ["Suhu Minimum (\u00b0C)", "97.031", "23,52 \u00b1 1,61", "12,00", "22,94", "23,61", "24,22", "28,56", "36,44"],
    ["Suhu Maksimum (\u00b0C)", "97.031", "31,96 \u00b1 2,30", "14,83", "30,83", "32,28", "33,50", "36,11", "42,33"],
    ["Kelembapan Avg (%)", "97.031", "85,79 \u00b1 5,71", "19,67", "83,02", "86,42", "89,45", "96,44", "100,00"],
    ["Tekanan Udara (hPa)", "97.031", "1000,52 \u00b1 13,06", "920,08", "1000,06", "1004,50", "1007,16", "1013,22", "1034,88"],
    ["Curah Hujan (mm/hari)", "97.031", "6,52 \u00b1 18,66", "0,00", "0,00", "0,00", "4,32", "76,59", "300,00"],
    ["Kecepatan Angin (km/h)", "97.031", "0,80 \u00b1 0,75", "0,00", "0,39", "0,67", "1,02", "3,06", "18,79"],
]
add_table(s, Inches(0.3), Inches(1.5), Inches(12.6), Inches(3.6), data12, col_widths=[Inches(1.8), Inches(0.8), Inches(1.5), Inches(0.9), Inches(1.0), Inches(1.0), Inches(1.0), Inches(0.8), Inches(0.8)], font_size=10.5, header_font_size=11)

add_image(s, os.path.join(fig_dir, "fig2_distributions.png"), Inches(0.3), Inches(5.3), width=Inches(12.6))

track(s)
set_notes(s, (
    "Slide ini menyajikan ringkasan statistik deskriptif dari 97.031 Station-Days Complete Cases, di mana "
    "seluruh 8 sensor beroperasi serentak tanpa missing value.\n\n"
    "1. Suhu Rata-rata: 50% data tengah berada pada rentang 26,11\u00b0C (Q1) hingga 27,87\u00b0C (Q3) dengan IQR hanya "
    "1,76\u00b0C, mencerminkan stabilitas mikroklimat kelapa sawit.\n\n"
    "2. Kelembapan Udara: Q1 bernilai 83,02% dan Q3 mencapai 89,45% (IQR 6,43%), lingkungan perkebunan hampir "
    "selalu berada pada kelembapan tinggi.\n\n"
    "3. Curah Hujan: Q1 dan Median bernilai 0,00 mm (lebih dari 50% hari tanpa hujan). Q3 tercatat 4,32 mm/hari, "
    "dan melonjak drastis pada P99 (76,59 mm) serta maksimum 300,00 mm/hari \u2014 distribusi right-skewed.\n\n"
    "4. Kecepatan Angin: Q1 tercatat 0,39 km/jam, Median 0,67 km/jam, dan Q3 1,02 km/jam, membuktikan sirkulasi "
    "udara di bawah kanopi perkebunan rata-rata sangat tenang (calm).\n\n"
    "Grafik di bawah tabel memvisualisasikan bentuk sebaran masing-masing variabel lengkap dengan boxplot."
))

# ============================================================================
# SLIDE 18: KORELASI MULTIVARIAT
# ============================================================================
s = new_slide()
draw_header(s, "Analisis Korelasi Multivariat Antar Variabel Cuaca", CAT2)

add_image(s, os.path.join(fig_dir, "fig3_correlation.png"), Inches(0.5), Inches(1.5), height=Inches(5.4))

tb = s.shapes.add_textbox(Inches(6.2), Inches(1.5), Inches(6.6), Inches(5.4))
tf = tb.text_frame
tf.word_wrap = True

corr_items = [
    ("\u2022 Suhu vs Kelembapan (r = \u22120.38): ", "Korelasi negatif lemah-sedang. Saat suhu siang hari memuncak, kapasitas udara menampung uap meningkat dan kelembapan relatif turun drastis."),
    ("\u2022 Radiasi Solar vs Suhu (+0.55) & Kelembapan (\u22120.48): ", "Insolasi matahari gelombang pendek merupakan penggerak utama pemanasan lapisan batas atmosfer di atas kanopi sawit."),
    ("\u2022 Korelasi Multivariat terhadap Curah Hujan: ", "Curah hujan berkorelasi sangat lemah dengan sebagian besar variabel (Suhu r = -0.14, Kelembapan r = -0.15, Tekanan r = -0.14, Radiasi r = +0.03); hanya Kecepatan Angin yang sedang (r = +0.46)."),
    ("\u2022 Rasionalisasi Pemodelan Prediksi 7-Hari: ", "Lemahnya keterkaitan pada hari yang sama menunjukkan sinyal prediksi hujan lebih banyak berasal dari pola riwayat beberapa hari dan beberapa variabel sekaligus, sehingga pendekatan multivariat (Machine Learning) lebih tepat daripada model univarian murni."),
]

for i, (bold_lbl, desc_lbl) in enumerate(corr_items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = Pt(10)
    r1 = p.add_run(); r1.text = bold_lbl; r1.font.bold = True; r1.font.size = Pt(11); r1.font.color.rgb = C_NAVY_PRI
    r2 = p.add_run(); r2.text = desc_lbl; r2.font.bold = False; r2.font.size = Pt(10.2); r2.font.color.rgb = C_DARK_TXT

track(s)
set_notes(s, (
    "Slide ini menampilkan matriks korelasi Pearson antar parameter cuaca harian AWS PPKS, sesuai mandat Notulen Rapat Butir 7.2.\n\n"
    "Temuan pertama: suhu dan kelembapan punya korelasi negatif, minus 0,38. Artinya ketika suhu naik di siang hari, udara punya kapasitas lebih besar menampung uap air, sehingga kelembapan relatifnya turun drastis. Sebaliknya malam hari atau saat hujan, kelembapan mendekati titik jenuh di atas 90%.\n\n"
    "Temuan kedua: radiasi matahari berkorelasi positif dengan suhu (plus 0,55) dan negatif dengan kelembapan (minus 0,48) \u2014 ini masuk akal secara fisika, karena radiasi matahari adalah sumber energi utama yang memanaskan atmosfer.\n\n"
    "Temuan ketiga dan paling penting untuk pemodelan: curah hujan punya korelasi sangat lemah dengan hampir semua variabel lain pada hari yang sama (sekitar minus 0,14 untuk suhu, kelembapan, dan tekanan), kecuali kecepatan angin yang sedang (plus 0,46). Artinya hujan tidak bisa diramal dari kondisi hari itu saja, sehingga model perlu memakai riwayat beberapa hari dari banyak variabel sekaligus, bukan model univarian yang hanya melihat riwayat hujan itu sendiri."
))

# ============================================================================
# SLIDE 19: SIKLUS DIURNAL
# ============================================================================
s = new_slide()
draw_header(s, "Profil Siklus Diurnal 24 Jam (WIB)", CAT2)
add_image(s, os.path.join(fig_dir, "fig7_diurnal_cycle.png"), Inches(0.4), Inches(1.35), width=Inches(7.5))

add_textbox(s, Inches(8.15), Inches(1.35), Inches(4.6), Inches(5.8), [
    ("Pola Harian Rata-rata 184 Stasiun AWS:", {"size": 12, "bold": True, "bullet": False}),
    ("Suhu: Minimum \u00b123,6\u00b0C pukul 05\u201306.00, puncak \u00b131,0\u00b0C pukul 13.00 (amplitudo \u00b17,4\u00b0C).", {"size": 11}),
    ("Radiasi Solar: Nol sepanjang malam, puncak \u00b1560\u2013570 W/m\u00b2 pukul 11\u201312.00 \u2014 driver utama pemanasan siang.", {"size": 11}),
    ("Kelembapan: Antifase dengan suhu \u2014 puncak \u00b193,7% saat subuh, minimum \u00b174,5% pukul 13\u201314.00.", {"size": 11}),
    ("Tekanan: Osilasi semi-diurnal (2 puncak & 2 lembah per hari) khas wilayah tropis \u2014 atmospheric thermal tide.", {"size": 11}),
    ("", {"size": 6, "bullet": False}),
    ("Sumber: Dataset Harian NusaKlim AWS", {"size": 10, "bold": True, "bullet": False}),
    ("184 Stasiun, Januari 2022 \u2013 Agustus 2026", {"size": 10, "bullet": False}),
    ("Referensi perangkat: device_nusaklim.csv", {"size": 10, "bullet": False}),
], line_spacing=1.2)

track(s)
set_notes(s, (
    "Slide ini menampilkan Profil Siklus Diurnal 24 Jam \u2014 rata-rata seluruh stasiun per jam Waktu Indonesia Barat "
    "(WIB). Ini menunjukkan pola harian yang konsisten dan saling terkait secara fisis.\n\n"
    "SUHU UDARA: Mencapai titik terendah \u00b123,6\u00b0C sekitar pukul 05\u201306.00 (sesaat sebelum matahari terbit, "
    "saat pelepasan panas radiatif malam hari mencapai puncaknya). Suhu naik tajam begitu radiasi matahari masuk "
    "dan mencapai puncak \u00b131,0\u00b0C pada pukul 13.00, sebelum menurun bertahap sepanjang sore hingga tengah malam. "
    "Amplitudo harian \u00b17,4\u00b0C ini tipikal mikroklimat kanopi kelapa sawit.\n\n"
    "RADIASI SOLAR: Bernilai nol sepanjang malam (18.00\u201306.00), naik seiring matahari terbit, dan memuncak "
    "\u00b1560\u2013570 W/m\u00b2 pada pukul 11\u201312.00. Ini adalah driver utama di balik kenaikan suhu dan penurunan kelembapan.\n\n"
    "KELEMBAPAN RELATIF: Bergerak berlawanan arah (antifase) dengan suhu \u2014 memuncak \u00b193,7% menjelang pagi saat "
    "suhu terendah, lalu turun ke \u00b174,5% pukul 13\u201314.00 bersamaan dengan puncak suhu & radiasi solar. "
    "Relasi fisis: udara hangat menampung uap air relatif lebih banyak sehingga RH menurun.\n\n"
    "TEKANAN ATMOSFER: Memperlihatkan pola osilasi semi-diurnal (dua puncak & dua lembah per hari) khas wilayah "
    "tropis \u2014 pasang atmosfer termal (atmospheric thermal tide). Puncak pertama \u00b11002,2 hPa pukul 09.00, "
    "lembah terdalam \u00b1997,6 hPa pukul 16.00.\n\n"
    "Pola diurnal ini penting bagi model prediksi 7-hari karena menjadi basis fitur waktu siklikal "
    "(sin_doy/cos_doy) dan membantu memvalidasi bahwa sensor AWS merekam dinamika atmosfer secara fisis konsisten."
))

# ============================================================================
# SLIDE 20: TREN DERET WAKTU & POLA MUSIMAN
# ============================================================================
s = new_slide()
draw_header(s, "Tren Deret Waktu \u0026 Pola Musiman (2022\u20132026)", CAT2)
add_image(s, os.path.join(fig_dir, "fig4_timeseries_trend.png"), Inches(1.0), Inches(1.45), width=Inches(11.3))

# Caption with data source
cap = s.shapes.add_textbox(Inches(1.0), Inches(6.55), Inches(11.3), Inches(0.7))
cp = cap.text_frame.paragraphs[0]; cp.text = "Gambar: Tren Cuaca Harian Nasional 2022\u20132026 (Moving Average 7 Hari)"; cp.font.size = Pt(10); cp.font.italic = True; cp.font.color.rgb = C_MUTED_TXT; cp.alignment = PP_ALIGN.CENTER
cp2 = cap.text_frame.add_paragraph()
cp2.text = "Sumber: nusaklim_daily_aggregated.csv (114.651 baris, 184 Stasiun AWS, Jan 2022 \u2013 Agt 2026) | Referensi stasiun: device_nusaklim.csv"
cp2.font.size = Pt(9); cp2.font.italic = True; cp2.font.color.rgb = C_MUTED_TXT; cp2.alignment = PP_ALIGN.CENTER

track(s)
set_notes(s, (
    "Grafik ini menunjukkan tren cuaca harian rata-rata nasional (digabung dari 184 stasiun) sepanjang periode "
    "observasi Januari 2022 sampai Agustus 2026, sudah dihaluskan dengan moving average 7 hari supaya tren musiman "
    "terlihat jelas tanpa noise harian.\n\n"
    "SUMBER DATA: Dataset nusaklim_daily_aggregated.csv berisi 114.651 baris harian dari 184 stasiun AWS NusaKlim, "
    "diproses oleh process_nusaklim.py dari data mentah nusaklim-aws-reduce.csv. Identitas dan lokasi setiap stasiun "
    "dirujuk-silang dari basis data referensi perangkat device_nusaklim.csv.\n\n"
    "Data selama 4 tahun lebih ini memungkinkan kita melihat pola osilasi musiman monsun Asia-Australia yang berulang "
    "setiap tahun \u2014 musim hujan dan musim kemarau yang bergantian. Ini juga membuka kemungkinan untuk mendeteksi "
    "anomali iklim global seperti El Ni\u00f1o-Southern Oscillation (ENSO) atau Indian Ocean Dipole (IOD).\n\n"
    "Kenapa ini penting untuk pemodelan? Karena model prediksi cuaca 7 hari yang baik perlu 'sadar' terhadap konteks "
    "musiman ini \u2014 prediksi di bulan Juli (biasanya kemarau) seharusnya berbeda karakteristiknya dengan prediksi di "
    "bulan Januari (biasanya musim hujan). Data 4 tahun ini cukup panjang untuk menangkap pola tahunan tersebut."
))

# ============================================================================
# SLIDE 21: KLASIFIKASI CURAH HUJAN BMKG
# ============================================================================
s = new_slide()
draw_header(s, "Klasifikasi Intensitas Curah Hujan Harian (Standar BMKG)", CAT2)
add_image(s, os.path.join(fig_dir, "fig6_rainfall_classification.png"), Inches(0.5), Inches(1.4), width=Inches(7.0))

add_textbox(s, Inches(7.75), Inches(1.55), Inches(5.1), Inches(5.4), [
    ("Dari 101.368 hari pengamatan presipitasi valid:", {"size": 12.5, "bold": True, "bullet": False}),
    ("Tidak Hujan (0,0 mm): 56.418 hari (55,7%)", {"size": 12.5}),
    ("Hujan Ringan (0,1\u201320,0 mm): 31.842 hari (31,4%)", {"size": 12.5}),
    ("Hujan Sedang (20,0\u201350,0 mm): 9.940 hari (9,8%)", {"size": 12.5}),
    ("Hujan Lebat (50,0\u2013100,0 mm): 2.812 hari (2,8%)", {"size": 12.5}),
    ("Hujan Sangat Lebat/Ekstrem (>100,0 mm): 356 hari (0,35%)", {"size": 12.5}),
], line_spacing=1.25)

track(s)
set_notes(s, (
    "Slide ini mengklasifikasikan intensitas curah hujan harian menggunakan standar resmi BMKG (Badan Meteorologi, "
    "Klimatologi, dan Geofisika) supaya hasilnya bisa dibandingkan langsung dengan laporan cuaca nasional.\n\n"
    "Dari total 101.368 hari pengamatan hujan yang valid: lebih dari separuh, 55,7%, adalah hari tanpa hujan sama "
    "sekali \u2014 ini hari-hari ideal untuk aktivitas panen dan transportasi TBS (Tandan Buah Segar) karena jalan kebun "
    "kering.\n\n"
    "31,4% adalah hari hujan ringan (0,1 sampai 20 mm) \u2014 ini kategori yang justru bagus untuk penyerapan air oleh "
    "akar tanaman sawit tanpa risiko banjir atau erosi.\n\n"
    "9,8% hujan sedang memerlukan monitoring drainase kebun agar air tidak menggenang. Dan yang paling perlu perhatian "
    "khusus: 2,8% hari hujan lebat dan 0,35% hari hujan sangat lebat/ekstrem \u2014 meski jumlahnya kecil secara "
    "persentase, dalam 4 tahun observasi itu setara dengan sekitar 356 hari kejadian ekstrem yang berpotensi "
    "menyebabkan aliran permukaan tinggi, erosi, atau bahkan gagal panen jika terjadi saat masa kritis.\n\n"
    "Grafik di kiri juga menampilkan Top 10 stasiun dengan akumulasi hujan tertinggi \u2014 berguna untuk mengidentifikasi "
    "kebun mana yang paling rawan terhadap risiko kelebihan air dan butuh perhatian sistem drainase lebih baik."
))

# ============================================================================
# SLIDE 22: KESIAPAN DATA & INVENTARIS ARTIFAK (PENUTUP LAPORAN 2)
# ============================================================================
s = new_slide()
draw_header(s, "Kesimpulan & Inventaris Artifak Output", CAT2)
add_textbox(s, Inches(0.6), Inches(1.5), Inches(11.9), Inches(0.8), [
    ("Proses preprocessing dan EDA terhadap 14,8 juta baris raw telemetri AWS NusaKlim telah selesai, sepenuhnya memenuhi mandat Notulen Rapat 20 Agustus 2026.", {"size": 13.5, "bullet": False}),
], bullet=False)

data13 = [
    ["Artifak / File", "Format & Ukuran", "Kegunaan"],
    ["nusaklim_daily_aggregated.csv", "CSV, 10,1 MB / 114.651 baris", "Dataset harian bersih terstandarisasi, siap untuk training model prediksi 7 hari"],
    ["figures/*.png (8 charts)", "PNG 300 DPI", "8 grafik analitis: QC, distribusi, korelasi, tren, angin, BMKG, diurnal, kelengkapan stasiun"],
    ["Laporan PDF (2 dokumen)", "PDF resmi", "Dokumentasi teknis lengkap untuk arsip PPKS & panduan tim riset"],
    ["process_nusaklim.py", "Python Script (ETL)", "Pipeline streaming chunk, dapat dijalankan otomatis (cron/batch harian)"],
]
add_table(s, Inches(0.6), Inches(2.5), Inches(12.1), Inches(3.2), data13, col_widths=[Inches(3.3), Inches(2.6), Inches(6.2)], font_size=11.5, header_font_size=12)

box = draw_card(s, Inches(0.6), Inches(6.0), Inches(12.1), Inches(1.0), bg_color=C_ACCENT_BG, border_color=C_NAVY_PRI, line_width=1.2)
btf = box.text_frame; btf.word_wrap = True; btf.margin_left = Inches(0.2); btf.margin_top = Inches(0.1)
bp = btf.paragraphs[0]; bp.text = "EFISIENSI KOMPUTASI"; bp.font.size = Pt(10.5); bp.font.bold = True; bp.font.color.rgb = C_NAVY_PRI
bp2 = btf.add_paragraph()
bp2.text = "Pipeline chunk 500.000 baris/batch memproses 14,8 juta baris data dalam < 2,5 menit dengan konsumsi memori stabil di bawah 500 MB RAM."
bp2.font.size = Pt(12); bp2.font.color.rgb = C_BODY_TXT

track(s)
set_notes(s, (
    "Ini slide penutup untuk Laporan 2, sekaligus penutup keseluruhan presentasi hari ini. Saya rangkum apa saja "
    "artifak konkret yang dihasilkan dari seluruh proses data cleaning dan preprocessing/EDA yang sudah kita bahas.\n\n"
    "Pertama, file nusaklim_daily_aggregated.csv \u2014 dataset harian bersih 10,1 MB berisi 114.651 baris, yang menjadi "
    "input utama untuk pengembangan model prediksi cuaca 7 hari (topik laporan selanjutnya).\n\n"
    "Kedua, delapan grafik analitis beresolusi tinggi yang mencakup seluruh aspek yang kita bahas hari ini: alur QC, "
    "distribusi variabel, korelasi, tren waktu, analisis angin, klasifikasi BMKG, siklus diurnal, dan kelengkapan "
    "stasiun.\n\n"
    "Ketiga, dua dokumen PDF resmi (Laporan Data Cleaning Interval dan Laporan Preprocessing & EDA) yang menjadi arsip "
    "teknis PPKS.\n\n"
    "Keempat, script Python pipeline ETL yang bisa dijalankan otomatis \u2014 jadi kalau ada data baru masuk di masa "
    "depan, kita tidak perlu mengulang proses ini secara manual.\n\n"
    "Satu hal yang saya ingin tekankan sebagai catatan efisiensi: seluruh 14,8 juta baris data ini diproses dalam "
    "waktu kurang dari 2,5 menit dengan memori komputer stabil di bawah 500 MB \u2014 jadi proses ini ringan dan bisa "
    "dijalankan ulang kapan saja tanpa perlu server khusus yang mahal.\n\n"
    "Dengan ini, tahap fondasi kualitas data \u2014 data cleaning, preprocessing, dan EDA \u2014 sudah selesai 100% dan siap "
    "menjadi landasan untuk tahap pemodelan AI prediksi cuaca 7 hari yang akan dibahas di laporan terpisah. "
    "Terima kasih, saya buka sesi tanya jawab jika ada yang ingin didiskusikan lebih lanjut."
))

prs.save(pptx_path)
print(f"PPTX berhasil dibuat: {pptx_path}")
print(f"Total slide: {SLIDE_NUM[0]}")
print(f"Ukuran file: {os.path.getsize(pptx_path):,} bytes")
