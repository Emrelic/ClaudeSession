#!/usr/bin/env python3
"""
Claude Session Manager Başlatıcı
Cross-platform başlatma scripti
"""

import sys
import subprocess
import os

def install_requirements():
    """Gereksinimleri yükle"""
    print("Gereksinimler kontrol ediliyor...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("OK Gereksinimler hazır")
        return True
    except subprocess.CalledProcessError:
        print("HATA Gereksinimler yüklenemedi")
        return False

def run_quick_test():
    """Hızlı test çalıştır"""
    print("Sistem testi yapılıyor...")
    try:
        result = subprocess.run([sys.executable, 'test_system.py', '--quick'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("OK Sistem testleri başarılı")
            return True
        else:
            print("HATA Sistem testleri başarısız")
            print("Detaylı test için: python test_system.py")
            return False
    except Exception as e:
        print(f"HATA Test çalıştırılamadı: {e}")
        return False

def start_gui():
    """GUI'yi başlat"""
    print("GUI başlatılıyor...")
    try:
        subprocess.run([sys.executable, 'claude_session_manager.py'])
        return True
    except KeyboardInterrupt:
        print("\nProgram kullanıcı tarafından durduruldu")
        return True
    except Exception as e:
        print(f"HATA GUI başlatılamadı: {e}")
        return False

def main():
    print("=" * 50)
    print("Claude Session Manager")
    print("=" * 50)
    
    if not os.path.exists('requirements.txt'):
        print("HATA requirements.txt bulunamadı")
        return False
    
    if not os.path.exists('claude_session_manager.py'):
        print("HATA claude_session_manager.py bulunamadı")
        return False
    
    if not install_requirements():
        return False
    
    if not run_quick_test():
        print("\nDetaylı test çalıştırmak ister misiniz? (y/n): ", end="")
        if input().lower() == 'y':
            subprocess.run([sys.executable, 'test_system.py'])
        return False
    
    print("\nHAZIR! Sistem hazır! GUI başlatılıyor...\n")
    return start_gui()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\nDevam etmek için Enter'a basın...")
    except KeyboardInterrupt:
        print("\n\nProgram durduruldu.")
    except Exception as e:
        print(f"\nBeklenmeyen hata: {e}")
        input("Devam etmek için Enter'a basın...")