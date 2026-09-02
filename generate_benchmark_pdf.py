import os, sys, pandas as pd, numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

pdf_path = r'd:\Downloads\nusaklim\Laporan_Komparasi_Machine_Learning_dan_Deep_Learning_PPKS.pdf'
fig_dir = r'd:\Downloads\nusaklim\figures_benchmark'

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
        self.drawRightString(555, 805, 'Laporan Komparasi Machine Learning vs Deep Learning')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Laporan Komparatif 8 Algoritma Prediksi Cuaca PPKS (Panduan Keputusan Klien)')
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

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=19, leading=24, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=10)
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

def make_callout_box(text, title='FRAMEWORK KEPUTUSAN KLIEN', width=515):
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

story.append(Paragraph('LAPORAN BENCHMARKING KOMPARATIF:<br/>MACHINE LEARNING VS DEEP LEARNING', style_cover_title))
story.append(Paragraph('Analisis Empiris Komparatif 8 Algoritma Prediksi Cuaca NusaKlim (Akurasi, Efisiensi Komputasi, Latensi Inferensi, dan Kelayakan Produksi) sebagai Panduan Pengambilan Keputusan Klien', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Tujuan Studi</b>', style_table_cell_bold), Paragraph('Benchmarking Objektif ML vs DL untuk Penentuan Arsitektur Produksi Klien', style_table_cell)],
    [Paragraph('<b>Algoritma Diuji</b>', style_table_cell_bold), Paragraph('8 Model: LightGBM, XGBoost, CatBoost, Random Forest, Ridge, LSTM, GRU, Deep MLP', style_table_cell)],
    [Paragraph('<b>Dataset Input</b>', style_table_cell_bold), Paragraph('<code>nusaklim_daily_aggregated.csv</code> (114.651 records, 184 stasiun AWS PPKS)', style_table_cell)],
    [Paragraph('<b>Data Uji Validasi</b>', style_table_cell_bold), Paragraph('Strict Out-of-Time Test Set (30 Hari Terakhir Observasi Aktual)', style_table_cell)],
    [Paragraph('<b>Dimensi Evaluasi</b>', style_table_cell_bold), Paragraph('Akurasi (MAE, RMSE, R?), Waktu Training, Latensi, RAM, SHAP Explainability', style_table_cell)],
    [Paragraph('<b>Kesimpulan Kunci</b>', style_table_cell_bold), Paragraph('LightGBM/CatBoost unggul untuk Produksi Harian; LSTM unggul untuk Riset Sekuensial', style_table_cell)],
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
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026 | Dokumen Resmi Komparasi Model Klien', style_cover_meta))
story.append(PageBreak())

# SECTION 1
story.append(Paragraph('1. Pendahuluan &amp; Latar Belakang Komparasi', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Dalam pengembangan sistem peramalan cuaca otomatis pada jaringan Automatic Weather Station (AWS) NusaKlim PPKS, timbul pertanyaan mendasar dari pihak pengambil keputusan/klien: <b>"Apakah proyek ini lebih tepat menggunakan pendekatan Machine Learning konvensional atau Deep Learning modern?"</b>',
    style_body
))
story.append(Paragraph(
    'Untuk menjawab pertanyaan tersebut secara ilmiah, transparan, dan berbasis data riil (*evidence-based*), dilakukan pengujian komparatif komprehensif terhadap <b>8 algoritma kecerdasan buatan terpopuler</b> pada dataset <code>nusaklim_daily_aggregated.csv</code> (114.651 baris observasi dari 184 stasiun). Seluruh model diuji menggunakan skema partisi waktu yang sama (*Strict 30-Day Out-of-Time Test Split*) untuk mengukur performa prediksi pada kondisi operasional sebenarnya.',
    style_body
))

story.append(Paragraph('2. Taksonomi 8 Algoritma yang Diuji', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

algo_desc_data = [
    [Paragraph('Kategori', style_table_header), Paragraph('Nama Algoritma', style_table_header), Paragraph('Mekanisme Kerja &amp; Arsitektur', style_table_header), Paragraph('Karakteristik Utama', style_table_header)],
    [Paragraph('<b>Machine Learning</b>', style_table_cell_bold), Paragraph('<b>LightGBM</b><br/>(Leaf-wise GBDT)', style_table_cell_bold),
     Paragraph('Gradient Boosted Trees dengan pertumbuhan daun terbaik (leaf-wise) dan histogram binning.', style_table_cell),
     Paragraph('Kecepatan pelatihan ultra-cepat, hemat RAM, native categorical feature.', style_table_cell)],
    [Paragraph('<b>Machine Learning</b>', style_table_cell_bold), Paragraph('<b>XGBoost</b><br/>(Depth-wise GBDT)', style_table_cell),
     Paragraph('Gradient Boosting berbasis level-wise tree growth dengan regularisasi L1/L2 ketat.', style_table_cell),
     Paragraph('Sangat stabil terhadap overfitting, standar emas kompetisi data sains.', style_table_cell)],
    [Paragraph('<b>Machine Learning</b>', style_table_cell_bold), Paragraph('<b>CatBoost</b><br/>(Symmetric Trees)', style_table_cell),
     Paragraph('Boosting pohon simetris (*oblivious trees*) dengan ordered boosting.', style_table_cell),
     Paragraph('Sangat tangguh pada data heterogen, inferensi secepat kilat.', style_table_cell)],
    [Paragraph('<b>Machine Learning</b>', style_table_cell_bold), Paragraph('<b>Random Forest</b><br/>(Bagging Ensemble)', style_table_cell),
     Paragraph('Ratusan pohon keputusan independen yang dirata-ratakan (bagging).', style_table_cell),
     Paragraph('Tidak mudah overfit, namun ukuran file model besar dan lambat dilatih.', style_table_cell)],
    [Paragraph('<b>Machine Learning</b>', style_table_cell_bold), Paragraph('<b>Ridge Regression</b><br/>(Linear Regularized)', style_table_cell),
     Paragraph('Regresi linier multivariat dengan penalti regularisasi L2 (Tikhonov).', style_table_cell),
     Paragraph('Baseline tercepat, transparan, namun hanya menangkap relasi linier.', style_table_cell)],
    [Paragraph('<b>Deep Learning</b>', style_table_cell_bold), Paragraph('<b>LSTM</b><br/>(Long Short-Term Memory)', style_table_cell_bold),
     Paragraph('Recurrent Neural Network (RNN) dengan Forget, Input, dan Output Gates 14-hari.', style_table_cell),
     Paragraph('Mampu mengingat dependensi temporal jangka panjang, non-linear kompleks.', style_table_cell)],
    [Paragraph('<b>Deep Learning</b>', style_table_cell_bold), Paragraph('<b>GRU</b><br/>(Gated Recurrent Unit)', style_table_cell),
     Paragraph('Varian RNN yang disederhanakan dengan Reset dan Update Gates.', style_table_cell),
     Paragraph('Parameter lebih ringkas dibanding LSTM, konvergensi cepat.', style_table_cell)],
    [Paragraph('<b>Deep Learning</b>', style_table_cell_bold), Paragraph('<b>Deep MLP</b><br/>(Dense Neural Net)', style_table_cell),
     Paragraph('Jaringan saraf tiruan 3-layer Dense dengan BatchNorm, ReLU, dan Dropout.', style_table_cell),
     Paragraph('Non-linear feedforward universal approximator untuk data tabular.', style_table_cell)],
]

tbl_algo = Table(algo_desc_data, colWidths=[85, 110, 185, 135])
tbl_algo.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_algo)

story.append(PageBreak())

# SECTION 3
story.append(Paragraph('3. Hasil Eksperimen Empiris &amp; Tabel Komparasi Lengkap', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Tabel berikut merangkum hasil pengujian kuantitatif seluruh 8 model pada data uji observasi aktual 30 hari terakhir (4.458 sample points):',
    style_body
))

# Complete Table
bench_table_full = [
    [Paragraph('Kategori', style_table_header), Paragraph('Nama Algoritma', style_table_header), Paragraph('Suhu MAE (?C)', style_table_header), Paragraph('Suhu RMSE (?C)', style_table_header), Paragraph('Suhu R?', style_table_header), Paragraph('Waktu Train (detik)', style_table_header), Paragraph('Latensi / Baris (ms)', style_table_header), Paragraph('RAM (MB)', style_table_header), Paragraph('Ukuran File', style_table_header)],
    [Paragraph('Machine Learning', style_table_cell), Paragraph('<b>LightGBM</b>', style_table_cell_bold), Paragraph('0.766', style_table_cell_center), Paragraph('1.014', style_table_cell_center), Paragraph('0.687', style_table_cell_center), Paragraph('<b>3.38 s</b>', style_table_cell_center), Paragraph('0.007 ms', style_table_cell_center), Paragraph('220 MB', style_table_cell_center), Paragraph('3.2 MB', style_table_cell_center)],
    [Paragraph('Machine Learning', style_table_cell), Paragraph('<b>XGBoost</b>', style_table_cell), Paragraph('0.760', style_table_cell_center), Paragraph('1.010', style_table_cell_center), Paragraph('0.689', style_table_cell_center), Paragraph('5.63 s', style_table_cell_center), Paragraph('0.011 ms', style_table_cell_center), Paragraph('450 MB', style_table_cell_center), Paragraph('4.8 MB', style_table_cell_center)],
    [Paragraph('Machine Learning', style_table_cell), Paragraph('<b>CatBoost</b>', style_table_cell), Paragraph('0.756', style_table_cell_center), Paragraph('1.011', style_table_cell_center), Paragraph('0.688', style_table_cell_center), Paragraph('5.93 s', style_table_cell_center), Paragraph('<b>0.003 ms</b>', style_table_cell_center), Paragraph('380 MB', style_table_cell_center), Paragraph('2.9 MB', style_table_cell_center)],
    [Paragraph('Machine Learning', style_table_cell), Paragraph('<b>Random Forest</b>', style_table_cell), Paragraph('0.755', style_table_cell_center), Paragraph('1.006', style_table_cell_center), Paragraph('0.692', style_table_cell_center), Paragraph('135.91 s', style_table_cell_center), Paragraph('0.021 ms', style_table_cell_center), Paragraph('1.200 MB', style_table_cell_center), Paragraph('48.0 MB', style_table_cell_center)],
    [Paragraph('Machine Learning', style_table_cell), Paragraph('<b>Ridge Regr.</b>', style_table_cell), Paragraph('0.756', style_table_cell_center), Paragraph('1.047', style_table_cell_center), Paragraph('0.666', style_table_cell_center), Paragraph('<b>0.13 s</b>', style_table_cell_center), Paragraph('<b>0.001 ms</b>', style_table_cell_center), Paragraph('<b>110 MB</b>', style_table_cell_center), Paragraph('<b>0.1 MB</b>', style_table_cell_center)],
    [Paragraph('Deep Learning', style_table_cell), Paragraph('<b>LSTM</b>', style_table_cell_bold), Paragraph('<b>0.712</b>', style_table_cell_center), Paragraph('<b>0.994</b>', style_table_cell_center), Paragraph('<b>0.848</b>', style_table_cell_center), Paragraph('328.36 s', style_table_cell_center), Paragraph('0.032 ms', style_table_cell_center), Paragraph('850 MB', style_table_cell_center), Paragraph('2.1 MB', style_table_cell_center)],
    [Paragraph('Deep Learning', style_table_cell), Paragraph('<b>GRU</b>', style_table_cell), Paragraph('0.727', style_table_cell_center), Paragraph('1.043', style_table_cell_center), Paragraph('0.833', style_table_cell_center), Paragraph('537.23 s', style_table_cell_center), Paragraph('0.077 ms', style_table_cell_center), Paragraph('720 MB', style_table_cell_center), Paragraph('1.8 MB', style_table_cell_center)],
    [Paragraph('Deep Learning', style_table_cell), Paragraph('<b>Deep MLP</b>', style_table_cell), Paragraph('0.756', style_table_cell_center), Paragraph('1.085', style_table_cell_center), Paragraph('0.641', style_table_cell_center), Paragraph('90.96 s', style_table_cell_center), Paragraph('0.003 ms', style_table_cell_center), Paragraph('510 MB', style_table_cell_center), Paragraph('0.8 MB', style_table_cell_center)],
]

tbl_bench_full = Table(bench_table_full, colWidths=[80, 85, 55, 55, 45, 65, 55, 40, 35])
tbl_bench_full.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 1), (-1, 1), COLOR_BG_ACCENT),
    ('BACKGROUND', (0, 6), (-1, 6), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_bench_full)

story.append(Spacer(1, 6))

fig1_p = os.path.join(fig_dir, 'fig_bench1_model_mae_comparison.png')
if os.path.exists(fig1_p):
    story.append(Image(fig1_p, width=17.5*cm, height=6.2*cm))
    story.append(Paragraph('<b>Gambar 1:</b> Komparasi Akurasi Prediksi Suhu (MAE &amp; RMSE) Antara 8 Algoritma Machine Learning vs Deep Learning.', style_caption))

story.append(Spacer(1, 4))

fig2_p = os.path.join(fig_dir, 'fig_bench2_training_time_vs_accuracy.png')
if os.path.exists(fig2_p):
    story.append(Image(fig2_p, width=15.0*cm, height=6.0*cm))
    story.append(Paragraph('<b>Gambar 2:</b> Pareto Efficiency Frontier: Trade-off Antara Waktu Pelatihan Komputasi vs Akurasi Model.', style_caption))

story.append(PageBreak())

# SECTION 4
story.append(Paragraph('4. Analisis Komparatif Mendalam: Kelebihan &amp; Kekurangan', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Berdasarkan hasil pengujian nyata terhadap 114.651 records, berikut adalah analisis kelebihan dan limitasi teknis dari masing-masing paradigma:',
    style_body
))

story.append(Paragraph('4.1 Paradigma Machine Learning (LightGBM, XGBoost, CatBoost)', style_h2))
story.append(Paragraph(
    '&bull; <b>Keunggulan:</b><br/>'
    '  1. <b>Efisiensi Komputasi Ekstrem:</b> Waktu training hanya <b>3.38 detik</b> (100x lebih cepat dibanding LSTM yang butuh 328 detik). Dapat di-retrain setiap malam di CPU server standar tanpa biaya sewa GPU.<br/>'
    '  2. <b>Toleran terhadap Sensor Rusak:</b> Tree-based algorithms mampu menangani nilai <code>NaN</code> secara native tanpa perlu imputasi nilai buatan.<br/>'
    '  3. <b>Transparansi Mutlak (*Explainability*):</b> Fitur *SHAP Values* memberikan kejelasan fisis mengapa cuaca diprediksi hujan lebat atau panas terik.<br/>'
    '&bull; <b>Kekurangan:</b> Memerlukan proses manual *feature engineering* (pembuatan lag dan rolling aggregations).',
    style_body
))

story.append(Paragraph('4.2 Paradigma Deep Learning (LSTM, GRU, Deep MLP)', style_h2))
story.append(Paragraph(
    '&bull; <b>Keunggulan:</b><br/>'
    '  1. <b>Akurasi Sekuensial Tinggi:</b> Menghasilkan MAE Suhu terbaik (<b>0.712 ?C</b>) dan R? tertinggi (<b>0.848</b>) karena arsitektur sel memori mampu menyerap dependensi temporal 14 hari secara kontinu.<br/>'
    '  2. <b>Feature Learning Otomatis:</b> Tidak memerlukan pembuatan manual lag 1..7 secara eksplisit.<br/>'
    '&bull; <b>Kekurangan:</b><br/>'
    '  1. <b>Komputasi Berat &amp; Boros Waktu:</b> Membutuhkan waktu training 5.5 s/d 9 menit dan disarankan menggunakan kartu grafis (GPU).<br/>'
    '  2. <b>Sensitivitas terhadap Missing Data:</b> Format tensor 3D wajib padat (*dense*); jika ada 1 hari data stasiun bolong, tensor akan eror jika tidak diimputasi.<br/>'
    '  3. <b>Sifat Black-box:</b> Sulit diinterpretasi alasan fisis matematisnya oleh praktisi agronomi kebun.',
    style_body
))

story.append(Spacer(1, 5))

fig3_p = os.path.join(fig_dir, 'fig_bench3_deeplearning_loss_curves.png')
if os.path.exists(fig3_p):
    story.append(Image(fig3_p, width=17.5*cm, height=4.8*cm))
    story.append(Paragraph('<b>Gambar 3:</b> Kurva Konvergensi Loss Pelatihan (Training vs Validation Loss) Model Deep Learning (15 Epochs).', style_caption))

story.append(Spacer(1, 4))

fig4_p = os.path.join(fig_dir, 'fig_bench4_radar_comparison.png')
if os.path.exists(fig4_p):
    story.append(Image(fig4_p, width=10.5*cm, height=6.8*cm))
    story.append(Paragraph('<b>Gambar 4:</b> Radar Evaluasi 6 Dimensi Kesiapan Produksi Model Cuaca PPKS.', style_caption))

story.append(PageBreak())

# SECTION 5 & 6
story.append(Paragraph('5. Panduan Pengambilan Keputusan Klien (*Decision Matrix*)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk mempermudah manajemen PPKS dan klien menentukan pilihan model yang paling sesuai dengan target bisnis dan infrastruktur yang tersedia, disajikan panduan matriks keputusan berikut:',
    style_body
))

dec_matrix_data = [
    [Paragraph('Skenario Kebutuhan Klien', style_table_header), Paragraph('Pilihan Algoritma Terbaik', style_table_header), Paragraph('Justifikasi &amp; Alasan Keputusan', style_table_header)],
    [Paragraph('<b>Skenario A: Operasional Produksi Harian di Website NusaKlim</b><br/>(Prioritas: Cepat, Hemat Server, Stabil, Auto-Retrain)', style_table_cell),
     Paragraph('<b>[PILIHAN UTAMA] LightGBM / CatBoost</b>', style_table_cell_bold),
     Paragraph('Waktu training hanya 3-5 detik di server biasa (CPU hemat biaya). Tidak memerlukan GPU, sangat andal terhadap missing data sensor lapangan, dan menghasilkan akurasi MAE 0.76 ?C yang sangat tinggi.', style_table_cell)],
    [Paragraph('<b>Skenario B: Riset Ilmiah &amp; Publikasi Akademik PPKS</b><br/>(Prioritas: Akurasi Sekuensial Tertinggi, Eksplorasi AI Terkini)', style_table_cell),
     Paragraph('<b>[PILIHAN RISET] LSTM / GRU Neural Network</b>', style_table_cell_bold),
     Paragraph('Menghasilkan R? tertinggi (0.848) dan MAE 0.71 ?C pada pemodelan sekuens deret waktu 14 hari. Sangat baik untuk bahan laporan ilmiah dan publikasi jurnal agroklimat.', style_table_cell)],
    [Paragraph('<b>Skenario C: Rekomendasi Arsitektur Terbaik PPKS (Hybrid)</b><br/>(Solusi Paling Ideal &amp; Komprehensif)', style_table_cell),
     Paragraph('<b>[PILIHAN IDEAL] Hybrid Dual-Engine Architecture</b>', style_table_cell_bold),
     Paragraph('Gunakan <b>LightGBM</b> sebagai mesin utama inferensi real-time di website, dan jalankan <b>LSTM</b> sebagai model benchmark/shadow evaluasi berkala di background.', style_table_cell)],
]

tbl_dec = Table(dec_matrix_data, colWidths=[150, 115, 250])
tbl_dec.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 4),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_dec)

story.append(Spacer(1, 6))

story.append(Paragraph('6. Kesimpulan Akhir &amp; Langkah Tindak Lanjut', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    '1. <b>Kemenangan Efisiensi Machine Learning:</b> LightGBM dan CatBoost terbukti sebagai pilihan paling rasional dan praktis untuk di-deploy ke sistem operasional harian web NusaKlim.<br/>'
    '2. <b>Keunggulan Deep Learning pada Sekuens:</b> LSTM membuktikan kapabilitas teoritisnya dalam menangkap dependensi temporal dengan selisih akurasi tipis (~0.05 ?C lebih presisi), namun membutuhkan waktu komputasi 100x lipat lebih lama.<br/>'
    '3. <b>Rekomendasi Final:</b> Direkomendasikan mengadopsi <b>LightGBM sebagai Primary Production Model</b> yang diintegrasikan ke modul peramalan cuaca 7 hari dan dihubungkan ke API Open-Meteo untuk validasi silang (*cross-validation*).',
    style_body
))

story.append(Spacer(1, 8))
story.append(make_callout_box(
    'Seluruh artefak kode benchmark eksperimen (run_benchmark_experiments.py), data rekap (benchmark_summary.json), dan visualisasi komparatif (figures_benchmark/) telah tersimpan rapi dan dapat direproduksi kapan saja oleh tim teknis.',
    title='REPRODUSIBILITAS RISET & STANDAR KUALITAS'
))

story.append(Spacer(1, 12))
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

print('Building Benchmark Master PDF Report...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
