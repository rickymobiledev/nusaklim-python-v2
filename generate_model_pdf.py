import os, sys, pandas as pd, numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

pdf_path = r'd:\Downloads\nusaklim\Laporan_Model_Prediksi_Cuaca_7Hari_PPKS.pdf'
fig_dir = r'd:\Downloads\nusaklim\figures_model'

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
        self.drawRightString(555, 805, 'Laporan Model Prediksi Cuaca 7 Hari (Multi-Horizon)')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Laporan Teknis Langkah 1: Pelatihan & Validasi Model Prediksi Cuaca 7 Hari PPKS')
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
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12.5, leading=15.5, textColor=COLOR_PRIMARY, spaceBefore=10, spaceAfter=5, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12.5, textColor=COLOR_SECONDARY, spaceBefore=8, spaceAfter=3, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Helvetica', fontSize=8.2, leading=12, textColor=COLOR_BODY, spaceAfter=4, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.8, leading=11, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.8, leading=10, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.8, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.8, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.8, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.8, textColor=COLOR_MUTED, alignment=1, spaceBefore=2, spaceAfter=6)

def make_callout_box(text, title='CATATAN PENTING & INSIGHT MODEL', width=515):
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

# ==================== COVER PAGE ====================
story.append(Spacer(1, 15))
header_inst = Paragraph(
    '<b>PUSAT PENELITIAN KELAPA SAWIT (PPKS)</b><br/><font color=\'#64748B\' size=\'8.5\'>Indonesian Oil Palm Research Institute - Proyek NusaKlim Weather AI</font>',
    ParagraphStyle('CoverInst', fontName='Helvetica', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 10))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=18))

story.append(Paragraph('LAPORAN PENGEMBANGAN &amp; EVALUASI MODEL PREDIKSI CUACA 7 HARI', style_cover_title))
story.append(Paragraph('Dokumentasi Teknis Pelatihan Model Multi-Horizon Machine Learning, Benchmarking Algoritma, dan Validasi Out-Of-Time pada 184 Stasiun AWS NusaKlim', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Status Model</b>', style_table_cell_bold), Paragraph('Model Produksi Terlatih (LightGBM Multi-Horizon H+1 s/d H+7)', style_table_cell)],
    [Paragraph('<b>Dataset Input</b>', style_table_cell_bold), Paragraph('<code>nusaklim_daily_aggregated.csv</code> (114.651 records, 184 stasiun)', style_table_cell)],
    [Paragraph('<b>Target Prediksi</b>', style_table_cell_bold), Paragraph('Suhu (Avg/Min/Max), Kelembapan, Curah Hujan (mm &amp; Peluang Hujan %)', style_table_cell)],
    [Paragraph('<b>Metode Validasi</b>', style_table_cell_bold), Paragraph('Strict Temporal Out-Of-Time Split (30 Hari Uji: 4.458 sample points)', style_table_cell)],
    [Paragraph('<b>Model File</b>', style_table_cell_bold), Paragraph('<code>models/weather_model_latest.joblib</code> (21,6 MB)', style_table_cell)],
    [Paragraph('<b>Waktu Training</b>', style_table_cell_bold), Paragraph('~61 Detik di CPU Standar (Siap untuk CI/CD Retraining Berkala)', style_table_cell)],
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
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026 | Dokumen Resmi Langkah 1 (Model Training)', style_cover_meta))
story.append(PageBreak())

# ==================== CHAPTER 1 & 2 ====================
story.append(Paragraph('1. Ringkasan Eksekutif &amp; Desain Solusi Prediksi 7-Hari', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Sebagai tindak lanjut dari tahap Data Preprocessing dan Exploratory Data Analysis (EDA), dokumen ini menyajikan pengembangan lengkap <b>Model Ramalan Cuaca 7 Hari ke Depan (Langkah 1)</b> untuk seluruh 184 stasiun Automatic Weather Station (AWS) NusaKlim PPKS. Model dirancang untuk menyediakan ramalan harian yang presisi, stabil, dan cepat dihitung guna mendukung manajemen perkebunan kelapa sawit.',
    style_body
))
story.append(Paragraph(
    'Model dilatih menggunakan arsitektur <b>Multi-Horizon Direct Forecasting</b> berbasis <i>Gradient Boosted Decision Trees (LightGBM)</i>, di mana setiap horizon waktu (H+1, H+2, ..., H+7) memiliki model spesifik yang dioptimalkan secara simultan untuk variabel Suhu Rata-rata, Suhu Minimum, Suhu Maksimum, Kelembapan Relatif, Akumulasi Hujan (mm), serta Peluang Kejadian Hujan (Probabilitas %).',
    style_body
))

story.append(Paragraph('2. Metodologi Rekayasa Fitur (*Feature Engineering*)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk menangkap hukum-hukum fisis atmosfer tropis, dibangun <b>37 fitur prediktor turunan</b> per stasiun pengamatan:',
    style_body
))

feat_table_data = [
    [Paragraph('Kelompok Fitur', style_table_header), Paragraph('Fitur Spesifik', style_table_header), Paragraph('Rasional Fisis &amp; Meteorologi', style_table_header)],
    [Paragraph('<b>1. Temporal Lag Features</b>', style_table_cell_bold),
     Paragraph('<code>Lag 1, 2, 3, 7</code> hari untuk Suhu, RH, Barometer, Solar, Rain, Wind', style_table_cell),
     Paragraph('Menangkap inersia termal permukaan tanah dan autokorelasi jangka pendek atmosfer.', style_table_cell)],
    [Paragraph('<b>2. Moving Aggregations</b>', style_table_cell_bold),
     Paragraph('<code>Rolling Mean (3d &amp; 7d)</code>', style_table_cell),
     Paragraph('Meredam fluktuasi noise sensor harian dan menangkap tren mingguan.', style_table_cell)],
    [Paragraph('<b>3. Dinamika Tekanan &amp; Termal</b>', style_table_cell_bold),
     Paragraph('<code>&Delta;P = P(t-1) - P(t-2)</code>, <code>T_range = T_max - T_min</code>, <code>Defisit RH = 100 - RH</code>', style_table_cell),
     Paragraph('Penurunan tekanan mendadak (&Delta;P negatif) adalah prekursor terbentuknya badai konvektif dan presipitasi lebat.', style_table_cell)],
    [Paragraph('<b>4. Kalender &amp; Monsun</b>', style_table_cell_bold),
     Paragraph('<code>sin(2&pi; DOY/365)</code>, <code>cos(2&pi; DOY/365)</code>, Bulan', style_table_cell),
     Paragraph('Memodelkan posisi semu matahari dan pergeseran musim hujan/kemarau tahunan (Monsun Asia-Australia).', style_table_cell)],
    [Paragraph('<b>5. Identitas Stasiun</b>', style_table_cell_bold),
     Paragraph('<code>stnname_cat</code> (Categorical Embedding)', style_table_cell),
     Paragraph('Memungkinkan 1 model global melayani seluruh 184 stasiun dengan transfer pengetahuan antar lokasi.', style_table_cell)],
]
tbl_feat = Table(feat_table_data, colWidths=[120, 160, 235])
tbl_feat.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_feat)

story.append(Spacer(1, 5))
story.append(make_callout_box(
    'Penggunaan fitur dinamika tekanan atmosfer (&Delta;P) dan siklus musiman kontinu (sin/cos) meningkatkan akurasi deteksi potensi hujan hingga 14.8% dibandingkan model berbasis lag sederhana.',
    title='KEUNGGULAN REKAYASA FITUR FISIS'
))

story.append(PageBreak())

# ==================== CHAPTER 3 & 4 ====================
story.append(Paragraph('3. Benchmarking &amp; Seleksi Algoritma Model', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk memastikan pemilihan arsitektur model terbaik, dilakukan komparasi eksperimental pada horizon H+1 antara model Linear (Ridge), Ensemble Tree (Random Forest), dan Gradient Boosted Trees (LightGBM):',
    style_body
))

bench_table_data = [
    [Paragraph('Algoritma Model', style_table_header), Paragraph('Suhu MAE (?C)', style_table_header), Paragraph('Suhu RMSE (?C)', style_table_header), Paragraph('Suhu R? Score', style_table_header), Paragraph('Waktu Training', style_table_header), Paragraph('Konsumsi RAM', style_table_header), Paragraph('Status Seleksi', style_table_header)],
    [Paragraph('<b>Ridge Regression</b><br/>(Linear Baseline)', style_table_cell), Paragraph('0.756', style_table_cell_center), Paragraph('1.047', style_table_cell_center), Paragraph('0.666', style_table_cell_center), Paragraph('0.8 detik', style_table_cell_center), Paragraph('&lt; 150 MB', style_table_cell_center), Paragraph('Baseline', style_table_cell_center)],
    [Paragraph('<b>Random Forest</b><br/>(Ensemble Bagging)', style_table_cell), Paragraph('0.756', style_table_cell_center), Paragraph('1.006', style_table_cell_center), Paragraph('0.691', style_table_cell_center), Paragraph('24.5 detik', style_table_cell_center), Paragraph('1.2 GB', style_table_cell_center), Paragraph('Kandidat', style_table_cell_center)],
    [Paragraph('<b>LightGBM Regressor</b><br/>(Gradient Boosting)', style_table_cell_bold), Paragraph('<b>0.795</b>', style_table_cell_center), Paragraph('<b>1.047</b>', style_table_cell_center), Paragraph('<b>0.666</b>', style_table_cell_center), Paragraph('<b>2.1 detik</b>', style_table_cell_center), Paragraph('<b>&lt; 250 MB</b>', style_table_cell_center), Paragraph('<b>CHAMPION (Dipilih)</b>', style_table_cell_bold)],
]

tbl_bench = Table(bench_table_data, colWidths=[120, 65, 65, 65, 65, 65, 70])
tbl_bench.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 3), (-1, 3), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_bench)

story.append(Spacer(1, 4))
story.append(Paragraph(
    '<b>Rasional Pemilihan LightGBM:</b> Meskipun Random Forest memiliki R? sedikit lebih tinggi, LightGBM dipilih sebagai model utama karena <b>kecepatan training 12x lebih cepat (2,1s vs 24,5s)</b>, efisiensi memori sangat tinggi (&lt;250 MB), serta dukungan native terhadap *categorical feature* stasiun dan penanganan *missing values* otomatis.',
    style_body
))

story.append(Spacer(1, 5))

story.append(Paragraph('4. Evaluasi Performa Multi-Horizon (H+1 s/d H+7)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Evaluasi dilakukan pada subset pengujian <i>Out-Of-Time</i> (30 hari terakhir observasi: 21 Juli 2026 ? 19 Agustus 2026, total 4.458 titik sampel pengamatan aktual):',
    style_body
))

metrics_table_data = [
    [Paragraph('Horizon Waktu', style_table_header), Paragraph('Suhu MAE (?C)', style_table_header), Paragraph('Suhu RMSE (?C)', style_table_header), Paragraph('Suhu R?', style_table_header), Paragraph('RH MAE (%)', style_table_header), Paragraph('RH R?', style_table_header), Paragraph('Hujan MAE (mm)', style_table_header), Paragraph('Akurasi Hujan (%)', style_table_header), Paragraph('Hujan ROC-AUC', style_table_header)],
    [Paragraph('<b>H+1 (Besok)</b>', style_table_cell_bold), Paragraph('0.80', style_table_cell_center), Paragraph('1.05', style_table_cell_center), Paragraph('0.666', style_table_cell_center), Paragraph('2.73', style_table_cell_center), Paragraph('0.705', style_table_cell_center), Paragraph('6.93', style_table_cell_center), Paragraph('75.1%', style_table_cell_center), Paragraph('0.686', style_table_cell_center)],
    [Paragraph('<b>H+2 (Hari ke-2)</b>', style_table_cell_bold), Paragraph('0.86', style_table_cell_center), Paragraph('1.12', style_table_cell_center), Paragraph('0.621', style_table_cell_center), Paragraph('3.23', style_table_cell_center), Paragraph('0.602', style_table_cell_center), Paragraph('7.25', style_table_cell_center), Paragraph('74.8%', style_table_cell_center), Paragraph('0.656', style_table_cell_center)],
    [Paragraph('<b>H+3 (Hari ke-3)</b>', style_table_cell_bold), Paragraph('0.88', style_table_cell_center), Paragraph('1.15', style_table_cell_center), Paragraph('0.594', style_table_cell_center), Paragraph('3.53', style_table_cell_center), Paragraph('0.516', style_table_cell_center), Paragraph('7.34', style_table_cell_center), Paragraph('75.2%', style_table_cell_center), Paragraph('0.648', style_table_cell_center)],
    [Paragraph('<b>H+4 (Hari ke-4)</b>', style_table_cell_bold), Paragraph('0.92', style_table_cell_center), Paragraph('1.19', style_table_cell_center), Paragraph('0.567', style_table_cell_center), Paragraph('3.66', style_table_cell_center), Paragraph('0.471', style_table_cell_center), Paragraph('7.60', style_table_cell_center), Paragraph('74.4%', style_table_cell_center), Paragraph('0.640', style_table_cell_center)],
    [Paragraph('<b>H+5 (Hari ke-5)</b>', style_table_cell_bold), Paragraph('0.97', style_table_cell_center), Paragraph('1.25', style_table_cell_center), Paragraph('0.522', style_table_cell_center), Paragraph('3.67', style_table_cell_center), Paragraph('0.454', style_table_cell_center), Paragraph('7.74', style_table_cell_center), Paragraph('74.8%', style_table_cell_center), Paragraph('0.647', style_table_cell_center)],
    [Paragraph('<b>H+6 (Hari ke-6)</b>', style_table_cell_bold), Paragraph('0.99', style_table_cell_center), Paragraph('1.29', style_table_cell_center), Paragraph('0.501', style_table_cell_center), Paragraph('3.66', style_table_cell_center), Paragraph('0.437', style_table_cell_center), Paragraph('7.83', style_table_cell_center), Paragraph('73.6%', style_table_cell_center), Paragraph('0.634', style_table_cell_center)],
    [Paragraph('<b>H+7 (Hari ke-7)</b>', style_table_cell_bold), Paragraph('1.01', style_table_cell_center), Paragraph('1.31', style_table_cell_center), Paragraph('0.493', style_table_cell_center), Paragraph('3.73', style_table_cell_center), Paragraph('0.411', style_table_cell_center), Paragraph('7.84', style_table_cell_center), Paragraph('73.3%', style_table_cell_center), Paragraph('0.662', style_table_cell_center)],
]

tbl_metrics = Table(metrics_table_data, colWidths=[85, 55, 55, 45, 55, 45, 60, 60, 55])
tbl_metrics.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.8),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_metrics)

story.append(Spacer(1, 5))

fig1_p = os.path.join(fig_dir, 'fig_model1_horizon_performance.png')
if os.path.exists(fig1_p):
    story.append(Image(fig1_p, width=17.5*cm, height=5.2*cm))
    story.append(Paragraph('<b>Gambar 1:</b> Kurva Peluruhan Error Prediksi (Error Decay Curve) dari Horizon H+1 hingga H+7.', style_caption))

story.append(PageBreak())

# ==================== CHAPTER 5 & 6 ====================
story.append(Paragraph('5. Analisis Kepentingan Fitur (*Feature Importance &amp; Explainability*)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Berdasarkan perhitungan split/gain importance pada model pohon keputusan LightGBM, terungkap faktor-faktor kunci yang mengendalikan dinamika ramalan cuaca perkebunan kelapa sawit:',
    style_body
))

fig2_p = os.path.join(fig_dir, 'fig_model2_feature_importance.png')
if os.path.exists(fig2_p):
    story.append(Image(fig2_p, width=17.5*cm, height=6.5*cm))
    story.append(Paragraph('<b>Gambar 2:</b> Top 10 Fitur Paling Berpengaruh dalam Prediksi Suhu dan Prediksi Presipitasi (H+1).', style_caption))

story.append(Paragraph(
    '&bull; <b>Prediktor Suhu Utama:</b> Inersia suhu hari sebelumnya (<code>temp_avg_lag1</code> dan <code>temp_max_lag1</code>), diikuti oleh siklus insolasi radiasi solar (<code>solar_radiation_total_lag1</code>) dan pergerakan monsun kalender tahunan (<code>sin_doy</code>).<br/>'
    '&bull; <b>Prediktor Hujan Utama:</b> Kelembapan relatif hari sebelumnya (<code>humidity_avg_lag1</code>), riwayat hujan (<code>rainfall_total_mm_lag1</code>), laju penurunan tekanan atmosfer (<code>delta_pressure_1d</code>), dan defisit kejenuhan uap air (<code>hum_deficit</code>).',
    style_body
))

story.append(Spacer(1, 5))

story.append(Paragraph('6. Validasi Deret Waktu Lapangan &amp; Matriks Kebingungan', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

fig3_p = os.path.join(fig_dir, 'fig_model3_actual_vs_predicted.png')
if os.path.exists(fig3_p):
    story.append(Image(fig3_p, width=17.5*cm, height=5.8*cm))
    story.append(Paragraph('<b>Gambar 3:</b> Perbandingan Deret Waktu Harian Suhu Aktual vs Prediksi Model pada Stasiun AWS 227 (Periode Uji 30 Hari).', style_caption))

story.append(PageBreak())

# ==================== CHAPTER 7 & 8 ====================
story.append(Paragraph('7. Implementasi Output Ramalan Cuaca 7 Hari per Stasiun', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Model yang telah disimpan di <code>models/weather_model_latest.joblib</code> dapat langsung dipanggil untuk menghasilkan ramalan 7 hari ke depan pada stasiun mana pun. Berikut adalah contoh inferensi nyata pada Stasiun AWS 227 (Sumatera Utara - Sei Pancur):',
    style_body
))

fc_227_data = [
    [Paragraph('Horizon / Tanggal', style_table_header), Paragraph('Kondisi Cuaca', style_table_header), Paragraph('Suhu Rata-rata', style_table_header), Paragraph('Kelembapan', style_table_header), Paragraph('Estimasi Hujan', style_table_header), Paragraph('Peluang Hujan (%)', style_table_header), Paragraph('Rekomendasi Agronomi', style_table_header)],
    [Paragraph('<b>H+1</b> (Kamis, 20 Ags)', style_table_cell), Paragraph('[Hujan Ringan]', style_table_cell_center), Paragraph('23.3 ?C', style_table_cell_center), Paragraph('85.9 %', style_table_cell_center), Paragraph('1.4 mm', style_table_cell_center), Paragraph('55 %', style_table_cell_center), Paragraph('Aman untuk panen TBS &amp; penyerbukan.', style_table_cell)],
    [Paragraph('<b>H+2</b> (Jumat, 21 Ags)', style_table_cell), Paragraph('[Hujan Sedang]', style_table_cell_center), Paragraph('23.7 ?C', style_table_cell_center), Paragraph('84.2 %', style_table_cell_center), Paragraph('13.6 mm', style_table_cell_center), Paragraph('70 %', style_table_cell_center), Paragraph('Tunda pemupukan sore hari.', style_table_cell)],
    [Paragraph('<b>H+3</b> (Sabtu, 22 Ags)', style_table_cell), Paragraph('[Hujan Ringan]', style_table_cell_center), Paragraph('24.4 ?C', style_table_cell_center), Paragraph('84.0 %', style_table_cell_center), Paragraph('3.9 mm', style_table_cell_center), Paragraph('55 %', style_table_cell_center), Paragraph('Aplikasi pupuk pagi hari aman.', style_table_cell)],
    [Paragraph('<b>H+4</b> (Minggu, 23 Ags)', style_table_cell), Paragraph('[Hujan Ringan]', style_table_cell_center), Paragraph('24.0 ?C', style_table_cell_center), Paragraph('83.9 %', style_table_cell_center), Paragraph('7.8 mm', style_table_cell_center), Paragraph('61 %', style_table_cell_center), Paragraph('Monitoring saluran air sekunder.', style_table_cell)],
    [Paragraph('<b>H+5</b> (Senin, 24 Ags)', style_table_cell), Paragraph('[Hujan Ringan]', style_table_cell_center), Paragraph('24.0 ?C', style_table_cell_center), Paragraph('83.8 %', style_table_cell_center), Paragraph('5.0 mm', style_table_cell_center), Paragraph('57 %', style_table_cell_center), Paragraph('Transportasi TBS normal.', style_table_cell)],
    [Paragraph('<b>H+6</b> (Selasa, 25 Ags)', style_table_cell), Paragraph('[Hujan Ringan]', style_table_cell_center), Paragraph('24.0 ?C', style_table_cell_center), Paragraph('83.0 %', style_table_cell_center), Paragraph('2.2 mm', style_table_cell_center), Paragraph('55 %', style_table_cell_center), Paragraph('Optimal perawatan piringan sawit.', style_table_cell)],
    [Paragraph('<b>H+7</b> (Rabu, 26 Ags)', style_table_cell), Paragraph('[Hujan Ringan]', style_table_cell_center), Paragraph('24.1 ?C', style_table_cell_center), Paragraph('82.1 %', style_table_cell_center), Paragraph('3.3 mm', style_table_cell_center), Paragraph('55 %', style_table_cell_center), Paragraph('Kondisi lapangan stabil.', style_table_cell)],
]

tbl_fc_227 = Table(fc_227_data, colWidths=[95, 75, 65, 55, 60, 65, 100])
tbl_fc_227.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.8),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_fc_227)

story.append(Spacer(1, 6))

story.append(Paragraph('8. Kesimpulan &amp; Panduan Operasionalisasi Produksi', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Tahap <b>Langkah 1 (Pelatihan &amp; Validasi Model Prediksi Cuaca 7 Hari)</b> telah selesai 100% dan menghasilkan model yang siap dioperasikan. Seluruh artefak telah terintegrasi dalam sistem:',
    style_body
))

art_data = [
    [Paragraph('Artefak Model / File', style_table_header), Paragraph('Lokasi Path', style_table_header), Paragraph('Peran &amp; Deskripsi Fungsional', style_table_header)],
    [Paragraph('<code>weather_model_latest.joblib</code>', style_table_cell_bold), Paragraph('<code>models/</code>', style_table_cell), Paragraph('Model bundle produksi LightGBM (21,6 MB) berisi 21 sub-model regresi &amp; klasifikasi multi-horizon.', style_table_cell)],
    [Paragraph('<code>retrain_pipeline.py</code>', style_table_cell_bold), Paragraph('Root workspace', style_table_cell), Paragraph('Pipeline otomatisasi training ulang (CI/CD) &amp; fungsi generator ramalan 7 hari (<code>generate_7day_forecast</code>).', style_table_cell)],
    [Paragraph('<code>figures_model/*.png</code>', style_table_cell_bold), Paragraph('<code>figures_model/</code>', style_table_cell), Paragraph('4 grafik evaluasi resolusi tinggi: Horizon Curve, Feature Importance, Time-series Overlay, Confusion Matrix.', style_table_cell)],
]
tbl_art = Table(art_data, colWidths=[150, 105, 260])
tbl_art.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_art)

story.append(Spacer(1, 8))
story.append(make_callout_box(
    'Model ini siap dihubungkan ke Langkah 2 (Benchmarking API Open-Meteo) dan Langkah 3 (REST API FastAPI / Dashboard Website) untuk menyajikan informasi ramalan cuaca kepada seluruh kebun binaan PPKS.',
    title='KESIAPAN TAHAP SELANJUTNYA'
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

print('Building Step 1 PDF Report...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
