"""Hitungan kemenangan Model Lokal vs Global per stasiun - SATU sumber untuk figur
(generate_local_benchmark_figures.py) dan teks laporan (generate_per_station_pdf.py)
supaya angka di gambar, tabel, dan kesimpulan Laporan 3b selalu sama.

Aturan per stasiun (strict, seri dihitung terpisah):
  - regresi      : model dengan MAE lebih kecil menang
  - klasifikasi  : model dengan Accuracy lebih besar menang
"""


def station_wins(R, var, clf_target):
    """Kembalikan (n_lokal, n_global, n_seri, n_total) untuk satu indikator."""
    n_local = n_global = n_tie = 0
    for sdata in R['stations'].values():
        ind = sdata['indicators'].get(var)
        if not ind:
            continue
        if var == clf_target:
            a, b = ind['local']['Accuracy'], ind['global']['Accuracy']
            if a > b:
                n_local += 1
            elif a < b:
                n_global += 1
            else:
                n_tie += 1
        else:
            a, b = ind['local']['MAE'], ind['global']['MAE']
            if a < b:
                n_local += 1
            elif a > b:
                n_global += 1
            else:
                n_tie += 1
    return n_local, n_global, n_tie, n_local + n_global + n_tie


def recommend(n_local, n_global, avg_winner):
    """Aturan keputusan tunggal: Model Lokal hanya direkomendasikan jika unggul di
    lebih banyak stasiun DAN unggul pada rata-rata metrik (Tabel 3.1/3.2). Jika dua
    kriteria itu tidak sejalan, atau seri, Model Global dipertahankan (lebih
    sederhana dioperasikan dan di-retrain)."""
    return 'Lokal' if (n_local > n_global and avg_winner == 'Lokal') else 'Global'
