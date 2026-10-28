@echo off
chcp 65001 > nul
echo ===================================================
echo 🚀 LingoReader AI Sunucusu Baslatiliyor...
echo ===================================================
echo.

:: Python kontrolu
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python'un yuklu ve PATH'e ekli oldugundan emin olun.
    pause
    exit /b
)

:: Tarayıcıyı aç (2 saniye sonra açılacak)
start "" cmd /c "timeout /t 2 >nul & start http://localhost:5001"

:: Sunucuyu çalıştır
python api.py

pause
