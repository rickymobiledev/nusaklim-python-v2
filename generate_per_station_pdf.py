import os, sys, json
import numpy as np
import pandas as pd
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
pdf_path = os.path.join(BASE_DIR, 'report', '3b.Laporan_Analisis_Model_Per_Stasiun_vs_Global_PPKS.pdf')
fig_dir = os.path.join(BASE_DIR, 'figures_per_station')

sys.path.insert(0, BASE_DIR)
from retrain_pipeline import REGRESSION_TARGETS, CLASSIFICATION_TARGET
from local_vs_global_stats import station_wins, recommend

with open(os.path.join(BASE_DIR, 'local_benchmark_v3.json'), encoding='utf-8') as f:
    LOCAL = json.load(f)
with open(os.path.join(BASE_DIR, 'station_sampling.json'), encoding='utf-8') as f:
    SAMPLING = json.load(f)

ALGO_USED = LOCAL['algo_used']  # per-indikator: algoritma juara produksi (Tabel 3.3 Laporan 3), dipakai sbg algoritma Model Lokal
INDICATORS = list(REGRESSION_TARGETS.items()) + [(CLASSIFICATION_TARGET, 'Arah Mata Angin')]
_algos = []
for _a in ALGO_USED.values():
    if _a not in _algos:
        _algos.append(_a)
ALGO_TEXT = ' dan '.join(_algos)


def idn(n):
    return f'{n:,}'.replace(',', '.')


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
        self.drawRightString(555, 805, 'Laporan Analisis Model Per-Stasiun vs Global')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, f'Laporan Model Individu (Lokal) vs Global: {len(LOCAL["stations"])} Stasiun, 7 Indikator, ML')
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

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=18, leading=23, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=10)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Arial', fontSize=10.5, leading=14.5, textColor=COLOR_BODY, alignment=1, spaceAfter=18)
style_cover_meta = ParagraphStyle('CoverMeta', parent=styles['Normal'], fontName='Arial', fontSize=8.5, leading=12, textColor=COLOR_MUTED, alignment=1)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Arial-Bold', fontSize=12, leading=15, textColor=COLOR_PRIMARY, spaceBefore=9, spaceAfter=4, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Arial-Bold', fontSize=9.5, leading=12.5, textColor=COLOR_SECONDARY, spaceBefore=7, spaceAfter=3, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Arial', fontSize=8.2, leading=11.8, textColor=COLOR_BODY, spaceAfter=4, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Arial-Italic', fontSize=7.8, leading=11, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.3, leading=9.2, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Arial', fontSize=7.1, leading=9.0, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.1, leading=9.0, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Arial', fontSize=7.1, leading=9.0, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=9.5, textColor=COLOR_MUTED, alignment=1, spaceBefore=2, spaceAfter=6)

def make_callout_box(text, title='CATATAN PENTING & INSIGHT', width=515):
    p_title = Paragraph(f'<b>{title}</b>', ParagraphStyle('CT', fontName='Arial-Bold', fontSize=7.8, leading=10, textColor=COLOR_PRIMARY, spaceAfter=2))
    p_text = Paragraph(text, style_callout)
    tbl = Table([[p_title], [p_text]], colWidths=[width])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_ACCENT), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 4.5), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl

# ---------------------------------------------------------------- Precompute summary stats
def is_clf(var):
    return var == CLASSIFICATION_TARGET


def multi_metric_winner(local_m, global_m, is_classification):
    """Kriteria sama dengan Laporan 3/4: menang jika unggul di >=2 dari 3 metrik
    (MAE+RMSE+R2 utk regresi, Accuracy+Precision/Recall/F1 disederhanakan jadi
    Accuracy+F1_Macro utk klasifikasi), bukan MAE/Accuracy saja."""
    if is_classification:
        votes = [local_m['Accuracy'] >= global_m['Accuracy'], local_m['F1_Macro'] >= global_m['F1_Macro']]
    else:
        votes = [local_m['MAE'] < global_m['MAE'], local_m['RMSE'] < global_m['RMSE'], local_m['R2'] > global_m['R2']]
    return 'Lokal' if sum(votes) >= (len(votes) / 2) else 'Global'


summary_rows = []
for var, label in INDICATORS:
    n_local_win, n_total, deltas = 0, 0, []
    mae_l, mae_g, rmse_l, rmse_g, r2_l, r2_g = [], [], [], [], [], []
    for sid, sdata in LOCAL['stations'].items():
        ind = sdata['indicators'].get(var)
        if not ind:
            continue
        n_total += 1
        if is_clf(var):
            win = ind['local']['Accuracy'] >= ind['global']['Accuracy']
            deltas.append(ind['local']['Accuracy'] - ind['global']['Accuracy'])
        else:
            win = ind['local']['MAE'] <= ind['global']['MAE']
            deltas.append(ind['global']['MAE'] - ind['local']['MAE'])
            mae_l.append(ind['local']['MAE']); mae_g.append(ind['global']['MAE'])
            rmse_l.append(ind['local']['RMSE']); rmse_g.append(ind['global']['RMSE'])
            r2_l.append(ind['local']['R2']); r2_g.append(ind['global']['R2'])
        n_local_win += int(win)
    avg_local = {'MAE': np.mean(mae_l) if mae_l else np.nan, 'RMSE': np.mean(rmse_l) if rmse_l else np.nan, 'R2': np.mean(r2_l) if r2_l else np.nan}
    avg_global = {'MAE': np.mean(mae_g) if mae_g else np.nan, 'RMSE': np.mean(rmse_g) if rmse_g else np.nan, 'R2': np.mean(r2_g) if r2_g else np.nan}
    summary_rows.append({'var': var, 'label': label, 'algo': ALGO_USED[var], 'n_local_win': n_local_win, 'n_total': n_total,
                          'pct_local': n_local_win / n_total * 100 if n_total else 0,
                          'avg_delta': np.mean(deltas) if deltas else 0,
                          'avg_local': avg_local, 'avg_global': avg_global,
                          'winner': multi_metric_winner(avg_local, avg_global, False) if not is_clf(var) else None})
df_summary = pd.DataFrame(summary_rows)
for _i, _r in df_summary.iterrows():
    _nl, _ng, _nt, _n = station_wins(LOCAL, _r['var'], CLASSIFICATION_TARGET)
    df_summary.loc[_i, 'n_local_win'] = _nl
    df_summary.loc[_i, 'n_global_win'] = _ng
    df_summary.loc[_i, 'n_tie'] = _nt
    df_summary.loc[_i, 'n_total'] = _n
    df_summary.loc[_i, 'pct_local'] = _nl / _n * 100 if _n else 0
n_excluded = sum(len(v) for v in LOCAL['excluded'].values())

# Klasifikasi Arah Angin: rata-rata Accuracy/Precision/Recall/F1 Lokal vs Global (Notulen Poin 14)
wd_local = {'Accuracy': [], 'Precision_Macro': [], 'Recall_Macro': [], 'F1_Macro': []}
wd_global = {'Accuracy': [], 'Precision_Macro': [], 'Recall_Macro': [], 'F1_Macro': []}
for sid, sdata in LOCAL['stations'].items():
    ind = sdata['indicators'].get(CLASSIFICATION_TARGET)
    if not ind:
        continue
    for k in wd_local:
        wd_local[k].append(ind['local'][k])
        wd_global[k].append(ind['global'][k])
wd_summary = {k: (np.mean(wd_local[k]), np.mean(wd_global[k])) for k in wd_local}
wd_winner = multi_metric_winner({'Accuracy': wd_summary['Accuracy'][0], 'F1_Macro': wd_summary['F1_Macro'][0]},
                                 {'Accuracy': wd_summary['Accuracy'][1], 'F1_Macro': wd_summary['F1_Macro'][1]}, True)

df_summary['avg_winner'] = [wd_winner if is_clf(v) else w for v, w in zip(df_summary['var'], df_summary['winner'])]
df_summary['rec'] = [recommend(r['n_local_win'], r['n_global_win'], r['avg_winner']) for _, r in df_summary.iterrows()]
n_rec_local = int((df_summary['rec'] == 'Lokal').sum())
_rec_local_names = [r['label'] for _, r in df_summary.iterrows() if r['rec'] == 'Lokal']

story = []

# ==================== COVER ====================
story.append(Spacer(1, 12))
header_inst = Paragraph(
    '<b>PUSAT PENELITIAN KELAPA SAWIT (PPKS)</b><br/><font color=\'#64748B\' size=\'8.5\'>Indonesian Oil Palm Research Institute - Proyek NusaKlim Weather AI</font>',
    ParagraphStyle('CoverInst', fontName='Arial', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 8))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=16))
story.append(Paragraph('LAPORAN ANALISIS MODEL PER-STASIUN (LOKAL) VS GLOBAL', style_cover_title))
story.append(Paragraph(f'Apakah Model Global Cukup, atau Perlu Model Terpisah per Stasiun? Pengujian {len(LOCAL["stations"])} Stasiun, Ketujuh Indikator Cuaca, Algoritma Juara Produksi Masing-Masing Indikator', style_cover_subtitle))

cover_rows = [
    [Paragraph('<b>Rumusan Pertanyaan</b>', style_table_cell_bold), Paragraph('Untuk tiap indikator cuaca, mana yang lebih akurat di suatu stasiun: model global (data seluruh stasiun) atau model lokal (data stasiun itu sendiri saja)?', style_table_cell)],
    [Paragraph('<b>Stasiun Uji</b>', style_table_cell_bold), Paragraph(f'{len(LOCAL["stations"])} stasiun, dipilih acak dari {SAMPLING["n_eligible_stations"]} stasiun berdata lengkap (seed=42) - lihat Bab 2.1', style_table_cell)],
    [Paragraph('<b>Algoritma</b>', style_table_cell_bold), Paragraph('Algoritma juara produksi masing-masing indikator (Tabel 3.3 Laporan 3) - BUKAN satu/dua algoritma dipaksakan ke semua indikator. HANYA Machine Learning di tahap ini, lihat rasional Bab 1', style_table_cell)],
    [Paragraph('<b>Target Prediksi</b>', style_table_cell_bold), Paragraph('7 indikator: Curah Hujan, Suhu, Kelembapan, Tekanan Udara, Radiasi Matahari, Kecepatan Angin, Arah Angin', style_table_cell)],
    [Paragraph('<b>Ukuran Performa</b>', style_table_cell_bold), Paragraph('MAE, RMSE, R&sup2; (regresi); Accuracy, Precision, Recall, F1-Macro (Arah Angin)', style_table_cell)],
    [Paragraph('<b>Temuan Utama</b>', style_table_cell_bold), Paragraph(f'Model Global tetap direkomendasikan pada {len(INDICATORS) - n_rec_local} dari {len(INDICATORS)} indikator; Model Lokal hanya direkomendasikan untuk {", ".join(_rec_local_names) if _rec_local_names else "-"} - rincian per indikator di Bab 3 dan 4', style_table_cell)],
]
tbl_cover = Table(cover_rows, colWidths=[110, 380])
tbl_cover.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT), ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 4.5), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_cover)
story.append(Spacer(1, 18))
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026', style_cover_meta))
story.append(PageBreak())

# ==================== BAB 1 ====================
story.append(Paragraph('1. Latar Belakang &amp; Mengapa Hanya ML di Tahap Lokal', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))
story.append(Paragraph(
    'Laporan 3 (Tabel 3.3 &amp; Bab 3.4) menetapkan algoritma produksi terbaik untuk tiap indikator secara terpisah - bukan satu algoritma seragam untuk semua. Laporan ini melanjutkan dengan pertanyaan berbeda: <b>apakah model global (dilatih dari seluruh 183 stasiun) itu tetap yang terbaik jika dievaluasi per-stasiun, atau model yang dilatih khusus untuk satu stasiun ("lokal") bisa lebih akurat?</b> Untuk tiap indikator, baik Model Lokal maupun Model Global yang dibandingkan di sini memakai algoritma juara produksi indikator tersebut (mis. Suhu dibandingkan memakai Ridge Regression, Curah Hujan memakai LightGBM) - bukan satu/dua algoritma yang dipaksakan sama ke semua indikator seperti revisi laporan sebelumnya.',
    style_body
))
story.append(Paragraph(
    '<b>Mengapa Deep Learning tidak diuji ulang di tahap lokal:</b> alasannya bersifat metodologis, bukan sekadar preferensi - data latih per-stasiun jauh lebih sedikit (ratusan baris per stasiun) dibanding data gabungan Laporan 3/4 (puluhan ribu baris). Model Deep Learning (LSTM/GRU) dikenal luas membutuhkan volume data jauh lebih besar untuk belajar dengan baik dibanding model pohon keputusan/linear yang lebih sederhana (Goodfellow, Bengio &amp; Courville, "Deep Learning", MIT Press 2016, Bab 5 &amp; 11). Percobaan sebelumnya pada beberapa stasiun mengonfirmasi hal ini secara empiris: model Deep Learning yang dilatih per-stasiun merosot tajam pada data sekecil itu, dengan tingkat kesalahan yang jauh lebih buruk dibanding tebakan sederhana. Atas dasar itu, tahap lokal ini hanya menguji algoritma Machine Learning yang menjadi juara produksi pada Laporan 3, yaitu ' + ALGO_TEXT + ' (lihat kolom "Algoritma" pada Tabel 3.1) - bukan seluruh algoritma yang dibandingkan di Laporan 3.',
    style_body
))

story.append(Paragraph('2. Metodologi', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))
story.append(Paragraph(f'2.1 Pemilihan {len(LOCAL["stations"])} Stasiun', style_h2))
story.append(Paragraph(
    f'Pemilihan stasiun dilakukan dalam dua tahap, <b>kelengkapan data dicek lebih dulu, baru kemudian diambil sampel</b> (bukan sebaliknya), supaya seluruh stasiun yang diuji punya data yang sama-sama memadai: '
    f'(1) dari seluruh {SAMPLING["n_data_stations_total"]} stasiun, hanya stasiun dengan data lengkap yang dipertimbangkan, yaitu pada <b>ketujuh indikator</b> memiliki minimal <b>{SAMPLING["criteria"]["min_train_days"]} hari data latih</b> (satu tahun penuh, mencakup satu siklus musim) dan minimal <b>{SAMPLING["criteria"]["min_test_days"]} dari 30 hari data uji</b> yang valid &ndash; sebanyak <b>{SAMPLING["n_eligible_stations"]} stasiun</b> memenuhi kriteria ini; '
    f'(2) dari {SAMPLING["n_eligible_stations"]} stasiun tersebut dipilih <b>{len(LOCAL["stations"])} stasiun secara acak</b> (seed=42, dapat direproduksi, lihat <code>station_sampling.json</code>). '
    f'Karena kelengkapan data sudah diperiksa sebelum pengambilan sampel, tidak ada stasiun yang gugur belakangan: seluruh {len(LOCAL["stations"])} stasiun diuji pada ketujuh indikator.',
    style_body
))
story.append(Paragraph('2.2 Perbandingan Model &amp; Metrik Koefisien Determinasi (R&sup2;)', style_h2))
story.append(Paragraph(
    f'<b>Model Lokal:</b> untuk tiap indikator, dilatih ulang khusus untuk satu stasiun (hanya dari riwayat data stasiun itu sendiri) memakai algoritma juara produksi indikator tersebut - lihat kolom "Algoritma" pada Tabel Bab 3. <b>Model Global:</b> model produksi yang SAMA PERSIS dengan Laporan 3 (`weather_model_latest.joblib`, dilatih sekali dari seluruh 183 stasiun) - bukan dilatih ulang di sini, hanya di-skor ulang pada baris uji milik stasiun yang sedang dibahas, agar perbandingan adil (baris uji identik, dan algoritma identik, untuk Lokal maupun Global - satu-satunya perbedaan adalah cakupan data latihnya). Split latih/uji per-stasiun mengikuti tanggal potong yang sama dengan Laporan 3 (30 hari terakhir sebagai data uji); {"seluruh kombinasi stasiun&times;indikator memenuhi kecukupan data (tidak ada yang dikecualikan)." if n_excluded == 0 else f"kombinasi stasiun&times;indikator dengan riwayat data kurang dari 60 baris latih atau 5 baris uji dikecualikan ({n_excluded} kombinasi)."}',
    style_body
))
story.append(Paragraph(
    '<b>Catatan penting soal istilah "Model Global":</b> pada laporan ini, "Global" murni merujuk pada <b>cakupan data pelatihan</b> (satu model dilatih dari gabungan seluruh 183 stasiun) - bukan pada pemilihan algoritma. Pemilihan algoritma sendiri tetap dilakukan berdasarkan hasil benchmarking per target/indikator (Tabel 3.3 Laporan 3), identik untuk sisi Lokal maupun Global pada indikator yang sama. Dengan kata lain, cakupan data (global vs lokal) dan pemilihan algoritma (per-indikator) adalah dua keputusan yang independen satu sama lain.',
    style_body
))
story.append(Paragraph(
    'Catatan mengenai R&sup2; (koefisien determinasi): <b>rentang R&sup2; bukan 0 s/d 100 (atau 0 s/d 1) seperti persentase akurasi</b> - nilai ini menunjukkan seberapa jauh model mengungguli tebakan sederhana (menebak rata-rata data uji untuk semua baris). R&sup2;=1 berarti prediksi sempurna, R&sup2;=0 berarti model sama baiknya dengan menebak rata-rata, dan <b>R&sup2; negatif berarti model LEBIH BURUK</b> daripada sekadar menebak rata-rata data uji. Ini lazim terjadi pada data lokal per-stasiun yang sangat sedikit (ratusan baris) dan bervariasi tinggi, di mana rata-rata 30-hari periode uji bisa jadi kebetulan sudah menjadi tebakan yang cukup baik sehingga sulit dikalahkan model manapun. R&sup2; negatif pada laporan ini bukan kesalahan perhitungan, melainkan sinyal bahwa model (lokal atau global) belum berhasil mengalahkan tebakan sederhana untuk stasiun/indikator tersebut - dibahas per kasus pada Bab 3.',
    style_body
))

story.append(PageBreak())

# ==================== BAB 3 ====================
story.append(Paragraph('3. Hasil: Model Lokal vs Global per Indikator', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))
story.append(Paragraph('3.1 Perbandingan Model per Variabel Regresi (MAE, RMSE, R&sup2;)', style_h2))
story.append(Paragraph(
    f'MAE, RMSE, dan R&sup2; berikut adalah rata-rata lintas seluruh stasiun uji yang punya data cukup untuk indikator tsb (dari {len(LOCAL["stations"])} stasiun sampel, lihat kolom "n"). Model Lokal = dilatih ulang khusus tiap stasiun; Model Global = model produksi yang sama persis dari Laporan 3, diskor pada baris uji stasiun yang sama. Baris dengan latar hijau menandai pemenang per indikator, memakai kriteria yang sama dengan Tabel 3.3 Laporan 3: unggul di &ge;2 dari 3 metrik (bukan MAE saja).',
    style_body
))
sum_rows = [[Paragraph('Variabel', style_table_header), Paragraph('Model', style_table_header), Paragraph('Algoritma', style_table_header),
             Paragraph('n (stasiun)', style_table_header), Paragraph('MAE', style_table_header), Paragraph('RMSE', style_table_header), Paragraph('R&sup2;', style_table_header)]]
style_cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 3), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
row_i = 0
for _, r in df_summary.iterrows():
    if is_clf(r['var']):
        continue
    for model_name, m in [('Lokal', r['avg_local']), ('Global', r['avg_global'])]:
        row_i += 1
        is_best = r['winner'] == model_name
        cs = style_table_cell_bold if is_best else style_table_cell
        sum_rows.append([
            Paragraph(f"<b>{r['label']}</b>", style_table_cell_bold),
            Paragraph((model_name + ' (Terbaik)') if is_best else model_name, cs),
            Paragraph(r['algo'], style_table_cell),
            Paragraph(str(r['n_total']), style_table_cell_center),
            Paragraph(f"{m['MAE']:.3f}", style_table_cell_center),
            Paragraph(f"{m['RMSE']:.3f}", style_table_cell_center),
            Paragraph(f"{m['R2']:.3f}", style_table_cell_center),
        ])
        if is_best:
            style_cmds.append(('BACKGROUND', (0, row_i), (-1, row_i), COLOR_BG_ACCENT))
tbl_sum = Table(sum_rows, colWidths=[95, 75, 115, 55, 55, 55, 50], repeatRows=1)
tbl_sum.setStyle(TableStyle(style_cmds))
story.append(tbl_sum)
story.append(Spacer(1, 4))

fig1_p = os.path.join(fig_dir, 'fig_local1_winrate_per_indicator.png')
if os.path.exists(fig1_p):
    story.append(Image(fig1_p, width=16.0 * cm, height=8.8 * cm))
    story.append(Paragraph(f'<b>Gambar 1:</b> Proporsi stasiun (dari {len(LOCAL["stations"])}) yang lebih akurat dengan Model Lokal (hijau), Model Global (abu-abu tua), atau seri (abu-abu muda), per indikator. Penilaian per stasiun memakai MAE untuk indikator angka dan Accuracy untuk Arah Mata Angin; algoritma juara masing-masing indikator.', style_caption))

story.append(PageBreak())
story.append(Paragraph('3.2 Detail Klasifikasi Arah Mata Angin', style_h2))
story.append(Paragraph(
    f'Untuk target kategori <b>Arah Mata Angin</b>, evaluasi dibedakan dari target regresi memakai Accuracy, Precision, Recall, dan F1-Score (rata-rata makro), dirata-ratakan lintas {len(wd_local["Accuracy"])} stasiun uji (algoritma {ALGO_USED[CLASSIFICATION_TARGET]}). Kriteria pemenang: unggul di &ge;1 dari 2 metrik acuan (Accuracy, F1-Macro):',
    style_body
))
wd_tbl_rows = [
    [Paragraph('Model', style_table_header), Paragraph('Accuracy', style_table_header), Paragraph('Precision (Macro)', style_table_header),
     Paragraph('Recall (Macro)', style_table_header), Paragraph('F1 (Macro)', style_table_header)],
]
wd_style_cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 3.5), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
for ridx, (model_name, idx) in enumerate([('Lokal', 0), ('Global', 1)], start=1):
    is_best = wd_winner == model_name
    cs = style_table_cell_bold if is_best else style_table_cell
    wd_tbl_rows.append([Paragraph((model_name + ' (Terbaik)') if is_best else model_name, cs)]
                        + [Paragraph(f"{wd_summary[k][idx]*100:.1f}%", style_table_cell_center) for k in ['Accuracy', 'Precision_Macro', 'Recall_Macro', 'F1_Macro']])
    if is_best:
        wd_style_cmds.append(('BACKGROUND', (0, ridx), (-1, ridx), COLOR_BG_ACCENT))
tbl_wd = Table(wd_tbl_rows, colWidths=[80, 90, 100, 90, 90])
tbl_wd.setStyle(TableStyle(wd_style_cmds))
story.append(tbl_wd)
story.append(Spacer(1, 4))

story.append(Paragraph('3.3 Ringkasan Keputusan per Indikator', style_h2))
story.append(Paragraph(
    'Tabel berikut menyatukan dua sudut pandang: <b>jumlah stasiun</b> yang lebih akurat dengan tiap model (dasar Gambar 1) dan <b>pemenang berdasarkan rata-rata metrik</b> (Tabel 3.1 dan 3.2). '
    '<b>Aturan keputusan:</b> Model Lokal direkomendasikan hanya jika ia unggul di lebih banyak stasiun <b>dan</b> unggul pada rata-rata metrik; bila dua kriteria itu tidak sejalan atau seri, Model Global dipertahankan karena lebih sederhana dioperasikan dan di-retrain.',
    style_body
))
rec_rows = [[Paragraph('Indikator', style_table_header), Paragraph('Stasiun: Lokal Lebih Akurat', style_table_header), Paragraph('Stasiun: Global Lebih Akurat', style_table_header),
             Paragraph('Seri', style_table_header), Paragraph('Pemenang Rata-rata Metrik', style_table_header), Paragraph('Rekomendasi', style_table_header)]]
rec_cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 3), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
for ri, (_, r) in enumerate(df_summary.iterrows(), start=1):
    rec_rows.append([
        Paragraph(f"<b>{r['label']}</b>", style_table_cell_bold),
        Paragraph(f"{int(r['n_local_win'])} dari {int(r['n_total'])}", style_table_cell_center),
        Paragraph(f"{int(r['n_global_win'])} dari {int(r['n_total'])}", style_table_cell_center),
        Paragraph(str(int(r['n_tie'])), style_table_cell_center),
        Paragraph(r['avg_winner'], style_table_cell_center),
        Paragraph(f"<b>Model {r['rec']}</b>", style_table_cell_center),
    ])
    rec_cmds.append(('BACKGROUND', (5, ri), (5, ri), COLOR_BG_ACCENT))
tbl_rec = Table(rec_rows, colWidths=[115, 80, 80, 40, 100, 90], repeatRows=1)
tbl_rec.setStyle(TableStyle(rec_cmds))
story.append(tbl_rec)
story.append(Spacer(1, 4))

story.append(Paragraph('4. Kesimpulan &amp; Rekomendasi Arsitektur', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))
story.append(Paragraph(
    f'Menjawab langsung pertanyaan "apakah rekomendasi akhirnya tetap model global?": <b>jawabannya berbeda-beda per indikator</b> (lihat Tabel 3.1), bukan satu jawaban tunggal untuk seluruh sistem:',
    style_body
))
for _, r in df_summary.iterrows():
    nl, ng, nt, nn = int(r['n_local_win']), int(r['n_global_win']), int(r['n_tie']), int(r['n_total'])
    if r['rec'] == 'Lokal':
        why = f'Model Lokal lebih akurat di {nl} dari {nn} stasiun (Global {ng}) dan juga unggul pada rata-rata metrik, sehingga kedua kriteria sejalan.'
    elif nl > ng:
        why = (f'Model Lokal memang lebih akurat di {nl} dari {nn} stasiun (Global {ng}), tetapi pada rata-rata metrik (Tabel 3.1/3.2) Model Global lebih baik '
               f'&ndash; keunggulan Lokal di banyak stasiun bersifat tipis, sedangkan di stasiun lain Lokal tertinggal jauh. Karena kedua kriteria tidak sejalan, Model Global dipertahankan.')
    elif ng > nl:
        why = f'Model Global lebih akurat di {ng} dari {nn} stasiun (Lokal {nl}) dan juga unggul pada rata-rata metrik, sehingga kedua kriteria sejalan.'
    else:
        why = f'Hasil seri antar stasiun (Lokal {nl}, Global {ng} dari {nn} stasiun), sehingga Model Global dipertahankan karena lebih sederhana dioperasikan.'
    story.append(Paragraph(f'&bull; <b>{r["label"]}:</b> <b>Model {r["rec"]}</b> direkomendasikan. {why}', style_body))

story.append(Spacer(1, 4))
story.append(make_callout_box(
    '<b>Rekomendasi arsitektur produksi:</b> untuk indikator di mana Model Global unggul di mayoritas stasiun, pertahankan pipeline produksi satu-model-global seperti Laporan 3 (lebih sederhana dioperasikan &amp; di-retrain). Untuk indikator di mana Model Lokal unggul di mayoritas stasiun, pertimbangkan pipeline hibrida: model global sebagai fallback/baseline, dilengkapi model lokal per-stasiun (dilatih otomatis saat riwayat data stasiun mencukupi, lihat ambang batas Bab 2.2) khusus untuk indikator tsb. Algoritma yang dipakai pada kedua skenario tetap algoritma juara produksi indikator tersebut (Tabel 3.3 Laporan 3, kolom "Algoritma" Bab 3) - keputusan lokal-vs-global tidak mengubah pemilihan algoritma, hanya cakupan data latihnya.',
    title='REKOMENDASI ARSITEKTUR'
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

print('Building Laporan 3b (Model Per Stasiun vs Global)...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
