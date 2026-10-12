#!/usr/bin/env bash
set -uo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." || exit 1
if ! command -v uv >/dev/null 2>&1; then
    echo "uv belum terpasang atau tidak ada di PATH." >&2
    exit 1
fi

open_path() {
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$1" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "$1" >/dev/null 2>&1 &
    elif command -v explorer.exe >/dev/null 2>&1; then
        explorer.exe "$1" >/dev/null 2>&1 &
    else
        printf 'Buka secara manual: %s\n' "$1"
    fi
}

while true; do
    printf '\n=== DEMO PERFORMA MODEL PREDIKSI NUSAKLIM ===\n'
    cat <<'MENU'
  [1] Demo Cepat
  [2] Demo Live Calculation (data uji sensor 30 hari)
  [3] Demo Live Suhu Saja (H+1 dan H+7)
  [4] Demo Live Curah Hujan Saja
  [5] Jalankan Server API Web
  [6] Buka Folder Hasil Demo
  [0] Keluar
MENU
    read -r -p "Masukkan pilihan (0-6): " opt || exit 0
    case "$opt" in
        1) uv run python demo_performa_model.py --cepat ;;
        2) uv run python demo_performa_model.py ;;
        3) uv run python demo_performa_model.py --indikator suhu --horizon 1,7 ;;
        4) uv run python demo_performa_model.py --indikator hujan ;;
        5)
            echo "Tekan Ctrl+C untuk menghentikan server."
            uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
            ;;
        6)
            open_path "$PWD/logs/demo"
            continue
            ;;
        0) exit 0 ;;
        *) echo "Pilihan tidak valid."; continue ;;
    esac
    result=$?
    if (( result != 0 )); then
        printf 'Perintah gagal (exit code %s).\n' "$result" >&2
    fi
    read -r -p "Tekan Enter untuk kembali ke menu..." _ || exit 0
done
