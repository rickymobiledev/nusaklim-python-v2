import os, sys, json, pandas as pd, numpy as np
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
pdf_path = os.path.join(BASE_DIR, 'report', '5.Laporan_Komparasi_NusaKlim_vs_OpenMeteo_PPKS.pdf')
fig_dir = os.path.join(BASE_DIR, 'figures')

with open(os.path.join(BASE_DIR, 'openmeteo_benchmark_summary.json'), encoding='utf-8') as f:
    OM = json.load(f)

ALGO_SHORT = {k: v.split(' (')[0] for k, v in OM['algo_used'].items()}
STN_ORDER = ['222', '2179', '248', '267']
IND_ORDER_COVER = ['temp_avg', 'humidity_avg', 'rainfall_total_mm', 'solar_radiation_avg', 'pressure_avg_hpa', 'wind_speed_avg', 'wind_direction_name']


def _join(items):
    items = list(items)
    if not items:
        return '-'
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' dan ' + items[-1]
R = OM['station_results']
OM_AVG = OM['open_meteo_metrics']
NK_AVG = OM['nusaklim_local_ai_metrics']


def fmt_bias(b):
    return f"{'+' if b >= 0 else ''}{b:.2f}&deg;C"


def better(nk_val, om_val, lower_is_better=True):
    if lower_is_better:
        return 'NusaKlim' if nk_val < om_val else 'Open-Meteo'
    return 'NusaKlim' if nk_val > om_val else 'Open-Meteo'

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
        self.drawRightString(555, 805, 'Laporan Komparasi NusaKlim vs Open-Meteo API')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Dokumen Validasi Data Aktual & Komparasi Eksternal API PPKS')
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
style_cover_subtitle = ParagraphStyle('CoverSubtitle', parent=styles['Normal'], fontName='Arial', fontSize=10, leading=14, textColor=COLOR_BODY, alignment=1, spaceAfter=16)
style_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Arial-Bold', fontSize=11.5, leading=14.5, textColor=COLOR_PRIMARY, spaceBefore=8, spaceAfter=4, keepWithNext=True)
style_h2 = ParagraphStyle('SectionH2', parent=styles['Normal'], fontName='Arial-Bold', fontSize=9.5, leading=12.5, textColor=COLOR_SECONDARY, spaceBefore=6, spaceAfter=3, keepWithNext=True)
style_body = ParagraphStyle('BodyDark', parent=styles['Normal'], fontName='Arial', fontSize=8.2, leading=11.8, textColor=COLOR_BODY, spaceAfter=4, alignment=4)
style_callout = ParagraphStyle('CalloutText', parent=styles['Normal'], fontName='Arial-Italic', fontSize=7.8, leading=11, textColor=COLOR_PRIMARY)
style_table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=9.5, textColor=colors.white, alignment=1)
style_table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Arial', fontSize=7.2, leading=9.2, textColor=COLOR_BODY)
style_table_cell_bold = ParagraphStyle('TableCellBold', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.2, leading=9.2, textColor=COLOR_DARK)
style_table_cell_center = ParagraphStyle('TableCellCenter', parent=styles['Normal'], fontName='Arial', fontSize=7.2, leading=9.2, textColor=COLOR_BODY, alignment=1)
style_caption = ParagraphStyle('FigCaption', parent=styles['Normal'], fontName='Arial-Bold', fontSize=7.5, leading=9.5, textColor=COLOR_MUTED, alignment=1, spaceBefore=2, spaceAfter=6)

def make_callout_box(text, title='INSIGHT KOMPARATIF UTAMA', width=515):
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
story.append(HRFlowable(width='100%', thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=16))

story.append(Paragraph('LAPORAN VALIDASI DATA AKTUAL &amp; KOMPARASI AKURASI:<br/>NUSAKLIM LOCAL AI VS OPEN-METEO GLOBAL API', style_cover_title))
story.append(Paragraph('Studi Komparatif Presisi Ramalan Cuaca 4 Stasiun AWS Perkebunan Kelapa Sawit (Sumatera Utara, Riau, Sumatera Selatan, dan Kalimantan Barat) Berdasarkan Notulen Rapat PPKS Butir 9', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Mandat Notulen</b>', style_table_cell_bold), Paragraph('Notulen Rapat PPKS 20 Agustus 2026 Butir 9 (Integrasi &amp; Komparasi Open-Meteo API)', style_table_cell)],
    [Paragraph('<b>Stasiun Referensi</b>', style_table_cell_bold), Paragraph('4 Stasiun AWS Riil (device_nusaklim.csv): Stn 222 Rambutan (Sumut), Stn 2179 Sei Pagar (Riau), Stn 248 Bentayan (Sumsel), Stn 267 Meliau (Kalbar)', style_table_cell)],
    [Paragraph('<b>Periode Observasi</b>', style_table_cell_bold), Paragraph(f'{OM["evaluation_period"].replace(" to ", " s/d ")} (30 Hari Observasi Aktual &ndash; periode data uji yang sama dengan pengujian model produksi, data yang tidak dipakai saat melatih model)', style_table_cell)],
    [Paragraph('<b>Resolusi Grid</b>', style_table_cell_bold), Paragraph('Open-Meteo Global Forecast (grid 11 km) vs NusaKlim Local AI (Point-Telemetry Stasiun Kebun)', style_table_cell)],
    [Paragraph('<b>Temuan Utama</b>', style_table_cell_bold), Paragraph(f'Rata-rata 4 stasiun, <b>NusaKlim lebih akurat pada {_join([OM["indicator_summary"][k]["label"] for k in IND_ORDER_COVER if OM["indicator_summary"][k]["winner_avg"] == "NusaKlim"])}</b>, sedangkan <b>Open-Meteo lebih akurat pada {_join([OM["indicator_summary"][k]["label"] for k in IND_ORDER_COVER if OM["indicator_summary"][k]["winner_avg"] == "Open-Meteo"])}</b> (ketujuh indikator dibandingkan di tiap stasiun, Bab 4)', style_table_cell_bold)],
    [Paragraph('<b>Penyusun Laporan</b>', style_table_cell_bold), Paragraph('Tim Data Analyst &amp; AI Engineering NusaKlim PPKS | Tanggal: Oktober 2026', style_table_cell)],
]
tbl_cover = Table(cover_box_content, colWidths=[130, 385])
tbl_cover.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 4.5),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_cover)

story.append(PageBreak())

# ==================== PAGE 2: LATAR BELAKANG & METODOLOGI ====================
story.append(Paragraph('1. Latar Belakang &amp; Mandat Notulen Rapat PPKS', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Sesuai dengan <b>Notulen Rapat PPKS tanggal 20 Agustus 2026 Butir 9</b>, sistem peramalan cuaca internal '
    'NusaKlim diuji dan dibandingkan langsung dengan data peramalan global '
    'dari <b>Open-Meteo API</b> (penyedia data prakiraan cuaca global dari model ECMWF IFS, GFS NOAA, dan DWD ICON, diambil lewat Historical Forecast API). '
    'Tujuan pengujian ini adalah mengevaluasi apakah model kecerdasan buatan yang dilatih langsung '
    'dari data sensor cuaca perkebunan PPKS memberikan keunggulan akurasi yang signifikan dibandingkan prakiraan cuaca global publik.',
    style_body
))

story.append(Paragraph('2. Perbedaan Fundamental Arsitektur Model', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

arch_data = [
    [Paragraph('Kriteria Perbandingan', style_table_header), Paragraph('Open-Meteo Global API', style_table_header), Paragraph('NusaKlim PPKS Local AI', style_table_header)],
    [Paragraph('<b>Dasar Model</b>', style_table_cell_bold), Paragraph('Model Fisika Numerik Global (NWP: ECMWF / GFS).', style_table_cell), Paragraph(f'Machine Learning per-variabel (Suhu/Kelembapan: {ALGO_SHORT["temp_avg"]}; Curah Hujan: {ALGO_SHORT["rainfall_total_mm"]} - lihat Laporan 3 Tabel 3.3).', style_table_cell_bold)],
    [Paragraph('<b>Resolusi Spasial Grid</b>', style_table_cell_bold), Paragraph('Grid horizontal 11 km &times; 11 km (Regional).', style_table_cell), Paragraph('Point-Telemetry AWS (Mikroklimat spesifik kebun).', style_table_cell_bold)],
    [Paragraph('<b>Sensitivitas Kanopi Sawit</b>', style_table_cell_bold), Paragraph('Rendah (Mengasumsikan permukaan tanah terbuka/rata-rata).', style_table_cell), Paragraph('Tinggi pada Suhu &amp; Kelembapan; masih terbatas pada Curah Hujan konvektif lokal.', style_table_cell_bold)],
    [Paragraph('<b>Ketergantungan Internet</b>', style_table_cell_bold), Paragraph('Wajib koneksi internet stabil &amp; kuota API publik.', style_table_cell), Paragraph('Dapat beroperasi offline/on-premise di server lokal PPKS.', style_table_cell_bold)],
    [Paragraph('<b>Waktu Respons / Latensi</b>', style_table_cell_bold), Paragraph('200 &ndash; 800 ms per pemanggilan jaringan internet.', style_table_cell), Paragraph('&lt; 30 ms (diproses langsung dari memori server).', style_table_cell_bold)],
]
tbl_arch = Table(arch_data, colWidths=[120, 195, 200])
tbl_arch.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_arch)

story.append(Spacer(1, 4))
story.append(Paragraph('3. Profil Koordinat Stasiun Referensi Pengujian', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

stn_data = [
    [Paragraph('ID Stasiun', style_table_header), Paragraph('Nama Stasiun AWS', style_table_header), Paragraph('Provinsi', style_table_header), Paragraph('Koordinat (Lat, Lon)', style_table_header), Paragraph('Unit Pengelola', style_table_header), Paragraph('Karakteristik Agro-Ekologi', style_table_header)],
    [Paragraph('<b>Stn 222</b>', style_table_cell_center), Paragraph('Rambutan', style_table_cell_bold), Paragraph('Sumatera Utara', style_table_cell), Paragraph('3.379&deg; N, 99.142&deg; E', style_table_cell_center), Paragraph('PalmCo &ndash; Regional 1', style_table_cell_center), Paragraph('Dataran rendah Sumatera Utara, sentra perkebunan sawit tua.', style_table_cell)],
    [Paragraph('<b>Stn 2179</b>', style_table_cell_center), Paragraph('Sei Pagar', style_table_cell_bold), Paragraph('Riau', style_table_cell), Paragraph('0.326&deg; N, 101.352&deg; E', style_table_cell_center), Paragraph('PalmCo &ndash; Regional 3', style_table_cell_center), Paragraph('Kawasan gambut &amp; mineral basah Riau, kelembapan tinggi.', style_table_cell)],
    [Paragraph('<b>Stn 248</b>', style_table_cell_center), Paragraph('Bentayan', style_table_cell_bold), Paragraph('Sumatera Selatan', style_table_cell), Paragraph('2.456&deg; S, 104.199&deg; E', style_table_cell_center), Paragraph('PalmCo &ndash; Regional 7', style_table_cell_center), Paragraph('Dataran rendah Sumatera Selatan, curah hujan musiman tinggi.', style_table_cell)],
    [Paragraph('<b>Stn 267</b>', style_table_cell_center), Paragraph('Meliau', style_table_cell_bold), Paragraph('Kalimantan Barat', style_table_cell), Paragraph('0.073&deg; S, 110.289&deg; E', style_table_cell_center), Paragraph('PalmCo &ndash; Regional 5', style_table_cell_center), Paragraph('Areal khatulistiwa ekuatorial, dinamika konvektif kuat.', style_table_cell)],
]
story.append(Paragraph(
    'Keempat stasiun di atas diambil langsung dari data referensi perangkat <code>device_nusaklim.csv</code> (nama, koordinat, dan unit pengelola sebenarnya), dan dipilih karena memiliki data harian lengkap tanpa data yang hilang sepanjang periode uji 30 hari.',
    style_body
))
tbl_stn = Table(stn_data, colWidths=[45, 105, 70, 100, 80, 115])
tbl_stn.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_stn)

story.append(PageBreak())

# ==================== PAGE 3: HASIL EVALUASI KOMPARATIF ====================
story.append(Paragraph('4. Hasil Evaluasi Komparatif Multi-Stasiun', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

IND_ORDER = ['temp_avg', 'humidity_avg', 'rainfall_total_mm', 'solar_radiation_avg', 'pressure_avg_hpa', 'wind_speed_avg', 'wind_direction_name']
ISUM = OM['indicator_summary']
STN_PROVINCE = {'222': 'Sumut', '2179': 'Riau', '248': 'Sumsel', '267': 'Kalbar'}


def _fmt(v, metric, unit):
    if metric == 'Accuracy':
        return f'{v * 100:.1f}%'
    return f'{v:.2f} {unit}'


def _diff_text(om_v, nk_v, metric):
    if metric == 'Accuracy':
        d = (nk_v - om_v) * 100
        return f'{d:+.1f} poin persen'
    if om_v == 0:
        return '-'
    d = (om_v - nk_v) / om_v * 100
    return f'{d:+.0f}% (error NusaKlim {"lebih kecil" if d > 0 else "lebih besar"})'


NK_BETTER_AVG = [ISUM[k]['label'] for k in IND_ORDER if ISUM[k]['winner_avg'] == 'NusaKlim']
OM_BETTER_AVG = [ISUM[k]['label'] for k in IND_ORDER if ISUM[k]['winner_avg'] == 'Open-Meteo']


def _join(items):
    items = list(items)
    if not items:
        return '-'
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' dan ' + items[-1]


story.append(Paragraph(
    f'Pengujian dilakukan pada <b>30 hari data aktual ({OM["evaluation_period"].replace(" to ", " s/d ")})</b> yang sama sekali tidak digunakan saat melatih model NusaKlim, sehingga hasilnya mencerminkan kemampuan model pada data baru. '
    'Perbandingan dilakukan untuk <b>ketujuh indikator</b> (Suhu, Kelembapan, Curah Hujan, Radiasi Matahari, Tekanan Udara, Kecepatan Angin, Arah Mata Angin) pada <b>masing-masing stasiun</b>.',
    style_body
))
story.append(Paragraph('4.1 Cara Perhitungan Error', style_h2))
story.append(Paragraph(
    'Untuk setiap stasiun dan setiap indikator, hasil peramalan <b>Open-Meteo</b> dan hasil peramalan <b>NusaKlim</b> (model produksi <code>weather_model_latest.joblib</code>, prediksi H+1 atau satu hari ke depan, memakai algoritma juara masing-masing indikator sesuai Tabel 3.3 Laporan 3) '
    'dibandingkan dengan <b>data aktual sensor AWS pada tanggal yang sama</b>. Kesalahan dihitung sebagai <b>MAE</b> (rata-rata selisih absolut harian antara prediksi dan data aktual selama 30 hari) untuk enam indikator berupa angka. '
    'Arah Mata Angin berupa kategori (Utara/Timur/Selatan/Barat), sehingga MAE tidak dapat dihitung dan digantikan <b>Accuracy</b> (persentase hari dengan kategori yang benar). Makin kecil MAE dan makin besar Accuracy, makin akurat.',
    style_body
))
story.append(Paragraph(
    'Data Open-Meteo diambil per jam lalu dirangkum ke harian (zona waktu WIB) dengan aturan yang sama seperti data AWS: rata-rata untuk suhu, kelembapan, radiasi, tekanan, dan kecepatan angin; jumlah untuk curah hujan; arah angin dari rata-rata vektor kemudian dikategorikan memakai batas sudut yang sama dengan data AWS. '
    'Radiasi Open-Meteo memakai radiasi gelombang pendek (shortwave) rata-rata 24 jam dalam W/m&sup2;, dan tekanan memakai tekanan permukaan (<i>surface pressure</i>).',
    style_body
))

story.append(Paragraph('4.2 Hasil per Stasiun: 7 Indikator, Open-Meteo vs NusaKlim', style_h2))
win_fill = colors.HexColor('#DCFCE7')
for sid in STN_ORDER:
    s = R[sid]
    ind = s['indicators']
    n_nk = sum(1 for k in IND_ORDER if ind[k]['winner'] == 'NusaKlim')
    story.append(Paragraph(
        f'<b>Stasiun {sid} &ndash; {s["station_name"]} ({STN_PROVINCE[sid]})</b> &mdash; NusaKlim lebih akurat pada <b>{n_nk} dari 7 indikator</b>, Open-Meteo pada {7 - n_nk}:',
        style_body
    ))
    rows = [[Paragraph('Indikator', style_table_header), Paragraph('Ukuran Error', style_table_header), Paragraph('Open-Meteo', style_table_header),
             Paragraph('NusaKlim', style_table_header), Paragraph('Lebih Akurat', style_table_header), Paragraph('Selisih', style_table_header)]]
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 2.8), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for ri, k in enumerate(IND_ORDER, start=1):
        x = ind[k]
        rows.append([
            Paragraph(f'<b>{x["label"]}</b>', style_table_cell_bold),
            Paragraph('Accuracy (%)' if x['metric'] == 'Accuracy' else f'MAE ({x["unit"]})', style_table_cell),
            Paragraph(_fmt(x['om']['value'], x['metric'], x['unit']), style_table_cell_center),
            Paragraph(_fmt(x['nk']['value'], x['metric'], x['unit']), style_table_cell_center),
            Paragraph(f'<b>{x["winner"]}</b>', style_table_cell_center),
            Paragraph(_diff_text(x['om']['value'], x['nk']['value'], x['metric']), style_table_cell),
        ])
        col = 3 if x['winner'] == 'NusaKlim' else 2
        cmds.append(('BACKGROUND', (col, ri), (col, ri), win_fill))
    t = Table(rows, colWidths=[95, 80, 80, 80, 75, 105], repeatRows=1)
    t.setStyle(TableStyle(cmds))
    story.append(t)
    story.append(Spacer(1, 5))

story.append(Paragraph('4.3 Ringkasan Lintas 4 Stasiun', style_h2))
rows = [[Paragraph('Indikator', style_table_header), Paragraph('Ukuran Error', style_table_header), Paragraph('Rata-rata Open-Meteo', style_table_header),
         Paragraph('Rata-rata NusaKlim', style_table_header), Paragraph('Stasiun yang Dimenangkan NusaKlim', style_table_header), Paragraph('Lebih Akurat (Rata-rata)', style_table_header)]]
cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY), ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER), ('PADDING', (0, 0), (-1, -1), 2.8), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]
for ri, k in enumerate(IND_ORDER, start=1):
    x = ISUM[k]
    rows.append([
        Paragraph(f'<b>{x["label"]}</b>', style_table_cell_bold),
        Paragraph('Accuracy (%)' if x['metric'] == 'Accuracy' else f'MAE ({x["unit"]})', style_table_cell),
        Paragraph(_fmt(x['om_avg'], x['metric'], x['unit']), style_table_cell_center),
        Paragraph(_fmt(x['nk_avg'], x['metric'], x['unit']), style_table_cell_center),
        Paragraph(f'{x["nk_wins"]} dari {x["n_stations"]}', style_table_cell_center),
        Paragraph(f'<b>{x["winner_avg"]}</b>', style_table_cell_center),
    ])
    cmds.append(('BACKGROUND', (3 if x['winner_avg'] == 'NusaKlim' else 2, ri), (3 if x['winner_avg'] == 'NusaKlim' else 2, ri), win_fill))
t = Table(rows, colWidths=[95, 80, 80, 80, 90, 95], repeatRows=1)
t.setStyle(TableStyle(cmds))
story.append(t)
story.append(Spacer(1, 4))

_wind_bias = np.mean([R[s]['indicators']['wind_speed_avg']['om']['bias'] for s in STN_ORDER])
story.append(Paragraph(
    f'<b>Catatan agar perbandingan dibaca adil:</b> (1) Kecepatan angin sensor AWS terpasang di dalam areal kebun dan terbaca sangat rendah (rata-rata &plusmn;0,8 km/jam), sedangkan Open-Meteo menyajikan angin 10 meter pada area terbuka (rata-rata bias Open-Meteo {_wind_bias:+.1f} km/jam terhadap AWS). '
    'Besarnya selisih pada Kecepatan Angin karena itu sebagian besar adalah perbedaan titik dan ketinggian pengukuran, bukan semata kemampuan meramal. '
    '(2) Radiasi dan Kelembapan Open-Meteo juga memiliki bias sistematis pada beberapa stasiun (lihat Gambar 2 s/d 5), sehingga keunggulan NusaKlim pada indikator tersebut mencerminkan kelebihan model yang dilatih langsung dari sensor stasiun yang sama.',
    style_body
))

story.append(Spacer(1, 2))
story.append(Paragraph('5. Visualisasi Perbandingan Error Multi-Stasiun', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

fig_bar_path = os.path.join(fig_dir, 'fig_openmeteo_ratio_heatmap.png')
if os.path.exists(fig_bar_path):
    story.append(Image(fig_bar_path, width=17.5*cm, height=8.9*cm))
    story.append(Paragraph('Gambar 1: Rasio error NusaKlim terhadap Open-Meteo untuk 7 indikator pada 4 stasiun. Hijau = error NusaKlim lebih kecil (NusaKlim lebih akurat), merah = error Open-Meteo lebih kecil. Angka di dalam sel adalah MAE (Accuracy untuk Arah Mata Angin) Open-Meteo (OM) dan NusaKlim (NK), serta rasio errornya.', style_caption))

story.append(make_callout_box(
    f'Rata-rata 4 stasiun, <b>NusaKlim lebih akurat pada {_join(NK_BETTER_AVG)}</b>, sedangkan <b>Open-Meteo lebih akurat pada {_join(OM_BETTER_AVG)}</b> '
    f'(Curah Hujan: MAE {ISUM["rainfall_total_mm"]["om_avg"]:.2f} mm vs {ISUM["rainfall_total_mm"]["nk_avg"]:.2f} mm; Tekanan Udara: {ISUM["pressure_avg_hpa"]["om_avg"]:.2f} hPa vs {ISUM["pressure_avg_hpa"]["nk_avg"]:.2f} hPa). '
    'Tidak ada satu mesin yang lebih baik untuk semua indikator, sehingga penggunaan keduanya secara bersamaan (Bab 8) lebih tepat.',
    title='RANGKUMAN HASIL VALIDASI EMPIRIS'
))

story.append(PageBreak())

# ==================== PAGE 4: ANALISIS FISIS & TIME SERIES ====================
story.append(Paragraph('6. Mengapa Hasilnya Berbeda Antar Indikator?', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

_rain_nk_stn = [s for s in STN_ORDER if R[s]['indicators']['rainfall_total_mm']['winner'] == 'NusaKlim']
_rain_om_stn = [s for s in STN_ORDER if R[s]['indicators']['rainfall_total_mm']['winner'] == 'Open-Meteo']
_press_om = sum(1 for s in STN_ORDER if R[s]['indicators']['pressure_avg_hpa']['winner'] == 'Open-Meteo')
_hum_bias = [R[s]['indicators']['humidity_avg']['om']['bias'] for s in STN_ORDER]
_sol_bias = [R[s]['indicators']['solar_radiation_avg']['om']['bias'] for s in STN_ORDER]

story.append(Paragraph(
    f'Hasil pada Bab 4 tidak seragam: rata-rata 4 stasiun, NusaKlim lebih akurat pada {_join(NK_BETTER_AVG)}, sedangkan Open-Meteo lebih akurat pada {_join(OM_BETTER_AVG)}. '
    'Beberapa faktor berikut menjelaskan pola ini:',
    style_body
))
story.append(Paragraph(
    '1. <b>Indikator yang dipengaruhi kondisi mikro kebun (Suhu, Kelembapan, Radiasi, Angin):</b> NusaKlim dilatih langsung dari sensor stasiun yang sama dengan data aktual, sehingga ikut menangkap karakter mikroklimat di bawah kanopi sawit. '
    f'Open-Meteo menyajikan nilai rata-rata grid 11 km pada area terbuka, sehingga muncul selisih sistematis, misalnya bias Kelembapan antara {min(_hum_bias):+.1f}% dan {max(_hum_bias):+.1f}% serta bias Radiasi antara {min(_sol_bias):+.0f} dan {max(_sol_bias):+.0f} W/m&sup2; terhadap sensor AWS.<br/>'
    f'2. <b>Tekanan Udara bersifat sinoptik (skala besar):</b> pola tekanan ditentukan sistem cuaca regional yang memang diramal dengan baik oleh model fisika numerik global, sehingga Open-Meteo lebih akurat pada {_press_om} dari 4 stasiun. NusaKlim hanya memakai riwayat tekanan stasiun sendiri. Meskipun demikian, selisih absolutnya kecil (MAE kurang dari 1,5 hPa pada kedua mesin).<br/>'
    f'3. <b>Curah Hujan konvektif bersifat sangat lokal dan sulit diramal:</b> hujan tropis di perkebunan umumnya konvektif jangka pendek. Hasilnya pun terbelah: NusaKlim lebih akurat di stasiun {_join(_rain_nk_stn)}, Open-Meteo di stasiun {_join(_rain_om_stn)}; rata-rata Open-Meteo sedikit lebih unggul '
    f'(MAE {ISUM["rainfall_total_mm"]["om_avg"]:.2f} mm vs {ISUM["rainfall_total_mm"]["nk_avg"]:.2f} mm). Curah hujan tetap menjadi area prioritas perbaikan model NusaKlim.<br/>'
    '4. <b>Kecepatan dan Arah Angin:</b> NusaKlim jauh lebih akurat, tetapi sebagian besar selisihnya berasal dari perbedaan lokasi dan tinggi pengukuran (lihat catatan Bab 4.3), sehingga angka ini sebaiknya tidak dibaca sebagai keunggulan prediksi murni.',
    style_body
))

story.append(Spacer(1, 4))
story.append(Paragraph('7. Validasi Rangkaian Waktu: Kurva Aktual vs Open-Meteo vs NusaKlim', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))
story.append(Paragraph(
    'Gambar 2 s/d 5 menampilkan kurva harian untuk <b>ketujuh indikator pada masing-masing stasiun</b>: garis hitam adalah data aktual sensor AWS, garis biru putus-putus adalah Open-Meteo, dan garis hijau adalah prediksi H+1 NusaKlim. '
    'Judul tiap panel menyebutkan mesin yang lebih akurat pada indikator tersebut, dan legenda memuat nilai MAE (atau Accuracy untuk Arah Mata Angin).',
    style_body
))
for fig_i, sid in enumerate(STN_ORDER, start=2):
    s = R[sid]
    ind = s['indicators']
    nk_list = [ind[k]['label'] for k in IND_ORDER if ind[k]['winner'] == 'NusaKlim']
    om_list = [ind[k]['label'] for k in IND_ORDER if ind[k]['winner'] == 'Open-Meteo']
    fp = os.path.join(fig_dir, f'fig_openmeteo_ts_{sid}.png')
    story.append(PageBreak())
    if os.path.exists(fp):
        story.append(Image(fp, width=16.0*cm, height=18.46*cm))
    story.append(Paragraph(f'Gambar {fig_i}: Kurva Perbandingan Data Aktual AWS vs Open-Meteo vs Prediksi H+1 NusaKlim untuk 7 Indikator &ndash; Stasiun {sid} {s["station_name"]} ({STN_PROVINCE[sid]}), {OM["evaluation_period"].replace(" to ", " s/d ")}.', style_caption))
    story.append(Paragraph(
        f'Pada Stasiun {sid} {s["station_name"]}, NusaKlim lebih akurat pada <b>{_join(nk_list) if nk_list else "-"}</b>; Open-Meteo lebih akurat pada <b>{_join(om_list) if om_list else "-"}</b>.',
        style_body
    ))

story.append(PageBreak())

# ==================== PAGE 5: STRATEGI HYBRID & PENGESAHAN ====================
story.append(Paragraph('8. Strategi Kombinasi Dua Mesin Prediksi (Hybrid) untuk PPKS', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    f'Mengingat NusaKlim Local AI lebih akurat pada {_join(NK_BETTER_AVG)} sedangkan Open-Meteo lebih akurat pada {_join(OM_BETTER_AVG)}, '
    'menggunakan kedua mesin prediksi secara bersamaan lebih tepat dibanding menggantikan Open-Meteo sepenuhnya. Open-Meteo API '
    'tetap memiliki nilai strategis dalam sistem IT terintegrasi PPKS:',
    style_body
))

hybrid_data = [
    [Paragraph('Komponen Sistem', style_table_header), Paragraph('Peran Fungsional', style_table_header), Paragraph('Implementasi Teknis di REST API Backend', style_table_header)],
    [Paragraph('<b>Mesin Utama (Primary Engine):<br/>NusaKlim Local AI</b>', style_table_cell_bold), Paragraph('Melayani peramalan 7 hari operasional, perhitungan peluang hujan harian, dan penerbitan <b>Rekomendasi Agronomi Kebun</b> (jadwal pemupukan, panen TBS, semprot hama).', style_table_cell), Paragraph('Endpoint <code>/api/v1/forecast/{stn_id}</code> dengan waktu respons sangat cepat (&lt; 30 ms) karena model (LightGBM atau Ridge Regression per indikator) diproses langsung di memori server.', style_table_cell)],
    [Paragraph('<b>Mesin Pendukung (Cadangan):<br/>Open-Meteo Global API</b>', style_table_cell_bold), Paragraph('Berfungsi sebagai sumber data atmosfer makro jika ada stasiun baru yang belum memiliki data historis sama sekali, serta sebagai tolok ukur komparasi transparansi publik.', style_table_cell), Paragraph('Endpoint <code>/api/v1/compare/{stn_id}</code>, diakses secara asinkron (tidak memblokir proses lain) menggunakan pustaka HTTPX.', style_table_cell)],
]
tbl_hybrid = Table(hybrid_data, colWidths=[130, 200, 185])
tbl_hybrid.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_hybrid)

story.append(Spacer(1, 4))
story.append(Paragraph('9. Kesimpulan &amp; Rekomendasi Manajerial', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

_isu = OM['indicator_summary']
story.append(Paragraph(
    f'1. <b>NusaKlim Layak Menjadi Mesin Utama untuk {_join(NK_BETTER_AVG)}:</b> pada pengujian 30 hari ({OM["evaluation_period"].replace(" to ", " – ")}) di 4 stasiun riil, NusaKlim memiliki error rata-rata lebih kecil (Suhu MAE {_isu["temp_avg"]["nk_avg"]:.2f}&deg;C vs {_isu["temp_avg"]["om_avg"]:.2f}&deg;C; Kelembapan {_isu["humidity_avg"]["nk_avg"]:.2f}% vs {_isu["humidity_avg"]["om_avg"]:.2f}%; Radiasi {_isu["solar_radiation_avg"]["nk_avg"]:.1f} vs {_isu["solar_radiation_avg"]["om_avg"]:.1f} W/m&sup2;; Arah Angin Accuracy {_isu["wind_direction_name"]["nk_avg"]*100:.0f}% vs {_isu["wind_direction_name"]["om_avg"]*100:.0f}%). Catatan: keunggulan Kecepatan Angin sebagian besar berasal dari perbedaan lokasi dan tinggi pengukuran (Bab 4.3).<br/>'
    f'2. <b>Open-Meteo Lebih Akurat pada {_join(OM_BETTER_AVG)}:</b> Curah Hujan (MAE {_isu["rainfall_total_mm"]["om_avg"]:.2f} mm vs {_isu["rainfall_total_mm"]["nk_avg"]:.2f} mm NusaKlim) dan Tekanan Udara ({_isu["pressure_avg_hpa"]["om_avg"]:.2f} hPa vs {_isu["pressure_avg_hpa"]["nk_avg"]:.2f} hPa). Disarankan menjadikan prediksi Open-Meteo sebagai fitur tambahan model untuk kedua indikator ini, atau menampilkannya berdampingan sebagai pembanding.<br/>'
    '3. <b>Efisiensi Biaya Server Tanpa Lisensi API:</b> Menggunakan model lokal (LightGBM atau Ridge Regression per indikator) membebaskan PPKS dari ketergantungan biaya langganan API komersial berbayar saat sistem dibuka untuk ribuan mandor dan petani kelapa sawit.<br/>'
    '4. <b>Kesiapan Tahap Selanjutnya:</b> Integrasi REST API Backend FastAPI telah berhasil menghubungkan kedua mesin ini secara mulus dan siap diintegrasikan dengan Dashboard Web UI NusaKlim dalam skema dua mesin ini.',
    style_body
))

story.append(Spacer(1, 6))
story.append(make_callout_box(
    f'Laporan ini mengesahkan bahwa Langkah 2 Roadmap NusaKlim Weather AI (Notulen Rapat Butir 9) telah selesai. NusaKlim Local AI direkomendasikan sebagai mesin utama untuk {_join(NK_BETTER_AVG)}, dioperasikan berdampingan dengan Open-Meteo API untuk {_join(OM_BETTER_AVG)} hingga model lokal untuk indikator tersebut ditingkatkan lebih lanjut.',
    title='PERNYATAAN PENGESAHAN HASIL VALIDASI'
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

print('Building Open-Meteo Master PDF Report...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
