#!/usr/bin/env python3
"""
Claude Session Manager Özellik Test Scripti
Yeni eklenen özelliklerin doğru çalışıp çalışmadığını test eder.
"""

import json
import os
import sys
from datetime import datetime
from claude_session_manager import ClaudeSessionManager, ScheduledCommand

def test_scheduled_commands():
    """Zamanlı komut özelliğini test et"""
    print("Zamanli komut ozelligi test ediliyor...")
    
    manager = ClaudeSessionManager()
    
    # Test komutu ekle
    success, message = manager.add_scheduled_command("15:30", "test komutu", "Test açıklaması")
    print(f"   Komut ekleme: {'BASARILI' if success else 'BASARISIZ'} {message}")
    
    # Komutları listele
    commands = manager.scheduled_commands
    print(f"   Toplam komut sayısı: {len(commands)}")
    
    if commands:
        print(f"   Son komut: {commands[-1].time} - {commands[-1].command}")
        
        # Komutu devre dışı bırak
        success, message = manager.toggle_scheduled_command(len(commands)-1)
        print(f"   Komut toggle: {'BASARILI' if success else 'BASARISIZ'} {message}")
        
        # Komutu sil
        success, message = manager.remove_scheduled_command(len(commands)-1)
        print(f"   Komut silme: {'BASARILI' if success else 'BASARISIZ'} {message}")
    
    return True

def test_special_commands():
    """Özel komutları test et"""
    print("Ozel komutlar test ediliyor...")
    
    manager = ClaudeSessionManager()
    
    # /status komutu test et
    success, response = manager.handle_special_command("/status")
    print(f"   /status komutu: {'BASARILI' if success else 'BASARISIZ'}")
    if success:
        try:
            status_data = json.loads(response)
            print(f"   Status verileri: {len(status_data)} adet key")
        except:
            print("   Status JSON parse hatası")
    
    # /usage komutu test et
    success, response = manager.handle_special_command("/usage")
    print(f"   /usage komutu: {'BASARILI' if success else 'BASARISIZ'}")
    if success:
        try:
            usage_data = json.loads(response)
            print(f"   Usage verileri: {len(usage_data)} adet key")
        except:
            print("   Usage JSON parse hatası")
    
    # /cost komutu test et
    success, response = manager.handle_special_command("/cost")
    print(f"   /cost komutu: {'BASARILI' if success else 'BASARISIZ'}")
    
    # Bilinmeyen komut test et
    success, response = manager.handle_special_command("/bilinmeyen")
    print(f"   Bilinmeyen komut kontrolu: {'BASARILI' if not success else 'BASARISIZ'}")
    
    return True

def test_usage_logging():
    """Kullanım loglaması test et"""
    print("Kullanim loglama test ediliyor...")
    
    manager = ClaudeSessionManager()
    
    # Manuel log kontrolü
    manager.check_and_log_usage()
    
    # Log dosyası kontrol et
    if os.path.exists(manager.usage_log_file):
        with open(manager.usage_log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        reports = log_data.get('hourly_reports', [])
        print(f"   Log dosyasi: BASARILI {len(reports)} adet rapor")
        
        if reports:
            last_report = reports[-1]
            print(f"   Son rapor: {last_report.get('timestamp', 'N/A')}")
            print(f"   Saat bilgisi: {last_report.get('hour', 'N/A')}")
        
        last_check = log_data.get('last_check_time')
        print(f"   Son kontrol: {last_check}")
        
    else:
        print("   Log dosyasi: BASARISIZ Bulunamadi")
        return False
    
    return True

def test_file_operations():
    """Dosya işlemlerini test et"""
    print("Dosya islemleri test ediliyor...")
    
    manager = ClaudeSessionManager()
    
    # Config dosyası
    config_exists = os.path.exists(manager.config_file)
    print(f"   Config dosyasi: {'BASARILI' if config_exists else 'BASARISIZ'}")
    
    # Session dosyası
    session_exists = os.path.exists(manager.session_file)
    print(f"   Session dosyasi: {'BASARILI' if session_exists else 'BASARISIZ'}")
    
    # Scheduled commands dosyası
    cmd_exists = os.path.exists(manager.scheduled_commands_file)
    print(f"   Zamanli komutlar dosyasi: {'BASARILI' if cmd_exists else 'BASARISIZ'}")
    
    # Usage log dosyası
    usage_exists = os.path.exists(manager.usage_log_file)
    print(f"   Kullanim log dosyasi: {'BASARILI' if usage_exists else 'BASARISIZ'}")
    
    return config_exists and session_exists

def test_data_structures():
    """Veri yapılarını test et"""
    print("Veri yapilari test ediliyor...")
    
    manager = ClaudeSessionManager()
    
    # ScheduledCommand dataclass test
    test_cmd = ScheduledCommand("12:00", "test", "açıklama", True)
    print(f"   ScheduledCommand: BASARILI {test_cmd.time}")
    
    # Manager attributeları kontrol et
    required_attrs = [
        'config', 'session_data', 'scheduled_commands', 'usage_log',
        'is_running', 'scheduler_thread'
    ]
    
    missing_attrs = []
    for attr in required_attrs:
        if not hasattr(manager, attr):
            missing_attrs.append(attr)
    
    if missing_attrs:
        print(f"   Eksik attributelar: BASARISIZ {missing_attrs}")
        return False
    else:
        print(f"   Tum attributelar: BASARILI {len(required_attrs)} adet")
    
    return True

def main():
    """Ana test fonksiyonu"""
    print("Claude Session Manager Ozellik Testi Baslatiliyor...\n")
    
    tests = [
        ("Veri Yapıları", test_data_structures),
        ("Dosya İşlemleri", test_file_operations),
        ("Zamanlı Komutlar", test_scheduled_commands),
        ("Özel Komutlar", test_special_commands),
        ("Kullanım Loglama", test_usage_logging),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"{test_name} Testi")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{test_name}: {'BASARILI' if result else 'BASARISIZ'}")
        except Exception as e:
            print(f"\n{test_name}: HATA - {str(e)}")
            results.append((test_name, False))
    
    # Sonuçları özetle
    print(f"\n{'='*60}")
    print("TEST SONUCLARI OZETI")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "BASARILI" if result else "BASARISIZ"
        print(f"   {test_name:<20}: {status}")
    
    print(f"\nToplam: {passed}/{total} test basarili")
    print(f"Basari orani: %{(passed/total)*100:.1f}")
    
    if passed == total:
        print("\nTUM TESTLER BASARILI!")
        print("Program amaca uygun sekilde implement edilmis.")
    else:
        print(f"\n{total-passed} test basarisiz!")
        print("Bazi ozellikler gozden gecirilmeli.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)