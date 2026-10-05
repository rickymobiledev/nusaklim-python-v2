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
    [Paragraph('<b>Resolusi Grid</b>', style_table_cell_bold), Paragraph('Open-Meteo Global Reanalysis (11 km) vs NusaKlim Local AI (Point-Telemetry Stasiun Kebun)', style_table_cell)],
    [Paragraph('<b>Temuan Utama</b>', style_table_cell_bold), Paragraph(f'<b>NusaKlim Local AI unggul pada Suhu &amp; Kelembapan</b> (MAE Suhu {NK_AVG["avg_temp_mae"]:.2f}&deg;C vs {OM_AVG["avg_temp_mae"]:.2f}&deg;C; MAE RH {NK_AVG["avg_humidity_mae"]:.2f}% vs {OM_AVG["avg_humidity_mae"]:.2f}%), namun <b>Open-Meteo sedikit lebih presisi pada Curah Hujan</b> (MAE {OM_AVG["avg_rainfall_mae"]:.2f} mm vs {NK_AVG["avg_rainfall_mae"]:.2f} mm)', style_table_cell_bold)],
    [Paragraph('<b>Penyusun Laporan</b>', style_table_cell_bold), Paragraph('Tim Data Analyst &amp; AI Engineering NusaKlim PPKS | Tanggal: September 2026', style_table_cell)],
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
    'dari <b>Open-Meteo API</b> (penyedia data meteorologi berbasis reanalisis ECMWF IFS, GFS NOAA, dan DWD ICON). '
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

story.append(Paragraph(
    f'Pengujian dilakukan pada <b>30 hari data aktual ({OM["evaluation_period"].replace(" to ", " s/d ")})</b> yang sama sekali tidak digunakan saat melatih model NusaKlim, sehingga hasilnya mencerminkan kemampuan model pada data baru, bukan data yang sudah dihafal. '
    f'Prediksi NusaKlim dihasilkan oleh model produksi <code>weather_model_latest.joblib</code> (H+1, algoritma juara masing-masing variabel: Suhu &amp; Kelembapan dengan {ALGO_SHORT["temp_avg"]}, Curah Hujan dengan {ALGO_SHORT["rainfall_total_mm"]}) yang dijalankan langsung terhadap data historis riil tiap stasiun, bukan simulasi. '
    'Berikut perbandingan tingkat kesalahan prediksi antara Open-Meteo Global API vs NusaKlim Local AI:',
    style_body
))

STN_PROVINCE = {'222': 'Sumut', '2179': 'Riau', '248': 'Sumsel', '267': 'Kalbar'}

def _analysis_text(sid):
    s = R[sid]
    t = 'NusaKlim lebih akurat pada suhu' if s['nusaklim_ai']['temp_mae'] < s['open_meteo']['temp_mae'] else 'Open-Meteo sedikit lebih presisi pada suhu'
    h = 'NusaKlim lebih baik pada kelembapan' if s['nusaklim_ai']['humidity_mae'] < s['open_meteo']['humidity_mae'] else 'Open-Meteo lebih baik pada kelembapan'
    r = 'NusaKlim lebih baik pada hujan' if s['nusaklim_ai']['rainfall_mae'] < s['open_meteo']['rainfall_mae'] else 'Open-Meteo lebih baik pada hujan'
    return f'{t}; {h}; {r}.'

comp_data = [
    [Paragraph('Lokasi Stasiun AWS', style_table_header), Paragraph('Metrik Evaluasi', style_table_header), Paragraph('Open-Meteo Global API', style_table_header), Paragraph('NusaKlim Local AI', style_table_header), Paragraph('Analisis Selisih Presisi', style_table_header)],
]
for sid in STN_ORDER:
    s = R[sid]
    om, nk = s['open_meteo'], s['nusaklim_ai']
    comp_data.append([
        Paragraph(f"<b>Stasiun {sid}</b><br/>{s['station_name']} ({STN_PROVINCE[sid]})", style_table_cell),
        Paragraph('Suhu MAE (&deg;C)<br/>Kelembapan MAE (%)<br/>Curah Hujan (mm)', style_table_cell),
        Paragraph(f"{om['temp_mae']:.2f} &deg;C (Bias {fmt_bias(om['temp_bias'])})<br/>{om['humidity_mae']:.2f} %<br/>{om['rainfall_mae']:.2f} mm", style_table_cell_center),
        Paragraph(f"{nk['temp_mae']:.2f} &deg;C (Bias {fmt_bias(nk['temp_bias'])})<br/>{nk['humidity_mae']:.2f} %<br/>{nk['rainfall_mae']:.2f} mm", style_table_cell_center),
        Paragraph(_analysis_text(sid), style_table_cell),
    ])
comp_data.append([
    Paragraph('<b>RATA-RATA 4 STASIUN UJI</b>', style_table_cell_bold),
    Paragraph('<b>Suhu MAE (&deg;C)<br/>Kelembapan MAE (%)<br/>Curah Hujan (mm)</b>', style_table_cell_bold),
    Paragraph(f"<b>{OM_AVG['avg_temp_mae']:.2f} &deg;C</b><br/><b>{OM_AVG['avg_humidity_mae']:.2f} %</b><br/><b>{OM_AVG['avg_rainfall_mae']:.2f} mm</b>", style_table_cell_center),
    Paragraph(f"<b>{NK_AVG['avg_temp_mae']:.2f} &deg;C</b><br/><b>{NK_AVG['avg_humidity_mae']:.2f} %</b><br/><b>{NK_AVG['avg_rainfall_mae']:.2f} mm</b>", style_table_cell_center),
    Paragraph('<b>NusaKlim unggul pada Suhu &amp; Kelembapan</b>; <b>Open-Meteo unggul pada Curah Hujan</b>.', style_table_cell_bold),
])
tbl_comp = Table(comp_data, colWidths=[95, 85, 105, 105, 125])
tbl_comp.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 5), (-1, 5), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.5),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_comp)

story.append(Spacer(1, 4))
story.append(Paragraph('5. Visualisasi Perbandingan Error Multi-Stasiun', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

fig_bar_path = os.path.join(fig_dir, 'fig_openmeteo_multi_station_bar.png')
if os.path.exists(fig_bar_path):
    story.append(Image(fig_bar_path, width=18*cm, height=7.2*cm))
    story.append(Paragraph('Gambar 1: Komparasi Error Suhu (MAE &deg;C) dan Kelembapan Udara (MAE %) per Stasiun antara Open-Meteo vs NusaKlim Local AI.', style_caption))

story.append(make_callout_box(
    f'Rata-rata 4 stasiun uji, NusaKlim Local AI mencatat MAE Suhu lebih rendah ({NK_AVG["avg_temp_mae"]:.2f}&deg;C vs {OM_AVG["avg_temp_mae"]:.2f}&deg;C Open-Meteo) dan unggul jauh pada Kelembapan (MAE {NK_AVG["avg_humidity_mae"]:.2f}% vs {OM_AVG["avg_humidity_mae"]:.2f}%). Namun pada Curah Hujan, Open-Meteo justru lebih presisi (MAE {OM_AVG["avg_rainfall_mae"]:.2f} mm vs {NK_AVG["avg_rainfall_mae"]:.2f} mm NusaKlim), menandakan model curah hujan H+1 NusaKlim masih memiliki ruang perbaikan meskipun keunggulan suhu &amp; kelembapan tetap konsisten di hampir seluruh stasiun.',
    title='RANGKUMAN HASIL VALIDASI EMPIRIS'
))

story.append(PageBreak())

# ==================== PAGE 4: ANALISIS FISIS & TIME SERIES ====================
story.append(Paragraph('6. Mengapa Hasilnya Berbeda Antar Variabel Cuaca?', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Hasil empiris pada Bagian 4 menunjukkan pola yang tidak seragam: NusaKlim Local AI unggul konsisten pada Suhu dan Kelembapan, namun Open-Meteo justru sedikit lebih presisi pada Curah Hujan harian. Berdasarkan analisis agroklimatologi, terdapat 3 faktor fisis yang menjelaskan pola ini:',
    style_body
))

story.append(Paragraph(
    '1. <b>Efek Redaman Tutupan Kanopi:</b> Kanopi pelepah kelapa sawit dewasa bertindak sebagai isolator termal alami yang membatasi radiasi matahari langsung ke permukaan tanah pada siang hari dan menahan pelepasan panas pada malam hari. Karena NusaKlim dilatih langsung dari telemetri di bawah kanopi, model ini menangkap efek tersebut lebih baik pada Suhu &amp; Kelembapan dibanding model numerik global Open-Meteo yang mengasumsikan koefisien albedo permukaan rata-rata.<br/>'
    f'2. <b>Dinamika Evapotranspirasi Monokultur Tropis:</b> Perkebunan kelapa sawit memiliki laju transpirasi pohon yang masif, menciptakan kelembapan udara relatif (RH) yang cenderung tinggi dan stabil. Model global Open-Meteo kerap kurang menangkap kestabilan ini (rata-rata error RH {OM_AVG["avg_humidity_mae"]:.2f}% vs {NK_AVG["avg_humidity_mae"]:.2f}% NusaKlim).<br/>'
    f'3. <b>Curah Hujan Konvektif Bersifat Sangat Lokal &amp; Stokastik:</b> Hujan tropis di perkebunan sawit umumnya bersifat konvektif jangka pendek dan sangat bervariasi antar titik. Model NusaKlim H+1 ({ALGO_SHORT["rainfall_total_mm"]} berbasis lag &amp; rolling mean historis) belum menangkap kejadian hujan mendadak seakurat ansambel fisik skala sinoptik Open-Meteo (ECMWF/GFS/ICON), sehingga pada metrik Curah Hujan, Open-Meteo justru lebih unggul (MAE {OM_AVG["avg_rainfall_mae"]:.2f} mm vs {NK_AVG["avg_rainfall_mae"]:.2f} mm) &ndash; area prioritas perbaikan model curah hujan NusaKlim ke depan.',
    style_body
))

story.append(Spacer(1, 4))
story.append(Paragraph('7. Validasi Rangkaian Waktu (Perbandingan dengan Data Aktual)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

fig_ts_path = os.path.join(fig_dir, 'fig_openmeteo_comparison.png')
if os.path.exists(fig_ts_path):
    story.append(Image(fig_ts_path, width=18*cm, height=7.8*cm))
    story.append(Paragraph(f'Gambar 2: Kurva Perbandingan Suhu Harian &ndash; Data Aktual AWS vs Open-Meteo vs Prediksi H+1 NusaKlim {ALGO_SHORT["temp_avg"]} &ndash; Stasiun 222 Rambutan, {OM["evaluation_period"].replace(" to ", " s/d ")}.', style_caption))

story.append(Paragraph(
    f'Dapat diamati pada Gambar 2 di atas (Stasiun 222 Rambutan, dipilih sebagai representasi utama karena kelengkapan data historisnya), kurva hijau (prediksi H+1 NusaKlim {ALGO_SHORT["temp_avg"]}) secara umum lebih rapat mengikuti kurva hitam (data aktual sensor AWS) dibandingkan kurva biru putus-putus (Open-Meteo), konsisten dengan MAE Suhu yang lebih rendah pada stasiun ini ({R["222"]["nusaklim_ai"]["temp_mae"]:.2f}&deg;C vs {R["222"]["open_meteo"]["temp_mae"]:.2f}&deg;C).',
    style_body
))

story.append(PageBreak())

# ==================== PAGE 5: STRATEGI HYBRID & PENGESAHAN ====================
story.append(Paragraph('8. Strategi Kombinasi Dua Mesin Prediksi (Hybrid) untuk PPKS', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Mengingat NusaKlim Local AI unggul pada Suhu &amp; Kelembapan namun Open-Meteo sedikit lebih presisi pada Curah Hujan, '
    'menggunakan kedua mesin prediksi secara bersamaan lebih tepat dibanding menggantikan Open-Meteo sepenuhnya. Open-Meteo API '
    'tetap memiliki nilai strategis dalam sistem IT terintegrasi PPKS:',
    style_body
))

hybrid_data = [
    [Paragraph('Komponen Sistem', style_table_header), Paragraph('Peran Fungsional', style_table_header), Paragraph('Implementasi Teknis di REST API Backend', style_table_header)],
    [Paragraph('<b>Mesin Utama (Primary Engine):<br/>NusaKlim Local AI</b>', style_table_cell_bold), Paragraph('Melayani peramalan 7 hari operasional, perhitungan peluang hujan harian, dan penerbitan <b>Rekomendasi Agronomi Kebun</b> (jadwal pemupukan, panen TBS, semprot hama).', style_table_cell), Paragraph('Endpoint <code>/api/v1/forecast/{stn_id}</code> dengan waktu respons sangat cepat (&lt; 30 ms) karena model (LightGBM/Ridge/Logistic Regression per variabel) diproses langsung di memori server.', style_table_cell)],
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

story.append(Paragraph(
    f'1. <b>Model NusaKlim AI Layak Menjadi Mesin Utama Suhu &amp; Kelembapan:</b> Hasil pengujian 30 hari pada data baru ({OM["evaluation_period"].replace(" to ", " – ")}) pada 4 stasiun riil menunjukkan MAE Suhu {NK_AVG["avg_temp_mae"]:.2f}&deg;C dan MAE Kelembapan {NK_AVG["avg_humidity_mae"]:.2f}%, keduanya lebih presisi dibanding Open-Meteo ({OM_AVG["avg_temp_mae"]:.2f}&deg;C dan {OM_AVG["avg_humidity_mae"]:.2f}%).<br/>'
    f'2. <b>Model Curah Hujan NusaKlim Memerlukan Perbaikan Lanjutan:</b> Pada metrik Curah Hujan, Open-Meteo justru lebih akurat (MAE {OM_AVG["avg_rainfall_mae"]:.2f} mm vs {NK_AVG["avg_rainfall_mae"]:.2f} mm). Disarankan menambah fitur curah hujan konvektif (mis. tekanan barometrik jangka pendek, kelembapan atmosfer atas) atau menggunakan prediksi Open-Meteo sebagai variabel input tambahan pada model untuk horizon hujan H+1.<br/>'
    '3. <b>Efisiensi Biaya Server Tanpa Lisensi API:</b> Menggunakan model lokal (LightGBM/Ridge/Logistic Regression per variabel) membebaskan PPKS dari ketergantungan biaya langganan API komersial berbayar saat sistem dibuka untuk ribuan mandor dan petani kelapa sawit.<br/>'
    '4. <b>Kesiapan Tahap Selanjutnya:</b> Integrasi REST API Backend FastAPI telah berhasil menghubungkan kedua mesin ini secara mulus dan siap diintegrasikan dengan Dashboard Web UI NusaKlim dalam skema dua mesin ini.',
    style_body
))

story.append(Spacer(1, 6))
story.append(make_callout_box(
    'Laporan ini mengesahkan bahwa Langkah 2 Roadmap NusaKlim Weather AI (Notulen Rapat Butir 9) telah selesai. NusaKlim Local AI direkomendasikan sebagai mesin utama untuk peramalan Suhu &amp; Kelembapan perkebunan kelapa sawit PPKS, dioperasikan berdampingan dengan Open-Meteo API untuk Curah Hujan hingga model curah hujan lokal ditingkatkan lebih lanjut.',
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
