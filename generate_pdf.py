import os, sys, pandas as pd, numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

pdf_path = r'd:\Downloads\nusaklim\Laporan_Preprocessing_dan_EDA_NusaKlim_PPKS.pdf'
figures_dir = r'd:\Downloads\nusaklim\figures'

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
        self.drawString(40, 805, 'Pusat Penelitian Kelapa Sawit (PPKS) - Proyek NusaKlim AWS')
        self.drawRightString(555, 805, 'Dokumentasi Preprocessing & EDA Cuaca')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Laporan Teknis Standar Persiapan Data & Analisis Cuaca (Berdasarkan Notulen Rapat)')
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

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=25, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=10)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=15, textColor=COLOR_BODY, alignment=1, spaceAfter=20)
style_cover_meta = ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=COLOR_MUTED, alignment=1)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=COLOR_PRIMARY, spaceBefore=12, spaceAfter=6, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=COLOR_SECONDARY, spaceBefore=9, spaceAfter=4, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12.5, textColor=COLOR_BODY, spaceAfter=5, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, leading=11.5, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=COLOR_MUTED, alignment=1, spaceBefore=3, spaceAfter=7)

def make_callout_box(text, title='CATATAN PENTING & LANDASAN TEKNIS', width=515):
    p_title = Paragraph(f'<b>{title}</b>', ParagraphStyle('CT', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=COLOR_PRIMARY, spaceAfter=2))
    p_text = Paragraph(text, style_callout)
    tbl = Table([[p_title], [p_text]], colWidths=[width])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_ACCENT),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl

story = []

# COVER PAGE
story.append(Spacer(1, 15))
header_inst = Paragraph(
    '<b>PUSAT PENELITIAN KELAPA SAWIT (PPKS)</b><br/><font color=\'#64748B\' size=\'8.5\'>Indonesian Oil Palm Research Institute</font>',
    ParagraphStyle('CoverInst', fontName='Helvetica', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 10))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=18))

story.append(Paragraph('LAPORAN TEKNIS PREPROCESSING DATA &amp; EXPLORATORY DATA ANALYSIS (EDA)', style_cover_title))
story.append(Paragraph('Standardisasi Pengolahan Data Telemetri AWS NusaKlim, Validasi Mutu Sensor, Agregasi Harian, dan Analisis Eksploratif Menuju Pengembangan Model Prediksi Cuaca 7 Hari', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Status Dokumen</b>', style_table_cell_bold), Paragraph('Laporan Komprehensif Preprocessing &amp; EDA (Final Production)', style_table_cell)],
    [Paragraph('<b>Dataset Target</b>', style_table_cell_bold), Paragraph('Data Telemetri AWS NusaKlim (14.827.287 raw records)', style_table_cell)],
    [Paragraph('<b>Jaringan Stasiun</b>', style_table_cell_bold), Paragraph('184 Automatic Weather Stations (AWS) Aktif PPKS', style_table_cell)],
    [Paragraph('<b>Rentang Observasi</b>', style_table_cell_bold), Paragraph('Januari 2022 – Agustus 2026 (4+ Tahun Operasional)', style_table_cell)],
    [Paragraph('<b>Dasar Rapat Notulen</b>', style_table_cell_bold), Paragraph('Rapat Tim Data Analyst &amp; Peneliti PPKS (Kamis, 20 Agustus 2026)', style_table_cell)],
    [Paragraph('<b>Target Akhir</b>', style_table_cell_bold), Paragraph('Pipeline ETL Bersih, Dataset Harian Standar, &amp; Kesiapan Model AI 7-Hari', style_table_cell)],
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

story.append(Spacer(1, 20))
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026 | Versi 1.0 (Production-Ready)', style_cover_meta))
story.append(PageBreak())

# SECTION 1
story.append(Paragraph('1. Pendahuluan dan Pemetaan Notulen Rapat', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Pusat Penelitian Kelapa Sawit (PPKS) mengoperasikan jaringan <i>Automatic Weather Station</i> (AWS) NusaKlim di berbagai perkebunan kelapa sawit di Indonesia. Informasi agroklimat yang presisi, kontinu, dan reliabel merupakan fondasi penting dalam penentuan jadwal agronomi (pemupukan, penyerbukan, pengendalian hama/penyakit, dan panen), analisis neraca air tanah, mitigasi defisit air, hingga prediksi hasil produksi kelapa sawit.',
    style_body
))
story.append(Paragraph(
    'Dokumen ini menyajikan metodologi menyeluruh, implementasi komputasi, dan analisis eksplorasi data (EDA) terhadap raw dataset telemetri AWS NusaKlim berukuran 1,37 GB (14.827.287 baris pencatatan). Seluruh tahapan perlakuan data dikembangkan secara ketat mengacu pada <b>Notulen Rapat Pembahasan Data Cuaca dan Pengembangan Model Prediksi Cuaca</b> tertanggal <b>20 Agustus 2026</b>.',
    style_body
))

story.append(Paragraph('1.1 Matriks Kesepakatan Notulen Rapat &amp; Implementasi Teknis', style_h2))

notulen_matrix = [
    [Paragraph('Poin Notulen', style_table_header), Paragraph('Arahan &amp; Kesepakatan Notulen', style_table_header), Paragraph('Implementasi Teknis &amp; Formula Preprocessing', style_table_header)],
    [Paragraph('<b>1. Konversi Suhu</b>', style_table_cell_bold), Paragraph('Suhu dari alat masih dalam satuan Fahrenheit. Harus dikonversi ke Celcius.', style_table_cell), Paragraph('<code>T_C = (tempout - 32.0) * (5.0 / 9.0)</code><br/>Validasi batas tropis: 12°C &le; T &le; 45°C. Kode eror 3276.7°F dan 0°F disaring menjadi NaN.', style_table_cell)],
    [Paragraph('<b>2. Konversi Tekanan</b>', style_table_cell_bold), Paragraph('Tekanan udara barometer dikoreksi dengan perkalian faktor kalibrasi.', style_table_cell), Paragraph('<code>P_hPa = bar * 33.864</code><br/>(Konversi inHg ke hPa/mbar). Filter ambang fisik: 920 &le; P &le; 1040 hPa.', style_table_cell)],
    [Paragraph('<b>3. Konversi Curah Hujan</b>', style_table_cell_bold), Paragraph('Data rain15 dikoreksi dengan faktor 12.70 untuk mendapatkan milimeter (mm).', style_table_cell), Paragraph('<code>Rain_mm = rain15 * 12.70</code><br/>Filter nilai anomali &gt; 60 mm/15-menit (pencegahan rollover pulse spike).', style_table_cell)],
    [Paragraph('<b>4. Aturan Agregasi Harian</b>', style_table_cell_bold), Paragraph('<b>Dijumlahkan (Sum):</b> Curah Hujan &amp; Solar Radiation.<br/><b>Dirata-ratakan (Mean):</b> Suhu, Tekanan, Kelembapan, Kec. Angin, Derajat Arah Angin.', style_table_cell), Paragraph('Agregasi per stasiun per tanggal lokal (WIB/UTC+7). Rain &amp; Solar diakumulasi, variabel kontinu dirata-ratakan. Dilengkapi nilai Min &amp; Max harian.', style_table_cell)],
    [Paragraph('<b>5. Kategorisasi Arah Angin</b>', style_table_cell_bold), Paragraph('Derajat harian dirata-ratakan dulu, lalu diklasifikasikan ke 4 arah mata angin:<br/>&gt;315° &amp; &le;45°: Utara; 45°-135°: Timur; 135°-225°: Selatan; 225°-315°: Barat.', style_table_cell), Paragraph('Logika bertingkat diterapkan pada rata-rata harian (0°-360°). Menghasilkan kolom <code>wind_direction_name</code>.', style_table_cell)],
    [Paragraph('<b>6. Penanganan Setup Awal</b>', style_table_cell_bold), Paragraph('Data saat instalasi awal (~9 ribuan baris bawaan/tes pabrik atau RTC default 2000/1970) harus dihapus/dibersihkan.', style_table_cell), Paragraph('Penyaringan timestamp UNIX epoch &lt; 2022-01-01 (1.640.995.200) dan penghapusan ID non-stasiun (WiFiLogger, 9991-9995).', style_table_cell)],
    [Paragraph('<b>7. Data Hilang &amp; Target Prediksi</b>', style_table_cell_bold), Paragraph('Evaluasi dampak missing data. Target peramalan cuaca 7 hari ke depan (univarian &amp; multivarian). Perbandingan dengan Open-Meteo.', style_table_cell), Paragraph('Audit missingness per variabel/stasiun, analisis korelasi fitur, dan rekomendasi model Machine Learning / Deep Learning time series.', style_table_cell)],
]

tbl_notulen = Table(notulen_matrix, colWidths=[95, 195, 225])
tbl_notulen.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_notulen)

story.append(Spacer(1, 6))
story.append(make_callout_box(
    'Setiap parameter meteorologi memiliki karakteristik instrumen tersendiri. Penerapan konversi satuan dan aturan agregasi yang tepat mencegah distorsi kalkulasi neraca air dan memastikan fitur masukan model prediksi 7-hari memiliki signifikansi fisis yang valid.',
    title='LANDASAN FISIS PENGOLAHAN AGROKLIMAT'
))

story.append(PageBreak())

# SECTION 2
story.append(Paragraph('2. Audit Mutu Raw Data &amp; Prosedur Quality Control (QC)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Raw dataset <code>nusaklim-aws-reduce.csv</code> memuat pencatatan telemetri stasiun cuaca interval 10-15 menitan. Sebelum dilakukan agregasi, dilakukan audit komprehensif terhadap seluruh 14.827.287 baris data untuk mendeteksi placeholder, anomali hardware sensor, dan error timestamp.',
    style_body
))

story.append(Paragraph('2.1 Hasil Profiling Raw Data &amp; Penyaringan Anomali', style_h2))

cleaning_table_data = [
    [Paragraph('Kategori Pembersihan', style_table_header), Paragraph('Deskripsi Kondisi / Error Code', style_table_header), Paragraph('Jumlah Baris', style_table_header), Paragraph('Persentase', style_table_header), Paragraph('Tindakan Preprocessing', style_table_header)],
    [Paragraph('<b>Total Raw Input</b>', style_table_cell_bold), Paragraph('Seluruh baris dalam file CSV', style_table_cell), Paragraph('14.827.287', style_table_cell_center), Paragraph('100.0%', style_table_cell_center), Paragraph('Read in Chunks (500k)', style_table_cell)],
    [Paragraph('ID Non-Stasiun', style_table_cell), Paragraph('Tag testing (WiFiLogger, 9991-9995)', style_table_cell), Paragraph('7', style_table_cell_center), Paragraph('&lt; 0.001%', style_table_cell_center), Paragraph('Dihapus permanen', style_table_cell)],
    [Paragraph('Timestamp Rusak / Null', style_table_cell), Paragraph('Nilai utctime bernilai \'---\' / string non-angka', style_table_cell), Paragraph('1', style_table_cell_center), Paragraph('&lt; 0.001%', style_table_cell_center), Paragraph('Dihapus permanen', style_table_cell)],
    [Paragraph('Setup Epoch (&lt; 2022)', style_table_cell), Paragraph('Tahun default 1970, 1999, 2000 (RTC uncalibrated)', style_table_cell), Paragraph('3.566', style_table_cell_center), Paragraph('0.024%', style_table_cell_center), Paragraph('Dihapus (Sesuai Notulen Poin 5)', style_table_cell)],
    [Paragraph('<b>Valid Interval Records</b>', style_table_cell_bold), Paragraph('Data interval operasional valid (2022-2026)', style_table_cell), Paragraph('<b>14.823.713</b>', style_table_cell_center), Paragraph('<b>99.976%</b>', style_table_cell_center), Paragraph('Diproses ke tahap QC Fisis', style_table_cell)],
    [Paragraph('Error Sensor Suhu', style_table_cell), Paragraph('Sentinel 3276.7°F (0x7FFF), 0°F ground fault, T&lt;12°C', style_table_cell), Paragraph('114.232', style_table_cell_center), Paragraph('0.77%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Solar', style_table_cell), Paragraph('Sentinel 32767 W/m² (0x7FFF) atau &gt; 1500 W/m²', style_table_cell), Paragraph('110.050', style_table_cell_center), Paragraph('0.74%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Arah Angin', style_table_cell), Paragraph('Sentinel 32767° (0x7FFF) atau derajat &gt; 360°', style_table_cell), Paragraph('138.268', style_table_cell_center), Paragraph('0.93%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Kelembapan', style_table_cell), Paragraph('Sentinel -1 (disconnect) atau 255 (0xFF)', style_table_cell), Paragraph('114.928', style_table_cell_center), Paragraph('0.78%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Kec. Angin', style_table_cell), Paragraph('Sentinel 255 (0xFF) atau kecepatan &gt; 80 km/h', style_table_cell), Paragraph('104.167', style_table_cell_center), Paragraph('0.70%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Placeholder String (\'---\')', style_table_cell), Paragraph('Sensor tidak terpasang / saluran kosong', style_table_cell), Paragraph('2.088k – 2.409k', style_table_cell_center), Paragraph('14.0% – 16.2%', style_table_cell_center), Paragraph('Konversi otomatis ke NaN', style_table_cell)],
]

tbl_cleaning = Table(cleaning_table_data, colWidths=[105, 145, 75, 65, 125])
tbl_cleaning.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 5), (-1, 5), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_cleaning)

story.append(Spacer(1, 5))
fig1_img = os.path.join(figures_dir, 'fig1_cleaning_summary.png')
if os.path.exists(fig1_img):
    story.append(Image(fig1_img, width=17.5*cm, height=6.8*cm))
    story.append(Paragraph('<b>Gambar 1:</b> Diagram Alur Pembersihan Data Raw NusaKlim dan Frekuensi Deteksi Error Hardware Sensor.', style_caption))

story.append(Paragraph('2.2 Alasan &amp; Rasional Ilmiah Pembersihan Sensor Sentinel', style_h2))
story.append(Paragraph(
    '<b>Mengapa sentinel hardware harus diubah menjadi NaN sebelum agregasi?</b> Pada stasiun cuaca digital berbasis mikroprosesor (seperti Davis Vantage Pro2), saat kabel sensor terputus, sensor mengalami korosi akibat kelembapan tinggi di kebun sawit, atau tegangan baterai solar drop, modul ADC mengirimkan nilai biner maksimum (misal <code>0x7FFF = 32767</code> untuk nilai 16-bit bertanda, yang diterjemahkan menjadi <code>3276.7°F</code> untuk suhu, atau <code>0xFF = 255</code> untuk 8-bit). Isolasi sentinel menjadi <code>NaN</code> mencegah distorsi perhitungan rata-rata iklim sesuai standar World Meteorological Organization (WMO No. 8).',
    style_body
))

story.append(PageBreak())

# SECTION 3
story.append(Paragraph('3. Prosedur Agregasi Harian &amp; Klasifikasi Arah Angin', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Sesuai arahan pada Notulen Rapat Butir 3 dan 4, data pengamatan berinterval 15-menit diagregasikan menjadi satu baris per stasiun per hari pengamatan lokal (Waktu Indonesia Barat / UTC+7). Agregasi harian ini menghasilkan dataset <code>nusaklim_daily_aggregated.csv</code> sebanyak <b>114.651 station-days</b> dari 184 stasiun aktif.',
    style_body
))

story.append(Paragraph('3.1 Formula Agregasi Harian', style_h2))

agg_rules_data = [
    [Paragraph('Variabel Cuaca', style_table_header), Paragraph('Satuan Raw', style_table_header), Paragraph('Satuan Target', style_table_header), Paragraph('Metode Agregasi', style_table_header), Paragraph('Formula Matematis &amp; Keterangan', style_table_header)],
    [Paragraph('<b>Curah Hujan (Rain)</b>', style_table_cell_bold), Paragraph('Tipping raw', style_table_cell), Paragraph('mm / hari', style_table_cell), Paragraph('<b>Penjumlahan (SUM)</b>', style_table_cell_bold), Paragraph('<code>R_harian = &Sigma; (rain15 * 12.70)</code><br/>Akumulasi presipitasi total dalam 24 jam.', style_table_cell)],
    [Paragraph('<b>Radiasi Solar</b>', style_table_cell_bold), Paragraph('W/m²', style_table_cell), Paragraph('W/m² kumulatif', style_table_cell), Paragraph('<b>Penjumlahan (SUM)</b>', style_table_cell_bold), Paragraph('<code>Solar_harian = &Sigma; (solar_15min)</code><br/>Total insolasi radiasi matahari harian.', style_table_cell)],
    [Paragraph('<b>Suhu Udara (Temp)</b>', style_table_cell_bold), Paragraph('°F', style_table_cell), Paragraph('°C', style_table_cell), Paragraph('<b>Rata-rata (MEAN)</b> + Min/Max', style_table_cell), Paragraph('<code>T_avg = (1/N) &Sigma; T_C</code><br/>Dilengkapi pencatatan <code>T_min</code> dan <code>T_max</code>.', style_table_cell)],
    [Paragraph('<b>Tekanan Barometer</b>', style_table_cell_bold), Paragraph('inHg', style_table_cell), Paragraph('hPa (mbar)', style_table_cell), Paragraph('<b>Rata-rata (MEAN)</b>', style_table_cell), Paragraph('<code>P_avg = (1/N) &Sigma; (bar * 33.864)</code><br/>Rata-rata tekanan permukaan laut / stasiun.', style_table_cell)],
    [Paragraph('<b>Kelembapan (RH)</b>', style_table_cell_bold), Paragraph('%', style_table_cell), Paragraph('%', style_table_cell), Paragraph('<b>Rata-rata (MEAN)</b> + Min/Max', style_table_cell), Paragraph('<code>RH_avg = (1/N) &Sigma; RH</code><br/>Dilengkapi pencatatan <code>RH_min</code> dan <code>RH_max</code>.', style_table_cell)],
    [Paragraph('<b>Kecepatan Angin</b>', style_table_cell_bold), Paragraph('knot / km/h', style_table_cell), Paragraph('km/h', style_table_cell), Paragraph('<b>Rata-rata (MEAN)</b> + Max', style_table_cell), Paragraph('<code>V_avg = (1/N) &Sigma; V</code><br/>Dilengkapi <code>V_max</code> (gust / kec. maksimum).', style_table_cell)],
    [Paragraph('<b>Arah Angin (Derajat)</b>', style_table_cell_bold), Paragraph('0° – 360°', style_table_cell), Paragraph('Derajat &amp; Kategori', style_table_cell), Paragraph('<b>Rata-rata (MEAN)</b> &rarr; Kategori', style_table_cell), Paragraph('<code>&theta;_avg = (1/N) &Sigma; &theta;</code><br/>Dilanjutkan konversi ke nama mata angin.', style_table_cell)],
]

tbl_agg_rules = Table(agg_rules_data, colWidths=[110, 60, 75, 105, 165])
tbl_agg_rules.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.2),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_agg_rules)

story.append(Spacer(1, 6))
story.append(Paragraph('3.2 Logika Klasifikasi Arah Mata Angin (Notulen Poin 4)', style_h2))

wind_class_data = [
    [Paragraph('Rentang Derajat Arah Angin (&theta;)', style_table_header), Paragraph('Sektor Derajat', style_table_header), Paragraph('Kategori Arah Angin', style_table_header), Paragraph('Kode Output', style_table_header)],
    [Paragraph('&gt; 315° atau &le; 45°', style_table_cell_bold), Paragraph('315.1° – 360.0° dan 0.0° – 45.0°', style_table_cell), Paragraph('<b>Utara</b>', style_table_cell_bold), Paragraph('<code>\'Utara\'</code>', style_table_cell)],
    [Paragraph('&gt; 225° s.d. 315°', style_table_cell_bold), Paragraph('225.1° – 315.0°', style_table_cell), Paragraph('<b>Barat</b>', style_table_cell_bold), Paragraph('<code>\'Barat\'</code>', style_table_cell)],
    [Paragraph('&gt; 135° s.d. 225°', style_table_cell_bold), Paragraph('135.1° – 225.0°', style_table_cell), Paragraph('<b>Selatan</b>', style_table_cell_bold), Paragraph('<code>\'Selatan\'</code>', style_table_cell)],
    [Paragraph('&gt; 45° s.d. 135°', style_table_cell_bold), Paragraph('45.1° – 135.0°', style_table_cell), Paragraph('<b>Timur</b>', style_table_cell_bold), Paragraph('<code>\'Timur\'</code>', style_table_cell)],
    [Paragraph('Nilai Hilang / Sensor Rusak', style_table_cell), Paragraph('NaN / Null / Error Code', style_table_cell), Paragraph('Tidak Tersedia', style_table_cell), Paragraph('<code>\'---\'</code>', style_table_cell)],
]
tbl_wind = Table(wind_class_data, colWidths=[150, 140, 115, 110])
tbl_wind.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_SECONDARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_SECONDARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.2),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_wind)

story.append(Spacer(1, 5))
fig5_img = os.path.join(figures_dir, 'fig5_wind_analysis.png')
if os.path.exists(fig5_img):
    story.append(Image(fig5_img, width=17.5*cm, height=6.8*cm))
    story.append(Paragraph('<b>Gambar 2:</b> Proporsi Distribusi Arah Mata Angin dan Boxplot Kecepatan Angin per Kategori Sesuai Aturan Notulen Rapat.', style_caption))

story.append(PageBreak())

# SECTION 4
story.append(Paragraph('4. Hasil Exploratory Data Analysis (EDA) Komprehensif', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Analisis eksploratif dilakukan terhadap data harian yang telah terstandarisasi untuk mengungkap pola fisis atmosfer di perkebunan kelapa sawit, meliputi statistik deskriptif, bentuk distribusi, interkorelasi antar variabel cuaca, pola deret waktu musiman, serta siklus diurnal 24-jam.',
    style_body
))

story.append(Paragraph('4.1 Statistik Deskriptif Agregasi Harian (114.651 Station-Days)', style_h2))

stats_table_data = [
    [Paragraph('Variabel Cuaca', style_table_header), Paragraph('N Valid', style_table_header), Paragraph('Mean &plusmn; Std', style_table_header), Paragraph('Min', style_table_header), Paragraph('P25', style_table_header), Paragraph('Median', style_table_header), Paragraph('P75', style_table_header), Paragraph('P99', style_table_header), Paragraph('Max', style_table_header)],
    [Paragraph('<b>Suhu Rata-rata (°C)</b>', style_table_cell_bold), Paragraph('99.792', style_table_cell_center), Paragraph('26.85 &plusmn; 1.84', style_table_cell_center), Paragraph('13.68', style_table_cell_center), Paragraph('26.03', style_table_cell_center), Paragraph('26.94', style_table_cell_center), Paragraph('27.84', style_table_cell_center), Paragraph('31.33', style_table_cell_center), Paragraph('36.44', style_table_cell_center)],
    [Paragraph('<b>Suhu Minimum (°C)</b>', style_table_cell_bold), Paragraph('99.792', style_table_cell_center), Paragraph('23.39 &plusmn; 1.85', style_table_cell_center), Paragraph('12.00', style_table_cell_center), Paragraph('22.83', style_table_cell_center), Paragraph('23.56', style_table_cell_center), Paragraph('24.22', style_table_cell_center), Paragraph('28.56', style_table_cell_center), Paragraph('36.44', style_table_cell_center)],
    [Paragraph('<b>Suhu Maksimum (°C)</b>', style_table_cell_bold), Paragraph('99.792', style_table_cell_center), Paragraph('31.62 &plusmn; 2.54', style_table_cell_center), Paragraph('15.22', style_table_cell_center), Paragraph('30.22', style_table_cell_center), Paragraph('31.94', style_table_cell_center), Paragraph('33.39', style_table_cell_center), Paragraph('36.89', style_table_cell_center), Paragraph('44.28', style_table_cell_center)],
    [Paragraph('<b>Kelembapan Avg (%)</b>', style_table_cell_bold), Paragraph('99.815', style_table_cell_center), Paragraph('85.12 &plusmn; 6.42', style_table_cell_center), Paragraph('25.10', style_table_cell_center), Paragraph('81.42', style_table_cell_center), Paragraph('86.25', style_table_cell_center), Paragraph('89.91', style_table_cell_center), Paragraph('96.88', style_table_cell_center), Paragraph('99.95', style_table_cell_center)],
    [Paragraph('<b>Tekanan Udara (hPa)</b>', style_table_cell_bold), Paragraph('100.200', style_table_cell_center), Paragraph('998.40 &plusmn; 19.43', style_table_cell_center), Paragraph('920.12', style_table_cell_center), Paragraph('996.15', style_table_cell_center), Paragraph('1004.36', style_table_cell_center), Paragraph('1007.82', style_table_cell_center), Paragraph('1013.10', style_table_cell_center), Paragraph('1038.50', style_table_cell_center)],
    [Paragraph('<b>Curah Hujan (mm/hr)</b>', style_table_cell_bold), Paragraph('101.368', style_table_cell_center), Paragraph('7.24 &plusmn; 14.85', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('7.62', style_table_cell_center), Paragraph('68.58', style_table_cell_center), Paragraph('215.90', style_table_cell_center)],
    [Paragraph('<b>Radiasi Solar (W/m²)</b>', style_table_cell_bold), Paragraph('99.805', style_table_cell_center), Paragraph('14.520 &plusmn; 5.610', style_table_cell_center), Paragraph('0', style_table_cell_center), Paragraph('10.840', style_table_cell_center), Paragraph('15.120', style_table_cell_center), Paragraph('18.760', style_table_cell_center), Paragraph('25.400', style_table_cell_center), Paragraph('31.280', style_table_cell_center)],
    [Paragraph('<b>Kecepatan Angin (km/h)</b>', style_table_cell_bold), Paragraph('99.937', style_table_cell_center), Paragraph('0.81 &plusmn; 0.82', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('0.39', style_table_cell_center), Paragraph('0.68', style_table_cell_center), Paragraph('1.03', style_table_cell_center), Paragraph('3.38', style_table_cell_center), Paragraph('45.77', style_table_cell_center)],
]

tbl_stats = Table(stats_table_data, colWidths=[105, 45, 75, 40, 40, 42, 40, 43, 45])
tbl_stats.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_stats)

story.append(Spacer(1, 5))
fig2_img = os.path.join(figures_dir, 'fig2_distributions.png')
if os.path.exists(fig2_img):
    story.append(Image(fig2_img, width=17.5*cm, height=9.2*cm))
    story.append(Paragraph('<b>Gambar 3:</b> Histogram dan Kernel Density Estimation (KDE) Distribusi Parameter Cuaca Harian NusaKlim.', style_caption))

story.append(PageBreak())

# SECTION 5
story.append(Paragraph('5. Analisis Korelasi Multivariat &amp; Dinamika Waktu', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Analisis keterkaitan antar variabel cuaca sangat penting untuk menentukan <b>seleksi fitur (feature engineering)</b> pada model prediksi 7 hari ke depan, sebagaimana ditekankan pada Notulen Butir 7.2 (Model dengan variabel tambahan seperti tekanan, kelembapan, suhu, dan insolasi radiasi).',
    style_body
))

fig3_img = os.path.join(figures_dir, 'fig3_correlation.png')
if os.path.exists(fig3_img):
    story.append(Image(fig3_img, width=13.0*cm, height=9.6*cm))
    story.append(Paragraph('<b>Gambar 4:</b> Matriks Korelasi Pearson Antar Parameter Cuaca Harian AWS NusaKlim.', style_caption))

story.append(Paragraph('5.1 Wawasan Kunci Dinamika Atmosferik', style_h2))
story.append(Paragraph(
    '&bull; <b>Hubungan Kuat Suhu vs Kelembapan (r = -0.74):</b> Terdapat korelasi negatif yang sangat kuat antara suhu rata-rata dan kelembapan relatif. Saat suhu naik (siang hari), kapasitas udara menampung uap air jenuh meningkat drastis, menyebabkan penurunan kelembapan relatif. Sebaliknya, saat malam hari atau cuaca hujan, kelembapan mendekati titik jenuh (&gt;90%).<br/>'
    '&bull; <b>Hubungan Radiasi Solar vs Suhu (r = +0.62) &amp; Kelembapan (r = -0.58):</b> Insolasi gelombang pendek dari matahari adalah penggerak utama fluks panas sensibel permukaan, yang memanaskan lapisan batas atmosfer.<br/>'
    '&bull; <b>Korelasi Multivariat terhadap Curah Hujan:</b> Curah hujan berkorelasi negatif dengan suhu rata-rata (r = -0.32) dan insolasi solar (r = -0.38), serta berkorelasi positif dengan kelembapan (r = +0.35) dan penurunan tekanan atmosfer lokal (r = -0.18). Pola fisis ini menegaskan bahwa model prediksi curah hujan 7-hari akan jauh lebih akurat jika menggunakan <b>pendekatan multivariat</b> dibandingkan univarian murni.',
    style_body
))

story.append(Spacer(1, 4))
fig7_img = os.path.join(figures_dir, 'fig7_diurnal_cycle.png')
if os.path.exists(fig7_img):
    story.append(Image(fig7_img, width=17.5*cm, height=9.2*cm))
    story.append(Paragraph('<b>Gambar 5:</b> Profil Siklus Diurnal 24 Jam (Waktu Indonesia Barat) Suhu, Radiasi Solar, Kelembapan, dan Tekanan Udara.', style_caption))

story.append(PageBreak())

# SECTION 6
story.append(Paragraph('6. Analisis Deret Waktu, Musiman, dan Ekstrem Presipitasi', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Data observasi NusaKlim yang mencakup periode Januari 2022 hingga Agustus 2026 memungkinkan evaluasi osilasi musiman (Monsoon Asia-Australia) dan fenomena anomali iklim global seperti El Niño–Southern Oscillation (ENSO) dan Indian Ocean Dipole (IOD).',
    style_body
))

fig4_img = os.path.join(figures_dir, 'fig4_timeseries_trend.png')
if os.path.exists(fig4_img):
    story.append(Image(fig4_img, width=17.5*cm, height=9.8*cm))
    story.append(Paragraph('<b>Gambar 6:</b> Tren Rangkaian Waktu Cuaca Harian Nasional Periode 2022 – 2026 (Moving Average 7 Hari).', style_caption))

story.append(Paragraph('6.1 Klasifikasi Intensitas Curah Hujan Harian Standar BMKG', style_h2))

fig6_img = os.path.join(figures_dir, 'fig6_rainfall_classification.png')
if os.path.exists(fig6_img):
    story.append(Image(fig6_img, width=17.5*cm, height=6.5*cm))
    story.append(Paragraph('<b>Gambar 7:</b> Klasifikasi Frekuensi Curah Hujan Standar BMKG dan Top 10 Stasiun AWS Akumulasi Hujan Tertinggi.', style_caption))

story.append(Paragraph(
    'Dari total 101.368 hari pengamatan presipitasi valid:<br/>'
    '&bull; <b>Berawan / Tidak Hujan (0.0 mm):</b> 56.418 hari (55.7%) &ndash; hari kering ideal untuk pemanenan dan transportasi TBS.<br/>'
    '&bull; <b>Hujan Ringan (0.1 &ndash; 20.0 mm):</b> 31.842 hari (31.4%) &ndash; intensitas optimal yang terserap oleh perakaran sawit.<br/>'
    '&bull; <b>Hujan Sedang (20.0 &ndash; 50.0 mm):</b> 9.940 hari (9.8%) &ndash; kelembapan tanah mencukupi, memerlukan monitoring drainase.<br/>'
    '&bull; <b>Hujan Lebat (50.0 &ndash; 100.0 mm):</b> 2.812 hari (2.8%) &ndash; potensi aliran permukaan tinggi.<br/>'
    '&bull; <b>Hujan Sangat Lebat &amp; Ekstrem (&gt; 100.0 mm):</b> 356 hari (0.35%) &ndash; kejadian cuaca ekstrem yang memerlukan peringatan dini.',
    style_body
))

story.append(PageBreak())

# SECTION 7
story.append(Paragraph('7. Evaluasi Kesiapan Data &amp; Desain Model Prediksi 7-Hari', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Mengacu pada Notulen Rapat Butir 7, 8, dan 9, target utama dari persiapan data ini adalah pengembangan model ramalan cuaca hingga 7 hari ke depan serta pembandingan dengan layanan API eksternal Open-Meteo.',
    style_body
))

fig8_img = os.path.join(figures_dir, 'fig8_station_longevity.png')
if os.path.exists(fig8_img):
    story.append(Image(fig8_img, width=15.0*cm, height=6.2*cm))
    story.append(Paragraph('<b>Gambar 8:</b> Distribusi Durasi Pengamatan per Stasiun AWS (Total 184 Stasiun Operasional).', style_caption))

story.append(Paragraph('7.1 Rekomendasi Arsitektur Pemodelan Prediksi Cuaca 7 Hari', style_h2))

model_matrix = [
    [Paragraph('Pendekatan Model', style_table_header), Paragraph('Deskripsi Fitur &amp; Algoritma', style_table_header), Paragraph('Kelebihan', style_table_header), Paragraph('Kelemahan &amp; Mitigasi', style_table_header)],
    [Paragraph('<b>Model 1: Univarian Historis</b>', style_table_cell_bold), Paragraph('Model autoregresif (ARIMA/SARIMA, Prophet, LSTM Univariate) menggunakan data lag target (misal: Rain(t-1..t-30) &rarr; Rain(t+1..t+7)).', style_table_cell), Paragraph('&bull; Komputasi sangat ringan.<br/>&bull; Mudah di-deploy untuk 184 stasiun secara independen.', style_table_cell), Paragraph('&bull; Kurang mampu menangkap badai konvektif tiba-tiba.<br/>&bull; Akurasi menurun tajam di atas horizon H+3.', style_table_cell)],
    [Paragraph('<b>Model 2: Multivarian Tabular (GBM)</b>', style_table_cell_bold), Paragraph('XGBoost / LightGBM / CatBoost dengan fitur lag multivariat (Suhu, RH, Barometer, Solar, Arah Angin, Siklus Sin/Cos Hari).', style_table_cell), Paragraph('&bull; Sangat tangguh terhadap tabular.<br/>&bull; Menangkap interaksi non-linear.<br/>&bull; Metrik evaluasi transparan (Feature Importance).', style_table_cell), Paragraph('&bull; Perlu strategi Direct Multi-Output.<br/>&bull; Rentan jika sensor input missing.', style_table_cell)],
    [Paragraph('<b>Model 3: Deep Sequence (TFT / PatchTST)</b>', style_table_cell_bold), Paragraph('Temporal Fusion Transformer (TFT) atau PatchTST untuk peramalan multi-horizon spatiotemporal.', style_table_cell), Paragraph('&bull; Estimasi interval kepercayaan (Quantile Loss 10%, 50%, 90%).<br/>&bull; State-of-the-art pada horizon 7 hari.', style_table_cell), Paragraph('&bull; Memerlukan resource GPU training.<br/>&bull; Kompleksitas deployment lebih tinggi.', style_table_cell)],
]

tbl_models = Table(model_matrix, colWidths=[105, 145, 125, 130])
tbl_models.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_models)

story.append(Paragraph('7.2 Metrik Evaluasi &amp; Protokol Komparasi dengan Open-Meteo', style_h2))
story.append(Paragraph(
    '&bull; <b>Variabel Kontinu (Suhu, Kelembapan, Tekanan):</b> <i>Mean Absolute Error</i> (MAE), <i>Root Mean Squared Error</i> (RMSE), dan <i>Coefficient of Determination</i> (R²).<br/>'
    '&bull; <b>Curah Hujan (Kejadian Hujan/Kering):</b> <i>Critical Success Index</i> (CSI), <i>Heidke Skill Score</i> (HSS), F1-Score, dan <i>Brier Score</i>.<br/>'
    '&bull; <b>Benchmarking Open-Meteo:</b> Model internal dibandingkan langsung <i>head-to-head</i> dengan data peramalan API Open-Meteo pada stasiun uji selama 30 hari observasi aktual (<i>ground-truth testing</i>). Jika model internal lebih stabil, model internal menjadi sumber utama; jika selisihnya tipis, sistem web NusaKlim akan menyajikan kedua sumber sebagai pembanding (<i>ensemble view</i>).',
    style_body
))

story.append(Paragraph('7.3 Strategi Tampilan Dashboard &amp; Website (Notulen Poin 10)', style_h2))
story.append(Paragraph(
    'Untuk mengakomodasi kebutuhan pengguna di kebun/lapangan yang membutuhkan akses data cepat sekaligus visualisasi interaktif bagi manajemen:<br/>'
    '1. <b>Tampilan Tabel Data Cepat:</b> Mempertahankan tabel ringkasan harian dengan fitur filter stasiun, sorting tanggal, dan tombol ekspor CSV/Excel.<br/>'
    '2. <b>Tampilan Visual Interaktif:</b> Menambahkan sparkline tren 7 hari, kartu metrik cuaca hari ini (Suhu, Curah Hujan, Arah Angin), grafik probabilitas hujan harian, dan peta sebaran kondisi stasiun berbasis warna BMKG.',
    style_body
))

story.append(PageBreak())

# SECTION 8
story.append(Paragraph('8. Kesimpulan &amp; Inventaris Artifak Output', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Proses data preprocessing dan Exploratory Data Analysis (EDA) terhadap 14,8 juta raw telemetri AWS NusaKlim telah berhasil diselesaikan dengan hasil yang sepenuhnya memenuhi mandat Notulen Rapat 20 Agustus 2026. Data cuaca yang telah dibersihkan kini siap digunakan secara optimal untuk pengembangan model prediksi dan integrasi visualisasi website.',
    style_body
))

artifact_data = [
    [Paragraph('Nama Artifak / File', style_table_header), Paragraph('Format &amp; Ukuran', style_table_header), Paragraph('Deskripsi &amp; Kegunaan', style_table_header)],
    [Paragraph('<code>nusaklim_daily_aggregated.csv</code>', style_table_cell_bold), Paragraph('CSV (10,1 MB / 114.651 baris)', style_table_cell_center), Paragraph('Dataset harian bersih terstandarisasi (184 stasiun, 2022-2026) lengkap dengan konversi metrik (°C, hPa, mm), Min/Max, dan kategori arah mata angin. Siap untuk training model prediksi 7 hari.', style_table_cell)],
    [Paragraph('<code>figures/*.png</code> (8 Charts)', style_table_cell_bold), Paragraph('PNG Resolusi Tinggi (300 DPI)', style_table_cell_center), Paragraph('Koleksi lengkap 8 grafik analitis: Alur QC, Distribusi Variabel, Matriks Korelasi, Tren Deret Waktu, Analisis Angin, Klasifikasi BMKG, Siklus Diurnal, dan Kelengkapan Stasiun.', style_table_cell)],
    [Paragraph('<code>Laporan_Preprocessing_dan_EDA_NusaKlim_PPKS.pdf</code>', style_table_cell_bold), Paragraph('PDF Dokumen Resmi', style_table_cell_center), Paragraph('Dokumentasi teknis lengkap berstandar akademik dan profesional industri untuk arsip PPKS dan panduan tim riset/pengembangan.', style_table_cell)],
    [Paragraph('<code>process_nusaklim.py</code>', style_table_cell_bold), Paragraph('Python Script (Production ETL)', style_table_cell_center), Paragraph('Pipeline kode pemrosesan streaming modular dan efisien memori yang dapat dijalankan secara otomatis (cron/batch ETL harian).', style_table_cell)],
]

tbl_artifacts = Table(artifact_data, colWidths=[150, 110, 245])
tbl_artifacts.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 4),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_artifacts)

story.append(Spacer(1, 8))
story.append(make_callout_box(
    'Seluruh kode sumber pemrosesan telah dioptimalkan dengan pembacaan chunk bertahap (500.000 baris/chunk), sehingga mampu memproses 14,8 juta baris data dalam waktu kurang dari 2,5 menit dengan konsumsi memori stabil di bawah 500 MB RAM.',
    title='EFISIENSI KOMPUTASI & KESIAPAN INTEGRASI'
))

story.append(Spacer(1, 12))
sig_data = [
    [Paragraph('<b>Disiapkan Oleh:</b><br/><br/><br/><u><b>Yudha Pratama</b></u><br/>Data Analyst NusaKlim PPKS', style_table_cell),
     Paragraph('<b>Disetujui Oleh:</b><br/><br/><br/><u><b>Tim Peneliti &amp; IT NusaKlim</b></u><br/>Pusat Penelitian Kelapa Sawit (PPKS)', style_table_cell)]
]
tbl_sig = Table(sig_data, colWidths=[250, 255])
tbl_sig.setStyle(TableStyle([
    ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 7),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_sig)

print('Building PDF document...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
