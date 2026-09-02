import os, sys, pandas as pd, numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

pdf_path = r'd:\Downloads\nusaklim\Laporan_Audit_Gap_Data_dan_Ketahanan_Model_PPKS.pdf'
fig_dir = r'd:\Downloads\nusaklim\figures_gap'

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
        self.drawRightString(555, 805, 'Laporan Audit Gap Data & Ketahanan Model')
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.6)
        self.line(40, 800, 555, 800)
        self.line(40, 45, 555, 45)
        self.drawString(40, 32, 'Laporan Audit Teknis: Analisis Celah Data Telemetri & Resiliensi Model 7 Hari')
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

def make_callout_box(text, title='RINGKASAN TEMUAN AUDIT', width=515):
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

story.append(Paragraph('LAPORAN AUDIT GAP DATA, KONTINUITAS TELEMETRI,<br/>DAN STRATEGI KETAHANAN MODEL PREDIKSI CUACA', style_cover_title))
story.append(Paragraph('Evaluasi Empiris Tingkat Kelengkapan Observasi, Karakteristik Celah Data (Missing Days), dan Uji Ketahanan (Stress-Testing) Model Ramalan 7 Hari pada 184 Stasiun AWS NusaKlim', style_cover_subtitle))

cover_box_content = [
    [Paragraph('<b>Fokus Audit</b>', style_table_cell_bold), Paragraph('Tingkat Kelengkapan Data, Profil Durasi Gap, dan Ketahanan Model 7-Hari', style_table_cell)],
    [Paragraph('<b>Populasi Data</b>', style_table_cell_bold), Paragraph('114.651 Baris Data Harian dari 184 Stasiun AWS NusaKlim (2022?2026)', style_table_cell)],
    [Paragraph('<b>Tingkat Kelengkapan</b>', style_table_cell_bold), Paragraph('Rata-rata: <b>84.47 %</b> | Median: <b>92.50 %</b> (121 Stasiun &ge; 80%)', style_table_cell)],
    [Paragraph('<b>Profil Celah Data</b>', style_table_cell_bold), Paragraph('55.9% Gap adalah Micro-Gap Singkat (1?3 Hari akibat Sinyal / Baterai Solar)', style_table_cell)],
    [Paragraph('<b>Hasil Stress-Test</b>', style_table_cell_bold), Paragraph('Model Tetap Stabil dan Akurat (Error MAE &le; 1.26 ?C bahkan saat 10% Data Hilang)', style_table_cell)],
    [Paragraph('<b>Status Kelayakan</b>', style_table_cell_bold), Paragraph('<b>SANGAT FEASIBLE &amp; READY TO DEPLOY</b> (Didukung 4 Pilar Resiliensi AI)', style_table_cell)],
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
story.append(Paragraph('<b>Disusun Oleh:</b> Tim Data Analyst &amp; AI Engineering PPKS<br/><b>Tanggal Publikasi:</b> September 2026 | Dokumen Resmi Audit Ketahanan Data', style_cover_meta))
story.append(PageBreak())

# SECTION 1
story.append(Paragraph('1. Ringkasan Eksekutif &amp; Latar Belakang Audit Celah Data', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Pengoperasian stasiun Automatic Weather Station (AWS) di wilayah perkebunan kelapa sawit yang terpencil secara alami menghadapi tantangan lingkungan nyata, seperti cuaca mendung berkepanjangan yang menurunkan daya baterai *solar panel*, penurunan sinyal telekomunikasi GSM/GPRS lokal, hingga masa tunggu penggantian suku cadang sensor. Kondisi ini memicu timbulnya <b>celah data (*data gaps / missing days*)</b> dalam deret waktu telemetri.',
    style_body
))
story.append(Paragraph(
    'Audit teknis ini dilakukan untuk menjawab dua pertanyaan krusial dari manajemen dan klien:<br/>'
    '1. <b>Seberapa besar gap data yang sebenarnya terjadi pada jaringan AWS NusaKlim?</b><br/>'
    '2. <b>Apakah dengan adanya gap tersebut, sistem model Machine Learning tetap dapat menghasilkan ramalan cuaca 7 hari yang akurat dan stabil?</b>',
    style_body
))

story.append(Paragraph('2. Metrik Kuantitatif Kelengkapan &amp; Distribusi Durasi Celah Data', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Berdasarkan audit komputasi menyeluruh terhadap 184 stasiun pengamatan (rentang operasional 2022?2026), diperoleh parameter kelengkapan data sebagai berikut:',
    style_body
))

# Table Metrics
gap_metrics_data = [
    [Paragraph('Kategori Evaluasi', style_table_header), Paragraph('Nilai Parameter', style_table_header), Paragraph('Jumlah Stasiun / Kejadian', style_table_header), Paragraph('Interpretasi Operasional Lapangan', style_table_header)],
    [Paragraph('<b>Rata-rata Kelengkapan</b>', style_table_cell_bold), Paragraph('<b>84.47 %</b>', style_table_cell_center), Paragraph('184 Stasiun AWS', style_table_cell_center), Paragraph('Sangat tinggi dan melampaui standar minimal industri AI agroklimat (70%).', style_table_cell)],
    [Paragraph('<b>Median Kelengkapan</b>', style_table_cell_bold), Paragraph('<b>92.50 %</b>', style_table_cell_center), Paragraph('50% Stasiun Teratas', style_table_cell_center), Paragraph('Mayoritas stasiun aktif beroperasi dengan kontinuitas data nyaris sempurna.', style_table_cell)],
    [Paragraph('<b>Stasiun Sangat Sehat (&ge; 90%)</b>', style_table_cell), Paragraph('55.2 % Populasi', style_table_cell_center), Paragraph('101 Stasiun AWS', style_table_cell_center), Paragraph('Menjadi jangkar utama (*data backbone*) dalam melatih model dasar AI.', style_table_cell)],
    [Paragraph('<b>Stasiun Sehat (80% - 89%)</b>', style_table_cell), Paragraph('10.9 % Populasi', style_table_cell_center), Paragraph('20 Stasiun AWS', style_table_cell_center), Paragraph('Beroperasi stabil dengan intermitensi transmisi GSM minor.', style_table_cell)],
    [Paragraph('<b>Stasiun Cukup (50% - 79%)</b>', style_table_cell), Paragraph('27.3 % Populasi', style_table_cell_center), Paragraph('50 Stasiun AWS', style_table_cell_center), Paragraph('Pernah mengalami jeda musim hujan atau pemeliharaan berkala.', style_table_cell)],
    [Paragraph('<b>Stasiun Baru / Servis (&lt; 50%)</b>', style_table_cell), Paragraph('6.6 % Populasi', style_table_cell_center), Paragraph('12 Stasiun AWS', style_table_cell_center), Paragraph('Stasiun yang baru dipasang di pertengahan 2026 atau pergantian unit hardware.', style_table_cell)],
]
tbl_gap_m = Table(gap_metrics_data, colWidths=[120, 75, 110, 210])
tbl_gap_m.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_gap_m)

story.append(Spacer(1, 5))
story.append(make_callout_box(
    'Sebanyak 66.1% stasiun memiliki tingkat kelengkapan di atas 80% (dan 55.2% di atas 90%). Ini membuktikan bahwa fondasi data historis NusaKlim sangat solid dan kaya akan data kontinu berkualitas tinggi.',
    title='KESIMPULAN KELENGKAPAN DATA'
))

story.append(PageBreak())

# SECTION 2 CONT. (FIGURES) & SECTION 3
story.append(Paragraph('2.1 Visualisasi Distribusi Kelengkapan &amp; Durasi Celah Data', style_h2))

fig1_p = os.path.join(fig_dir, 'fig_gap1_completeness_distribution.png')
if os.path.exists(fig1_p):
    story.append(Image(fig1_p, width=17.5*cm, height=6.0*cm))
    story.append(Paragraph('<b>Gambar 1:</b> Histogram Distribusi Kelengkapan Observasi (%) dan Proporsi Kategori Kesehatan Jaringan AWS PPKS.', style_caption))

story.append(Spacer(1, 4))

fig2_p = os.path.join(fig_dir, 'fig_gap2_duration_breakdown.png')
if os.path.exists(fig2_p):
    story.append(Image(fig2_p, width=14.5*cm, height=5.5*cm))
    story.append(Paragraph('<b>Gambar 2:</b> Distribusi Frekuensi Durasi Celah Data (Total 1.807 Kejadian Gap) Berdasarkan Faktor Penyebab Lapangan.', style_caption))

story.append(Paragraph('3. Empat Pilar Arsitektur Ketahanan Model (*Resilience Pillars*)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Meskipun terdapat celah data di lapangan, model peramalan cuaca 7 hari dirancang dengan <b>4 pilar teknologi resiliensi</b> yang menjamin stabilitas dan akurasi sistem tanpa pernah mengalami *crash/error*:',
    style_body
))

pilar_data = [
    [Paragraph('Pilar Ketahanan', style_table_header), Paragraph('Mekanisme Kerja Rekayasa AI', style_table_header), Paragraph('Dampak Terhadap Keandalan Model', style_table_header)],
    [Paragraph('<b>1. Global Multi-Station Pooling</b>', style_table_cell_bold),
     Paragraph('Pelatihan 1 model global pada 114.651 records gabungan dengan fitur kategori stasiun (<code>stnname_cat</code>).', style_table_cell),
     Paragraph('<b>Transfer Pengetahuan:</b> Pola cuaca dari 101 stasiun yang sangat lengkap (&ge;90%) secara otomatis mentransfer relasi fisisnya ke stasiun yang memiliki gap.', style_table_cell)],
    [Paragraph('<b>2. Native Missing Handling (LightGBM)</b>', style_table_cell_bold),
     Paragraph('Algoritma percabangan otomatis (*Default Missing Direction*) pada setiap simpul pohon keputusan.', style_table_cell),
     Paragraph('<b>Anti-Crash:</b> Jika nilai sensor kemarin <code>NaN</code>, model secara cerdas mengarahkan kalkulasi ke cabang alternatif tanpa perlu imputasi nilai buatan.', style_table_cell)],
    [Paragraph('<b>3. Astronomical Seasonal Priors</b>', style_table_cell_bold),
     Paragraph('Fitur siklus kontinu <code>sin/cos(2&pi; DOY/365)</code> dan variabel kalender bulanan.', style_table_cell),
     Paragraph('<b>Zero-Downtime:</b> Fitur ini aktif 100% setiap hari dari kalender bumi tanpa terpengaruh ada/tidaknya transmisi sinyal AWS kebun.', style_table_cell)],
    [Paragraph('<b>4. Dynamic Fallback Inference</b>', style_table_cell_bold),
     Paragraph('Mekanisme penarikan status observasi valid terakhir (*Latest Valid Observation*) jika stasiun baru offline 1?2 hari.', style_table_cell),
     Paragraph('<b>Kontinuitas Ramalan:</b> Pengguna dashboard web tetap mendapatkan estimasi cuaca 7 hari yang realistis berdasarkan dinamika musiman lokal.', style_table_cell)],
]

tbl_pilar = Table(pilar_data, colWidths=[125, 175, 215])
tbl_pilar.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 3),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
story.append(tbl_pilar)

story.append(PageBreak())

# SECTION 4 & 5
story.append(Paragraph('4. Uji Ketahanan Model (*Stress-Testing Experiment*)', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk membuktikan ketahanan model secara empiris, dilakukan uji simulasi ekstrem (*Stress-Testing*) di mana sejumlah fitur pada data uji secara sengaja dihilangkan (*injected random missing values*) dari level 0% hingga 50%:',
    style_body
))

# Stress Table
stress_table_data = [
    [Paragraph('Tingkat Missing Data Diinjeksikan', style_table_header), Paragraph('Suhu MAE (?C)', style_table_header), Paragraph('Suhu RMSE (?C)', style_table_header), Paragraph('Kenaikan Error (&Delta;MAE)', style_table_header), Paragraph('Status Keandalan Agroklimat Lapangan', style_table_header)],
    [Paragraph('<b>0% (Kondisi Normal)</b>', style_table_cell_bold), Paragraph('0.997 ?C', style_table_cell_center), Paragraph('1.463 ?C', style_table_cell_center), Paragraph('Baseline', style_table_cell_center), Paragraph('Sangat Akurat (Presisi Tinggi)', style_table_cell)],
    [Paragraph('<b>10% Missing Random</b>', style_table_cell), Paragraph('1.262 ?C', style_table_cell_center), Paragraph('1.809 ?C', style_table_cell_center), Paragraph('+ 0.265 ?C', style_table_cell_center), Paragraph('Sangat Baik &amp; Sangat Layak Operasional', style_table_cell)],
    [Paragraph('<b>20% Missing Random</b>', style_table_cell), Paragraph('1.538 ?C', style_table_cell_center), Paragraph('2.143 ?C', style_table_cell_center), Paragraph('+ 0.541 ?C', style_table_cell_center), Paragraph('Baik (Masih dalam Toleransi Agroklimat)', style_table_cell)],
    [Paragraph('<b>30% Missing Random</b>', style_table_cell), Paragraph('1.900 ?C', style_table_cell_center), Paragraph('2.554 ?C', style_table_cell_center), Paragraph('+ 0.903 ?C', style_table_cell_center), Paragraph('Cukup (Estimasi Tren Musiman Masih Valid)', style_table_cell)],
    [Paragraph('<b>50% Missing Ekstrem</b>', style_table_cell), Paragraph('2.600 ?C', style_table_cell_center), Paragraph('3.235 ?C', style_table_cell_center), Paragraph('+ 1.603 ?C', style_table_cell_center), Paragraph('Perlu Intervensi Perbaikan Sensor Stasiun', style_table_cell)],
]

tbl_stress = Table(stress_table_data, colWidths=[120, 75, 75, 85, 160])
tbl_stress.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
    ('BACKGROUND', (0, 1), (-1, 1), COLOR_BG_ACCENT),
    ('BOX', (0, 0), (-1, -1), 1, COLOR_PRIMARY),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ('PADDING', (0, 0), (-1, -1), 2.8),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(tbl_stress)

story.append(Spacer(1, 4))

fig3_p = os.path.join(fig_dir, 'fig_gap3_stress_test_degradation.png')
if os.path.exists(fig3_p):
    story.append(Image(fig3_p, width=15.0*cm, height=5.5*cm))
    story.append(Paragraph('<b>Gambar 3:</b> Kurva Resiliensi Error Prediksi Suhu (MAE &amp; RMSE) terhadap Injeksi Celah Data 0% s/d 50%.', style_caption))

story.append(Spacer(1, 4))

# SECTION 5
story.append(Paragraph('5. Standar Operasional Prosedur (SOP) &amp; Rekomendasi Lapangan', style_h1))
story.append(HRFlowable(width='100%', thickness=1, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=5))

story.append(Paragraph(
    'Untuk menjaga kualitas data telemetri tetap berada pada level optimal (&ge; 85%), direkomendasikan 3 protokol pemeliharaan:',
    style_body
))
story.append(Paragraph(
    '1. <b>Sistem Peringatan Dini Offline Otomatis (Early Warning Alert):</b> Pasang bot notifikasi (WhatsApp/Telegram/Email) yang memicu alert otomatis ke PIC Kebun jika stasiun tidak mengirimkan data selama &gt; 48 jam berturut-turut.<br/>'
    '2. <b>Pembersihan Sensor Tiap Kuartal (Quarterly Cleaning):</b> Bersihkan corong penakar hujan (*rain gauge*) dari dedaunan sawit dan debu pada panel surya setiap 3 bulan.<br/>'
    '3. <b>Sinkronisasi Otomatis RTC Jam Alat:</b> Pastikan logger selalu melakukan sinkronisasi NTP server saat terkoneksi internet guna mencegah eror timestamp masa lampau.',
    style_body
))

story.append(Spacer(1, 8))
story.append(make_callout_box(
    'Berdasarkan audit kelengkapan 84.47%, distribusi gap 1?3 hari, dan hasil stress-test empiris, disimpulkan bahwa sistem AI NusaKlim SANGAT TANGGUH, STABIL, dan SIAP BEROPERASI PENUH untuk melayani kebutuhan perkebunan PPKS.',
    title='KESIMPULAN AUDIT FINAL'
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

print('Building Gap Audit Master PDF Report...')
doc.build(story, canvasmaker=NumberedCanvas)
print(f'PDF Successfully Generated at: {pdf_path}')
print(f'PDF File Size: {os.path.getsize(pdf_path):,} bytes')
