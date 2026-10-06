# ==============================================================================
# SCRIPT TO BUILD HIGH-QUALITY CLEAN MASTER DOCUMENTATION PDF
# Proyek NusaKlim Weather AI - Pusat Penelitian Kelapa Sawit (PPKS)
# ==============================================================================

import os
import sys
import json
import joblib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable, KeepTogether
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


BASE_DIR = r"D:\Projects\Kodepanda\Nusaklim\nusaklim"
pdf_path = os.path.join(BASE_DIR, "report", "6.Dokumentasi_Lengkap_Pengerjaan_Proyek_NusaKlim_PPKS.pdf")
fig_dir = os.path.join(BASE_DIR, "figures")

# ------------------------------------------------------------------------------
# LIVE DATA (bukan hardcode) - model bundle produksi & hasil komparasi Open-Meteo,
# supaya dokumen master ini selalu konsisten dengan Laporan 3 & Laporan 5.
# ------------------------------------------------------------------------------
sys.path.insert(0, BASE_DIR)
from retrain_pipeline import REGRESSION_TARGETS, CLASSIFICATION_TARGET

_bundle = joblib.load(os.path.join(BASE_DIR, "models", "weather_model_latest.joblib"))
_metrics = _bundle['metrics']
_algo_used = _bundle['algo_used']
N_FEATURE = len(_bundle['feature_cols'])
N_TEST_REF = _metrics['temp_avg_h1']['n_test']
MODEL_MB = os.path.getsize(os.path.join(BASE_DIR, "models", "weather_model_latest.joblib")) / (1024 * 1024)
_ALGO_SET = sorted(set(a.split(' (')[0] for a in _algo_used.values()))

with open(os.path.join(BASE_DIR, "nusaklim_daily_aggregated.csv"), encoding="utf-8") as _f:
    N_RAW_ROWS = sum(1 for _ in _f) - 1

with open(os.path.join(BASE_DIR, "openmeteo_benchmark_summary.json"), encoding="utf-8") as _f:
    _OM = json.load(_f)
OM_AVG = _OM['open_meteo_metrics']
_ISUM = _OM['indicator_summary']
_IND_ORDER = ['temp_avg', 'humidity_avg', 'rainfall_total_mm', 'solar_radiation_avg', 'pressure_avg_hpa', 'wind_speed_avg', 'wind_direction_name']


def _join_labels(items):
    items = list(items)
    if len(items) <= 1:
        return items[0] if items else '-'
    return ', '.join(items[:-1]) + ' dan ' + items[-1]


_NK_BETTER = [_ISUM[k]['label'] for k in _IND_ORDER if _ISUM[k]['winner_avg'] == 'NusaKlim']
_OM_BETTER = [_ISUM[k]['label'] for k in _IND_ORDER if _ISUM[k]['winner_avg'] == 'Open-Meteo']
NK_AVG = _OM['nusaklim_local_ai_metrics']


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
        self.drawRightString(555, 805, 'Dokumentasi Lengkap End-to-End Pengerjaan Sistem')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Dokumen Master Arsitektur, Metodologi & Implementasi NusaKlim PPKS')
        self.drawRightString(555, 32, f'Halaman {self._pageNumber} dari {page_count}')
        self.restoreState()

doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=50, bottomMargin=55)
styles = getSampleStyleSheet()

# Theme Colors
COLOR_PRIMARY = colors.HexColor('#1E3A8A')
COLOR_SECONDARY = colors.HexColor('#0D9488')
COLOR_DARK = colors.HexColor('#0F172A')
COLOR_BODY = colors.HexColor('#334155')
COLOR_MUTED = colors.HexColor('#64748B')
COLOR_BG_LIGHT = colors.HexColor('#F8FAFC')
COLOR_BG_ACCENT = colors.HexColor('#EFF6FF')
COLOR_BORDER = colors.HexColor('#E2E8F0')

style_cover_title = ParagraphStyle('CoverTitle', parent=styles['Normal'], fontName='Arial-Bold', fontSize=16, leading=21, textColor=COLOR_PRIMARY, alignment=1, spaceAfter=8)
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Arial', fontSize=9.5, leading=13.5, textColor=COLOR_BODY, alignment=1, spaceAfter=14)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Arial-Bold', fontSize=11, leading=14, textColor=COLOR_PRIMARY, spaceBefore=7, spaceAfter=3, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Arial-Bold', fontSize=9, leading=12, textColor=COLOR_SECONDARY, spaceBefore=5, spaceAfter=2, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Arial', fontSize=8, leading=11.2, textColor=COLOR_BODY, spaceAfter=3.5, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Arial-Italic', fontSize=7.6, leading=10.5, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.2, leading=9, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Arial', fontSize=7, leading=8.8, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7, leading=8.8, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Arial', fontSize=7, leading=8.8, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.2, leading=9, textColor=COLOR_MUTED, alignment=1, spaceBefore=2, spaceAfter=5)

def make_callout_box(text, title='POIN KUNCI & RASIONALISASI TEKNIS', width=515):
    p_title = Paragraph(f'<b>{title}</b>', ParagraphStyle('CT', fontName='Arial-Bold', fontSize=7.5, leading=9.5, textColor=COLOR_PRIMARY, spaceAfter=2))
    p_text = Paragraph(text, style_callout)
    tbl = Table([[p_title], [p_text]], colWidths=[width])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_ACCENT),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return tbl

story = []

# ==================== HALAMAN 1: COVER EKSEKUTIF MASTER ====================
story.append(Spacer(1, 10))
header_inst = Paragraph(
    '<b>PUSAT PENELITIAN KELAPA SAWIT (PPKS)</b><br/><font color="#64748B" size="8.5">Indonesian Oil Palm Research Institute - Proyek NusaKlim Weather AI</font>',
    ParagraphStyle('CoverInst', fontName='Arial', fontSize=10, leading=13, textColor=COLOR_PRIMARY, alignment=1)
)
story.append(header_inst)
story.append(Spacer(1, 8))
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=14))

story.append(Paragraph('DOKUMENTASI MASTER END-TO-END:<br/>PENGEMBANGAN SISTEM AI PREDIKSI CUACA 7 HARI NUSAKLIM', style_cover_title))
story.append(Paragraph('Laporan Komprehensif Seluruh Alur Pengerjaan: Dari Pembersihan 14,8 Juta Data Mentah, Agregasi Notulen Rapat, Pelatihan Model 7-Hari, Benchmarking 5 Algoritma per Variabel, Uji Celah Data, Validasi Open-Meteo, hingga REST API Backend FastAPI', style_cover_subtitle))

cover_meta = [
    [Paragraph('<b>Nama Proyek</b>', style_table_cell_bold), Paragraph('NusaKlim Weather AI - Sistem Prediksi Cuaca 7 Hari Perkebunan Kelapa Sawit', style_table_cell)],
    [Paragraph('<b>Populasi Data Mentah</b>', style_table_cell_bold), Paragraph('14.827.287 baris data sensor interval 10-15 menit (1,37 GB) dari 183 stasiun AWS PPKS', style_table_cell)],
    [Paragraph('<b>Dataset Bersih Terstandar</b>', style_table_cell_bold), Paragraph(f'14.823.713 baris interval bersih (969 MB) &amp; {idn(N_RAW_ROWS)} baris harian (10 MB)', style_table_cell)],
    [Paragraph('<b>Model Champion Produksi</b>', style_table_cell_bold), Paragraph(f'<b>Algoritma Juara per-Variabel ({"/".join(_ALGO_SET)}, H+1 s/d H+7)</b> | Akurasi Suhu MAE &plusmn;{_metrics["temp_avg_h1"]["MAE"]:.2f}&deg;C di H+1 | Retrain Penuh &plusmn;21 Menit', style_table_cell_bold)],
    [Paragraph('<b>Layanan Backend &amp; API</b>', style_table_cell_bold), Paragraph('REST API FastAPI Modular (&lt; 30 ms latensi inferensi) + Rekomendasi Agronomi Kebun', style_table_cell)],
    [Paragraph('<b>Validasi Data Aktual</b>', style_table_cell_bold), Paragraph(f'Dibandingkan dengan Open-Meteo pada 7 indikator di 4 stasiun: NusaKlim lebih akurat pada {_join_labels(_NK_BETTER)}; Open-Meteo lebih akurat pada {_join_labels(_OM_BETTER)}', style_table_cell_bold)],
    [Paragraph('<b>Tim Penyusun</b>', style_table_cell_bold), Paragraph('Tim Data Analyst &amp; AI Engineering PPKS | Tanggal: September 2026', style_table_cell)],
]
tbl_cov = Table(cover_meta, colWidths=[135, 380])
tbl_cov.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 4),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_cov)

story.append(PageBreak())

# ==================== HALAMAN 2: FLOWCHART END-TO-END ====================
story.append(Paragraph('1. Flowchart Arsitektur &amp; Peta Alur Kerja End-to-End', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Pengembangan sistem NusaKlim Weather AI dirancang melalui 6 tahapan besar yang saling terhubung secara terpadu (beberapa tahapan pada diagram menggabungkan lebih dari satu bab pada laporan ini). '
    'Diagram alur berikut mengilustrasikan transformasi dari data mentah lapangan hingga menjadi layanan prediksi cuaca operasional:',
    style_body
))

flow_img = os.path.join(fig_dir, 'fig_end_to_end_flowchart.png')
if os.path.exists(flow_img):
    story.append(Image(flow_img, width=18.5*cm, height=10.5*cm))
    story.append(Paragraph('Gambar 1: Flowchart Garis Besar Alur Pengerjaan End-to-End NusaKlim Weather AI PPKS.', style_caption))

story.append(make_callout_box(
    'Alur pengerjaan mencakup seluruh siklus hidup AI (Data Engineering -> Feature Store -> Model Training &amp; Benchmarking -> Stress-Testing -> External API Cross-Validation -> Production API Serving). Setiap tahap memiliki alasan teknis dan bisnis yang jelas.',
    title='RANGKUMAN ALUR KERJA PROYEK'
))

story.append(PageBreak())

# ==================== HALAMAN 3: TAHAP 1 & 2 ====================
story.append(Paragraph('2. Tahap 1: Pembersihan Data Interval (Data Cleaning)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; Memproses 14.827.287 baris data sensor mentah (1,37 GB) dari 183 stasiun AWS PPKS secara bertahap per 500.000 baris agar tidak membebani RAM.<br/>'
    '&bull;&nbsp; Menyaring 3.567 baris data artefak reset jam alat tahun 2000 (saat alat pertama dinyalakan) dan 7 baris tag pengujian non-AWS (<code>WiFiLogger</code>, <code>9991-9995</code>).<br/>'
    '&bull;&nbsp; Mengubah kode eror sensor (3276.7, 32767, 255, -90&deg;F) menjadi nilai kosong (<code>NaN</code>) agar tidak mengotori perhitungan rata-rata.<br/>'
    '&bull;&nbsp; Mengonversi seluruh parameter ke standar satuan baku internasional: Suhu (&deg;F ke &deg;C), Tekanan (inHg ke hPa), Curah Hujan (rain15 ke mm), dan waktu ke WIB (UTC+7).<br/>'
    '&bull;&nbsp; Menghasilkan file baru: <code>nusaklim_cleaned_interval.csv</code> (14.823.713 baris valid, 969,45 MB).',
    style_body
))

story.append(Paragraph('<b>B. Alasan Mengapa Dilakukan (Rasionalisasi Teknis):</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; <b>Mencegah Anomali Fisis Ekstrem:</b> Menghilangkan suhu mustahil -67.78&deg;C (kabel sensor copot) dan curah hujan tidak wajar 6.337 mm/15-menit (gangguan penakar hujan).<br/>'
    '&bull;&nbsp; <b>Menyelamatkan +2,75 Juta Baris Data:</b> Metode lama membuang seluruh baris jika ada 1 sensor rusak. Metode baru kita menyelamatkan sensor lain yang sehat (Suhu &amp; Tekanan tetap aman meski sensor hujan rusak).',
    style_body
))

story.append(Spacer(1, 4))
story.append(Paragraph('3. Tahap 2: Agregasi Harian &amp; Standarisasi Notulen PPKS', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; Meringkas 14,8 juta data interval 15-menit (96 observasi per hari) menjadi 1 baris ringkasan harian per stasiun.<br/>'
    '&bull;&nbsp; Menerapkan formula Notulen Rapat PPKS 20 Agustus 2026: <b>SUM</b> untuk Curah Hujan &amp; Radiasi Solar; <b>MEAN</b> untuk Suhu, RH, Tekanan Barometer, dan Kecepatan Angin.<br/>'
    '&bull;&nbsp; Mengekstrak parameter ekstrem harian: Suhu Min (T<sub>min</sub>), Suhu Max (T<sub>max</sub>), RH Min (RH<sub>min</sub>), RH Max (RH<sub>max</sub>), dan Angin Maksimum.<br/>'
    '&bull;&nbsp; Mengonversi derajat arah angin ke 4 arah mata angin kardinal: Utara (&gt;315&deg; atau &le;45&deg;), Timur (&gt;45&deg; s/d &le;135&deg;), Selatan (&gt;135&deg; s/d &le;225&deg;), Barat (&gt;225&deg; s/d &le;315&deg;).<br/>'
    f'&bull;&nbsp; Menghasilkan dataset bersih harian (<i>Golden Dataset</i>): <code>nusaklim_daily_aggregated.csv</code> ({idn(N_RAW_ROWS)} baris, 10,12 MB).',
    style_body
))

story.append(Paragraph('<b>B. Alasan Mengapa Dilakukan (Rasionalisasi Teknis):</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; <b>Efisiensi Komputasi 100x Lipat:</b> Merampingkan dataset dari 1,37 GB menjadi 10,12 MB sehingga dapat dilatih dalam hitungan detik tanpa membebani RAM server.<br/>'
    '&bull;&nbsp; <b>Kebutuhan Bisnis Perkebunan:</b> Keputusan operasional kebun (jadwal pemupukan dan panen TBS) dibuat berbasis skala harian.',
    style_body
))

story.append(PageBreak())

# ==================== HALAMAN 4: TAHAP 3 ====================
story.append(Paragraph('4. Tahap 3: Penyusunan Fitur &amp; Pelatihan Model 7-Hari Multi-Horizon', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    f'&bull;&nbsp; <b>Membangun {N_FEATURE} Fitur Prediktor:</b> Riwayat 1/3/7 hari sebelumnya &amp; rata-rata 7 hari untuk 6 variabel cuaca, perubahan tekanan harian, rentang suhu harian, Day of the Year (sin/cos), dan arah angin hari ini (satu-satunya fitur yang dipakai langsung dari dataset). Seluruh fitur berasal dari data pengamatan nyata. Fitur identitas stasiun (ID/nama sebagai kategori) sengaja <b>tidak diikutsertakan</b> karena hanya pengenal unik, bukan variabel fisis cuaca &ndash; lihat <i>Laporan Model Prediksi Cuaca 7 Hari</i> Bab 2.1.<br/>'
    f'&bull;&nbsp; <b>Melatih Model Multi-Horizon Mandiri:</b> Membangun model regresi &amp; klasifikasi independen untuk masing-masing horizon H+1 hingga H+7, dengan <b>algoritma juara dipilih per-variabel</b> dari hasil benchmarking (Suhu/Kelembapan/Tekanan/Angin: Ridge Regression; Hujan/Radiasi/Arah Angin: LightGBM - lihat <i>Laporan Model Prediksi Cuaca 7 Hari</i> Tabel 3.3), tetap sebagai <b>1 model global</b> yang dilatih dari gabungan seluruh 183 stasiun.<br/>'
    f'&bull;&nbsp; <b>Evaluasi pada Data Uji Riil:</b> Menguji performa model pada 30 hari observasi aktual terakhir yang sama sekali tidak dipakai saat melatih model (21 Juli 2026 &ndash; 19 Agustus 2026, &plusmn;{idn(N_TEST_REF)} titik sampel per target).<br/>'
    f'&bull;&nbsp; <b>Penyimpanan Bundle Produksi:</b> Model dibundel dalam file <code>models/weather_model_latest.joblib</code> ({MODEL_MB:.1f} MB).',
    style_body
))

story.append(Paragraph('<b>B. Bukti Metrik Akurasi Validasi Lapangan (30 Hari Uji):</b>', style_h2))

HARI_KE = {1: 'Besok', 2: 'Hari-2', 3: 'Hari-3', 4: 'Hari-4', 5: 'Hari-5', 6: 'Hari-6', 7: 'Hari-7'}
m_data = [
    [Paragraph('Horizon', style_table_header), Paragraph('Suhu MAE', style_table_header), Paragraph('Suhu RMSE', style_table_header), Paragraph('Suhu R<sup>2</sup>', style_table_header), Paragraph('Kelembapan MAE (%)', style_table_header), Paragraph('Hujan MAE (mm)', style_table_header), Paragraph('Arah Angin Akurasi', style_table_header)],
]
for h in range(1, 8):
    t = _metrics[f'temp_avg_h{h}']
    rh = _metrics[f'humidity_avg_h{h}']
    rain = _metrics[f'rainfall_total_mm_h{h}']
    wd = _metrics[f'wind_direction_name_h{h}']
    cs = style_table_cell_bold if h == 1 else style_table_cell_center
    m_data.append([
        Paragraph(f'<b>H+{h} ({HARI_KE[h]})</b>', style_table_cell_bold),
        Paragraph(f"{t['MAE']:.2f} &deg;C", style_table_cell_center), Paragraph(f"{t['RMSE']:.2f} &deg;C", style_table_cell_center), Paragraph(f"{t['R2']:.3f}", style_table_cell_center),
        Paragraph(f"{rh['MAE']:.2f} %", style_table_cell_center), Paragraph(f"{rain['MAE']:.2f} mm", style_table_cell_center),
        Paragraph(f"<b>{wd['Accuracy']*100:.1f} %</b>" if h == 1 else f"{wd['Accuracy']*100:.1f} %", style_table_cell_center),
    ])
tbl_m = Table(m_data, colWidths=[75, 70, 70, 65, 75, 85, 75])
tbl_m.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_m)

story.append(Spacer(1, 4))
story.append(Paragraph('<b>C. Alasan Mengapa Dilakukan (Rasionalisasi Teknis):</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; <b>Mencegah Akumulasi Kesalahan:</b> Pendekatan multi-horizon mandiri (setiap horizon dilatih dan diramal terpisah) tidak menggunakan hasil tebakan hari ini untuk menebak hari esok, sehingga error tidak menumpuk hingga hari ke-7.<br/>'
    '&bull;&nbsp; <b>Keluaran Lengkap:</b> Menghasilkan 7 parameter sekaligus (Suhu Rata-rata, Kelembapan, Curah Hujan mm, Radiasi Solar, Tekanan Udara, Kecepatan Angin, dan Arah Mata Angin).',
    style_body
))

story.append(PageBreak())

# ==================== HALAMAN 5: TAHAP 4 & 5 ====================
story.append(Paragraph('5. Tahap 4: Benchmarking 5 Algoritma per Variabel (ML vs Deep Learning)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    'Melatih dan mengevaluasi 5 algoritma (LightGBM, Ridge Regression, Random Forest, LSTM, GRU) untuk <b>ketujuh variabel target sekaligus</b> pada horizon H+1 &amp; H+7 &ndash; bukan hanya Curah Hujan seperti iterasi benchmark sebelumnya &ndash; karena algoritma terbaik untuk satu variabel terbukti belum tentu terbaik untuk variabel lain (lihat <i>Laporan Model Prediksi Cuaca 7 Hari</i> Bab 3.4). Kriteria juara: rata-rata peringkat gabungan MAE+RMSE+R&sup2; (regresi) atau F1-Macro (klasifikasi), bukan MAE/Accuracy saja.',
    style_body
))

bench_data = [
    [Paragraph('Variabel Target', style_table_header), Paragraph('Algoritma Juara (Dipakai Produksi)', style_table_header), Paragraph('Kategori', style_table_header)],
]
for var, label in REGRESSION_TARGETS.items():
    algo = _algo_used[f'{var}_h1']
    cat = 'Linear (ML)' if algo.startswith('Ridge') else 'Gradient Boosting (ML)'
    bench_data.append([Paragraph(f'<b>{label}</b>', style_table_cell_bold), Paragraph(algo, style_table_cell), Paragraph(cat, style_table_cell_center)])
_wd_algo = _algo_used[f'{CLASSIFICATION_TARGET}_h1']
bench_data.append([Paragraph('<b>Arah Mata Angin</b>', style_table_cell_bold), Paragraph(_wd_algo, style_table_cell), Paragraph('Gradient Boosting (ML)', style_table_cell_center)])
tbl_b = Table(bench_data, colWidths=[150, 215, 150])
tbl_b.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_b)
story.append(Spacer(1, 3))
story.append(Paragraph(
    'Ketika seluruh 5 algoritma (termasuk LSTM &amp; GRU) diikutsertakan, Deep Learning justru unggul di 5 dari 7 indikator secara informasional. Namun DL <b>tidak dipakai sebagai model produksi</b> untuk iterasi ini &ndash; model PyTorch-nya tidak disimpan/diintegrasikan ke jalur inferensi, dan dilatih hanya 10 epoch (indikatif, bukan hasil teroptimasi penuh) &ndash; sehingga algoritma produksi yang benar-benar dipakai (tabel di atas) tetap dipilih hanya dari 3 algoritma ML yang siap di-deploy. Rinciannya ada di <i>Laporan Model Prediksi Cuaca 7 Hari</i> Bab 3.4.',
    style_body
))

story.append(Spacer(1, 4))
story.append(Paragraph('6. Tahap 5: Audit Celah Data (Data Gap) &amp; Uji Ketahanan Stress-Test', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; Mengaudit kelengkapan data historis 183 stasiun selama 4,5 tahun: Rata-rata kelengkapan mencapai <b>84,47% (Median 92,50%)</b>; 101 stasiun (55,2%) memiliki kelengkapan &ge;90%; 55,9% jeda data hanya berlangsung 1-3 hari akibat sinyal GSM/baterai panel surya lemah saat mendung tebal.<br/>'
    '&bull;&nbsp; Melakukan uji ketahanan model dengan menyuntikkan simulasi data hilang 0% s/d 50% secara acak.',
    style_body
))

story.append(Paragraph('<b>B. Alasan Mengapa Dilakukan (Rasionalisasi Teknis):</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; <b>Menjamin Sistem Tetap Berjalan:</b> Di lapangan kebun sawit terpencil, gangguan sinyal adalah hal yang pasti terjadi. '
    'Hasil uji ketahanan membuktikan bahwa bahkan saat 10% data hilang, error suhu hanya naik dari 0.997&deg;C menjadi 1.262&deg;C (sangat tangguh dan tidak pernah gagal total) berkat 4 pilar ketahanan model.',
    style_body
))

story.append(PageBreak())

# ==================== HALAMAN 6: TAHAP 6 ====================
story.append(Paragraph('7. Tahap 6: Validasi Data Aktual vs Open-Meteo Global API (Langkah 2)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; Menarik data telemetri historis &amp; peramalan dari <b>Open-Meteo API</b> untuk 4 stasiun referensi riil PPKS, diresolusi dari <code>device_nusaklim.csv</code>: '
    'Stn 222 Rambutan (Sumut), Stn 2179 Sei Pagar (Riau), Stn 248 Bentayan (Sumsel), Stn 267 Meliau (Kalbar) &ndash; pada periode 30 hari observasi aktual (21 Juli 2026 s/d 19 Agustus 2026, identik dengan periode data uji model produksi).<br/>'
    '&bull;&nbsp; Membandingkan metrik akurasi terhadap data aktual sensor AWS PPKS (rata-rata 4 stasiun):',
    style_body
))

om_tbl_data = [
    [Paragraph('Indikator (Ukuran Error)', style_table_header), Paragraph('Open-Meteo Global API', style_table_header), Paragraph('NusaKlim PPKS Local AI', style_table_header), Paragraph('Lebih Akurat (Rata-rata 4 Stasiun)', style_table_header)],
]
om_cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 3), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
for _ri, _k in enumerate(_IND_ORDER, start=1):
    _x = _ISUM[_k]
    _fmt = (lambda v: f'{v * 100:.1f}%') if _x['metric'] == 'Accuracy' else (lambda v: f'{v:.2f} {_x["unit"]}')
    om_tbl_data.append([
        Paragraph(f'<b>{_x["label"]}</b> ({"Accuracy" if _x["metric"] == "Accuracy" else "MAE"})', style_table_cell_bold),
        Paragraph(_fmt(_x['om_avg']), style_table_cell_center), Paragraph(_fmt(_x['nk_avg']), style_table_cell_center),
        Paragraph(f'<b>{_x["winner_avg"]}</b> (NusaKlim menang di {_x["nk_wins"]} dari {_x["n_stations"]} stasiun)', style_table_cell),
    ])
    om_cmds.append(('BACKGROUND', (2 if _x['winner_avg'] == 'NusaKlim' else 1, _ri), (2 if _x['winner_avg'] == 'NusaKlim' else 1, _ri), COLOR_BG_ACCENT))
tbl_om = Table(om_tbl_data, colWidths=[130, 90, 90, 205])
tbl_om.setStyle(TableStyle(om_cmds))
story.append(tbl_om)
story.append(Paragraph('Rincian per stasiun beserta kurva aktual vs Open-Meteo vs NusaKlim untuk ketujuh indikator ada di Laporan 5.', style_body))

story.append(Spacer(1, 4))
story.append(Paragraph('<b>B. Alasan Hasil Berbeda Antar Indikator:</b>', style_h2))
story.append(Paragraph(
    f'1. <b>Indikator yang dipengaruhi kondisi mikro kebun ({_join_labels(_NK_BETTER)}):</b> NusaKlim dilatih langsung dari sensor stasiun yang sama dengan data aktual, sehingga ikut menangkap karakter mikroklimat kebun, sedangkan Open-Meteo menyajikan rata-rata grid 11 km pada area terbuka. Khusus Kecepatan Angin, selisih besar terutama berasal dari perbedaan lokasi dan tinggi pengukuran.<br/>'
    f'2. <b>Tekanan Udara bersifat sinoptik:</b> pola tekanan ditentukan sistem cuaca regional yang diramal baik oleh model fisika numerik global, sehingga Open-Meteo lebih akurat (MAE {_ISUM["pressure_avg_hpa"]["om_avg"]:.2f} hPa vs {_ISUM["pressure_avg_hpa"]["nk_avg"]:.2f} hPa).<br/>'
    f'3. <b>Curah Hujan konvektif bersifat lokal dan stokastik:</b> hasilnya terbelah antar stasiun; rata-rata Open-Meteo sedikit lebih unggul (MAE {_ISUM["rainfall_total_mm"]["om_avg"]:.2f} mm vs {_ISUM["rainfall_total_mm"]["nk_avg"]:.2f} mm) &ndash; area prioritas perbaikan model berikutnya.',
    style_body
))

story.append(PageBreak())

# ==================== HALAMAN 7: TAHAP 7 ====================
story.append(Paragraph('8. Tahap 7: Pembangunan Layanan REST API Backend FastAPI (Langkah 3)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Apa yang Dilakukan pada Tahap Ini:</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; <b>Membangun Arsitektur Backend Modular:</b> Struktur paket di <code>api/</code> (<code>main.py</code>, <code>config.py</code>, <code>stations_db.py</code>, <code>models_schema.py</code>, <code>forecast_service.py</code>, <code>openmeteo_service.py</code>).<br/>'
    '&bull;&nbsp; <b>Menyediakan Endpoint REST Lengkap:</b> Termasuk health-check sistem, registri 183 stasiun AWS, ramalan 7 hari, komparasi Open-Meteo, dan pemicu retraining background.<br/>'
    '&bull;&nbsp; <b>Integrasi Server Eksternal:</b> Endpoint <code>/weather</code> (format nilai fisik ringkas + mode batch multi-stasiun, dilindungi API key) untuk sistem lain yang ingin menarik ramalan NusaKlim ke server mereka sendiri.<br/>'
    '&bull;&nbsp; <b>Pipeline Ingest Data Mentah Otomatis:</b> Endpoint <code>/ingest</code> menjalankan cleaning &amp; agregasi data mentah terbaru lalu retrain model dalam satu panggilan (&plusmn;24 menit), dengan kunci konkurensi agar tidak ada dua proses training tumpang tindih.<br/>'
    '&bull;&nbsp; <b>Mesin Rekomendasi Tindakan Agronomi Otomatis:</b> Menerjemahkan angka ramalan cuaca menjadi instruksi kerja harian bagi mandor dan manajer kebun kelapa sawit.<br/>'
    '&bull;&nbsp; <b>Verifikasi Pengujian Otomatis:</b> Skrip <code>tests/test_api.py</code> menguji seluruh 8 endpoint (13 skenario uji, termasuk otorisasi API key &amp; batas bulk) dengan hasil <b>100% PASS</b> dan latensi inferensi super cepat (&lt; 30 ms).',
    style_body
))

api_tbl = [
    [Paragraph('Metode', style_table_header), Paragraph('Endpoint URL', style_table_header), Paragraph('Fungsi &amp; Output', style_table_header), Paragraph('Peran dalam Sistem', style_table_header)],
    [Paragraph('<code>GET</code>', style_table_cell_bold), Paragraph('<code>/api/v1/health</code>', style_table_cell), Paragraph('Diagnostic status model, RAM, &amp; latensi (< 30 ms).', style_table_cell), Paragraph('Monitoring kesehatan server.', style_table_cell)],
    [Paragraph('<code>GET</code>', style_table_cell_bold), Paragraph('<code>/api/v1/stations</code>', style_table_cell), Paragraph('Mengambil 183 stasiun AWS + koordinat Lat/Lon.', style_table_cell), Paragraph('Peta &amp; dropdown filter kebun di web.', style_table_cell)],
    [Paragraph('<code>GET</code>', style_table_cell_bold), Paragraph('<code>/api/v1/forecast/{stn}</code>', style_table_cell_bold), Paragraph('<b>Ramalan 7 Hari (Suhu, RH, Hujan mm, Peluang %, Angin, &amp; Rekomendasi Agronomi).</b>', style_table_cell_bold), Paragraph('<b>Endpoint Utama Operasional Kebun.</b>', style_table_cell_bold)],
    [Paragraph('<code>GET</code>', style_table_cell_bold), Paragraph('<code>/api/v1/compare/{stn}</code>', style_table_cell), Paragraph('Komparasi live NusaKlim AI vs Open-Meteo API.', style_table_cell), Paragraph('Transparansi &amp; data atmosfer makro.', style_table_cell)],
    [Paragraph('<code>GET</code>', style_table_cell_bold), Paragraph('<code>/api/v1/weather/{stn}</code>', style_table_cell), Paragraph('Ramalan 7 Hari format nilai fisik ringkas (tanpa agronomi), dgn dataSource &amp; generatedAt. Butuh API key.', style_table_cell), Paragraph('Integrasi server eksternal.', style_table_cell)],
    [Paragraph('<code>GET</code>', style_table_cell_bold), Paragraph('<code>/api/v1/weather</code>', style_table_cell), Paragraph('Versi batch /weather - banyak stasiun sekaligus (maks 50 id). Butuh API key.', style_table_cell), Paragraph('Integrasi server eksternal (batch).', style_table_cell)],
    [Paragraph('<code>POST</code>', style_table_cell_bold), Paragraph('<code>/api/v1/retrain</code>', style_table_cell), Paragraph('Memicu retraining model otomatis di background (&plusmn;21 menit, 49 sub-model).', style_table_cell), Paragraph('MLOps &amp; Continuous Learning.', style_table_cell)],
    [Paragraph('<code>POST</code>', style_table_cell_bold), Paragraph('<code>/api/v1/ingest</code>', style_table_cell), Paragraph('Cleaning data mentah baru + agregasi + retrain dlm 1 panggilan (&plusmn;24 menit). Butuh API key.', style_table_cell), Paragraph('MLOps - data sensor baru.', style_table_cell)],
]
tbl_a = Table(api_tbl, colWidths=[45, 125, 205, 140])
tbl_a.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 3), (-1, 3), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_a)

story.append(Spacer(1, 4))
story.append(Paragraph('<b>B. Alasan Mengapa Dilakukan (Rasionalisasi Teknis):</b>', style_h2))
story.append(Paragraph(
    '&bull;&nbsp; <b>Kesiapan Integrasi Antarmuka Web / Mobile:</b> Backend FastAPI menyediakan kontrak data terstandar (Pydantic Schema JSON) yang langsung dapat dihubungkan ke UI Dashboard Website NusaKlim.<br/>'
    '&bull;&nbsp; <b>Nilai Bisnis Langsung bagi Mandor:</b> Rekomendasi agronomi otomatis mencegah pupuk hanyut ratusan juta rupiah saat hujan lebat dan mengoptimalkan ritme transportasi truk TBS ke pabrik (PKS).',
    style_body
))

story.append(PageBreak())

# ==================== HALAMAN 8: PANDUAN PENGOPERASIAN & MATRIKS ====================
story.append(Paragraph('9. Panduan Pengoperasian Sistem &amp; Matriks Berkas Lengkap', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph('<b>A. Cara Menjalankan Layanan Backend FastAPI:</b>', style_h2))
cmd_text = '&amp; "D:\\Projects\\Kodepanda\\Nusaklim\\nusaklim\\.venv\\Scripts\\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload'
story.append(Paragraph(
    f'Untuk menyalakan server backend FastAPI di environment lokal/server PPKS:<br/>'
    f'<font face="Courier" size="7"><code>{cmd_text}</code></font><br/>'
    f'Akses dokumentasi interaktif API di browser: <b>Swagger UI</b>: <code>http://127.0.0.1:8000/docs</code> | <b>ReDoc</b>: <code>http://127.0.0.1:8000/redoc</code>',
    style_body
))

story.append(Paragraph('<b>B. Matriks Seluruh Berkas Laporan PDF Resmi Proyek NusaKlim:</b>', style_h2))

docs_data = [
    [Paragraph('No', style_table_header), Paragraph('Nama File Laporan PDF Resmi', style_table_header), Paragraph('Topik Bahasan &amp; Lingkup Teknis', style_table_header)],
    [Paragraph('<b>1</b>', style_table_cell_center), Paragraph('<code>1.Laporan_Data_Cleaning_Interval_NusaKlim_PPKS.pdf</code>', style_table_cell_bold), Paragraph('Pembersihan 14,8 Juta Baris Data Interval 10-15 Menit &amp; Kamus Data.', style_table_cell)],
    [Paragraph('<b>2</b>', style_table_cell_center), Paragraph('<code>2.Laporan_Preprocessing_dan_EDA_NusaKlim_PPKS.pdf</code>', style_table_cell_bold), Paragraph('Agregasi Harian, Kepatuhan Notulen Rapat &amp; 8 Visualisasi Analisis EDA.', style_table_cell)],
    [Paragraph('<b>3</b>', style_table_cell_center), Paragraph('<code>3.Laporan_Model_Prediksi_Cuaca_7Hari_PPKS.pdf</code>', style_table_cell_bold), Paragraph('Pelatihan &amp; Validasi Model Prediksi 7-Hari Multi-Horizon, termasuk Benchmarking ML vs Deep Learning (Bab 3.4).', style_table_cell)],
    [Paragraph('<b>3b</b>', style_table_cell_center), Paragraph('<code>3b.Laporan_Analisis_Model_Per_Stasiun_vs_Global_PPKS.pdf</code>', style_table_cell_bold), Paragraph('Studi Lanjutan: Model Global (Gabungan) vs Model Per-Stasiun Lokal.', style_table_cell)],
    [Paragraph('<b>4</b>', style_table_cell_center), Paragraph('<code>4.Laporan_Audit_Gap_Data_dan_Ketahanan_Model_PPKS.pdf</code>', style_table_cell_bold), Paragraph('Audit Kontinuitas Data (84,5% Kelengkapan) &amp; Uji Ketahanan Stress-Test.', style_table_cell)],
    [Paragraph('<b>5</b>', style_table_cell_center), Paragraph('<code>5.Laporan_Komparasi_NusaKlim_vs_OpenMeteo_PPKS.pdf</code>', style_table_cell_bold), Paragraph('Validasi terhadap Data Aktual &amp; Komparasi Akurasi Open-Meteo API (Langkah 2).', style_table_cell)],
    [Paragraph('<b>6</b>', style_table_cell_center), Paragraph('<code>6.Dokumentasi_Lengkap_Pengerjaan_Proyek_NusaKlim_PPKS.pdf</code>', style_table_cell_bold), Paragraph('<b>Dokumentasi Master End-to-End Arsitektur, Flowchart, &amp; Implementasi.</b>', style_table_cell_bold)],
]
tbl_docs = Table(docs_data, colWidths=[20, 255, 240])
tbl_docs.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 8), (-1, 8), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.2),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_docs)

story.append(Spacer(1, 4))
story.append(make_callout_box(
    'Seluruh tahapan pengerjaan (Langkah 1: Model 7-Hari, Langkah 2: Komparasi Open-Meteo, Langkah 3: REST API Backend FastAPI) telah selesai 100%, teruji otomatis, dan siap diintegrasikan dengan Dashboard Web UI NusaKlim.',
    title='STATUS AKHIR PENGERJAAN PROYEK'
))

story.append(Spacer(1, 6))
sig_data = [
    [Paragraph('<b>Disiapkan Oleh:</b><br/><br/><br/><u><b>Yudha Pratama</b></u><br/>Data Analyst NusaKlim PPKS', style_table_cell),
     Paragraph('<b>Disetujui Oleh:</b><br/><br/><br/><u><b>Tim Peneliti &amp; IT NusaKlim</b></u><br/>Pusat Penelitian Kelapa Sawit (PPKS)', style_table_cell)]
]
tbl_sig = Table(sig_data, colWidths=[250, 255])
tbl_sig.setStyle(TableStyle([
    ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_sig)

print('Building Clean Master End-to-End Documentation PDF Report...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'Master PDF Successfully Generated at: {pdf_path}')
print(f'Master PDF File Size: {os.path.getsize(pdf_path):,} bytes')
