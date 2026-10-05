import os, sys, json, joblib
import pandas as pd
import numpy as np
from datetime import timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Arial', r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', r'C:\Windows\Fonts\arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', r'C:\Windows\Fonts\ariali.ttf'))
pdfmetrics.registerFont(TTFont('Arial-BoldItalic', r'C:\Windows\Fonts\arialbi.ttf'))
from reportlab.lib.fonts import addMapping
addMapping('Arial', 0, 0, 'Arial')
addMapping('Arial', 1, 0, 'Arial-Bold')
addMapping('Arial', 0, 1, 'Arial-Italic')
addMapping('Arial', 1, 1, 'Arial-BoldItalic')

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
pdf_path = os.path.join(BASE_DIR, 'report', '3.Laporan_Model_Prediksi_Cuaca_7Hari_PPKS.pdf')
fig_dir = os.path.join(BASE_DIR, 'figures_model')

sys.path.insert(0, BASE_DIR)
from retrain_pipeline import (generate_7day_forecast, REGRESSION_TARGETS, CLASSIFICATION_TARGET,
                               REG_ALGO_ORDER, CLF_ALGO_ORDER, load_champion_algorithms,
                               extract_feature_importance, BENCHMARK_JSON_PATH, multi_metric_rank)

# ------------------------------------------------------------------------------
# LOAD REAL MODEL BUNDLE & BENCHMARK RESULTS (live, not hardcoded)
# ------------------------------------------------------------------------------
bundle = joblib.load(os.path.join(BASE_DIR, 'models', 'weather_model_latest.joblib'))
metrics = bundle['metrics']
feature_cols = bundle['feature_cols']
target_cols = bundle['target_cols']
models = bundle['models']
algo_used = bundle['algo_used']
n_feature = len(feature_cols)
n_target = len(target_cols)

with open(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'), encoding='utf-8') as f:
    n_raw_rows = sum(1 for _ in f) - 1

with open(os.path.join(BASE_DIR, 'figures_model', 'permutation_importance_h1.json'), encoding='utf-8') as _f:
    _perm_imp = json.load(_f)

def top_features(target_key, n=5):
    """Ambil n fitur terpenting (permutation importance pada data uji, dihitung
    gen_figures_model.py) untuk narasi Bab 5 agar teks sinkron dengan figur."""
    return pd.Series(_perm_imp[target_key]).sort_values(ascending=False).head(n)

def fmt_feature_list(imp_series):
    return ', '.join(f'<code>{name}</code>' for name in imp_series.index)

with open(BENCHMARK_JSON_PATH, 'r', encoding='utf-8') as f:
    bench_records = json.load(f)
df_bench_all = pd.DataFrame(bench_records)

fc_df = generate_7day_forecast(station_id='222')

REG_VARS = list(REGRESSION_TARGETS.keys())
REG_LABELS = REGRESSION_TARGETS

df_bench_reg = df_bench_all[df_bench_all['Variabel'] != CLASSIFICATION_TARGET].copy()
df_bench_clf = df_bench_all[df_bench_all['Variabel'] == CLASSIFICATION_TARGET].copy()

# Benchmark gabungan 5 algoritma (3 ML dari Laporan 3 + 2 DL dari run_dl_benchmark_h1_h7.py)
# untuk Bab 3.4 (perbandingan dengan Deep Learning) - laporan gabungan Laporan 3+4.
with open(os.path.join(BASE_DIR, 'benchmark_merged_5algo_h1_h7.json'), 'r', encoding='utf-8') as f:
    merged_records = json.load(f)
df_merged_all = pd.DataFrame(merged_records)
df_merged_reg = df_merged_all[df_merged_all['Variabel'] != CLASSIFICATION_TARGET].copy()
df_merged_clf = df_merged_all[df_merged_all['Variabel'] == CLASSIFICATION_TARGET].copy()

# Algoritma juara per variabel - SUMBER TUNGGAL: fungsi yang sama persis dipakai
# retrain_pipeline.train_and_evaluate() untuk melatih model produksi (bundle di atas),
# supaya narasi/tabel laporan selalu konsisten dengan model yang benar-benar dipakai.
_champions = load_champion_algorithms(BENCHMARK_JSON_PATH)

def champion_algo_regresi(var):
    return _champions[var]

def champion_algo_klasifikasi():
    return _champions[CLASSIFICATION_TARGET]

# ------------------------------------------------------------------------------
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
        self.drawString(40, 805, 'Pusat Penelitian Kelapa Sawit (PPKS) - NusaKlim Weather AI')
        self.drawRightString(555, 805, 'Laporan Model Prediksi Cuaca 7 Hari (Multi-Horizon)')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Laporan Teknis Langkah 1: Pelatihan & Pengujian Model Prediksi Cuaca 7 Hari PPKS')
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

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=19, leading=24, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=10)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Arial', fontSize=11, leading=15, textColor=COLOR_BODY, alignment=1, spaceAfter=20)
style_cover_meta = ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12, textColor=COLOR_MUTED, alignment=1)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Arial-Bold', fontSize=12.5, leading=15.5, textColor=COLOR_PRIMARY, spaceBefore=10, spaceAfter=5, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Arial-Bold', fontSize=9.5, leading=12.5, textColor=COLOR_SECONDARY, spaceBefore=8, spaceAfter=3, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Arial', fontSize=8.2, leading=12, textColor=COLOR_BODY, spaceAfter=4, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Arial-Italic', fontSize=7.8, leading=11, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Arial', fontSize=7.3, leading=9.5, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.3, leading=9.5, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Arial', fontSize=7.3, leading=9.5, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=9.8, textColor=COLOR_MUTED, alignment=1, spaceBefore=2, spaceAfter=6)

def make_callout_box(text, title='CATATAN PENTING & INSIGHT MODEL', width=515):
    p_title = Paragraph(f'<b>{title}</b>', ParagraphStyle('CT', fontName='Arial-Bold', fontSize=7.8, leading=10, textColor=COLOR_PRIMARY, spaceAfter=2))
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
    ParagraphStyle('CoverInst', fontName='Arial', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 10))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=18))

story.append(Paragraph('LAPORAN PENGEMBANGAN &amp; EVALUASI MODEL PREDIKSI CUACA 7 HARI', style_cover_title))
story.append(Paragraph('Dokumentasi Teknis Pelatihan Model Multi-Horizon Machine Learning, Benchmarking Algoritma (termasuk Perbandingan dengan Deep Learning), dan Pengujian Out-Of-Time pada 183 Stasiun AWS NusaKlim', style_cover_subtitle))

n_test_ref = metrics['temp_avg_h1']['n_test']
n_train_ref = metrics['temp_avg_h1']['n_train']
model_size_mb = os.path.getsize(os.path.join(BASE_DIR, 'models', 'weather_model_latest.joblib')) / (1024 * 1024)

cover_box_content = [
    [Paragraph('<b>Status Model</b>', style_table_cell_bold), Paragraph('Model Produksi Terlatih (Prediksi Multi-Hari H+1 s/d H+7, 7 Variabel)', style_table_cell)],
    [Paragraph('<b>Dataset Input</b>', style_table_cell_bold), Paragraph(f'Dataset harian bersih ({n_raw_rows:,} baris, 183 stasiun)', style_table_cell)],
    [Paragraph('<b>Data Latih Efektif</b>', style_table_cell_bold), Paragraph(f'&plusmn;{n_train_ref:,} baris per target (&asymp;{n_train_ref/n_raw_rows*100:.0f}% dari {n_raw_rows:,}) setelah pembagian data berdasarkan waktu &amp; penyaringan baris dengan riwayat/fitur tidak lengkap (lihat Bab 1.1)', style_table_cell)],
    [Paragraph('<b>Target Prediksi</b>', style_table_cell_bold), Paragraph('Suhu Rata-rata, Kelembapan, Curah Hujan (mm), Radiasi Matahari, Tekanan Udara, Kecepatan Angin (6 nilai angka) &amp; Arah Mata Angin (4 kategori)', style_table_cell)],
    [Paragraph('<b>Metode Pengujian</b>', style_table_cell_bold), Paragraph(f'Diuji dengan 30 hari data terbaru yang tidak dipakai saat pelatihan: 21 Juli &ndash; 19 Agustus 2026 (&plusmn;{n_test_ref:,} titik data per target)', style_table_cell)],
    [Paragraph('<b>Ukuran Model</b>', style_table_cell_bold), Paragraph(f'{model_size_mb:.1f} MB', style_table_cell)],
    [Paragraph('<b>Jumlah Sub-Model</b>', style_table_cell_bold), Paragraph(f'{n_target} sub-model ({7*6} regresi + {7} klasifikasi arah angin) dari {n_feature} fitur prediktor', style_table_cell)],
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
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026 | Dokumen Resmi Tahap Pelatihan Model', style_cover_meta))
story.append(PageBreak())

# ==================== CHAPTER 1 & 2 ====================
story.append(Paragraph('1. Ringkasan Eksekutif &amp; Desain Solusi Prediksi 7-Hari', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Sebagai tindak lanjut dari tahap Preprocessing Data dan Analisis Eksploratif (EDA), dokumen ini menyajikan pengembangan lengkap <b>Model Ramalan Cuaca 7 Hari ke Depan (Langkah 1)</b> untuk seluruh 183 Stasiun Cuaca Otomatis (AWS) NusaKlim PPKS. Model dirancang untuk menyediakan ramalan harian yang presisi, stabil, dan cepat dihitung guna mendukung manajemen perkebunan kelapa sawit.',
    style_body
))
story.append(Paragraph(
    'Model dilatih dengan pendekatan pohon keputusan bertingkat (<i>Gradient Boosting</i>), di mana setiap horizon waktu (H+1, H+2, ..., H+7) memiliki model khusus yang dilatih untuk <b>7 variabel cuaca</b>: Suhu Rata-rata, Kelembapan, Curah Hujan (mm), Radiasi Matahari, Tekanan Udara, dan Kecepatan Angin (berupa angka), serta Arah Mata Angin (berupa kategori Utara/Timur/Selatan/Barat). Ketujuh variabel ini dipilih karena paling relevan dan langsung dibutuhkan untuk kebutuhan operasional di lapangan.',
    style_body
))

story.append(Paragraph('1.1 Skema Pembagian Data: Latih dan Uji', style_h2))
story.append(Paragraph(
    f'Berikut rincian pembagian {n_raw_rows:,} baris data harian (183 stasiun, hingga observasi terakhir 19 Agustus 2026): pembagian dilakukan secara <b>berurutan menurut waktu per stasiun, bukan acak</b>, supaya model tidak "mengintip" data masa depan saat belajar dari data masa lalu. Data dibagi menjadi dua bagian: <b>(1) Data Latih</b> &ndash; seluruh observasi sebelum 21 Juli 2026, menghasilkan &plusmn;{n_train_ref:,} baris valid per target; dan <b>(2) Data Uji</b> &ndash; 30 hari terakhir (21 Juli &ndash; 19 Agustus 2026), &plusmn;{n_test_ref:,} baris valid per target, yang sama sekali tidak dilihat model selama pelatihan. Total baris valid gabungan ({n_train_ref + n_test_ref:,}, &asymp;{(n_train_ref + n_test_ref)/n_raw_rows*100:.0f}% dari {n_raw_rows:,}) lebih kecil dari data mentah karena baris dengan riwayat/fitur tidak lengkap dibuang &ndash; bukan hanya di hari-hari pertama tiap stasiun, tapi di titik manapun sepanjang deret waktunya: data mentah tiap parameter cuaca sudah memiliki &plusmn;13% nilai kosong (gangguan sensor/QC, lihat Laporan Preprocessing &amp; EDA Bab 2), dan karena fitur lag/rolling dihitung dengan menggeser nilai per hari, satu nilai kosong pada hari-T akan ikut mengosongkan fitur turunannya hingga 7 hari berikutnya. Demikian pula, tidak semua dari 183 stasiun memiliki baris pada setiap hari di jendela uji 30 hari (beberapa berhenti melapor lebih awal), sehingga jumlah baris uji juga lebih kecil dari perkiraan ideal 183 &times; 30 hari.',
    style_body
))
story.append(Paragraph(
    'Bab 3 menyajikan hasil benchmarking algoritma per-target yang menjadi dasar pemilihan algoritma produksi: setiap dari ke-7 variabel target dilatih dengan algoritma yang terbukti memiliki performa rata-rata terbaik untuk variabel tersebut (lihat Bab 3.3), bukan satu algoritma seragam untuk semua. Karena Data Uji tetap murni tidak pernah dilihat model, angka akurasi yang dilaporkan pada Bab 3 dan 4 tetap valid sebagai perkiraan performa di kondisi nyata.',
    style_body
))

story.append(Paragraph('2. Fitur Input Model (Prediktor)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    f'Model ini menggunakan <b>{n_feature} fitur prediktor</b> per stasiun pengamatan, dirinci per kelompok pada tabel berikut. <b>Seluruh fitur berasal dari data pengamatan nyata stasiun</b> &ndash; tidak ada data sintetis atau simulasi. Sebagian dipakai langsung dari dataset, sebagian lagi hanyalah nilai pengamatan hari-hari sebelumnya yang disusun ulang (misalnya suhu kemarin atau rata-rata hujan 7 hari terakhir). Jumlah fitur dijaga tetap ringkas dan tidak berlebihan: menambah fitur yang tumpang tindih (mengulang informasi yang sama) justru meningkatkan risiko model "menghafal" data latih tanpa menambah kemampuan prediksi yang nyata.',
    style_body
))

feat_table_data = [
    [Paragraph('Kelompok Fitur', style_table_header), Paragraph('Fitur Spesifik', style_table_header), Paragraph('Jml', style_table_header), Paragraph('Alasan Ilmiah &amp; Meteorologi', style_table_header)],
    [Paragraph('<b>1. Lag Temporal</b>', style_table_cell_bold),
     Paragraph('<code>Lag 1, 3, 7</code> hari untuk 6 variabel target (Suhu, RH, Tekanan, Hujan, Radiasi, Angin)', style_table_cell),
     Paragraph('18', style_table_cell_center),
     Paragraph('Menangkap inersia termal permukaan dan autokorelasi jangka pendek atmosfer. Diterapkan simetris untuk seluruh 6 variabel &ndash; sama seperti rolling mean di bawah. Lag 2 hari dihapus karena informasinya tumpang tindih dengan lag 1 &amp; 3 hari (redundan).', style_table_cell)],
    [Paragraph('<b>2. Rolling Mean 7-Hari</b>', style_table_cell_bold),
     Paragraph('<code>roll_mean7</code> untuk 6 variabel target yang sama (simetris dengan grup Lag)', style_table_cell),
     Paragraph('6', style_table_cell_center),
     Paragraph('Meredam derau harian &amp; menangkap tren mingguan. Rolling 3-hari dihapus karena informasinya sudah tercakup oleh kombinasi lag 1&ndash;3 hari + rolling 7-hari (redundan, lihat analisis feature importance Bab 5).', style_table_cell)],
    [Paragraph('<b>3. Dinamika Tekanan &amp; Termal</b>', style_table_cell_bold),
     Paragraph('<code>&Delta;P = P(t-1) - P(t-2)</code>, <code>T_range = T_max - T_min</code>', style_table_cell),
     Paragraph('2', style_table_cell_center),
     Paragraph('Penurunan tekanan mendadak (&Delta;P negatif) biasanya menjadi tanda awal badai &amp; hujan lebat yang datang tiba-tiba.', style_table_cell)],
    [Paragraph('<b>4. Day of the Year</b>', style_table_cell_bold),
     Paragraph('<code>sin(2&pi; &times; DOY/365,25)</code>, <code>cos(2&pi; &times; DOY/365,25)</code>, dengan DOY = urutan hari dalam setahun (1&ndash;365)', style_table_cell),
     Paragraph('2', style_table_cell_center),
     Paragraph('Memodelkan posisi semu matahari &amp; pergeseran musim hujan/kemarau. Day of the Year diubah ke bentuk sin &amp; cos agar akhir tahun (hari ke-365) dan awal tahun (hari ke-1) dikenali sebagai hari yang berdekatan. Kolom <code>Bulan</code> dan nilai DOY mentah tidak dipakai karena informasinya sudah tercakup oleh sin/cos.', style_table_cell)],
    [Paragraph('<b>5. Fitur Langsung dari Dataset</b><br/>(dipakai langsung, tanpa dihitung ulang)', style_table_cell_bold),
     Paragraph('<code>wind_direction_name</code> hari berjalan (kategori Utara/Timur/Selatan/Barat)', style_table_cell),
     Paragraph('1', style_table_cell_center),
     Paragraph('Satu-satunya fitur yang dipakai apa adanya dari kolom dataset. Arah angin cenderung bertahan (persistence) dalam beberapa hari, sehingga arah angin hari ini menjadi petunjuk kuat untuk memprediksi arah angin hari-hari berikutnya.', style_table_cell)],
]
tbl_feat = Table(feat_table_data, colWidths=[95, 175, 25, 220])
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
    'Total fitur input model = 18 + 6 + 2 + 2 + 1 = <b>29</b>, terdiri dari <b>28 fitur turunan dari data pengamatan nyata</b> (nilai hari-hari sebelumnya, rata-rata 7 hari, &Delta;P, T_range, sin/cos Day of the Year) dan <b>1 fitur langsung dari dataset</b> (arah angin hari berjalan). <b>Nilai rata-rata harian hari berjalan (suhu, kelembapan, hujan, dll.) tidak dipakai langsung</b> &ndash; model melihat riwayat hari-hari sebelumnya (lag, rolling) dan kalender; dari hari berjalan hanya dipakai rentang suhu (T_range) dan arah angin.',
        title='RINGKASAN & JUSTIFIKASI JUMLAH FITUR'
))

story.append(Spacer(1, 5))
story.append(Paragraph('2.1 Kenapa Identitas Stasiun Tidak Dipakai sebagai Fitur', style_h2))
story.append(Paragraph(
    'Identitas atau ID stasiun sengaja <b>tidak</b> dijadikan salah satu input model, karena ID stasiun hanyalah pengenal unik, bukan variabel cuaca &ndash; jika dijadikan input, model berisiko sekadar "menghafal" pola per stasiun alih-alih mempelajari dinamika cuaca yang dapat digeneralisasi ke kondisi baru. Pendekatan <b>1 model global</b> tetap dipertahankan: seluruh 183 stasiun dilatih bersama dalam satu dataset gabungan, hanya identitas stasiun sebagai input yang tidak disertakan.',
    style_body
))

story.append(Paragraph('2.2 Daftar Lengkap Fitur Input Model', style_h2))
story.append(Paragraph(
    'Berikut seluruh 29 fitur yang menjadi input prediktor model (sama untuk semua target dan semua horizon H+1 s/d H+7). '
    'Nama kolom: <code>&lt;variabel&gt;_lag1/lag3/lag7</code> = nilai variabel tersebut 1, 3, dan 7 hari sebelumnya; '
    '<code>&lt;variabel&gt;_roll_mean7</code> = rata-rata 7 hari terakhir (hingga kemarin).',
    style_body
))
_feat_vars = [('Suhu Rata-rata', 'temp_avg'), ('Kelembapan', 'humidity_avg'), ('Tekanan Udara', 'pressure_avg_hpa'),
              ('Curah Hujan', 'rainfall_total_mm'), ('Radiasi Matahari', 'solar_radiation_avg'), ('Kecepatan Angin', 'wind_speed_avg')]
_list_rows = [[Paragraph('Variabel Dasar', style_table_header), Paragraph('Lag 1 hari', style_table_header), Paragraph('Lag 3 hari', style_table_header),
               Paragraph('Lag 7 hari', style_table_header), Paragraph('Rolling Mean 7-Hari', style_table_header)]]
for _lbl, _v in _feat_vars:
    _list_rows.append([Paragraph(f'<b>{_lbl}</b>', style_table_cell_bold)] +
                      [Paragraph(f'<code>{_v}_{_sfx}</code>', style_table_cell) for _sfx in ('lag1', 'lag3', 'lag7', 'roll_mean7')])
_list_rows += [
    [Paragraph('<b>Dinamika Tekanan &amp; Termal</b>', style_table_cell_bold), Paragraph('<code>delta_pressure_1d</code>', style_table_cell), Paragraph('<code>temp_range</code>', style_table_cell), '', ''],
    [Paragraph('<b>Day of the Year</b>', style_table_cell_bold), Paragraph('<code>sin_doy</code>', style_table_cell), Paragraph('<code>cos_doy</code>', style_table_cell), '', ''],
    [Paragraph('<b>Fitur Langsung dari Dataset</b>', style_table_cell_bold), Paragraph('<code>wind_direction_today_cat</code>', style_table_cell), '', '', ''],
]
tbl_featlist = Table(_list_rows, colWidths=[95, 95, 95, 95, 110])
tbl_featlist.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('SPAN', (3, -3), (4, -3)), ('SPAN', (3, -2), (4, -2)), ('SPAN', (1, -1), (4, -1)),
]))
story.append(tbl_featlist)
story.append(Spacer(1, 3))
story.append(Paragraph(
    '&Delta;P = tekanan kemarin dikurangi tekanan 2 hari lalu; T_range = suhu maksimum dikurangi suhu minimum (kolom data asli suhu max/min) pada hari berjalan (titik awal ramalan). '
    'Deep Learning (Bab 3.4) tidak memakai daftar fitur ini, melainkan jendela mentah 14 hari terakhir dari 6 variabel dasar.',
    style_body
))

story.append(PageBreak())

# ==================== CHAPTER 3 ====================
story.append(Paragraph('3. Benchmarking &amp; Seleksi Algoritma Model', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk memastikan pemilihan algoritma terbaik dan konsisten di seluruh horizon (bukan hanya H+1), dilakukan komparasi eksperimental antara model Linear (Ridge Regression untuk target angka, Logistic Regression untuk target kategori), Ensemble Tree (Random Forest), dan Gradient Boosted Trees (LightGBM) pada <b>horizon H+1 DAN H+7</b>, untuk <b>seluruh 7 variabel target produksi</b> (bukan hanya Curah Hujan seperti benchmark tahap sebelumnya) &ndash; sesuai catatan review bahwa algoritma terbaik untuk satu variabel belum tentu menjadi yang terbaik untuk variabel lain, sehingga pemilihan algoritma perlu dilakukan per-target. Algoritma juara regresi per variabel ditentukan dari rata-rata peringkat gabungan MAE, RMSE, dan R&sup2; (bukan MAE saja) supaya tidak salah memilih ketika satu algoritma hanya kalah tipis di MAE namun unggul di metrik lain (lihat Tabel 3.3).',
    style_body
))

story.append(Paragraph('3.1 Perbandingan Algoritma per Variabel Regresi (MAE, RMSE, R&sup2;)', style_h2))

bench_reg_rows = [
    [Paragraph('Variabel', style_table_header), Paragraph('Horizon', style_table_header), Paragraph('Algoritma', style_table_header),
     Paragraph('MAE', style_table_header), Paragraph('RMSE', style_table_header), Paragraph('R&sup2;', style_table_header),
     Paragraph('Waktu (s)', style_table_header)],
]
reg_highlight_rows = []
row_i = 0
for var in REG_VARS:
    for h in [1, 7]:
        sub = df_bench_reg[(df_bench_reg['Variabel'] == var) & (df_bench_reg['Horizon'] == f'H+{h}')]
        sub = sub.set_index('Algoritma').loc[REG_ALGO_ORDER].reset_index()
        # Kriteria "Terbaik" per baris: rata-rata peringkat gabungan MAE+RMSE+R2
        # (bukan MAE saja) - konsisten dengan kriteria juara Tabel 3.3.
        combined_rank = sub['MAE'].rank() + sub['RMSE'].rank() + sub['R2'].rank(ascending=False)
        best_algo = sub.loc[combined_rank.idxmin(), 'Algoritma']
        for _, r in sub.iterrows():
            row_i += 1
            is_best = r['Algoritma'] == best_algo
            if is_best:
                reg_highlight_rows.append(row_i)
            cs = style_table_cell_bold if is_best else style_table_cell
            bench_reg_rows.append([
                Paragraph(f"<b>{REG_LABELS[var]}</b>", style_table_cell_bold),
                Paragraph(f'H+{h}', style_table_cell_center),
                Paragraph((r['Algoritma'] + ' (Terbaik)') if is_best else r['Algoritma'], cs),
                Paragraph(f"{r['MAE']:.3f}", style_table_cell_center),
                Paragraph(f"{r['RMSE']:.3f}", style_table_cell_center),
                Paragraph(f"{r['R2']:.3f}", style_table_cell_center),
                Paragraph(f"{r['Training_s']:.2f}", style_table_cell_center),
            ])

tbl_bench_reg_style = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTSIZE', (0, 0), (-1, -1), 6.8),
]
for ridx in reg_highlight_rows:
    tbl_bench_reg_style.append(('BACKGROUND', (0, ridx), (-1, ridx), COLOR_BG_ACCENT))

tbl_bench_reg = Table(bench_reg_rows, colWidths=[75, 35, 155, 50, 50, 45, 45], repeatRows=1)
tbl_bench_reg.setStyle(TableStyle(tbl_bench_reg_style))
story.append(tbl_bench_reg)

story.append(Paragraph('3.2 Perbandingan Algoritma Klasifikasi Arah Mata Angin (Accuracy, Precision, Recall, F1-Score)', style_h2))
story.append(Paragraph(
    'Karena Arah Mata Angin adalah target kategori (4 kelas: Utara/Timur/Selatan/Barat), evaluasinya dibedakan dari target regresi &ndash; memakai Accuracy, Precision, Recall, dan F1-Score (rata-rata makro di seluruh kelas), bukan MAE/RMSE.',
    style_body
))

bench_clf_rows = [
    [Paragraph('Horizon', style_table_header), Paragraph('Algoritma', style_table_header), Paragraph('Accuracy', style_table_header),
     Paragraph('Precision (Macro)', style_table_header), Paragraph('Recall (Macro)', style_table_header), Paragraph('F1 (Macro)', style_table_header), Paragraph('Waktu (s)', style_table_header)],
]
clf_highlight_rows = []
row_i = 0
for h in [1, 7]:
    sub = df_bench_clf[df_bench_clf['Horizon'] == f'H+{h}'].set_index('Algoritma').loc[CLF_ALGO_ORDER].reset_index()
    best_algo = sub.loc[sub['F1_Macro'].idxmax(), 'Algoritma']
    for _, r in sub.iterrows():
        row_i += 1
        is_best = r['Algoritma'] == best_algo
        if is_best:
            clf_highlight_rows.append(row_i)
        cs = style_table_cell_bold if is_best else style_table_cell
        bench_clf_rows.append([
            Paragraph(f'<b>H+{h}</b>', style_table_cell_bold),
            Paragraph((r['Algoritma'] + ' (Terbaik)') if is_best else r['Algoritma'], cs),
            Paragraph(f"{r['Accuracy']*100:.1f}%", style_table_cell_center),
            Paragraph(f"{r['Precision_Macro']*100:.1f}%", style_table_cell_center),
            Paragraph(f"{r['Recall_Macro']*100:.1f}%", style_table_cell_center),
            Paragraph(f"{r['F1_Macro']*100:.1f}%", style_table_cell_center),
            Paragraph(f"{r['Training_s']:.2f}", style_table_cell_center),
        ])

tbl_bench_clf_style = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
for ridx in clf_highlight_rows:
    tbl_bench_clf_style.append(('BACKGROUND', (0, ridx), (-1, ridx), COLOR_BG_ACCENT))

tbl_bench_clf = Table(bench_clf_rows, colWidths=[45, 150, 60, 75, 70, 65, 50])
tbl_bench_clf.setStyle(TableStyle(tbl_bench_clf_style))
story.append(tbl_bench_clf)

story.append(Spacer(1, 6))
story.append(Paragraph('3.3 Ringkasan Seleksi Algoritma Terbaik per Target', style_h2))
story.append(Paragraph(
    'Algoritma terpilih per variabel ditentukan dari rata-rata peringkat gabungan MAE+RMSE+R&sup2; (regresi) atau F1-Macro (klasifikasi) di kedua horizon H+1 &amp; H+7 pada Tabel 3.1/3.2 di atas &ndash; sesuai catatan review bahwa pemilihan algoritma harus dilakukan untuk masing-masing target, bukan satu algoritma yang sama dipaksakan untuk semua variabel:',
    style_body
))

champion_summary_rows = [
    [Paragraph('Variabel Target', style_table_header), Paragraph('Algoritma Terbaik (Rata-rata Peringkat H+1 &amp; H+7)', style_table_header),
     Paragraph('MAE / Accuracy H+1', style_table_header), Paragraph('MAE / Accuracy H+7', style_table_header)],
]
n_lgb_wins = 0
for var in REG_VARS:
    champ = champion_algo_regresi(var)
    if champ == 'LightGBM (Gradient Boosting)':
        n_lgb_wins += 1
    r1 = df_bench_reg[(df_bench_reg['Variabel'] == var) & (df_bench_reg['Horizon'] == 'H+1') & (df_bench_reg['Algoritma'] == champ)].iloc[0]
    r7 = df_bench_reg[(df_bench_reg['Variabel'] == var) & (df_bench_reg['Horizon'] == 'H+7') & (df_bench_reg['Algoritma'] == champ)].iloc[0]
    champion_summary_rows.append([
        Paragraph(f'<b>{REG_LABELS[var]}</b>', style_table_cell_bold),
        Paragraph(champ, style_table_cell),
        Paragraph(f"MAE {r1['MAE']:.3f}", style_table_cell_center),
        Paragraph(f"MAE {r7['MAE']:.3f}", style_table_cell_center),
    ])
champ_clf = champion_algo_klasifikasi()
if champ_clf == 'LightGBM (Gradient Boosting)':
    n_lgb_wins += 1
c1 = df_bench_clf[(df_bench_clf['Horizon'] == 'H+1') & (df_bench_clf['Algoritma'] == champ_clf)].iloc[0]
c7 = df_bench_clf[(df_bench_clf['Horizon'] == 'H+7') & (df_bench_clf['Algoritma'] == champ_clf)].iloc[0]
champion_summary_rows.append([
    Paragraph('<b>Arah Mata Angin (Klasifikasi)</b>', style_table_cell_bold),
    Paragraph(champ_clf, style_table_cell),
    Paragraph(f"Accuracy {c1['Accuracy']*100:.1f}%<br/>(F1 {c1['F1_Macro']*100:.1f}%)", style_table_cell_center),
    Paragraph(f"Accuracy {c7['Accuracy']*100:.1f}%<br/>(F1 {c7['F1_Macro']*100:.1f}%)", style_table_cell_center),
])

tbl_champ = Table(champion_summary_rows, colWidths=[110, 210, 90, 90])
tbl_champ.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 1), (-1, -1), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_champ)

n_total_targets = len(REG_VARS) + 1
story.append(Spacer(1, 4))
_champ_by_algo = {}
for _v in REG_VARS:
    _champ_by_algo.setdefault(champion_algo_regresi(_v), []).append(REG_LABELS[_v])
_champ_by_algo.setdefault(champ_clf, []).append('Arah Mata Angin')
_champ_txt = '; '.join(f"<b>{a}</b>: {', '.join(v)}" for a, v in _champ_by_algo.items())
story.append(Paragraph(
    f'<b>Temuan Penting:</b> Algoritma yang terpilih sebagai model produksi per target adalah &ndash; {_champ_txt}. '
    'Algoritma yang tidak menjadi juara pada target mana pun hanya berperan sebagai pembanding dan tidak dipakai di produksi. '
    'Ini menegaskan bahwa <b>tidak ada satu algoritma yang unggul untuk seluruh variabel sekaligus</b>. '
    'Logistic Regression hanya relevan untuk target klasifikasi (Arah Mata Angin); Ridge Regression untuk target regresi. '
    'Untuk Arah Mata Angin, kolom tabel menampilkan Accuracy (utama) dan F1-Macro (dalam kurung); juara tetap dipilih dari F1-Macro '
    'karena distribusi kelas tidak seimbang (kelas "Selatan" mayoritas).',
    style_body
))
story.append(Paragraph(
    '<b>Rekomendasi tindak lanjut:</b> Berdasarkan Tabel 3.3, sistem produksi saat ini melatih setiap dari 7 target dengan algoritma juaranya masing-masing sebagaimana tercantum pada tabel di atas (bukan LightGBM seragam untuk seluruh target) &ndash; Bab 4 menyajikan evaluasi performa aktual dari konfigurasi ini pada data uji 30 hari.',
    style_body
))

story.append(PageBreak())
story.append(Paragraph('3.4 Perbandingan dengan Deep Learning (LSTM, GRU)', style_h2))
story.append(Paragraph(
    'Bab 3.1-3.3 membandingkan 3 algoritma <i>Machine Learning</i> (ML) tabular. Sebagai pelengkap, dilakukan juga eksperimen dengan '
    '2 algoritma <i>Deep Learning</i> (DL) berbasis deret waktu &ndash; LSTM dan GRU &ndash; untuk menjawab pertanyaan riset "apakah pendekatan '
    'deep learning bisa mengungguli model ML tabular untuk data cuaca ini?". Berbeda dari ML yang memakai 29 fitur riwayat dan kalender (Bab 2), '
    'DL memakai input mentah berupa jendela deret waktu 14 hari terakhir dari 6 variabel cuaca dasar (tanpa fitur lag/rolling manual) &ndash; '
    'arsitektur RNN memang dirancang mempelajari pola temporal langsung dari data mentah.',
    style_body
))
story.append(make_callout_box(
    'DL (LSTM, GRU) di sini dilatih hanya <b>10 epoch</b> demi kepraktisan waktu komputasi (14 indikator&times;horizon &times; 2 arsitektur RNN '
    'di CPU) &ndash; jumlah ini <b>tidak diuji dengan kurva konvergensi loss</b>, sehingga hasil DL pada bab ini bersifat <b>indikatif</b> '
    '(gambaran kasar potensi pendekatan sequence-based), <u>bukan</u> hasil akhir yang sudah dioptimalkan penuh. DL <u>tidak</u> dipakai sebagai '
    'kandidat model produksi meski menang di beberapa indikator di bawah &ndash; model PyTorch tidak disimpan ke disk maupun diintegrasikan ke '
    'jalur inferensi produksi (`retrain_pipeline.py`), sehingga hanya algoritma ML yang dibandingkan di Bab 3 (LightGBM, Ridge Regression untuk regresi, Logistic Regression untuk klasifikasi, dan Random Forest) '
    'yang dapat dipakai sebagai model produksi, dan yang benar-benar dipakai adalah juara per target pada Tabel 3.3.',
    title='KETERBATASAN & CAKUPAN EKSPERIMEN DL'
))

fig_m1_p = os.path.join(fig_dir, '..', 'figures_benchmark', 'fig_merged1_5algo_mae_grid.png')
if os.path.exists(fig_m1_p):
    story.append(Image(fig_m1_p, width=16.5 * cm, height=9.3 * cm))
    story.append(Paragraph('<b>Gambar 1:</b> Perbandingan MAE 5 Algoritma (3 ML + 2 DL) per Indikator Regresi, H+1. Kotak hitam menandai MAE terendah.', style_caption))

fig_m2_p = os.path.join(fig_dir, '..', 'figures_benchmark', 'fig_merged2_wind_classification.png')
if os.path.exists(fig_m2_p):
    story.append(Image(fig_m2_p, width=14.5 * cm, height=6.5 * cm))
    story.append(Paragraph('<b>Gambar 2:</b> Accuracy &amp; F1-Macro Klasifikasi Arah Mata Angin, 5 Algoritma, H+1 &amp; H+7.', style_caption))

story.append(PageBreak())
story.append(Paragraph(
    'Tabel berikut merangkum algoritma juara per indikator dari dua sudut pandang: <b>(1) Juara dari seluruh 5 algoritma</b> (ML+DL, murni '
    'informasional/riset) dan <b>(2) Juara Deployable</b> &ndash; juara terbaik yang benar-benar bisa dipakai produksi, hanya dari algoritma ML di Bab 3. '
    'Kriteria juara sama seperti Tabel 3.3: rata-rata peringkat gabungan MAE+RMSE+R&sup2; (regresi) atau F1-Macro (klasifikasi), dihitung dari '
    '<b>kedua horizon H+1 dan H+7 sekaligus</b> (bukan H+1 saja).',
    style_body
))

dl_summary_rows = [[Paragraph('Variabel Target', style_table_header), Paragraph('Juara dari 5 Algoritma<br/>(ML+DL, Informasional)', style_table_header),
                     Paragraph('Juara Deployable<br/>(ML saja, Dipakai Produksi)', style_table_header)]]
dl_style_cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 3.5), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
n_dl_wins = 0
DEPLOYABLE_ALGOS = REG_ALGO_ORDER
for var in REG_VARS:
    sub_all = df_merged_reg[df_merged_reg['Variabel'] == var]
    champ_all = multi_metric_rank(sub_all).index[0]
    sub_ml = sub_all[sub_all['Algoritma'].isin(DEPLOYABLE_ALGOS)]
    champ_ml = multi_metric_rank(sub_ml).index[0]
    is_dl = champ_all not in DEPLOYABLE_ALGOS
    if is_dl:
        n_dl_wins += 1
    dl_summary_rows.append([
        Paragraph(f'<b>{REG_LABELS[var]}</b>', style_table_cell_bold),
        Paragraph(('<b>' + champ_all + '</b>') if is_dl else champ_all, style_table_cell_bold if is_dl else style_table_cell),
        Paragraph(champ_ml, style_table_cell),
    ])
piv_c_all = df_merged_clf.pivot(index='Algoritma', columns='Horizon', values='F1_Macro')
champ_clf_all = piv_c_all.rank(axis=0, ascending=False).mean(axis=1).sort_values().index[0]
piv_c_ml = df_merged_clf[df_merged_clf['Algoritma'].isin(CLF_ALGO_ORDER)].pivot(index='Algoritma', columns='Horizon', values='F1_Macro')
champ_clf_ml = piv_c_ml.rank(axis=0, ascending=False).mean(axis=1).sort_values().index[0]
is_dl_clf = champ_clf_all not in CLF_ALGO_ORDER
if is_dl_clf:
    n_dl_wins += 1
dl_summary_rows.append([
    Paragraph('<b>Arah Mata Angin (Klasifikasi)</b>', style_table_cell_bold),
    Paragraph(('<b>' + champ_clf_all + '</b>') if is_dl_clf else champ_clf_all, style_table_cell_bold if is_dl_clf else style_table_cell),
    Paragraph(champ_clf_ml, style_table_cell),
])
tbl_dl_summary = Table(dl_summary_rows, colWidths=[130, 190, 190])
tbl_dl_summary.setStyle(TableStyle(dl_style_cmds))
story.append(tbl_dl_summary)
story.append(Spacer(1, 5))
story.append(Paragraph(
    f'<b>Temuan:</b> Dari {n_total_targets} indikator, algoritma DL (LSTM/GRU) unggul di {n_dl_wins} indikator ketika seluruh 5 algoritma '
    f'diikutsertakan &ndash; menunjukkan pendekatan sequence-based punya potensi nyata untuk data cuaca ini. Namun karena keterbatasan cakupan '
    'eksperimen (Kotak Catatan di atas) dan DL belum terintegrasi ke jalur produksi, kolom "Juara Deployable" &ndash; identik dengan Tabel 3.3 '
    'Bab 3.3 &ndash; tetap menjadi acuan algoritma yang benar-benar dipakai sistem produksi saat ini.',
    style_body
))

fig_m3_p = os.path.join(fig_dir, '..', 'figures_benchmark', 'fig_merged3_pareto_rain.png')
if os.path.exists(fig_m3_p):
    story.append(Image(fig_m3_p, width=11.5 * cm, height=8.6 * cm))
    story.append(Paragraph('<b>Gambar 3:</b> Waktu Latih vs MAE, Curah Hujan (H+1), 5 Algoritma.', style_caption))

story.append(PageBreak())
story.append(Paragraph('4. Evaluasi Performa Multi-Horizon (H+1 s/d H+7)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    f'Evaluasi performa produksi (Bab ini) menggunakan model <b>produksi aktual</b> &ndash; masing-masing dari 7 variabel dilatih dengan algoritma juaranya sendiri sesuai Tabel 3.3 di Bab 3 (bukan LightGBM seragam) &ndash; dievaluasi pada data uji 30 hari terakhir (21 Juli 2026 &ndash; 19 Agustus 2026, &plusmn;{n_test_ref:,} titik sampel pengamatan aktual per target) untuk <b>seluruh 7 variabel target produksi</b>:',
    style_body
))

metrics_table_data = [
    [Paragraph('Horizon', style_table_header)] + [Paragraph(f'{lbl}<br/>MAE', style_table_header) for lbl in REG_LABELS.values()] + [Paragraph('Arah Angin<br/>Accuracy', style_table_header)],
]
for h in range(1, 8):
    row = [Paragraph(f'<b>H+{h}</b>', style_table_cell_bold)]
    for var in REG_VARS:
        row.append(Paragraph(f"{metrics[f'{var}_h{h}']['MAE']:.3f}", style_table_cell_center))
    row.append(Paragraph(f"{metrics[f'wind_direction_name_h{h}']['Accuracy']*100:.1f}%", style_table_cell_center))
    metrics_table_data.append(row)

tbl_metrics = Table(metrics_table_data, colWidths=[40, 62, 58, 58, 65, 62, 62, 55])
tbl_metrics.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTSIZE', (0, 0), (-1, -1), 6.8),
]))
story.append(tbl_metrics)
story.append(Spacer(1, 3))
story.append(Paragraph(
    'Catatan satuan MAE: Suhu (&deg;C), Kelembapan (%), Curah Hujan (mm), Radiasi Matahari (W/m&sup2;, rata-rata harian), Tekanan Udara (hPa), Kecepatan Angin (km/h). Arah Mata Angin dievaluasi dengan Accuracy klasifikasi 4-kelas (baseline kelas mayoritas "Selatan" &asymp; 56.8%). Radiasi Matahari dimodelkan sebagai <b>rata-rata harian</b> dari seluruh pembacaan sensor (median &plusmn;166 W/m&sup2;), bukan jumlah pembacaan, supaya nilainya tidak bergantung pada banyaknya pembacaan per hari. R&sup2; radiasi relatif lebih rendah dibanding suhu atau tekanan karena radiasi sangat dipengaruhi tutupan awan yang berubah cepat dan sulit diramal beberapa hari ke depan.',
    style_body
))

story.append(Spacer(1, 5))
fig1_p = os.path.join(fig_dir, 'fig_model1_horizon_performance.png')
if os.path.exists(fig1_p):
    story.append(Image(fig1_p, width=17.0*cm, height=9.0*cm))
    story.append(Paragraph('<b>Gambar 4:</b> Kurva Peluruhan Error Prediksi (MAE) per Horizon H+1 s/d H+7 untuk 6 Target Regresi.', style_caption))

fig1b_p = os.path.join(fig_dir, 'fig_model1b_wind_direction_performance.png')
if os.path.exists(fig1b_p):
    story.append(Image(fig1b_p, width=11.0*cm, height=7.01*cm))
    story.append(Paragraph('<b>Gambar 5:</b> Accuracy &amp; F1-Macro Klasifikasi Arah Mata Angin per Horizon vs Baseline Kelas Mayoritas (Model Produksi).', style_caption))

story.append(PageBreak())

# ==================== CHAPTER 5 & 6 ====================
story.append(Paragraph('5. Analisis Kepentingan Fitur (Feature Importance)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    f'Berikut tingkat kontribusi setiap fitur pada model, dihitung terpisah untuk <b>masing-masing dari 7 variabel target</b> memakai algoritma juaranya sendiri sesuai Tabel 3.3. Metode yang dipakai seragam untuk semua algoritma, yaitu <b>permutation importance</b> pada data uji 30 hari: nilai satu fitur diacak (5 kali pengulangan), lalu dicatat seberapa besar error model naik (MAE untuk regresi) atau F1-Macro turun (klasifikasi). Makin besar penurunan performa, makin penting fitur tersebut. Metode ini dipilih karena Ridge/Logistic Regression tidak punya importance bawaan, dan koefisien, gain, atau <i>feature_importances_</i> tidak sebanding antar-algoritma. Dalam satuan error, nilai importance tetap berbeda skala antar variabel, jadi perbandingan dilakukan per-variabel (fitur mana yang dominan):',
    style_body
))

fig2_p = os.path.join(fig_dir, 'fig_model2_feature_importance.png')
if os.path.exists(fig2_p):
    story.append(Image(fig2_p, width=17.0*cm, height=7.7*cm))
    story.append(Paragraph('<b>Gambar 6:</b> Top 10 Fitur Paling Berpengaruh per Variabel Target (H+1), 7 Variabel dengan Algoritma Juaranya Masing-Masing.', style_caption))

temp_top5 = top_features('temp_avg_h1')
rain_top5 = top_features('rainfall_total_mm_h1')
winddir_top5 = top_features('wind_direction_name_h1')
story.append(Paragraph(
    f'&bull; <b>Prediktor Suhu Utama (5 fitur paling berpengaruh, {algo_used["temp_avg_h1"]}):</b> {fmt_feature_list(temp_top5)} &ndash; menunjukkan bahwa fitur yang ringkas ({n_feature}) tetap menangkap sinyal utama cuaca (inersia suhu dan tekanan udara) tanpa memerlukan fitur berlebih, dan tanpa bergantung pada identitas stasiun (Bab 2.1).<br/>'
    f'&bull; <b>Prediktor Hujan Utama (5 fitur paling berpengaruh, {algo_used["rainfall_total_mm_h1"]}):</b> {fmt_feature_list(rain_top5)} &ndash; sejalan dengan keterkaitan yang lemah antar variabel cuaca pada hari yang sama untuk hujan, sinyal prediktif justru berasal dari pola perubahan pada hari-hari sebelumnya, bukan nilai variabel cuaca hari yang sama.<br/>'
    f'&bull; <b>Prediktor Arah Angin Utama (5 fitur paling berpengaruh, {algo_used["wind_direction_name_h1"]}):</b> {fmt_feature_list(winddir_top5)} &ndash; arah angin hari berjalan (persistence) diperkirakan mendominasi karena arah angin cenderung tidak berubah drastis dalam rentang beberapa hari. Rincian variabel lain tersedia pada Gambar 6.',
    style_body
))

story.append(Spacer(1, 5))

story.append(Paragraph('6. Pengujian Deret Waktu Lapangan', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))
story.append(Paragraph('6.1 Pengujian Rolling H+1 (10 Stasiun)', style_h2))

with open(os.path.join(fig_dir, 'fig_model3_stations.json'), 'r', encoding='utf-8') as f:
    _fig3_meta = json.load(f)
fig3_station_ids = _fig3_meta['station_ids']
fig3_files = _fig3_meta['files']

story.append(Paragraph(
    f'Gambar 7 di bawah menampilkan perbandingan deret waktu aktual-vs-prediksi untuk <b>keenam target angka</b>, masing-masing memakai algoritma juaranya sendiri sesuai Tabel 3.3, pada <b>{len(fig3_station_ids)} stasiun</b> dengan data uji paling lengkap pada jendela 30 hari terakhir (Stasiun AWS {", ".join(fig3_station_ids)}) &ndash; dipilih supaya perbandingan tetap representatif, bukan stasiun dengan hanya sedikit hari uji yang valid. Pengujian Arah Mata Angin (target kategori) disajikan secara terpisah lewat metrik Accuracy, Precision, Recall, dan F1-Score pada Bab 3.2 dan 4.',
    style_body
))

for i, (stn_id, fname) in enumerate(zip(fig3_station_ids, fig3_files), start=1):
    fig3_p = os.path.join(fig_dir, fname)
    if os.path.exists(fig3_p):
        story.append(Image(fig3_p, width=17.0*cm, height=9.04*cm))
        story.append(Paragraph(f'<b>Gambar 7.{i}:</b> Perbandingan Deret Waktu Harian Aktual vs Prediksi Model (H+1) untuk 6 Target Regresi pada Stasiun AWS {stn_id} (Periode Uji 30 Hari: 21 Juli s/d 19 Agustus 2026).', style_caption))
        story.append(PageBreak())

story.append(Paragraph('6.2 Showcase Trajektori Ramalan H+1 s/d H+7', style_h2))
with open(os.path.join(fig_dir, '..', 'figures_benchmark', 'fig_merged4_stations.json'), 'r', encoding='utf-8') as f:
    _traj_meta = json.load(f)
traj_issue_date = _traj_meta['issue_date']
traj_station_ids = _traj_meta['station_ids']
traj_files = _traj_meta['files']
story.append(Paragraph(
    f'Gambar 7 di atas menunjukkan performa H+1 yang diulang (<i>rolling</i>) di banyak tanggal pengujian berbeda. Sebagai pelengkap, berikut '
    f'contoh <b>satu kali proses ramal</b> yang diambil dari tanggal {traj_issue_date} (dalam periode uji 30 hari) &ndash; model menghasilkan '
    f'ramalan H+1 s/d H+7 sekaligus dari observasi hari itu, dibandingkan langsung dengan realisasi cuaca aktual 7 hari berikutnya ({traj_issue_date} '
    f's/d 19 Agustus 2026) yang sudah tersedia di data historis. Setiap indikator memakai algoritma produksinya sendiri (Tabel 3.3) pada '
    f'<b>{len(traj_station_ids)} stasiun</b> (Stasiun AWS {", ".join(traj_station_ids)}). Pola umum yang terlihat: garis prediksi cenderung lebih '
    'landai/stabil dibanding realisasi aktual yang lebih berfluktuasi hari-ke-hari &ndash; wajar karena model meramalkan nilai ekspektasi, bukan '
    'menebak fluktuasi cuaca jangka pendek yang secara inheren sulit diprediksi 7 hari ke depan.',
    style_body
))
for i, (stn_id, fname) in enumerate(zip(traj_station_ids, traj_files), start=1):
    p_traj = os.path.join(fig_dir, '..', 'figures_benchmark', fname)
    if os.path.exists(p_traj):
        story.append(Image(p_traj, width=17.0 * cm, height=8.94 * cm))
        story.append(Paragraph(f'<b>Gambar 8.{i}:</b> Trajektori Ramalan H+1 s/d H+7 vs Realisasi Aktual, Stasiun AWS {stn_id} (Titik Ramal: {traj_issue_date}).', style_caption))
        story.append(PageBreak())

# ==================== CHAPTER 7 & 8 ====================
story.append(Paragraph('7. Implementasi Output Ramalan Cuaca 7 Hari per Stasiun', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Model yang telah disimpan dapat langsung dipakai untuk menghasilkan ramalan 7 hari ke depan pada stasiun mana pun. Berikut adalah <b>hasil ramalan nyata (bukan simulasi)</b> pada <b>Stasiun AWS 222 &ndash; Rambutan</b>, dihitung menggunakan observasi riil terakhir stasiun tersebut:',
    style_body
))

fc_rows = [[
    Paragraph('Horizon / Tanggal', style_table_header), Paragraph('Kondisi', style_table_header),
    Paragraph('Suhu', style_table_header), Paragraph('Kelembapan', style_table_header),
    Paragraph('Hujan', style_table_header), Paragraph('Radiasi', style_table_header),
    Paragraph('Tekanan', style_table_header), Paragraph('Angin', style_table_header),
    Paragraph('Arah', style_table_header),
]]
for _, r in fc_df.iterrows():
    fc_rows.append([
        Paragraph(f"<b>{r['Day']}</b> ({r['Date']})", style_table_cell),
        Paragraph(str(r['Condition']), style_table_cell_center),
        Paragraph(f"{r['Temp_Avg_C']} &deg;C", style_table_cell_center),
        Paragraph(f"{r['Humidity_Avg_Pct']} %", style_table_cell_center),
        Paragraph(f"{r['Rain_Total_mm']} mm", style_table_cell_center),
        Paragraph(f"{r['Solar_Wm2']:.0f} W/m&sup2;", style_table_cell_center),
        Paragraph(f"{r['Pressure_hPa']} hPa", style_table_cell_center),
        Paragraph(f"{r['Wind_Speed_kmh']} km/h", style_table_cell_center),
        Paragraph(str(r['Wind_Direction']), style_table_cell_center),
    ])

tbl_fc = Table(fc_rows, colWidths=[85, 55, 42, 48, 42, 55, 45, 42, 42])
tbl_fc.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTSIZE', (0, 0), (-1, -1), 6.8),
]))
story.append(tbl_fc)
story.append(Paragraph(
    '<i>Catatan: seluruh 7 kolom nilai di atas adalah keluaran langsung dari model untuk setiap horizon. Kondisi cuaca (Cerah Berawan/Hujan Ringan/Sedang/Lebat) diturunkan langsung dari nilai prediksi Curah Hujan (mm) menggunakan ambang batas standar BMKG.</i>',
    style_caption
))

story.append(Spacer(1, 6))

story.append(Paragraph('8. Kesimpulan &amp; Panduan Operasionalisasi Produksi', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    f'Tahap pelatihan dan validasi model prediksi cuaca 7 hari mencakup 7 variabel operasional dengan {n_feature} fitur prediktor, benchmarking algoritma pada horizon H+1 <b>dan</b> H+7, serta validasi lapangan (Bab 6) yang mencakup seluruh 7 indikator utama. Hasil tahap ini meliputi:',
    style_body
))

art_data = [
    [Paragraph('Hasil', style_table_header), Paragraph('Bentuk', style_table_header), Paragraph('Peran &amp; Deskripsi Fungsional', style_table_header)],
    [Paragraph('<b>Model Prediksi Terlatih</b>', style_table_cell_bold), Paragraph(f'{model_size_mb:.1f} MB', style_table_cell), Paragraph(f'Model produksi berisi {n_target} sub-model ({7*6} regresi &amp; {7} klasifikasi arah angin) untuk 7 horizon waktu ke depan.', style_table_cell)],
    [Paragraph('<b>Program Pelatihan Ulang</b>', style_table_cell_bold), Paragraph('Program otomatis', style_table_cell), Paragraph('Program yang dapat melatih ulang model secara otomatis serta menghasilkan ramalan 7 hari untuk stasiun mana pun.', style_table_cell)],
    [Paragraph('<b>Perbandingan Algoritma</b>', style_table_cell_bold), Paragraph('Program analisis', style_table_cell), Paragraph('Program pembanding 5 algoritma (LightGBM, Ridge Regression/Logistic Regression, Random Forest, LSTM, GRU) untuk seluruh 7 variabel target di H+1 &amp; H+7 (Bab 3.4); algoritma produksi tetap dipilih hanya dari 3 ML yang bisa di-deploy (Bab 3.3).', style_table_cell)],
    [Paragraph('<b>Grafik Evaluasi</b>', style_table_cell_bold), Paragraph('21 gambar resolusi tinggi', style_table_cell), Paragraph('Kurva performa per horizon (regresi & arah angin), perbandingan 5 algoritma (ML+DL), tingkat kepentingan fitur per variabel, perbandingan deret waktu aktual vs prediksi pada 10 stasiun, dan trajektori ramalan H+1-H+7 pada 5 stasiun.', style_table_cell)],
]
tbl_art = Table(art_data, colWidths=[145, 105, 265])
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
    'Model ini siap dihubungkan ke tahap perbandingan dengan layanan cuaca Open-Meteo dan tahap penyajian ramalan lewat dashboard website untuk seluruh kebun binaan PPKS. Target &amp; fitur yang ringkas mempermudah pemahaman dan pemeliharaan model jangka panjang.',
    title='KESIAPAN TAHAP SELANJUTNYA'
))

story.append(Spacer(1, 10))
sig_data = [
    [Paragraph('<b>Disiapkan Oleh:</b><br/><br/><br/><u><b>Yudha</b></u><br/>Data Analyst NusaKlim PPKS', style_table_cell),
     Paragraph('<b>Diverifikasi Oleh:</b><br/><br/><br/><u><b>Cut Mardiana</b></u><br/>Asisten TI', style_table_cell),
     Paragraph('<b>Disetujui Oleh:</b><br/><br/><br/><u><b>Iput Pradiko</b></u><br/>Peneliti NusaKlim', style_table_cell)]
]
tbl_sig = Table(sig_data, colWidths=[172, 172, 171])
tbl_sig.setStyle(TableStyle([
    ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 6),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_sig)

print('Building Model Training Report PDF...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
