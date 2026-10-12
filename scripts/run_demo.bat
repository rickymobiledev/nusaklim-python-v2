@echo off
where uv >nul 2>nul
if errorlevel 1 (
    echo uv belum terpasang atau tidak ada di PATH.
    exit /b 1
)
chcp 65001 >nul
title Demo Performa Model NusaKlim
cd /d "%~dp0.."

:menu
cls
echo ======================================================================
echo                 DEMO PERFORMA MODEL PREDIKSI NUSAKLIM                
echo ======================================================================
echo.
echo  Pilih opsi demo yang ingin dijalankan:
echo.
echo   [1] Demo Cepat (Rekomendasi - Langsung tampil semua metrik dan ramalan)
echo   [2] Demo Live Calculation (Hitung langsung dari data uji sensor 30 hari)
echo   [3] Demo Live Suhu Saja (H+1 dan H+7)
echo   [4] Demo Live Curah Hujan Saja
echo   [5] Jalankan Server API Web (Buka Swagger UI di Browser)
echo   [6] Buka File Hasil Demo Terakhir (Markdown / CSV)
echo   [0] Keluar
echo.
echo ======================================================================
set /p opt="Masukkan pilihan (0-6): "

if "%opt%"=="1" goto demo_cepat
if "%opt%"=="2" goto demo_full
if "%opt%"=="3" goto demo_suhu
if "%opt%"=="4" goto demo_hujan
if "%opt%"=="5" goto run_api
if "%opt%"=="6" goto open_logs
if "%opt%"=="0" goto end
goto menu

:demo_cepat
cls
echo Menjalankan Demo Cepat Model Produksi...
echo.
uv run python demo_performa_model.py --cepat
echo.
echo Selesai. Hasil juga disimpan di folder logs\demo\.
pause
goto menu

:demo_full
cls
echo Menjalankan Evaluasi Langsung pada Data Uji 30 Hari Terakhir...
echo (Proses membutuhkan waktu sekitar 20-30 detik)
echo.
uv run python demo_performa_model.py
echo.
echo Selesai. Hasil juga disimpan di folder logs\demo\.
pause
goto menu

:demo_suhu
cls
echo Menjalankan Evaluasi Langsung Indikator Suhu (H+1 dan H+7)...
echo.
uv run python demo_performa_model.py --indikator suhu --horizon 1,7
echo.
pause
goto menu

:demo_hujan
cls
echo Menjalankan Evaluasi Langsung Indikator Curah Hujan...
echo.
uv run python demo_performa_model.py --indikator hujan
echo.
pause
goto menu

:run_api
cls
echo ======================================================================
echo Memulai Server API NusaKlim...
echo Tekan Ctrl+C di terminal ini jika ingin menghentikan server.
echo ======================================================================
uv run python -m api.serve --open-browser
pause
goto menu

:open_logs
cls
echo Membuka folder logs\demo...
explorer "%~dp0..\logs\demo"
goto menu

:end
exit /b 0
