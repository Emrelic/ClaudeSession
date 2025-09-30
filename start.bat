@echo off
title Claude Session Manager
echo Claude Session Manager Baslatiliyor...

REM Gereksinimler kontrol et
echo Gereksinimler kontrol ediliyor...
pip install -r requirements.txt >nul 2>&1

REM Test calistir
echo Sistem testi yapiliyor...
python test_system.py --quick

if %errorlevel% neq 0 (
    echo.
    echo HATA: Sistem testleri basarisiz!
    echo Detayli test icin: python test_system.py
    pause
    exit /b 1
)

echo.
echo Sistem hazir! GUI baslatiliyor...
echo.

REM Ana programi baslat
python claude_session_manager.py

if %errorlevel% neq 0 (
    echo.
    echo Program hata ile sonlandi.
    pause
)