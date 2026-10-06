import os, sys, pandas as pd, numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Arial TTF fonts for full Unicode support (±, °, →, ², −, ñ, etc.)
pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', r'C:\Windows\Fonts\arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', r'C:\Windows\Fonts\ariali.ttf'))
pdfmetrics.registerFont(TTFont('Arial-BoldItalic', r'C:\Windows\Fonts\arialbi.ttf'))
from reportlab.lib.fonts import addMapping
addMapping('Arial', 0, 0, 'Arial')
addMapping('Arial', 1, 0, 'Arial-Bold')
addMapping('Arial', 0, 1, 'Arial-Italic')
addMapping('Arial', 1, 1, 'Arial-BoldItalic')


pdf_path = r'D:\Projects\Kodepanda\Nusaklim\nusaklim\report\2.Laporan_Preprocessing_dan_EDA_NusaKlim_PPKS.pdf'
figures_dir = r'D:\Projects\Kodepanda\Nusaklim\nusaklim\figures'

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
        self.setFont('Arial', 8)
        self.setFillColor(colors.HexColor('#475569'))
        self.drawString(40, 805, 'Pusat Penelitian Kelapa Sawit (PPKS) - Proyek NusaKlim AWS')
        self.drawRightString(555, 805, 'Dokumentasi Preprocessing & EDA Cuaca')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Laporan Teknis Persiapan Data & Analisis Cuaca')
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

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=20, leading=25, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=10)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Arial', fontSize=11, leading=15, textColor=COLOR_BODY, alignment=1, spaceAfter=20)
style_cover_meta = ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12, textColor=COLOR_MUTED, alignment=1)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Arial-Bold', fontSize=13, leading=16, textColor=COLOR_PRIMARY, spaceBefore=12, spaceAfter=6, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Arial-Bold', fontSize=10, leading=13, textColor=COLOR_SECONDARY, spaceBefore=9, spaceAfter=4, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12.5, textColor=COLOR_BODY, spaceAfter=5, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Arial-Italic', fontSize=8, leading=11.5, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Arial-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Arial', fontSize=7.5, leading=10, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=10, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Arial', fontSize=7.5, leading=10, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=10, textColor=COLOR_MUTED, alignment=1, spaceBefore=3, spaceAfter=7)

def make_callout_box(text, title='CATATAN PENTING & LANDASAN TEKNIS', width=515):
    p_title = Paragraph(f'<b>{title}</b>', ParagraphStyle('CT', fontName='Arial-Bold', fontSize=8, leading=10, textColor=COLOR_PRIMARY, spaceAfter=2))
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
    ParagraphStyle('CoverInst', fontName='Arial', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 10))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=18))

story.append(Paragraph('LAPORAN TEKNIS PREPROCESSING DATA &amp; EXPLORATORY DATA ANALYSIS (EDA)', style_cover_title))
story.append(Paragraph('Standardisasi Pengolahan Data AWS NusaKlim, Validasi Mutu Sensor, Agregasi Harian, dan Analisis Eksploratif Menuju Pengembangan Model Prediksi Cuaca 7 Hari', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Status Dokumen</b>', style_table_cell_bold), Paragraph('Laporan Komprehensif Preprocessing &amp; EDA (Final Production)', style_table_cell)],
    [Paragraph('<b>Dataset Target</b>', style_table_cell_bold), Paragraph('Data AWS NusaKlim (14.827.287 raw records)', style_table_cell)],
    [Paragraph('<b>Jaringan Stasiun</b>', style_table_cell_bold), Paragraph('183 Stasiun Cuaca Otomatis (AWS) Aktif PPKS', style_table_cell)],
    [Paragraph('<b>Rentang Observasi</b>', style_table_cell_bold), Paragraph('Januari 2022 – Agustus 2026 (4+ Tahun Operasional)', style_table_cell)],
    [Paragraph('<b>Target Akhir</b>', style_table_cell_bold), Paragraph('Data Bersih, Dataset Harian Standar, &amp; Kesiapan Model Prediksi 7-Hari', style_table_cell)],
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
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> Oktober 2026 | Versi 1.0 (Production-Ready)', style_cover_meta))
story.append(PageBreak())

# SECTION 1
story.append(Paragraph('1. Pendahuluan', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Pusat Penelitian Kelapa Sawit (PPKS) mengoperasikan jaringan <i>Automatic Weather Station</i> (AWS) NusaKlim di berbagai perkebunan kelapa sawit di Indonesia. Informasi agroklimat yang presisi, kontinu, dan reliabel merupakan fondasi penting dalam penentuan jadwal agronomi (pemupukan, penyerbukan, pengendalian hama/penyakit, dan panen), analisis neraca air tanah, mitigasi defisit air, hingga prediksi hasil produksi kelapa sawit.',
    style_body
))
story.append(Paragraph(
    'Dokumen ini menyajikan metodologi menyeluruh, implementasi komputasi, dan analisis eksplorasi data terhadap seluruh data cuaca AWS NusaKlim berukuran 1,37 GB (14.827.287 baris pencatatan).',
    style_body
))

story.append(Paragraph('1.1 Ringkasan Metodologi Pengolahan Data', style_h2))

notulen_matrix = [
    [Paragraph('Tahapan', style_table_header), Paragraph('Aturan yang Diterapkan', style_table_header), Paragraph('Cara Kerja Teknis', style_table_header)],
    [Paragraph('<b>1. Konversi Suhu</b>', style_table_cell_bold), Paragraph('Suhu dari alat masih dalam satuan Fahrenheit. Harus dikonversi ke Celcius.', style_table_cell), Paragraph('<code>T_C = (tempout - 32.0) * (5.0 / 9.0)</code><br/>Batas kewajaran fisik: 0°C &le; T &le; 100°C. Kode eror 3276.7°F dan -90°F disaring menjadi NaN.', style_table_cell)],
    [Paragraph('<b>2. Konversi Tekanan</b>', style_table_cell_bold), Paragraph('Tekanan udara barometer dikoreksi dengan perkalian faktor kalibrasi.', style_table_cell), Paragraph('<code>P_hPa = bar * 33.864</code><br/>(Konversi inHg ke hPa/mbar). Batas kewajaran fisik: 500 &le; P &le; 1200 hPa.', style_table_cell)],
    [Paragraph('<b>3. Konversi Curah Hujan</b>', style_table_cell_bold), Paragraph('Data rain15 dikoreksi dengan faktor 12.70 untuk mendapatkan milimeter (mm).', style_table_cell), Paragraph('<code>Rain_mm = rain15 * 12.70</code><br/>Batas kewajaran fisik: 0 &le; RR &le; 1000 mm per interval.', style_table_cell)],
    [Paragraph('<b>4. Aturan Agregasi Harian</b>', style_table_cell_bold), Paragraph('<b>Dijumlahkan (Sum):</b> Curah Hujan &amp; Solar Radiation.<br/><b>Dirata-ratakan (Mean):</b> Suhu, Tekanan, Kelembapan, Kec. Angin, Derajat Arah Angin.', style_table_cell), Paragraph('Agregasi per stasiun per tanggal lokal (WIB/UTC+7). Rain &amp; Solar diakumulasi, variabel kontinu dirata-ratakan. Dilengkapi nilai Min &amp; Max harian.', style_table_cell)],
    [Paragraph('<b>5. Kategorisasi Arah Angin</b>', style_table_cell_bold), Paragraph('Derajat harian dirata-ratakan dulu, lalu diklasifikasikan ke 4 arah mata angin:<br/>&gt;315° &amp; &le;45°: Utara; 45°-135°: Timur; 135°-225°: Selatan; 225°-315°: Barat.', style_table_cell), Paragraph('Logika bertingkat diterapkan pada rata-rata harian (0°-360°). Menghasilkan kolom <code>wind_direction_name</code>.', style_table_cell)],
    [Paragraph('<b>6. Penanganan Setup Awal</b>', style_table_cell_bold), Paragraph('Data saat instalasi awal (~9 ribuan baris bawaan/tes pabrik atau RTC default 2000/1970) harus dihapus/dibersihkan.', style_table_cell), Paragraph('Penyaringan timestamp UNIX epoch &lt; 2022-01-01 (1.640.995.200) dan penghapusan ID non-stasiun (WiFiLogger, 9991-9995).', style_table_cell)],
    [Paragraph('<b>7. Data Hilang &amp; Target Prediksi</b>', style_table_cell_bold), Paragraph('Evaluasi dampak data yang hilang. Target peramalan cuaca 7 hari ke depan. Perbandingan dengan layanan cuaca Open-Meteo.', style_table_cell), Paragraph('Audit data hilang per variabel/stasiun, analisis keterkaitan antar variabel, dan rekomendasi model peramalan deret waktu.', style_table_cell)],
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
    'Setiap parameter meteorologi memiliki karakteristik instrumen tersendiri. Penerapan konversi satuan dan aturan agregasi yang tepat mencegah distorsi kalkulasi neraca air dan memastikan fitur masukan model prediksi 7-hari secara ilmiah valid.',
    title='LANDASAN ILMIAH PENGOLAHAN AGROKLIMAT'
))

story.append(PageBreak())

# SECTION 2
story.append(Paragraph('2. Audit Mutu Raw Data &amp; Prosedur Quality Control (QC)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Data mentah memuat pencatatan stasiun cuaca interval 10-15 menitan. Sebelum dilakukan agregasi, dilakukan audit menyeluruh terhadap seluruh 14.827.287 baris data untuk mendeteksi data kosong, kesalahan pembacaan sensor, dan kesalahan waktu pencatatan.',
    style_body
))

story.append(Paragraph('2.1 Hasil Profiling Raw Data &amp; Penyaringan Anomali', style_h2))

cleaning_table_data = [
    [Paragraph('Kategori Pembersihan', style_table_header), Paragraph('Deskripsi Kondisi / Error Code', style_table_header), Paragraph('Jumlah Baris', style_table_header), Paragraph('Persentase', style_table_header), Paragraph('Tindakan Preprocessing', style_table_header)],
    [Paragraph('<b>Total Data Mentah</b>', style_table_cell_bold), Paragraph('Seluruh baris data pencatatan', style_table_cell), Paragraph('14.827.287', style_table_cell_center), Paragraph('100.0%', style_table_cell_center), Paragraph('Dibaca bertahap per 500 ribu baris', style_table_cell)],
    [Paragraph('ID Non-Stasiun', style_table_cell), Paragraph('Tag pengujian internal, bukan stasiun AWS sungguhan', style_table_cell), Paragraph('7', style_table_cell_center), Paragraph('&lt; 0.001%', style_table_cell_center), Paragraph('Dihapus permanen', style_table_cell)],
    [Paragraph('Waktu Rusak / Kosong', style_table_cell), Paragraph('Nilai waktu pencatatan kosong atau bukan angka', style_table_cell), Paragraph('1', style_table_cell_center), Paragraph('&lt; 0.001%', style_table_cell_center), Paragraph('Dihapus permanen', style_table_cell)],
    [Paragraph('Waktu Sebelum 2022', style_table_cell), Paragraph('Jam internal alat belum diatur saat pemasangan awal', style_table_cell), Paragraph('3.566', style_table_cell_center), Paragraph('0.024%', style_table_cell_center), Paragraph('Dihapus', style_table_cell)],
    [Paragraph('<b>Valid Interval Records</b>', style_table_cell_bold), Paragraph('Data interval operasional valid (2022-2026)', style_table_cell), Paragraph('<b>14.823.713</b>', style_table_cell_center), Paragraph('<b>99.976%</b>', style_table_cell_center), Paragraph('Diproses ke tahap QC Kewajaran Fisik', style_table_cell)],
    [Paragraph('Error Sensor Suhu', style_table_cell), Paragraph('Kode eror 3276.7°F / -90°F (kode biner 0x7FFF), atau T &lt; 0°C / &gt; 100°C', style_table_cell), Paragraph('150.080', style_table_cell_center), Paragraph('1.01%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Kelembapan', style_table_cell), Paragraph('Kode eror -1 (terputus) atau 255 (0xFF), atau RH &lt; 0% / &gt; 100%', style_table_cell), Paragraph('112.360', style_table_cell_center), Paragraph('0.76%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Tekanan Udara', style_table_cell), Paragraph('Tekanan &lt; 500 hPa atau &gt; 1200 hPa (di luar batas kewajaran fisik)', style_table_cell), Paragraph('117.649', style_table_cell_center), Paragraph('0.79%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Curah Hujan', style_table_cell), Paragraph('Hasil konversi &lt; 0 mm atau &gt; 1000 mm per interval', style_table_cell), Paragraph('29.767', style_table_cell_center), Paragraph('0.20%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Solar', style_table_cell), Paragraph('Kode eror 32767 W/m² (0x7FFF) atau &gt; 2000 W/m²', style_table_cell), Paragraph('125.808', style_table_cell_center), Paragraph('0.85%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Arah Angin', style_table_cell), Paragraph('Kode eror 32767° (0x7FFF) atau derajat &gt; 360°', style_table_cell), Paragraph('146.834', style_table_cell_center), Paragraph('0.99%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Error Sensor Kec. Angin', style_table_cell), Paragraph('Kode eror 255 (0xFF) atau kecepatan &gt; 100 km/h', style_table_cell), Paragraph('105.758', style_table_cell_center), Paragraph('0.71%', style_table_cell_center), Paragraph('Masking menjadi NaN', style_table_cell)],
    [Paragraph('Placeholder String (\'---\')', style_table_cell), Paragraph('Sensor tidak terpasang / saluran kosong', style_table_cell), Paragraph('2.088k – 2.409k', style_table_cell_center), Paragraph('14.0% – 16.2%', style_table_cell_center), Paragraph('Konversi otomatis ke NaN', style_table_cell)],
]

tbl_cleaning = Table(cleaning_table_data, colWidths=[100, 160, 65, 60, 130])
tbl_cleaning.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 5), (-1, 5), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_cleaning)

story.append(Spacer(1, 4))
story.append(Paragraph(
    '<b>Catatan Cara Membaca Kolom "Jumlah Baris":</b> Untuk baris <b>ID Non-Stasiun</b>, <b>Waktu Rusak/Kosong</b>, dan <b>Waktu Sebelum 2022</b>, angka menyatakan jumlah baris data yang dihapus permanen dari dataset. Untuk ketujuh baris <b>Error Sensor</b> (Suhu s.d. Kec. Angin), angka menyatakan jumlah <b>nilai per parameter</b> yang di-masking menjadi kosong (NaN) &ndash; bukan jumlah baris yang dihapus. Satu baris data yang sama masih bisa dipakai untuk parameter lain yang nilainya tetap valid; hanya kolom parameter yang errornya yang dikosongkan.',
    style_body
))

story.append(Spacer(1, 5))
fig1_img = os.path.join(figures_dir, 'fig1_cleaning_summary.png')
if os.path.exists(fig1_img):
    story.append(Image(fig1_img, width=17.5*cm, height=6.8*cm))
    story.append(Paragraph('<b>Gambar 1:</b> Diagram Alur Pembersihan Data Raw NusaKlim dan Frekuensi Error Sensor per Parameter (angka kanan identik dengan Tabel 2.1).', style_caption))

story.append(Paragraph('2.2 Alasan &amp; Rasional Ilmiah Pembersihan Kode Eror Sensor', style_h2))
story.append(Paragraph(
    '<b>Mengapa kode eror bawaan hardware harus diubah menjadi NaN (kosong) sebelum agregasi?</b> Pada stasiun cuaca digital berbasis mikroprosesor (seperti Davis Vantage Pro2), saat kabel sensor terputus, sensor mengalami korosi akibat kelembapan tinggi di kebun sawit, atau tegangan baterai solar drop, modul ADC mengirimkan nilai biner maksimum sebagai kode error bawaan (misal <code>0x7FFF = 32767</code> untuk nilai 16-bit bertanda, yang diterjemahkan menjadi <code>3276.7°F</code> untuk suhu, atau <code>0xFF = 255</code> untuk 8-bit). Nilai kode error ini dikosongkan (dijadikan <code>NaN</code>) &ndash; <b>bukan menghapus keseluruhan barisnya</b> &ndash; supaya tidak mencemari perhitungan rata-rata iklim, sesuai standar World Meteorological Organization (WMO No. 8).',
    style_body
))
story.append(Paragraph(
    '<b>Penanganan Nilai Eror &amp; Data Hilang pada Tahap Selanjutnya:</b><br/>'
    '&bull; <b>Prinsip dasar:</b> apabila suatu nilai tidak valid untuk parameter tertentu, nilai tersebut tidak diikutsertakan dalam perhitungan parameter itu (dikosongkan/NaN). Namun, apabila parameter lain pada baris (stasiun &amp; waktu) yang sama masih valid, baris tersebut tetap dipakai untuk perhitungan parameter lain yang valid itu &ndash; satu nilai eror pada satu parameter tidak menggugurkan seluruh baris.<br/>'
    '&bull; <b>Dampak pada rata-rata &amp; agregasi harian:</b> Rata-rata/penjumlahan harian pada Bab 3 dihitung hanya dari nilai interval yang valid (non-NaN) untuk parameter itu pada hari &amp; stasiun bersangkutan; nilai NaN diabaikan (bukan dianggap nol), sehingga tidak mengecilkan rata-rata secara keliru.<br/>'
    '&bull; <b>Status dalam data training model:</b> Nilai eror yang sudah dikosongkan (NaN) <b>tidak diikutsertakan</b> sebagai input pelatihan model &ndash; nilai NaN pada suatu parameter membuat baris tersebut di-skip khusus untuk parameter itu, dan tidak ada nilai eror mentah (mis. 3276.7&deg;F atau 32767) yang pernah masuk ke tahap pemodelan.<br/>'
    '&bull; <b>Baris dengan sebagian parameter kosong:</b> baris hari-stasiun yang salah satu parameternya kosong tetap disertakan dalam dataset harian 114.507 baris dan tetap dipakai untuk analisis/pemodelan parameter lain yang datanya lengkap; baris tersebut hanya dikeluarkan dari analisis/statistik yang secara khusus mensyaratkan kelengkapan seluruh 8 variabel sekaligus (lihat catatan N Valid 98.911 pada Bab 4.1).',
    style_body
))

story.append(PageBreak())

# SECTION 3
story.append(Paragraph('3. Prosedur Agregasi Harian &amp; Klasifikasi Arah Angin', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Data pengamatan berinterval 15-menit diagregasikan menjadi satu baris per stasiun per hari pengamatan lokal (Waktu Indonesia Barat). Agregasi harian ini menghasilkan dataset harian sebanyak <b>114.507 baris (kombinasi stasiun &amp; hari)</b> dari 183 stasiun aktif.',
    style_body
))

story.append(Paragraph('3.1 Formula Agregasi Harian', style_h2))

agg_rules_data = [
    [Paragraph('Variabel Cuaca', style_table_header), Paragraph('Satuan Raw', style_table_header), Paragraph('Satuan Target', style_table_header), Paragraph('Metode Agregasi', style_table_header), Paragraph('Formula Matematis &amp; Keterangan', style_table_header)],
    [Paragraph('<b>Curah Hujan (Rain)</b>', style_table_cell_bold), Paragraph('Tipping raw', style_table_cell), Paragraph('mm / hari', style_table_cell), Paragraph('<b>Penjumlahan (SUM)</b>', style_table_cell_bold), Paragraph('<code>R_harian = &Sigma; (rain15 * 12.70)</code><br/>Akumulasi presipitasi total dalam 24 jam.', style_table_cell)],
    [Paragraph('<b>Radiasi Solar</b>', style_table_cell_bold), Paragraph('W/m²', style_table_cell), Paragraph('W/m² (rata-rata harian)', style_table_cell), Paragraph('<b>Rata-rata (MEAN)</b>', style_table_cell_bold), Paragraph('<code>Solar_harian = rata-rata (solar_15min)</code><br/>Rata-rata radiasi matahari harian; bukan jumlah, agar tidak bergantung pada banyaknya pembacaan per hari.', style_table_cell)],
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
story.append(Paragraph('3.2 Logika Klasifikasi Arah Mata Angin', style_h2))

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
    story.append(Paragraph('<b>Gambar 2:</b> Proporsi Distribusi Arah Mata Angin dan Boxplot Kecepatan Angin per Kategori.', style_caption))

story.append(PageBreak())

# SECTION 4
story.append(Paragraph('4. Hasil Exploratory Data Analysis (EDA) Komprehensif', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Analisis eksploratif dilakukan terhadap data harian yang telah terstandarisasi untuk mengungkap pola alami atmosfer di perkebunan kelapa sawit, meliputi statistik deskriptif, bentuk distribusi, interkorelasi antar variabel cuaca, pola deret waktu musiman, serta siklus harian (24 jam).',
    style_body
))

story.append(Paragraph('4.1 Statistik Deskriptif Agregasi Harian (Data Lengkap: 98.911 Baris)', style_h2))

stats_table_data = [
    [Paragraph('Variabel Cuaca', style_table_header), Paragraph('N Valid', style_table_header), Paragraph('Mean &plusmn; Std', style_table_header), Paragraph('Min', style_table_header), Paragraph('Quartil 1<br/>(Q1 / P25)', style_table_header), Paragraph('Median<br/>(Q2 / P50)', style_table_header), Paragraph('Quartil 3<br/>(Q3 / P75)', style_table_header), Paragraph('P99', style_table_header), Paragraph('Max', style_table_header)],
    [Paragraph('<b>Suhu Rata-rata (°C)</b>', style_table_cell_bold), Paragraph('98.911', style_table_cell_center), Paragraph('26.86 &plusmn; 1.83', style_table_cell_center), Paragraph('12.28', style_table_cell_center), Paragraph('26.04', style_table_cell_center), Paragraph('26.95', style_table_cell_center), Paragraph('27.84', style_table_cell_center), Paragraph('31.33', style_table_cell_center), Paragraph('36.44', style_table_cell_center)],
    [Paragraph('<b>Kelembapan Avg (%)</b>', style_table_cell_bold), Paragraph('98.911', style_table_cell_center), Paragraph('85.45 &plusmn; 6.69', style_table_cell_center), Paragraph('1.17', style_table_cell_center), Paragraph('82.86', style_table_cell_center), Paragraph('86.32', style_table_cell_center), Paragraph('89.39', style_table_cell_center), Paragraph('96.40', style_table_cell_center), Paragraph('100.00', style_table_cell_center)],
    [Paragraph('<b>Tekanan Udara (hPa)</b>', style_table_cell_bold), Paragraph('98.911', style_table_cell_center), Paragraph('998.07 &plusmn; 21.60', style_table_cell_center), Paragraph('543.89', style_table_cell_center), Paragraph('999.51', style_table_cell_center), Paragraph('1004.35', style_table_cell_center), Paragraph('1007.11', style_table_cell_center), Paragraph('1013.08', style_table_cell_center), Paragraph('1020.29', style_table_cell_center)],
    [Paragraph('<b>Curah Hujan (mm/hari)</b>', style_table_cell_bold), Paragraph('98.911', style_table_cell_center), Paragraph('9.19 &plusmn; 32.56', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('0.10', style_table_cell_center), Paragraph('4.80', style_table_cell_center), Paragraph('185.43', style_table_cell_center), Paragraph('300.00', style_table_cell_center)],
    [Paragraph('<b>Radiasi Solar (W/m²)</b>', style_table_cell_bold), Paragraph('98.911', style_table_cell_center), Paragraph('173.7 &plusmn; 86.2', style_table_cell_center), Paragraph('0', style_table_cell_center), Paragraph('126.7', style_table_cell_center), Paragraph('166.1', style_table_cell_center), Paragraph('204.9', style_table_cell_center), Paragraph('498.9', style_table_cell_center), Paragraph('1141.3', style_table_cell_center)],
    [Paragraph('<b>Kecepatan Angin (km/h)</b>', style_table_cell_bold), Paragraph('98.911', style_table_cell_center), Paragraph('0.82 &plusmn; 0.94', style_table_cell_center), Paragraph('0.00', style_table_cell_center), Paragraph('0.39', style_table_cell_center), Paragraph('0.68', style_table_cell_center), Paragraph('1.03', style_table_cell_center), Paragraph('3.47', style_table_cell_center), Paragraph('45.77', style_table_cell_center)],
]

tbl_stats = Table(stats_table_data, colWidths=[96, 40, 70, 36, 48, 48, 48, 36, 38])
tbl_stats.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_stats)

story.append(Spacer(1, 3))
story.append(Paragraph(
    '<b>Standardisasi N Valid &amp; Interpretasi Rentang Interkuartil (IQR):</b><br/>'
    '&bull; <b>Mengapa N Valid (98.911) Lebih Kecil dari 114.507 Baris:</b> Statistik pada tabel ini hanya dihitung dari baris yang <b>lengkap</b>, yaitu hari-stasiun di mana seluruh 8 variabel cuaca (suhu, kelembapan, tekanan, curah hujan, radiasi solar, kecepatan angin, dsb.) tercatat valid secara bersamaan pada hari yang sama. Selisih 15.596 baris (13,6%) disebabkan oleh data yang hilang pada salah satu sensor akibat gangguan hardware, koneksi terputus, atau perawatan stasiun, sehingga baris tersebut tidak bisa dipakai untuk perbandingan antar-variabel yang konsisten.<br/>'
    '&bull; <b>Suhu Rata-rata:</b> 50% data observasi tengah berada pada rentang stabil 26.04&deg;C (Q1) hingga 27.84&deg;C (Q3) dengan IQR hanya 1.80&deg;C, mencerminkan kestabilan suhu harian yang khas iklim tropis dataran rendah/menengah perkebunan kelapa sawit.<br/>'
    '&bull; <b>Kelembapan Udara:</b> Q1 bernilai 82.86% dan Q3 mencapai 89.39% (IQR 6.53%), membuktikan lingkungan perkebunan hampir selalu berada pada kelembapan tinggi.<br/>'
    '&bull; <b>Curah Hujan Harian:</b> Curah hujan memiliki distribusi yang tidak merata. Sebagian besar periode pengamatan nyaris tidak mengalami hujan (median hanya 0,1 mm), sementara beberapa kejadian hujan dengan intensitas lebih tinggi menyebabkan nilai rerata mencapai 9,19 mm &ndash; jauh di atas median. Kesenjangan yang sama terlihat antara Q3 (4.80 mm), P99 (185.43 mm), dan maksimum (300.00 mm): lonjakan drastis dari P99 ke Max mengindikasikan adanya sejumlah kecil hari dengan hujan sangat ekstrem (badai tropis yang datang tiba-tiba), bukan kesalahan pencatatan, karena nilai tersebut masih berada dalam ambang fisik wajar (&le; 300 mm/hari) setelah filter anomali <i>rollover pulse</i>.<br/>'
    '&bull; <b>Kecepatan Angin:</b> Q1 sebesar 0.39 km/h dan Q3 sebesar 1.03 km/h (Median 0.68 km/h) menandakan sirkulasi udara kanopi harian tergolong sangat tenang (<i>calm</i>). Namun nilai maksimum mencapai 45.77 km/h &ndash; lebih dari 13x lipat dari P99 (3.47 km/h) &ndash; mengindikasikan keberadaan sejumlah kecil kejadian hembusan angin kencang (<i>gust</i>) berdurasi pendek, umumnya bersamaan dengan sistem badai lokal, dan berbeda karakter dari kondisi angin kanopi sawit sehari-hari yang didominasi udara tenang.<br/>'
    '&bull; <b>Tekanan Udara:</b> Bagian tengah sebaran (IQR) tetap sangat sempit (Q1 999.51 hPa hingga Q3 1007.11 hPa, IQR hanya 7.60 hPa) dengan median 1004.35 hPa, mencerminkan kondisi tekanan permukaan yang stabil khas wilayah dataran rendah tropis ekuatorial. Namun nilai minimum tercatat 543.89 hPa &ndash; jauh di luar IQR &ndash; menandakan segelintir pembacaan ekstrem yang masih lolos batas kewajaran fisik (500-1200 hPa) dan perlu diverifikasi lebih lanjut ke perangkat keras di lapangan.<br/>'
    '&bull; <b>Radiasi Solar:</b> Dihitung sebagai <b>rata-rata harian</b> dari seluruh pembacaan sensor (siang dan malam). Bagian tengah sebaran (IQR) berada pada Q1 126,7 hingga Q3 204,9 W/m&sup2; dengan median 166,1 W/m&sup2;, mencerminkan variasi tutupan awan harian &ndash; dari hari cerah hingga hari berawan/hujan. Nilai P99 (498,9 W/m&sup2;) dan maksimum (1.141,3 W/m&sup2;) berada <b>di atas batas fisik rata-rata harian</b> di ekuator (sekitar 430 W/m&sup2; di puncak atmosfer), sehingga diduga berasal dari sensor yang tidak terkalibrasi atau macet pada sebagian stasiun (sekitar 1,6% hari-stasiun bernilai &gt;450 W/m&sup2;, terbanyak pada stasiun 252, 2105, dan 2176). Nilai ini ditandai sebagai kandidat pemeriksaan lapangan dan belum dihapus otomatis karena masih lolos filter kewajaran per-pembacaan (0&ndash;2.000 W/m&sup2;).',
    style_body
))

story.append(Spacer(1, 4))
fig2_img = os.path.join(figures_dir, 'fig2_distributions.png')
if os.path.exists(fig2_img):
    story.append(Image(fig2_img, width=16.8*cm, height=7.2*cm))
    story.append(Paragraph('<b>Gambar 3:</b> Histogram dan Kernel Density Estimation (KDE) Distribusi Parameter Cuaca Harian NusaKlim.', style_caption))

story.append(PageBreak())

# SECTION 5
story.append(Paragraph('5. Analisis Korelasi Multivariat &amp; Dinamika Waktu', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Analisis keterkaitan antar variabel cuaca sangat penting untuk menentukan pemilihan variabel cuaca yang akan diikutsertakan sebagai input pada model prediksi 7 hari ke depan (suhu, kelembapan, tekanan, curah hujan, dan radiasi solar).',
    style_body
))

fig3_img = os.path.join(figures_dir, 'fig3_correlation.png')
if os.path.exists(fig3_img):
    story.append(Image(fig3_img, width=13.0*cm, height=9.6*cm))
    story.append(Paragraph('<b>Gambar 4:</b> Matriks Korelasi Pearson Antar Parameter Cuaca Harian AWS NusaKlim.', style_caption))

story.append(Paragraph('5.1 Wawasan Kunci Dinamika Atmosferik', style_h2))

story.append(Paragraph(
    '<b>Kategori Kekuatan Korelasi yang Digunakan:</b> Seluruh interpretasi nilai koefisien korelasi Pearson (r) pada bab ini mengacu secara konsisten pada skala interpretasi Sugiyono (2007) berikut, berdasarkan nilai mutlak |r|:',
    style_body
))

corr_scale_data = [
    [Paragraph('Rentang |r|', style_table_header), Paragraph('0,00 &ndash; 0,199', style_table_header), Paragraph('0,20 &ndash; 0,399', style_table_header), Paragraph('0,40 &ndash; 0,599', style_table_header), Paragraph('0,60 &ndash; 0,799', style_table_header), Paragraph('0,80 &ndash; 1,00', style_table_header)],
    [Paragraph('Kategori', style_table_cell_bold), Paragraph('Sangat Lemah', style_table_cell_center), Paragraph('Lemah', style_table_cell_center), Paragraph('Sedang', style_table_cell_center), Paragraph('Kuat', style_table_cell_center), Paragraph('Sangat Kuat', style_table_cell_center)],
]
tbl_corr_scale = Table(corr_scale_data, colWidths=[75, 88, 88, 88, 88, 88])
tbl_corr_scale.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 1), (0, 1), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(Spacer(1, 3))
story.append(tbl_corr_scale)
story.append(Spacer(1, 5))

story.append(Paragraph(
    '&bull; <b>Hubungan Suhu vs Kelembapan (r = -0.38, Lemah&ndash;Sedang):</b> Suhu rata-rata dan kelembapan relatif menunjukkan korelasi negatif <b>lemah</b> (bukan sangat kuat). Arah hubungan tetap konsisten dengan fisika atmosfer &ndash; saat suhu naik, kapasitas udara menampung uap air jenuh meningkat sehingga RH cenderung turun &ndash; namun kekuatannya lemah karena basis harian merata-ratakan variasi siang-malam, dan faktor lain (tutupan awan, curah hujan, angin) turut memengaruhi kelembapan secara independen dari suhu semata. Hubungan paling menonjol pada matriks korelasi (Gambar 4) justru muncul antara <b>Tekanan Udara dan Suhu Rata-rata (r = +0.52, Sedang)</b>.<br/>'
    '&bull; <b>Hubungan Radiasi Solar vs Suhu &amp; Kelembapan:</b> Radiasi solar berkorelasi positif dengan suhu rata-rata (r = +0.55, kategori <b>sedang</b>) dan negatif dengan kelembapan (r = -0.48, kategori <b>sedang</b>). Arahnya sesuai dugaan ilmiah (radiasi matahari memanaskan permukaan dan menurunkan kelembapan); kekuatannya hanya sedang (bukan kuat) karena radiasi solar harian sangat dipengaruhi tutupan awan sepanjang hari, sementara suhu rata-rata/kelembapan mencerminkan kondisi 24 jam penuh termasuk malam hari saat radiasi bernilai nol.<br/>'
    '&bull; <b>Korelasi terhadap Curah Hujan:</b> Curah hujan menunjukkan korelasi <b>sangat lemah</b> terhadap sebagian besar variabel cuaca lain pada basis harian (suhu rata-rata r = -0.14, kelembapan r = -0.15, tekanan r = -0.14, radiasi solar r = +0.03), kecuali kecepatan angin yang menunjukkan korelasi <b>sedang</b> (r = +0.46) &ndash; hari-hari berangin lebih kencang cenderung juga lebih banyak hujan, konsisten dengan pola badai tropis yang membawa angin kencang bersamaan dengan hujan lebat. Lemahnya keterkaitan pada variabel lain wajar secara alami karena hujan adalah kejadian yang muncul tiba-tiba (khas tropis), bukan proses yang berubah bertahap seperti suhu atau tekanan. <b>Implikasi bagi desain model:</b> lemahnya keterkaitan antar-variabel pada hari yang sama ini menegaskan bahwa hanya mengandalkan riwayat curah hujan itu sendiri tidak cukup untuk meramal hujan secara akurat. Sinyal yang lebih relevan justru berasal dari pola perubahan beberapa hari sebelumnya pada berbagai variabel sekaligus (mis. riwayat/lag kelembapan 1&ndash;3 hari terakhir, penurunan tekanan &Delta;P = P(t-1) &minus; P(t-2)) &ndash; sehingga model yang mempelajari fitur riwayat dari banyak variabel sekaligus, seperti yang dipakai pada Model Prediksi Cuaca 7 Hari (lihat Bab 2 Laporan Model Prediksi Cuaca 7 Hari), lebih tepat dibandingkan model sederhana yang hanya melihat satu variabel pada satu titik waktu.',
    style_body
))

story.append(Spacer(1, 4))
fig7_img = os.path.join(figures_dir, 'fig7_diurnal_cycle.png')
if os.path.exists(fig7_img):
    story.append(Image(fig7_img, width=15.5*cm, height=13.29*cm))
    story.append(Paragraph('<b>Gambar 5:</b> Profil Siklus Harian (24 Jam, Waktu Indonesia Barat) Suhu, Radiasi Solar, Kelembapan, Tekanan Udara, Curah Hujan, dan Kecepatan Angin.', style_caption))

story.append(Paragraph('5.2 Penjelasan Siklus Harian (24 Jam)', style_h2))
story.append(Paragraph(
    'Rata-rata seluruh stasiun per jam (Waktu Indonesia Barat) pada Gambar 5 menunjukkan pola harian yang konsisten dan saling terkait secara ilmiah:<br/>'
    '&bull; <b>Suhu Udara:</b> Mencapai titik terendah &plusmn;23,6&deg;C sekitar pukul 05.00&ndash;06.00 (sesaat sebelum matahari terbit, saat pelepasan panas radiatif malam hari mencapai puncaknya), kemudian naik tajam begitu radiasi matahari masuk dan mencapai puncak &plusmn;31,0&deg;C pada pukul 13.00, sebelum menurun bertahap sepanjang sore hingga tengah malam.<br/>'
    '&bull; <b>Radiasi Solar:</b> Bernilai nol sepanjang malam (pukul 18.00&ndash;06.00), naik seiring matahari terbit, dan memuncak &plusmn;560&ndash;570 W/m&sup2; pada pukul 11.00&ndash;12.00 &ndash; menjadi penyebab utama kenaikan suhu dan penurunan kelembapan pada siang hari.<br/>'
    '&bull; <b>Kelembapan Relatif:</b> Bergerak <b>berlawanan arah (antifase)</b> dengan suhu &ndash; memuncak &plusmn;93,7% menjelang pagi hari saat suhu terendah, lalu turun tajam ke titik terendah &plusmn;74,5% pada pukul 13.00&ndash;14.00 bersamaan dengan puncak suhu &amp; radiasi solar, sesuai sifat alami udara bahwa udara hangat menampung uap air relatif lebih banyak sehingga RH menurun meski kadar uap air absolut relatif stabil.<br/>'
    '&bull; <b>Tekanan Atmosfer:</b> Memperlihatkan pola <b>osilasi semi-diurnal (dua puncak &amp; dua lembah per hari)</b> yang khas wilayah tropis &ndash; puncak pertama &plusmn;1002,0 hPa sekitar pukul 09.00, lembah pertama &plusmn;999,6 hPa sekitar pukul 03.00, lembah kedua (terdalam) &plusmn;998,1 hPa sekitar pukul 15.00&ndash;16.00, dan puncak kedua &plusmn;1001,5 hPa sekitar pukul 21.00&ndash;22.00. Pola dua-siklus ini terjadi akibat pemanasan dan pemuaian lapisan atmosfer oleh radiasi matahari, dan lazim diamati pada wilayah ekuatorial.<br/>'
    '&bull; <b>Curah Hujan:</b> Intensitas rata-rata per interval bacaan relatif rendah dan stabil sepanjang pagi hingga tengah hari (pukul 05.00&ndash;11.00), kemudian meningkat bertahap pada siang-sore dan mencapai puncak &plusmn;pukul 18.00 sesaat setelah puncak suhu &amp; radiasi solar mereda &ndash; pola khas hujan tropis sore-malam yang terbentuk dari pemanasan permukaan siang hari yang mendorong udara lembap naik ke atas hingga terkondensasi menjadi hujan.<br/>'
    '&bull; <b>Kecepatan Angin:</b> Bergerak <b>searah (in-phase)</b> dengan suhu &amp; radiasi solar &ndash; terendah &plusmn;0,4 km/h pada malam-dini hari, meningkat seiring pemanasan permukaan, dan memuncak &plusmn;1,65&ndash;1,67 km/h pada pukul 12.00&ndash;14.00. Pola ini konsisten dengan meningkatnya sirkulasi udara di permukaan kanopi akibat pemanasan siang hari.<br/>'
    'Pola harian ini penting bagi model prediksi 7-hari karena menjadi bagian dari perhitungan pola musiman, dan membantu memastikan bahwa sensor AWS merekam perubahan cuaca kanopi sawit secara konsisten, bukan sekadar gangguan sinyal acak.',
    style_body
))

story.append(PageBreak())

# SECTION 6
story.append(Paragraph('6. Analisis Deret Waktu, Musiman, dan Ekstrem Presipitasi', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    '<b>Sumber Data:</b> Dataset harian bersih (114.507 baris, 183 stasiun AWS, periode Januari 2022 hingga Agustus 2026).',
    style_body
))

fig4_img = os.path.join(figures_dir, 'fig4_timeseries_trend.png')
if os.path.exists(fig4_img):
    story.append(Image(fig4_img, width=17.5*cm, height=9.8*cm))
    story.append(Paragraph('<b>Gambar 6:</b> Tren Rangkaian Waktu Cuaca Harian Nasional Periode 2022 – 2026 (Moving Average 7 Hari).', style_caption))

story.append(PageBreak())
fig4b_img = os.path.join(figures_dir, 'fig4b_timeseries_trend_extra.png')
if os.path.exists(fig4b_img):
    story.append(Image(fig4b_img, width=17.5*cm, height=9.6*cm))
    story.append(Paragraph(
        '<b>Gambar 7:</b> Tren Rangkaian Waktu Parameter Tambahan (Tekanan Udara, Radiasi Solar, Kecepatan Angin, dan Arah Angin) Nasional Periode 2022 – 2026 (Moving Average 7 Hari). '
        'Rata-rata dan Moving Average Arah Angin dihitung secara sirkular (melalui komponen vektor sin/cos), bukan rata-rata aritmetik biasa, karena arah angin adalah data sudut (0&ndash;360&deg;) yang melingkar di titik 360&deg;/0&deg;.',
        style_caption
    ))

story.append(PageBreak())
story.append(Paragraph('6.1 Dekomposisi Time Series Bulanan per Parameter Cuaca (Observed, Trend, Seasonal, Residual)', style_h2))
story.append(Paragraph(
    'Untuk memperjelas pola tren jangka panjang dan pola musiman tahunan pada tiap parameter cuaca, rata-rata nasional harian tiap parameter diagregasi menjadi rata-rata bulanan, kemudian didekomposisi menggunakan model aditif (<code>Observed = Trend + Seasonal + Residual</code>). Periode Januari&ndash;Agustus 2022 dan Januari&ndash;Maret 2023 dikeluarkan dari analisis ini karena jaringan AWS baru beroperasi dengan 1&ndash;18 stasiun pada rentang tersebut (dibandingkan 183 stasiun penuh saat ini), sehingga rata-rata nasionalnya belum representatif. Dekomposisi dihitung dari Mei 2023 hingga Agustus 2026 (40 bulan).<br/>'
    '&bull; <b>Komponen Observed:</b> representasi rata-rata nasional aktual parameter tersebut per bulan.<br/>'
    '&bull; <b>Komponen Trend:</b> menggambarkan arah pergerakan jangka panjang setelah pengaruh musiman dihilangkan.<br/>'
    '&bull; <b>Komponen Seasonal:</b> pola musiman berulang setiap 12 bulan (siklus tahunan).<br/>'
    '&bull; <b>Komponen Residual:</b> sisa fluktuasi acak setelah tren dan musiman dikeluarkan, idealnya tersebar di sekitar garis nol.',
    style_body
))

decomp_figs = [
    ('suhu', 'Suhu Rata-rata', '°C', '27,06 → 26,80°C (turun tipis 1,0%, relatif stabil)',
     'puncak bulan Mei, terendah bulan Januari, amplitudo ±1,19°C', '±0,21°C di sekitar nol'),
    ('kelembapan', 'Kelembapan Rata-rata', '%', '85,45% → 83,81% (turun 1,9%)',
     'puncak bulan Januari, terendah bulan Juli, amplitudo ±3,96%', '±1,06% di sekitar nol'),
    ('tekanan', 'Tekanan Udara Rata-rata', 'hPa', '1.004,03 → 995,69 hPa (turun 0,8%)',
     'puncak bulan Februari, terendah bulan Agustus, amplitudo ±2,59 hPa', '±1,25 hPa di sekitar nol'),
    ('hujan', 'Curah Hujan Rata-rata', 'mm/hari', '4,28 → 11,04 mm/hari (naik, mengikuti pertumbuhan cakupan &amp; distribusi stasiun baru)',
     'puncak bulan November, terendah bulan Juli, amplitudo ±4,99 mm', '±1,90 mm di sekitar nol'),
    ('radiasi', 'Radiasi Solar Rata-rata', 'W/m²', '161,7 → 191,3 W/m² (naik 18,3%)',
     'puncak bulan September, terendah bulan Januari, amplitudo ±32,2 W/m²', '±7,9 W/m² di sekitar nol'),
    ('angin', 'Kecepatan Angin Rata-rata', 'km/jam', '0,83 → 0,97 km/jam (naik 16,1%)',
     'puncak bulan Agustus, terendah bulan Mei, amplitudo ±0,15 km/jam', '±0,06 km/jam di sekitar nol'),
]
gambar_no = 8
for slug, title, unit, trend_txt, seasonal_txt, resid_txt in decomp_figs:
    fimg = os.path.join(figures_dir, f'fig9_decomp_{slug}.png')
    if os.path.exists(fimg):
        story.append(Image(fimg, width=15.5*cm, height=12.7*cm))
        story.append(Paragraph(f'<b>Gambar {gambar_no}:</b> Dekomposisi Time Series Bulanan {title} ({unit}), Mei 2023 &ndash; Agustus 2026 (Observed, Trend, Seasonal, Residual).', style_caption))
        story.append(Paragraph(
            '&bull; <b>Makna Komponen Grafik:</b><br/>'
            f'1. <b>Component Observed:</b> representasi nilai rata-rata nasional aktual {title.lower()} per bulan.<br/>'
            f'2. <b>Component Trend:</b> arah pergerakan jangka panjang: {trend_txt}.<br/>'
            f'3. <b>Component Seasonal:</b> pola musiman tahunan berulang (siklus 12 bulan) dengan {seasonal_txt}.<br/>'
            f'4. <b>Component Residual:</b> komponen sisa acak terdistribusi {resid_txt}, tanpa pola sistematis yang tersisa.',
            style_body
        ))
        story.append(Spacer(1, 4))
        gambar_no += 1

story.append(PageBreak())
story.append(Paragraph('6.2 Klasifikasi Intensitas Curah Hujan Harian Standar BMKG', style_h2))

fig6_img = os.path.join(figures_dir, 'fig6_rainfall_classification.png')
if os.path.exists(fig6_img):
    story.append(Image(fig6_img, width=17.5*cm, height=6.5*cm))
    story.append(Paragraph(f'<b>Gambar {gambar_no}:</b> Klasifikasi Frekuensi Curah Hujan Standar BMKG dan 10 Stasiun AWS dengan Akumulasi Hujan Tertinggi (setelah mengeluarkan stasiun dengan indikasi gangguan sensor).', style_caption))

story.append(Paragraph(
    'Dari total 101.224 hari pengamatan curah hujan yang valid, mengacu pada standar klasifikasi intensitas curah hujan harian Badan Meteorologi, Klimatologi, dan Geofisika (BMKG):<br/>'
    '&bull; <b>Tidak Hujan (0,0 mm):</b> 51.280 hari (50,66%) &ndash; hari kering ideal untuk pemanenan dan transportasi TBS.<br/>'
    '&bull; <b>Hujan Ringan (0,1 &ndash; 20,0 mm):</b> 39.081 hari (38,61%) &ndash; intensitas optimal yang terserap oleh perakaran sawit.<br/>'
    '&bull; <b>Hujan Sedang (20,0 &ndash; 50,0 mm):</b> 6.934 hari (6,85%) &ndash; kelembapan tanah mencukupi, memerlukan pemantauan drainase.<br/>'
    '&bull; <b>Hujan Lebat (50,0 &ndash; 100,0 mm):</b> 2.349 hari (2,32%) &ndash; potensi aliran permukaan tinggi.<br/>'
    '&bull; <b>Hujan Sangat Lebat (100,0 &ndash; 150,0 mm):</b> 424 hari (0,42%) &ndash; berisiko genangan pada lahan berdrainase buruk.<br/>'
    '&bull; <b>Hujan Ekstrem (&gt; 150,0 mm):</b> 1.156 hari (1,14%) &ndash; kejadian cuaca ekstrem yang memerlukan kewaspadaan.<br/>'
    f'Dua stasiun (2134 dan 2140) tercatat mencapai batas maksimum akumulasi harian (300 mm) pada 48% dan 65% dari seluruh hari pengamatannya &ndash; porsi yang tidak wajar tinggi, sehingga pola ini lebih mencerminkan kemungkinan gangguan pada alat ukur hujan di lapangan dibanding curah hujan sungguhan. Kedua stasiun tersebut dikeluarkan dari peringkat "akumulasi hujan tertinggi" pada Gambar {gambar_no} dan ditandai sebagai kandidat pemeriksaan lapangan lebih lanjut.',
    style_body
))
gambar_no += 1

story.append(PageBreak())

# SECTION 7
story.append(Paragraph('7. Evaluasi Kesiapan Data &amp; Desain Model Prediksi 7-Hari', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Target utama dari persiapan data ini adalah pengembangan model ramalan cuaca hingga 7 hari ke depan serta pembandingan dengan layanan cuaca eksternal Open-Meteo.',
    style_body
))

fig8_img = os.path.join(figures_dir, 'fig8_station_longevity.png')
if os.path.exists(fig8_img):
    story.append(Image(fig8_img, width=15.0*cm, height=6.2*cm))
    story.append(Paragraph(f'<b>Gambar {gambar_no}:</b> Distribusi Durasi Pengamatan per Stasiun AWS (Total 183 Stasiun Operasional).', style_caption))

story.append(Paragraph('7.1 Rekomendasi Arsitektur Pemodelan Prediksi Cuaca 7 Hari', style_h2))

model_matrix = [
    [Paragraph('Pendekatan Model', style_table_header), Paragraph('Cara Kerja', style_table_header), Paragraph('Kelebihan', style_table_header), Paragraph('Kelemahan', style_table_header)],
    [Paragraph('<b>Model 1: Riwayat Variabel Itu Sendiri</b>', style_table_cell_bold), Paragraph('Model klasik peramalan deret waktu (misal ARIMA atau Prophet) yang hanya memakai riwayat data satu variabel itu sendiri (contoh: riwayat hujan 30 hari terakhir untuk meramal hujan 7 hari ke depan), tanpa memperhitungkan variabel cuaca lain.', style_table_cell), Paragraph('&bull; Komputasi sangat ringan.<br/>&bull; Mudah dijalankan untuk 183 stasiun secara independen.', style_table_cell), Paragraph('&bull; Kurang mampu menangkap badai yang datang tiba-tiba.<br/>&bull; Akurasi menurun tajam di atas horizon H+3.', style_table_cell)],
    [Paragraph('<b>Model 2: Gabungan Banyak Variabel (Dipilih untuk Produksi)</b>', style_table_cell_bold), Paragraph('XGBoost / LightGBM / CatBoost dengan fitur riwayat dari banyak variabel sekaligus (Suhu, Kelembapan, Tekanan, Radiasi Solar, Arah Angin, Siklus Musiman).', style_table_cell), Paragraph('&bull; Sangat tangguh untuk data tabel.<br/>&bull; Menangkap hubungan antar variabel yang tidak linear.<br/>&bull; Hasil mudah dijelaskan lewat Feature Importance.', style_table_cell), Paragraph('&bull; Perlu strategi khusus untuk meramal 7 hari sekaligus.<br/>&bull; Rentan jika salah satu sensor input hilang datanya.', style_table_cell)],
    [Paragraph('<b>Model 3: Deep Learning Sekuensial Lanjutan</b>', style_table_cell_bold), Paragraph('Arsitektur neural network modern (mis. Transformer) yang dirancang untuk peramalan deret waktu banyak lokasi sekaligus.', style_table_cell), Paragraph('&bull; Bisa memberi perkiraan rentang (bukan cuma satu angka pasti).<br/>&bull; Berpotensi paling akurat secara teori untuk horizon 7 hari.', style_table_cell), Paragraph('&bull; Memerlukan komputasi berat (GPU).<br/>&bull; Lebih rumit untuk dijalankan di server produksi.', style_table_cell)],
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
    '&bull; <b>Variabel Angka (Suhu, Kelembapan, Tekanan, Curah Hujan, Radiasi Solar, Kecepatan Angin):</b> diukur dengan rata-rata selisih error (MAE), akar rata-rata error kuadrat (RMSE), dan seberapa besar variasi data yang berhasil dijelaskan model (R&sup2;) &ndash; metrik yang sama seperti dipakai pada Laporan Model Prediksi Cuaca 7 Hari (termasuk perbandingan dengan Deep Learning, Bab 3.4).<br/>'
    '&bull; <b>Arah Mata Angin (Kategori):</b> diukur dengan Accuracy (persentase tebakan benar) dan F1-Score.<br/>'
    '&bull; <b>Benchmarking Open-Meteo:</b> Model internal dibandingkan langsung berdampingan dengan data peramalan API Open-Meteo pada stasiun uji, memakai periode data uji riil 30 hari yang sama dengan model produksi (21 Juli &ndash; 19 Agustus 2026; hasil lengkap 4 stasiun riil lihat <i>Laporan Komparasi NusaKlim vs Open-Meteo PPKS</i>). Jika model internal lebih stabil, model internal menjadi sumber utama; jika selisihnya tipis, sistem web NusaKlim akan menyajikan kedua sumber sekaligus sebagai pembanding.',
    style_body
))

story.append(Paragraph('7.3 Strategi Tampilan Dashboard &amp; Website', style_h2))
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
    'Proses pembersihan dan analisis data terhadap 14,8 juta baris data cuaca AWS telah selesai. Data cuaca yang telah dibersihkan kini siap digunakan untuk pengembangan model prediksi dan integrasi visualisasi website.',
    style_body
))

artifact_data = [
    [Paragraph('Hasil', style_table_header), Paragraph('Bentuk', style_table_header), Paragraph('Deskripsi &amp; Kegunaan', style_table_header)],
    [Paragraph('<b>Dataset Harian Bersih</b>', style_table_cell_bold), Paragraph('Tabel data (10,1 MB / 114.507 baris)', style_table_cell_center), Paragraph('Dataset harian bersih terstandarisasi (183 stasiun, 2022-2026) lengkap dengan konversi satuan metrik (°C, hPa, mm), nilai Min/Max, dan kategori arah mata angin. Siap untuk melatih model prediksi 7 hari.', style_table_cell)],
    [Paragraph('<b>Kumpulan Grafik Analitis</b>', style_table_cell_bold), Paragraph('14 gambar resolusi tinggi', style_table_cell_center), Paragraph('Koleksi lengkap 14 grafik analitis: alur pembersihan data, distribusi variabel, keterkaitan antar variabel, tren deret waktu, dekomposisi bulanan 6 parameter cuaca, analisis angin, klasifikasi curah hujan BMKG, siklus harian, dan kelengkapan data stasiun.', style_table_cell)],
    [Paragraph('<b>Dokumen Laporan Ini</b>', style_table_cell_bold), Paragraph('Dokumen PDF', style_table_cell_center), Paragraph('Dokumentasi teknis lengkap untuk arsip PPKS dan panduan tim riset/pengembangan.', style_table_cell)],
    [Paragraph('<b>Kode Pemrosesan Data</b>', style_table_cell_bold), Paragraph('Program otomatis', style_table_cell_center), Paragraph('Program pemrosesan data yang efisien dan dapat dijalankan otomatis secara berkala.', style_table_cell)],
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
    [Paragraph('<b>Disiapkan Oleh:</b><br/><br/><br/><u><b>Yudha</b></u><br/>Data Analyst NusaKlim PPKS', style_table_cell),
     Paragraph('<b>Diverifikasi Oleh:</b><br/><br/><br/><u><b>Cut Mardiana</b></u><br/>Asisten TI', style_table_cell),
     Paragraph('<b>Disetujui Oleh:</b><br/><br/><br/><u><b>Iput Pradiko</b></u><br/>Peneliti NusaKlim', style_table_cell)]
]
tbl_sig = Table(sig_data, colWidths=[172, 172, 171])
tbl_sig.setStyle(TableStyle([
    ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 7),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_sig)

doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
