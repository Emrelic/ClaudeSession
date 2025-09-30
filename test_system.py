#!/usr/bin/env python3
"""
Claude Session Manager Test Script
Bu script sistemin çalışıp çalışmadığını test eder.
"""

import subprocess
import sys
import json
import os
from datetime import datetime

def test_python_version():
    """Python sürümünü kontrol et"""
    print("Python sürümü kontrol ediliyor...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"OK Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"HATA Python {version.major}.{version.minor}.{version.micro} - Minimum Python 3.7 gerekli")
        return False

def test_required_modules():
    """Gerekli modülleri kontrol et"""
    print("\nGerekli modüller kontrol ediliyor...")
    required_modules = ['tkinter', 'schedule', 'threading', 'subprocess', 'json', 'datetime']
    
    success = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"OK {module} - OK")
        except ImportError:
            print(f"HATA {module} - BULUNAMADI")
            success = False
    
    return success

def test_claude_executable():
    """Claude komutunun çalışıp çalışmadığını kontrol et"""
    print("\nClaude executable kontrol ediliyor...")
    try:
        result = subprocess.run(['claude', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"OK Claude Code bulundu - {version}")
            return True
        else:
            print(f"HATA Claude komutu hata verdi: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("HATA Claude komutu zaman aşımına uğradı")
        return False
    except FileNotFoundError:
        print("HATA Claude komutu bulunamadı - PATH'te tanımlı değil")
        return False
    except Exception as e:
        print(f"HATA Claude komutu test edilemedi: {e}")
        return False

def test_claude_simple_command():
    """Claude ile basit komut göndermeyi test et"""
    print("\nClaude ile test komutu gönderiliyor...")
    try:
        result = subprocess.run(['claude', '--print', 'test'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("OK Claude test komutu başarılı")
            print(f"  Response: {result.stdout[:100]}...")
            return True
        else:
            print(f"HATA Claude test komutu başarısız: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("HATA Claude test komutu zaman aşımına uğradı")
        return False
    except Exception as e:
        print(f"HATA Claude test komutu hata verdi: {e}")
        return False

def test_config_files():
    """Konfig dosyalarının oluşturulup oluşturulmadığını test et"""
    print("\nKonfig dosyaları test ediliyor...")
    
    try:
        from claude_session_manager import ClaudeSessionManager
        manager = ClaudeSessionManager()
        
        if os.path.exists(manager.config_file):
            print(f"OK {manager.config_file} bulundu")
            with open(manager.config_file, 'r') as f:
                config = json.load(f)
                print(f"  Config keys: {list(config.keys())}")
        else:
            print(f"HATA {manager.config_file} bulunamadı")
            return False
        
        if os.path.exists(manager.session_file):
            print(f"OK {manager.session_file} bulundu")
        else:
            print(f"INFO {manager.session_file} henüz oluşturulmamış (normal)")
        
        return True
    except Exception as e:
        print(f"HATA Konfig testi başarısız: {e}")
        return False

def test_session_manager_import():
    """Session manager'ın import edilip edilemediğini test et"""
    print("\nSession Manager import test ediliyor...")
    try:
        from claude_session_manager import ClaudeSessionManager, ClaudeSessionGUI
        manager = ClaudeSessionManager()
        status = manager.get_session_status()
        print("OK ClaudeSessionManager import edildi")
        print(f"  Status keys: {list(status.keys())}")
        return True
    except Exception as e:
        print(f"HATA ClaudeSessionManager import edilemedi: {e}")
        return False

def test_gui_creation():
    """GUI'nin oluşturulup oluşturulmadığını test et (gerçek gösterim olmadan)"""
    print("\nGUI oluşturma test ediliyor...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Pencereyi gösterme
        
        from claude_session_manager import ClaudeSessionGUI
        print("OK GUI komponenleri yüklenebilir")
        root.destroy()
        return True
    except Exception as e:
        print(f"HATA GUI test başarısız: {e}")
        return False

def test_scheduler():
    """Scheduler'ın çalışıp çalışmadığını test et"""
    print("\nScheduler test ediliyor...")
    try:
        import schedule
        schedule.clear()
        
        def test_job():
            pass
        
        schedule.every().minute.do(test_job)
        schedule.run_pending()
        schedule.clear()
        
        print("OK Scheduler çalışıyor")
        return True
    except Exception as e:
        print(f"HATA Scheduler test başarısız: {e}")
        return False

def run_full_test():
    """Tüm testleri çalıştır"""
    print("=" * 50)
    print("Claude Session Manager - Sistem Testi")
    print("=" * 50)
    
    tests = [
        ("Python Sürümü", test_python_version),
        ("Gerekli Modüller", test_required_modules),
        ("Claude Executable", test_claude_executable),
        ("Claude Test Komutu", test_claude_simple_command),
        ("Session Manager Import", test_session_manager_import),
        ("Konfig Dosyaları", test_config_files),
        ("GUI Oluşturma", test_gui_creation),
        ("Scheduler", test_scheduler)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"HATA {test_name} - Exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Sonuçları: {passed}/{total} başarılı")
    print("=" * 50)
    
    if passed == total:
        print("BASARILI! Tüm testler başarılı! Sistem kullanıma hazır.")
        return True
    else:
        print("UYARI  Bazı testler başarısız. Lütfen hataları düzeltin.")
        return False

def quick_test():
    """Hızlı test - sadece temel işlevsellik"""
    print("Hızlı test çalıştırılıyor...")
    
    success = True
    success &= test_python_version()
    success &= test_required_modules()
    success &= test_session_manager_import()
    
    if success:
        print("\nOK Temel testler başarılı")
    else:
        print("\nHATA Temel testlerde hata var")
    
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        run_full_test()