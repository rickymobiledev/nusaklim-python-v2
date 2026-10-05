# ==============================================================================
# BENCHMARK DEEP LEARNING (LSTM, GRU) UNTUK GABUNGAN LAPORAN 3+4
#
# Melatih HANYA 2 algoritma DL (LSTM, GRU) untuk ketujuh indikator cuaca x
# horizon H+1 & H+7 (14 x 2 = 28 kombinasi), lalu MENGGABUNGKAN hasilnya ke
# records benchmark_algo_allvars_h1_h7.json yang SUDAH ADA (3 algoritma ML:
# LightGBM, Ridge Regression, Random Forest/Logistic Regression - fitur 29,
# hasil retrain 28-09-2026) - bukan melatih ulang ML, supaya angka ML di
# laporan gabungan identik persis dengan Laporan 3 (satu sumber kebenaran).
#
# Catatan keterbatasan DL (per Notulen 28-09-2026, permintaan agar tetap
# jujur bukan diklaim final): DL dilatih hanya 10 epoch (DL_EPOCHS) murni demi
# kepraktisan waktu komputasi (14 indikator x horizon x 2 arsitektur RNN pada
# CPU) - TIDAK diuji dengan kurva konvergensi loss, sehingga hasil MAE/Accuracy
# DL di laporan ini bersifat INDIKATIF (gambaran kasar apakah pendekatan
# sequence-based DL punya potensi), bukan hasil final yang sudah dioptimalkan
# penuh. DL juga tidak dipakai sebagai kandidat model produksi (lihat catatan
# "3 algoritma ML" di retrain_pipeline.py) karena model PyTorch tidak disimpan
# ke disk/diintegrasikan ke jalur inferensi produksi.
# ==============================================================================
import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, f1_score

BASE_DIR = r'D:\Projects\Kodepanda\Nusaklim\nusaklim'
sys.path.insert(0, BASE_DIR)
from retrain_pipeline import build_features_and_targets, REGRESSION_TARGETS, CLASSIFICATION_TARGET, BASE_VARS

torch.manual_seed(42)
np.random.seed(42)

SEQ_LEN = 14
DL_EPOCHS = 10
WIND_CLASSES = ['Barat', 'Selatan', 'Timur', 'Utara']
CLASS_TO_IDX = {c: i for i, c in enumerate(WIND_CLASSES)}
HORIZONS = [1, 7]

DL_ALGO_LABEL = {'lstm': 'LSTM (Recurrent Neural Network)', 'gru': 'GRU (Recurrent Neural Network)'}
FITUR_SET_DL = 'Sequence 14-Hari (DL)'

print('=== BENCHMARK DL (LSTM, GRU) UNTUK LAPORAN GABUNGAN: 7 INDIKATOR x H+1 & H+7 ===')
t_total0 = time.time()

df_daily = pd.read_csv(os.path.join(BASE_DIR, 'nusaklim_daily_aggregated.csv'))
print(f'Loaded {len(df_daily):,} baris, {df_daily["stnname"].nunique()} stasiun.')

df, feature_cols, target_cols, target_types = build_features_and_targets(df_daily, horizons=HORIZONS)
df['date_dt'] = pd.to_datetime(df['date'])
max_date = df['date_dt'].max()
split_date = max_date - pd.Timedelta(days=30)
train_mask = df['date_dt'] <= split_date
test_mask = df['date_dt'] > split_date
print(f'Split OOT: train <= {split_date.date()}, test > {split_date.date()} (s/d {max_date.date()})')

seq_vars = BASE_VARS
scaler_seq = StandardScaler()
df_seq_scaled = df.copy()
df_seq_scaled[seq_vars] = scaler_seq.fit_transform(df_seq_scaled[seq_vars].fillna(df_seq_scaled[seq_vars].median()))


def create_sequences(data_df, target_col, seq_length=SEQ_LEN, classification=False):
    seqs, targets = [], []
    for stn, grp in data_df.groupby('stnname'):
        vals = grp[seq_vars].values
        t_vals = grp[target_col].values
        if len(vals) < seq_length + 1:
            continue
        for i in range(len(vals) - seq_length):
            tv = t_vals[i + seq_length - 1]
            if pd.isna(tv):
                continue
            if classification and tv not in CLASS_TO_IDX:
                continue
            seqs.append(vals[i:i + seq_length])
            targets.append(CLASS_TO_IDX[tv] if classification else tv)
    dtype = np.int64 if classification else np.float32
    return np.array(seqs, dtype=np.float32), np.array(targets, dtype=dtype)


class RNNModel(nn.Module):
    def __init__(self, cell, input_dim, hidden_dim=64, num_layers=2, output_dim=1):
        super().__init__()
        rnn_cls = nn.LSTM if cell == 'lstm' else nn.GRU
        self.rnn = rnn_cls(input_dim, hidden_dim, num_layers=num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.output_dim = output_dim

    def forward(self, x):
        out, _ = self.rnn(x)
        out = self.fc(out[:, -1, :])
        return out.squeeze(-1) if self.output_dim == 1 else out


def train_torch(model, tr_loader, epochs, lr, classification):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss() if classification else nn.MSELoss()
    for _ in range(epochs):
        model.train()
        for bx, by in tr_loader:
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
    return model


def run_dl(cell, X_train, y_train, X_test, y_test, classification, epochs=DL_EPOCHS, lr=0.003):
    output_dim = len(WIND_CLASSES) if classification else 1

    if classification:
        y_train_t = torch.from_numpy(y_train).long()
        y_scaler = None
    else:
        y_scaler = StandardScaler().fit(y_train.reshape(-1, 1))
        y_train_scaled = y_scaler.transform(y_train.reshape(-1, 1)).flatten().astype(np.float32)
        y_train_t = torch.from_numpy(y_train_scaled)

    train_loader = DataLoader(TensorDataset(torch.from_numpy(X_train), y_train_t), batch_size=256, shuffle=True)

    model = RNNModel(cell, input_dim=X_train.shape[2], hidden_dim=64, num_layers=2, output_dim=output_dim)
    t0 = time.time()
    train_torch(model, train_loader, epochs, lr, classification)
    train_s = time.time() - t0

    model.eval()
    with torch.no_grad():
        preds = model(torch.from_numpy(X_test))
        if classification:
            pred_cls = preds.argmax(dim=1).numpy()
        else:
            pred_val = y_scaler.inverse_transform(preds.numpy().reshape(-1, 1)).flatten()

    if classification:
        return {
            'Accuracy': round(accuracy_score(y_test, pred_cls), 4),
            'F1_Macro': round(f1_score(y_test, pred_cls, average='macro'), 4),
            'Training_s': round(train_s, 2),
            'n_train': int(len(y_train)), 'n_test': int(len(y_test)),
        }
    return {
        'MAE': round(mean_absolute_error(y_test, pred_val), 4),
        'RMSE': round(float(np.sqrt(mean_squared_error(y_test, pred_val))), 4),
        'R2': round(r2_score(y_test, pred_val), 4),
        'Training_s': round(train_s, 2),
        'n_train': int(len(y_train)), 'n_test': int(len(y_test)),
    }


# ------------------------------------------------------------------------------
# MAIN LOOP: 6 indikator regresi x H+1 & H+7 x (LSTM, GRU)
# ------------------------------------------------------------------------------
dl_records = []

for var, label in REGRESSION_TARGETS.items():
    for h in HORIZONS:
        tcol = target_cols[f'{var}_h{h}']
        print(f'\n--- {var} H+{h} ---')
        X_train_seq, y_train_seq = create_sequences(df_seq_scaled[train_mask], tcol)
        X_test_seq, y_test_seq = create_sequences(df_seq_scaled[test_mask], tcol)
        print(f'  seq shapes: train={X_train_seq.shape} test={X_test_seq.shape}')

        for cell in ['lstm', 'gru']:
            r = run_dl(cell, X_train_seq, y_train_seq, X_test_seq, y_test_seq, classification=False)
            print(f'  [{cell.upper()}] MAE={r["MAE"]:.4f} R2={r["R2"]:.4f} ({r["Training_s"]}s)')
            dl_records.append(dict(Variabel=var, Horizon=f'H+{h}', Algoritma=DL_ALGO_LABEL[cell],
                                    FiturSet=FITUR_SET_DL, MAE=r['MAE'], RMSE=r['RMSE'], R2=r['R2'],
                                    Training_s=r['Training_s'], n_train=r['n_train'], n_test=r['n_test']))

# Klasifikasi arah angin x H+1 & H+7 x (LSTM, GRU)
for h in HORIZONS:
    tcol = target_cols[f'{CLASSIFICATION_TARGET}_h{h}']
    print(f'\n--- {CLASSIFICATION_TARGET} H+{h} (klasifikasi) ---')
    X_train_seq, y_train_seq = create_sequences(df_seq_scaled[train_mask], tcol, classification=True)
    X_test_seq, y_test_seq = create_sequences(df_seq_scaled[test_mask], tcol, classification=True)
    print(f'  seq shapes: train={X_train_seq.shape} test={X_test_seq.shape}')

    for cell in ['lstm', 'gru']:
        r = run_dl(cell, X_train_seq, y_train_seq, X_test_seq, y_test_seq, classification=True)
        print(f'  [{cell.upper()}] Acc={r["Accuracy"]:.4f} F1={r["F1_Macro"]:.4f} ({r["Training_s"]}s)')
        dl_records.append(dict(Variabel=CLASSIFICATION_TARGET, Horizon=f'H+{h}', Algoritma=DL_ALGO_LABEL[cell],
                                FiturSet=FITUR_SET_DL, Accuracy=r['Accuracy'], F1_Macro=r['F1_Macro'],
                                Training_s=r['Training_s'], n_train=r['n_train'], n_test=r['n_test']))

# ------------------------------------------------------------------------------
# GABUNGKAN dengan hasil 3 ML yang sudah ada (Laporan 3, benchmark_algo_allvars_h1_h7.json)
# ------------------------------------------------------------------------------
ml_json_path = os.path.join(BASE_DIR, 'benchmark_algo_allvars_h1_h7.json')
with open(ml_json_path, 'r', encoding='utf-8') as f:
    ml_records = json.load(f)

merged = ml_records + dl_records
out_path = os.path.join(BASE_DIR, 'benchmark_merged_5algo_h1_h7.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2)

print(f'\nTotal records: {len(merged)} ({len(ml_records)} ML dari Laporan 3 + {len(dl_records)} DL baru)')
print(f'Total waktu DL: {time.time() - t_total0:.1f}s')
print(f'Saved: {out_path}')
