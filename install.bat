@echo off
echo Claude Session Manager Kurulum Scripti
echo ========================================

echo.
echo Python versiyonunu kontrol ediliyor...
python --version
if %errorlevel% neq 0 (
    echo HATA: Python bulunamadi! Python 3.7+ yukleyiniz.
    pause
    exit /b 1
)

echo.
echo Gerekli Python paketleri yukleniyor...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo HATA: Paket yukleme basarisiz!
    pause
    exit /b 1
)

echo.
echo Veri dizinleri olusturuluyor...
if not exist "claude_session_data" mkdir claude_session_data
if not exist "claude_session_data\logs" mkdir claude_session_data\logs
if not exist "claude_session_data\sessions" mkdir claude_session_data\sessions
if not exist "claude_session_data\tokens" mkdir claude_session_data\tokens
if not exist "claude_session_data\confirmations" mkdir claude_session_data\confirmations
if not exist "claude_session_data\backups" mkdir claude_session_data\backups

echo.
echo Windows bağımlılıkları kontrol ediliyor...
python -c "import win32gui; print('✓ pywin32 OK')"
python -c "import psutil; print('✓ psutil OK')" 
python -c "import tkinter; print('✓ tkinter OK')"

echo.
echo Kurulum tamamlandi!
echo.
echo Calistirmak icin: python main_application.py
echo.
pause