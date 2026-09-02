import os, sys, pandas as pd, numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

pdf_path = r'd:\Downloads\nusaklim\Laporan_Data_Cleaning_Interval_NusaKlim_PPKS.pdf'

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#475569'))
        self.drawString(40, 805, 'Pusat Penelitian Kelapa Sawit (PPKS) - NusaKlim Weather AI')
        self.drawRightString(555, 805, 'Laporan Data Cleaning Tingkat Interval Telemetri')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Dokumentasi Dataset Bersih 10-15 Menitan (Sebelum Agregasi Harian) - PPKS')
        self.drawRightString(555, 32, f'Halaman {self._pageNumber} dari {page_count}')
        self.restoreState()

doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=55)
styles = getSampleStyleSheet()

COLOR_PRIMARY = colors.HexColor('#1E3A8A')
COLOR_SECONDARY = colors.HexColor('#0D9488')
COLOR_DARK = colors.HexColor('#0F172A')
COLOR_BODY = colors.HexColor('#334155')
COLOR_MUTED = colors.HexColor('#64748B')
COLOR_BG_LIGHT = colors.HexColor('#F8FAFC')
COLOR_BG_ACCENT = colors.HexColor('#EFF6FF')
COLOR_BORDER = colors.HexColor('#E2E8F0')

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18.5, leading=23.5, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=10)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=14.5, textColor=COLOR_BODY, alignment=1, spaceAfter=18)
style_cover_meta = ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=COLOR_MUTED, alignment=1)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=COLOR_PRIMARY, spaceBefore=9, spaceAfter=4, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12.5, textColor=COLOR_SECONDARY, spaceBefore=7, spaceAfter=3, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Helvetica', fontSize=8.2, leading=11.8, textColor=COLOR_BODY, spaceAfter=4, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.8, leading=11, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=9.2, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=9.2, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=COLOR_MUTED, alignment=1, spaceBefore=2, spaceAfter=6)

def make_callout_box(text, title='CATATAN PENTING DATA INTERVAL', width=515):
    p_title = Paragraph(f'<b>{title}</b>', ParagraphStyle('CT', fontName='Helvetica-Bold', fontSize=7.8, leading=10, textColor=COLOR_PRIMARY, spaceAfter=2))
    p_text = Paragraph(text, style_callout)
    tbl = Table([[p_title], [p_text]], colWidths=[width])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_ACCENT),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl

story = []

# COVER PAGE
story.append(Spacer(1, 15))
header_inst = Paragraph(
    '<b>PUSAT PENELITIAN KELAPA SAWIT (PPKS)</b><br/><font color=\'#64748B\' size=\'8.5\'>Indonesian Oil Palm Research Institute - Proyek NusaKlim Weather AI</font>',
    ParagraphStyle('CoverInst', fontName='Helvetica', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 10))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=16))

story.append(Paragraph('LAPORAN DATA CLEANING TINGKAT INTERVAL TELEMETRI<br/>(DATASET BERSIH SEBELUM AGREGASI)', style_cover_title))
story.append(Paragraph('Dokumentasi Teknis Pembersihan 14,8 Juta Baris Data Interval 10-15 Menitan, Konversi Satuan Metrik Baku, Penanganan Nilai Sentinel Hardware, dan Penyaringan Celah Fisis Jaringan AWS PPKS', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Nama File Output</b>', style_table_cell_bold), Paragraph('<code>nusaklim_cleaned_interval.csv</code> (969.45 MB / 1.016.543.935 bytes)', style_table_cell)],
    [Paragraph('<b>Level Granularitas</b>', style_table_cell_bold), Paragraph('Data Interval Mentah Bersih per 10 s/d 15 Menit (High-Frequency Series)', style_table_cell)],
    [Paragraph('<b>Jumlah Baris Bersih</b>', style_table_cell_bold), Paragraph('<b>14.823.713 Baris Valid</b> (dari 14.827.287 baris mentah)', style_table_cell)],
    [Paragraph('<b>Cakupan Waktu &amp; Zona</b>', style_table_cell_bold), Paragraph('01 Januari 2022 s/d 19 Agustus 2026 | Waktu Indonesia Barat (WIB / UTC+7)', style_table_cell)],
    [Paragraph('<b>Jumlah Stasiun AWS</b>', style_table_cell_bold), Paragraph('184 Stasiun AWS Otentik di Seluruh Perkebunan Kelapa Sawit PPKS', style_table_cell)],
    [Paragraph('<b>Kegunaan Khusus</b>', style_table_cell_bold), Paragraph('Riset Deep Learning Sekuensial, Siklus Diurnal 24-Jam, Deteksi Badai Menit-ke-Menit', style_table_cell)],
]
tbl_cover = Table(cover_box_content, colWidths=[130, 360])
tbl_cover.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 4.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_cover)

story.append(Spacer(1, 18))
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026 | Dokumen Resmi Rilis Dataset Interval Bersih', style_cover_meta))
story.append(PageBreak())

# SECTION 1
story.append(Paragraph('1. Ringkasan Eksekutif &amp; Tujuan Penyediaan Dataset Interval', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk memenuhi kebutuhan riset agroklimat presisi tinggi dan pemodelan kecerdasan buatan tingkat lanjut (*Deep Learning RNN/LSTM*), telah diekstrak dataset bersih tingkat interval 10?15 menitan: <b><code>nusaklim_cleaned_interval.csv</code></b>.',
    style_body
))
story.append(Paragraph(
    'Berbeda dengan file <code>nusaklim_daily_aggregated.csv</code> (yang meringkas data menjadi 1 baris per hari untuk model tabular 7 hari), file <code>nusaklim_cleaned_interval.csv</code> mempertahankan <b>seluruh titik pencatatan resolusi tinggi (14.823.713 baris)</b> dalam keadaan bersih, terkalibrasi, dan bebas dari eror hardware sensor.',
    style_body
))

story.append(Paragraph('2. Metodologi Pembersihan Data Tingkat Interval', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Pembersihan dilakukan menggunakan algoritma streaming chunk (500.000 baris/batch) dengan menerapkan aturan fisis dan notulen rapat PPKS 20 Agustus 2026:',
    style_body
))

rules_data = [
    [Paragraph('Tahapan Pembersihan', style_table_header), Paragraph('Operasi &amp; Formula Matematika', style_table_header), Paragraph('Kriteria Eliminasi / Standarisasi', style_table_header)],
    [Paragraph('<b>1. Filter Stasiun Non-AWS</b>', style_table_cell_bold),
     Paragraph('Eliminasi ID pengujian bengkel: <code>WiFiLogger</code>, <code>9991-9995</code>.', style_table_cell),
     Paragraph('Memastikan hanya 184 stasiun AWS otentik di kebun sawit yang diproses.', style_table_cell)],
    [Paragraph('<b>2. Filter RTC Reset (&lt; 2022)</b>', style_table_cell_bold),
     Paragraph('Filter <code>utctime &lt; 1640995200</code> (Sebelum 01 Jan 2022 00:00 UTC).', style_table_cell),
     Paragraph('Menghapus 3.567 baris artefak instalasi awal tahun 2000 (Notulen Poin 5).', style_table_cell)],
    [Paragraph('<b>3. Konversi Waktu Lokal WIB</b>', style_table_cell_bold),
     Paragraph('<code>datetime_wib = pd.to_datetime(utctime, unit=\'s\') + 7 Jam</code>', style_table_cell),
     Paragraph('Waktu UTC dikonversi ke Waktu Indonesia Barat (WIB) berformat <code>YYYY-MM-DD HH:MM:SS</code>.', style_table_cell)],
    [Paragraph('<b>4. Konversi &amp; Filter Suhu</b>', style_table_cell_bold),
     Paragraph('<code>temp_c = (tempout - 32.0) * (5.0 / 9.0)</code>', style_table_cell),
     Paragraph('Sentinel hardware <code>3276.7 ?F</code> dan <code>-90 ?F</code> di-NaN. Batas fisis: 12.0 ?C &le; T &le; 45.0 ?C.', style_table_cell)],
    [Paragraph('<b>5. Konversi &amp; Filter Tekanan</b>', style_table_cell_bold),
     Paragraph('<code>pressure_hpa = bar * 33.864</code>', style_table_cell),
     Paragraph('inHg dikonversi ke hPa. Nilai di luar 920?1040 hPa diisolasi ke NaN.', style_table_cell)],
    [Paragraph('<b>6. Konversi &amp; Filter Hujan</b>', style_table_cell_bold),
     Paragraph('<code>rainfall_mm = rain15 * 12.70</code>', style_table_cell),
     Paragraph('Tipping bucket mentah dikonversi ke mm. Curah hujan &gt; 60 mm/15-menit diisolasi ke NaN.', style_table_cell)],
    [Paragraph('<b>7. Filter Radiasi &amp; Angin</b>', style_table_cell_bold),
     Paragraph('Sentinel <code>solar=32767</code>, <code>windspd=255</code>, <code>winddir=32767</code> di-NaN.', style_table_cell),
     Paragraph('Batas solar: 0?2000 W/m?, batas kecepatan angin: 0?150 km/jam, arah: 0?360?.', style_table_cell)],
]
tbl_rules = Table(rules_data, colWidths=[125, 175, 215])
tbl_rules.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.8),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_rules)

story.append(PageBreak())

# SECTION 3 & 4
story.append(Paragraph('3. Ringkasan Transformasi &amp; Statistik Volume Data', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Berikut adalah perbandingan volume data mentah masukan (*input*) dibandingkan dengan dataset bersih keluaran (*output*):',
    style_body
))

vol_data = [
    [Paragraph('Komponen Data', style_table_header), Paragraph('Dataset Mentah (Raw)', style_table_header), Paragraph('Dataset Bersih Interval (Cleaned)', style_table_header), Paragraph('Perubahan / Tindakan Preprocessing', style_table_header)],
    [Paragraph('<b>Nama File</b>', style_table_cell_bold), Paragraph('<code>nusaklim-aws-reduce.csv</code>', style_table_cell), Paragraph('<code>nusaklim_cleaned_interval.csv</code>', style_table_cell_bold), Paragraph('File baru berstandar metrik internasional.', style_table_cell)],
    [Paragraph('<b>Ukuran File Disk</b>', style_table_cell_bold), Paragraph('1,37 GB (1.472.934.120 bytes)', style_table_cell), Paragraph('<b>969,45 MB (1.016.543.935 bytes)</b>', style_table_cell_bold), Paragraph('Reduksi ukuran file sebesar 30,9% akibat optimasi string.', style_table_cell)],
    [Paragraph('<b>Total Baris</b>', style_table_cell_bold), Paragraph('14.827.287 baris', style_table_cell), Paragraph('<b>14.823.713 baris valid</b>', style_table_cell_bold), Paragraph('Menyaring 3.574 baris sampah (3.567 RTC default + 7 test tags).', style_table_cell)],
    [Paragraph('<b>Satuan Suhu</b>', style_table_cell_bold), Paragraph('Fahrenheit (?F)', style_table_cell), Paragraph('<b>Celsius (?C)</b>', style_table_cell_bold), Paragraph('Dikonversi sesuai formula Notulen Rapat PPKS.', style_table_cell)],
    [Paragraph('<b>Satuan Tekanan</b>', style_table_cell_bold), Paragraph('inHg', style_table_cell), Paragraph('<b>hPa (Hektopaskal)</b>', style_table_cell_bold), Paragraph('Dikonversi dengan faktor kali 33.864.', style_table_cell)],
    [Paragraph('<b>Satuan Curah Hujan</b>', style_table_cell_bold), Paragraph('Tipping bucket raw', style_table_cell), Paragraph('<b>Milimeter (mm)</b>', style_table_cell_bold), Paragraph('Dikonversi dengan faktor kali 12.70 dan isolasi loop.', style_table_cell)],
    [Paragraph('<b>Representasi Waktu</b>', style_table_cell_bold), Paragraph('utctime (Unix integer)', style_table_cell), Paragraph('<b>datetime_wib (String readable)</b>', style_table_cell_bold), Paragraph('Waktu lokal WIB siap dibaca manusia &amp; sistem database.', style_table_cell)],
]
tbl_vol = Table(vol_data, colWidths=[105, 125, 140, 145])
tbl_vol.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_vol)

story.append(Spacer(1, 6))

story.append(Paragraph('4. Kamus Data (*Data Dictionary*) File `nusaklim_cleaned_interval.csv`', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

dict_data = [
    [Paragraph('Nama Kolom', style_table_header), Paragraph('Tipe Data', style_table_header), Paragraph('Satuan Baku', style_table_header), Paragraph('Rentang Fisis Valid', style_table_header), Paragraph('Deskripsi Fungsional', style_table_header)],
    [Paragraph('<code>stnname</code>', style_table_cell_bold), Paragraph('String/Text', style_table_cell), Paragraph('-', style_table_cell_center), Paragraph('ID Stasiun 7 s/d 2244', style_table_cell), Paragraph('Kode identifikasi unik stasiun AWS kebun kelapa sawit.', style_table_cell)],
    [Paragraph('<code>datetime_wib</code>', style_table_cell_bold), Paragraph('Datetime', style_table_cell), Paragraph('WIB (UTC+7)', style_table_cell_center), Paragraph('2022-01-01 s/d 2026-08-19', style_table_cell), Paragraph('Waktu pencatatan lokal WIB berformat <code>YYYY-MM-DD HH:MM:SS</code>.', style_table_cell)],
    [Paragraph('<code>utctime</code>', style_table_cell_bold), Paragraph('Integer', style_table_cell), Paragraph('Detik (Unix)', style_table_cell_center), Paragraph('&ge; 1640995200', style_table_cell), Paragraph('Timestamp standar Unix UTC untuk audit sinkronisasi IoT.', style_table_cell)],
    [Paragraph('<code>temp_c</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('Celsius (?C)', style_table_cell_center), Paragraph('12.0 ?C s/d 45.0 ?C', style_table_cell), Paragraph('Suhu udara ambien bersih per interval pencatatan.', style_table_cell)],
    [Paragraph('<code>humidity_pct</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('Persen (%)', style_table_cell_center), Paragraph('0.0 % s/d 100.0 %', style_table_cell), Paragraph('Kelembapan relatif udara (*Relative Humidity*).', style_table_cell)],
    [Paragraph('<code>pressure_hpa</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('hPa (mbar)', style_table_cell_center), Paragraph('920.0 s/d 1040.0 hPa', style_table_cell), Paragraph('Tekanan udara barometrik permukaan tanah.', style_table_cell)],
    [Paragraph('<code>rainfall_mm</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('Milimeter (mm)', style_table_cell_center), Paragraph('0.0 s/d 60.0 mm', style_table_cell), Paragraph('Akumulasi curah hujan per interval 15 menit.', style_table_cell)],
    [Paragraph('<code>solar_radiation_wm2</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('W/m?', style_table_cell_center), Paragraph('0.0 s/d 2000.0 W/m?', style_table_cell), Paragraph('Intensitas radiasi flux penyinaran matahari.', style_table_cell)],
    [Paragraph('<code>wind_speed_kmh</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('km/jam', style_table_cell_center), Paragraph('0.0 s/d 150.0 km/h', style_table_cell), Paragraph('Kecepatan angin permukaan pada interval observasi.', style_table_cell)],
    [Paragraph('<code>wind_direction_deg</code>', style_table_cell_bold), Paragraph('Float', style_table_cell), Paragraph('Derajat (?)', style_table_cell_center), Paragraph('0.0? s/d 360.0?', style_table_cell), Paragraph('Arah datangnya angin (0?/360? = Utara, 90? = Timur, dst).', style_table_cell)],
]
tbl_dict = Table(dict_data, colWidths=[95, 55, 65, 95, 205])
tbl_dict.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_dict)

story.append(PageBreak())

# SECTION 5 & 6
story.append(Paragraph('5. Perbandingan Tiga Level Dataset NusaKlim', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk memastikan pemahaman yang utuh di lingkungan riset dan operasional PPKS, berikut adalah matriks peran dari ketiga file yang tersedia:',
    style_body
))

three_level_data = [
    [Paragraph('Kriteria Evaluasi', style_table_header), Paragraph('1. Raw Input Dataset', style_table_header), Paragraph('2. Cleaned Interval Dataset (File Baru)', style_table_header), Paragraph('3. Daily Aggregated Dataset', style_table_header)],
    [Paragraph('<b>Nama File</b>', style_table_cell_bold), Paragraph('<code>nusaklim-aws-reduce.csv</code>', style_table_cell), Paragraph('<code>nusaklim_cleaned_interval.csv</code>', style_table_cell_bold), Paragraph('<code>nusaklim_daily_aggregated.csv</code>', style_table_cell_bold)],
    [Paragraph('<b>Level Waktu</b>', style_table_cell_bold), Paragraph('Interval 10-15 Menit', style_table_cell), Paragraph('<b>Interval 10-15 Menit</b>', style_table_cell_bold), Paragraph('<b>Agregasi Harian (1 Hari/Baris)</b>', style_table_cell_bold)],
    [Paragraph('<b>Jumlah Baris</b>', style_table_cell_bold), Paragraph('14.827.287 baris', style_table_cell), Paragraph('<b>14.823.713 baris valid</b>', style_table_cell_bold), Paragraph('<b>114.651 baris ringkasan</b>', style_table_cell_bold)],
    [Paragraph('<b>Ukuran File</b>', style_table_cell_bold), Paragraph('1,37 GB', style_table_cell), Paragraph('<b>969,45 MB</b>', style_table_cell_bold), Paragraph('<b>10,12 MB (Sangat Ringkas)</b>', style_table_cell_bold)],
    [Paragraph('<b>Status Kualitas</b>', style_table_cell_bold), Paragraph('Mentah (Ada error hardware)', style_table_cell), Paragraph('<b>Bersih &amp; Terkalibrasi (?C, hPa, mm)</b>', style_table_cell_bold), Paragraph('<b>Bersih + Ekstrem Harian + Arah Kardinal</b>', style_table_cell_bold)],
    [Paragraph('<b>Peruntukan Utama</b>', style_table_cell_bold), Paragraph('Sumber arsip mentah asli.', style_table_cell), Paragraph('<b>Riset Deep Learning LSTM, Siklus Diurnal 24-Jam, Deteksi Badai Konvektif.</b>', style_table_cell_bold), Paragraph('<b>Model Prediksi Cuaca 7-Hari Produksi di Website &amp; Dashboard Kebun.</b>', style_table_cell_bold)],
]
tbl_three = Table(three_level_data, colWidths=[95, 120, 150, 150])
tbl_three.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 2), (-1, 2), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_three)

story.append(Spacer(1, 6))

story.append(Paragraph('6. Rekomendasi Penggunaan Dataset Interval Bersih untuk Riset', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'File <code>nusaklim_cleaned_interval.csv</code> siap digunakan secara langsung untuk sejumlah penelitian lanjutan PPKS:',
    style_body
))
story.append(Paragraph(
    '1. <b>Pemodelan Deep Learning Beresolusi Tinggi (*Sub-Daily Forecasting*):</b> Pelatihan jaringan saraf tiruan (LSTM/GRU/Transformer) untuk meramal pola fluktuasi cuaca per jam atau per 15 menit ke depan.<br/>'
    '2. <b>Analisis Siklus Diurnal Mikroklimat Kebun:</b> Mempelajari kurva pemanasan tanah dari pagi hingga sore hari, jam puncak radiasi matahari, dan waktu terjadinya presipitasi konvektif lokal.<br/>'
    '3. <b>Sistem Peringatan Dini Badai Mendadak (*Nowcasting Alert*):</b> Mendeteksi lonjakan kecepatan angin (*gust*) atau penurunan tekanan barometrik mendadak dalam hitungan menit sebelum hujan badai melanda perkebunan.',
    style_body
))

story.append(Spacer(1, 6))
story.append(make_callout_box(
    'File nusaklim_cleaned_interval.csv telah tersimpan di root workspace d:\\Downloads\\nusaklim\\nusaklim_cleaned_interval.csv (969.45 MB) dan siap diakses oleh seluruh peneliti dan tim AI PPKS.',
    title='LOKASI DATASET INTERVAL BERSIH'
))

story.append(Spacer(1, 10))
sig_data = [
    [Paragraph('<b>Disiapkan Oleh:</b><br/><br/><br/><u><b>Yudha Pratama</b></u><br/>Data Analyst NusaKlim PPKS', style_table_cell),
     Paragraph('<b>Disetujui Oleh:</b><br/><br/><br/><u><b>Tim Peneliti &amp; IT NusaKlim</b></u><br/>Pusat Penelitian Kelapa Sawit (PPKS)', style_table_cell)]
]
tbl_sig = Table(sig_data, colWidths=[250, 255])
tbl_sig.setStyle(TableStyle([
    ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 6),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_sig)

print('Building Interval Cleaned Master PDF Report...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
