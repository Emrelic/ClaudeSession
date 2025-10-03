import win32gui
import win32con
import win32clipboard
import win32api
import win32process
import time
import threading
import re
import json
import datetime
from collections import deque
import tkinter as tk
from tkinter import scrolledtext
import psutil

class AdvancedTextMonitor:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.monitored_windows = {}
        self.last_window_texts = {}
        self.text_buffer = deque(maxlen=1000)
        
        # Claude-specific patterns
        self.patterns = {
            'user_prompt': r'(?:Human:|User:)\s*(.*?)(?=(?:Assistant:|Claude:|\n\n|$))',
            'claude_response': r'(?:Assistant:|Claude:)\s*(.*?)(?=(?:Human:|User:|\n\n|$))',
            'confirmation_request': r'(.*(?:yes|no|1|2|3|continue|abort|proceed).*\?)',
            'approach_limit': r'.*(approaching.*5.*hour.*limit|5.*hour.*approaching).*',
            'time_until_limit': r'.*(until.*\d{1,2}:\d{2}.*(?:limit|reset)|limit.*until.*\d{1,2}:\d{2}).*',
            'session_start': r'.*(new.*session|session.*start|welcome.*claude).*',
            'token_usage': r'.*(token.*usage|usage.*token|tokens.*used).*',
            'error_message': r'.*(error|failed|unable|sorry.*cannot).*'
        }
    
    def get_window_text_advanced(self, hwnd):
        """Pencere metnini gelişmiş yöntemlerle al"""
        texts = []
        
        try:
            # Yöntem 1: Normal window text
            window_text = win32gui.GetWindowText(hwnd)
            if window_text:
                texts.append(window_text)
            
            # Yöntem 2: Child window'ları enumere et
            child_texts = []
            def enum_child_proc(child_hwnd, param):
                try:
                    child_text = win32gui.GetWindowText(child_hwnd)
                    if child_text and len(child_text) > 10:  # Anlamlı text
                        child_texts.append(child_text)
                except:
                    pass
                return True
            
            win32gui.EnumChildWindows(hwnd, enum_child_proc, None)
            texts.extend(child_texts)
            
            # Yöntem 3: Clipboard monitoring (eğer kullanıcı kopyalarsa)
            # Bu kısım daha dikkatli implement edilmeli
            
        except Exception as e:
            pass
        
        return ' '.join(texts)
    
    def analyze_text_changes(self, window_id, current_text, previous_text):
        """Text değişikliklerini analiz et"""
        if not current_text or current_text == previous_text:
            return []
        
        findings = []
        
        # Yeni eklenen text'i bul
        if previous_text and len(current_text) > len(previous_text):
            new_text = current_text[len(previous_text):]
            
            # Pattern'leri kontrol et
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, new_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    for match in matches:
                        finding = {
                            'type': pattern_name,
                            'content': match.strip() if isinstance(match, str) else str(match),
                            'window_id': window_id,
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                        findings.append(finding)
        
        return findings
    
    def monitor_claude_interactions(self):
        """Claude etkileşimlerini izle"""
        while True:
            try:
                # Tüm Claude pencerelerini bul
                claude_windows = self.main_monitor.find_claude_windows()
                browser_tabs = self.main_monitor.find_browser_claude_tabs()
                
                all_windows = claude_windows + browser_tabs
                
                for window in all_windows:
                    window_id = f"{window['pid']}_{window.get('hwnd', 0)}"
                    hwnd = window.get('hwnd')
                    
                    if hwnd:
                        current_text = self.get_window_text_advanced(hwnd)
                        previous_text = self.last_window_texts.get(window_id, "")
                        
                        # Text değişikliklerini analiz et
                        findings = self.analyze_text_changes(window_id, current_text, previous_text)
                        
                        for finding in findings:
                            self.process_finding(finding)
                        
                        # Text'i kaydet
                        self.last_window_texts[window_id] = current_text
                
                time.sleep(2)  # 2 saniyede bir kontrol
                
            except Exception as e:
                print(f"Text monitoring error: {e}")
                time.sleep(5)
    
    def process_finding(self, finding):
        """Bulunan pattern'i işle"""
        finding_type = finding['type']
        content = finding['content']
        window_id = finding['window_id']
        
        # Ana monitöre raporla
        if finding_type in ['user_prompt', 'claude_response']:
            self.main_monitor.log_prompt(window_id, finding_type, content)
        
        elif finding_type == 'confirmation_request':
            self.main_monitor.add_alert('confirmation_needed', 
                                      f"Claude onay bekliyor: {content[:100]}...", 
                                      window_id)
        
        elif finding_type == 'approach_limit':
            self.main_monitor.add_alert('approaching_limit', 
                                      "5 saat limitine yaklaşılıyor!", 
                                      window_id)
        
        elif finding_type == 'time_until_limit':
            self.main_monitor.add_alert('time_limit_info', 
                                      f"Limit bilgisi: {content}", 
                                      window_id)
        
        elif finding_type == 'session_start':
            self.main_monitor.add_alert('session_detected', 
                                      "Yeni session başladı", 
                                      window_id)
        
        elif finding_type == 'token_usage':
            self.main_monitor.add_alert('token_info', 
                                      f"Token kullanım bilgisi: {content}", 
                                      window_id)
        
        # Text buffer'a ekle
        self.text_buffer.append(finding)
    
    def start_monitoring(self):
        """Text monitoring'i başlat"""
        monitor_thread = threading.Thread(target=self.monitor_claude_interactions, daemon=True)
        monitor_thread.start()

class ClipboardMonitor:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.last_clipboard_content = ""
        
    def monitor_clipboard(self):
        """Clipboard'u izle - Claude'dan kopyalanan text için"""
        while True:
            try:
                win32clipboard.OpenClipboard()
                try:
                    clipboard_content = win32clipboard.GetClipboardData()
                    if (clipboard_content and 
                        clipboard_content != self.last_clipboard_content and
                        len(clipboard_content) > 50):  # Anlamlı content
                        
                        # Claude içeriklerini tespit et
                        if any(keyword in clipboard_content.lower() for keyword in 
                               ['claude', 'assistant', 'anthropic', 'human:']):
                            
                            self.main_monitor.log_prompt('clipboard', 'clipboard_copy', clipboard_content)
                            self.main_monitor.add_alert('clipboard_activity', 
                                                       f"Claude içeriği kopyalandı: {len(clipboard_content)} karakter")
                        
                        self.last_clipboard_content = clipboard_content
                
                finally:
                    win32clipboard.CloseClipboard()
                
                time.sleep(1)
                
            except Exception as e:
                time.sleep(2)
    
    def start_monitoring(self):
        """Clipboard monitoring'i başlat"""
        monitor_thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
        monitor_thread.start()

# Ana Claude Monitor'a entegrasyon için ekleme
class EnhancedClaudeMonitor:
    def __init__(self):
        # Orijinal ClaudeMonitor'dan miras al
        from claude_monitor import ClaudeMonitor
        self.base_monitor = ClaudeMonitor()
        
        # Gelişmiş özellikler ekle
        self.text_monitor = AdvancedTextMonitor(self.base_monitor)
        self.clipboard_monitor = ClipboardMonitor(self.base_monitor)
        
        self.start_enhanced_monitoring()
    
    def start_enhanced_monitoring(self):
        """Gelişmiş izleme özelliklerini başlat"""
        self.text_monitor.start_monitoring()
        self.clipboard_monitor.start_monitoring()
    
    def run(self):
        """Enhanced monitor'u çalıştır"""
        self.base_monitor.run()

if __name__ == "__main__":
    try:
        enhanced_monitor = EnhancedClaudeMonitor()
        enhanced_monitor.run()
    except Exception as e:
        print(f"Enhanced monitor başlatma hatası: {e}")
        input("Devam etmek için Enter'a basın...")