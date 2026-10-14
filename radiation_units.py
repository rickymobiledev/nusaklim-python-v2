"""Konversi radiasi matahari ke MJ/m2 per hari - HANYA lapisan tampilan.

Kolom `solar_radiation_avg` pada data harian, model produksi, dan benchmark berisi TOTAL pembacaan W/m2 dalam sehari
(SUM, skala puluhan ribu; Notulen Poin 12). Data dan model TIDAK diubah. Nilai itu hanya diubah menjadi energi harian
(MJ/m2, skala belasan, sebanding dengan Open-Meteo) ketika ditampilkan di API dan laporan:

    MJ/m2 per hari = SUM x 0,0864 / N_stasiun

0,0864 = 86.400 detik / 1.000.000 (rata-rata W/m2 selama 24 jam menjadi MJ/m2). N_stasiun = median jumlah pembacaan per hari
stasiun itu (`records_count`, sekitar 143 untuk interval 10 menit), sehingga SUM dikembalikan menjadi rata-rata W/m2.

Catatan keterbatasan: hari dengan pembacaan kurang dari normal tampil lebih rendah dari nilai sebenarnya (bias rata-rata
sekitar -6%), dan MAE/RMSE agregat lintas stasiun diskalakan dengan faktor global (N median seluruh stasiun).
"""
import os
import numpy as np
import pandas as pd

WM2_TO_MJ_PER_DAY = 0.0864
SOLAR = 'solar_radiation_avg'
UNIT_LABEL = 'MJ/mÂ²'

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_state = {}


def normal_readings(daily=None):
    """Median jumlah pembacaan per hari tiap stasiun (Series berindeks str) + median global."""
    if daily is None:
        if 'cache' in _state:
            return _state['cache']
        daily = pd.read_csv(os.path.join(_BASE_DIR, 'nusaklim_daily_aggregated.csv'), usecols=['stnname', 'records_count'])
        use_cache = True
    else:
        use_cache = False
    n = daily.groupby(daily['stnname'].astype(str))['records_count'].median().clip(lower=1.0)
    out = (n, float(n.median()))
    if use_cache:
        _state['cache'] = out
    return out


def station_factor(station_id, daily=None):
    """Pengali SUM -> MJ/m2 untuk satu stasiun (fallback: N median global)."""
    n, n_global = normal_readings(daily)
    return WM2_TO_MJ_PER_DAY / float(n.get(str(station_id), n_global))


def global_factor(daily=None):
    return WM2_TO_MJ_PER_DAY / normal_readings(daily)[1]


def to_mj(values, stations, daily=None):
    """Konversi deret nilai SUM per baris (stasiun per baris) ke MJ/m2."""
    n, n_global = normal_readings(daily)
    f = WM2_TO_MJ_PER_DAY / pd.Series(np.asarray(stations).astype(str)).map(n).fillna(n_global).to_numpy(dtype=float)
    return np.asarray(values, dtype=float) * f


def convert_daily(df, daily=None):
    """Salinan data harian dengan kolom radiasi dalam MJ/m2 (skala per stasiun)."""
    out = df.copy()
    out[SOLAR] = to_mj(out[SOLAR].to_numpy(), out['stnname'].to_numpy(), daily)
    return out


def _scale_error(rec, f):
    for k in ('MAE', 'RMSE', 'MAEmed', 'RMSEmed'):
        if k in rec and rec[k] is not None:
            rec[k] = rec[k] * f
    return rec


def scale_bundle_metrics(metrics):
    """bundle['metrics']: MAE/RMSE radiasi x faktor global (R2 tidak berubah)."""
    f = global_factor()
    out = {}
    for k, v in metrics.items():
        out[k] = _scale_error(dict(v), f) if k.startswith(SOLAR) else v
    return out


def scale_benchmark_records(records):
    """Daftar record benchmark (JSON algoritma/merged): MAE/RMSE baris radiasi x faktor global."""
    f = global_factor()
    return [_scale_error(dict(r), f) if r.get('Variabel') == SOLAR else r for r in records]


def scale_local_benchmark(R):
    """local_benchmark_v3.json: MAE/RMSE radiasi per stasiun x faktor stasiun itu (pemenang per stasiun tidak berubah)."""
    for sid, sdata in R['stations'].items():
        ind = sdata['indicators'].get(SOLAR)
        if not ind:
            continue
        f = station_factor(sid)
        for side in ('local', 'global'):
            if side in ind:
                _scale_error(ind[side], f)
    return R
