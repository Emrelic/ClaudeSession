#!/usr/bin/env python3
"""
Manuel Scheduler - Zamanlı komutları zorla çalıştırır
"""

import json
import time
from datetime import datetime
from claude_session_manager import ClaudeSessionManager

def run_manual_scheduler():
    """Manuel olarak zamanlı komutları çalıştır"""
    print("=== MANUEL SCHEDULER BAŞLATILIYOR ===")
    
    manager = ClaudeSessionManager()
    
    # Tüm geçmiş komutları çalıştır
    now = datetime.now()
    missed_commands = []
    
    for cmd in manager.scheduled_commands:
        if not cmd.enabled:
            continue
            
        try:
            cmd_hour, cmd_min = map(int, cmd.time.split(':'))
            
            # Geçmiş saatlerdeki komutları bul
            if cmd_hour < now.hour or (cmd_hour == now.hour and cmd_min <= now.minute):
                missed_commands.append((cmd.time, cmd.command))
        except:
            continue
    
    print(f"Kaçırılan komut sayısı: {len(missed_commands)}")
    
    # Kaçırılan komutları çalıştır
    for cmd_time, command in missed_commands:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Çalıştırılıyor: {cmd_time} - {command[:50]}...")
        
        try:
            success, response = manager.send_claude_prompt(command)
            if success:
                print(f"  ✅ BAŞARILI: {response[:100]}...")
                # Sohbet geçmişine kaydet
                manager.add_chat_entry(command, response, "scheduled")
            else:
                print(f"  ❌ BAŞARISIZ: {response}")
                manager.add_chat_error(command, response, "scheduled")
        except Exception as e:
            print(f"  ❌ HATA: {str(e)}")
            manager.add_chat_error(command, str(e), "scheduled")
        
        # Komutlar arası 2 saniye bekle
        time.sleep(2)
    
    print(f"\n=== MANUEL SCHEDULER TAMAMLANDI ===")
    print(f"Toplam çalıştırılan komut: {len(missed_commands)}")
    print(f"Sohbet geçmişi kayıt sayısı: {len(manager.chat_history)}")

if __name__ == "__main__":
    run_manual_scheduler()