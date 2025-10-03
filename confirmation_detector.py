import re
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import win32gui
import win32con
import datetime
import json
import os

class ConfirmationDetector:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.pending_confirmations = {}
        self.confirmation_history = []
        
        # Onay sorusu pattern'leri
        self.confirmation_patterns = [
            r'(?i)(yes|no).*\?',
            r'(?i)(1|2|3).*(?:option|choice|select)',
            r'(?i)(continue|abort|proceed).*\?',
            r'(?i)do you want.*\?',
            r'(?i)would you like.*\?',
            r'(?i)should i.*\?',
            r'(?i)confirm.*\?',
            r'(?i)are you sure.*\?',
            r'(?i)ready to.*\?',
        ]
        
        # Limit uyarı pattern'leri
        self.limit_patterns = [
            r'(?i)approaching.*5.*hour.*limit',
            r'(?i)5.*hour.*limit.*approaching',
            r'(?i)usage.*limit.*soon',
            r'(?i)session.*expire.*soon',
        ]
        
        # Zaman bilgisi pattern'leri
        self.time_patterns = [
            r'(?i)until.*(\d{1,2}:\d{2}).*(?:limit|reset)',
            r'(?i)limit.*until.*(\d{1,2}:\d{2})',
            r'(?i)reset.*at.*(\d{1,2}:\d{2})',
            r'(?i)available.*at.*(\d{1,2}:\d{2})',
        ]
        
        self.create_confirmation_ui()
    
    def create_confirmation_ui(self):
        """Onay soruları için UI oluştur"""
        self.confirmation_window = None
        
    def show_confirmation_dialog(self, message, session_id, window_title):
        """Onay dialogu göster"""
        if self.confirmation_window and self.confirmation_window.winfo_exists():
            self.confirmation_window.destroy()
        
        self.confirmation_window = tk.Toplevel()
        self.confirmation_window.title("Claude Onay Gerekli")
        self.confirmation_window.geometry("500x300")
        self.confirmation_window.attributes('-topmost', True)
        
        # Ana frame
        main_frame = ttk.Frame(self.confirmation_window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Claude Onay Bekliyor", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Session bilgisi
        session_label = ttk.Label(main_frame, text=f"Session: {session_id}")
        session_label.pack()
        
        window_label = ttk.Label(main_frame, text=f"Pencere: {window_title}")
        window_label.pack(pady=(0, 10))
        
        # Mesaj
        message_frame = ttk.LabelFrame(main_frame, text="Onay Mesajı", padding="5")
        message_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        message_text = tk.Text(message_frame, wrap=tk.WORD, height=6)
        message_text.pack(fill="both", expand=True)
        message_text.insert(1.0, message)
        message_text.config(state="disabled")
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        def close_dialog():
            self.confirmation_window.destroy()
            self.confirmation_window = None
        
        def snooze_dialog():
            self.confirmation_window.withdraw()
            # 30 saniye sonra tekrar göster
            threading.Timer(30.0, lambda: self.confirmation_window.deiconify() if self.confirmation_window else None).start()
        
        ttk.Button(button_frame, text="Pencereye Git", command=self.focus_claude_window).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="30s Ertele", command=snooze_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Kapat", command=close_dialog).pack(side="right")
        
        # Confirmation'ı kaydet
        self.log_confirmation(session_id, message, window_title)
    
    def focus_claude_window(self):
        """Claude penceresine focus yap"""
        try:
            # En son aktif Claude penceresini bul
            claude_windows = self.main_monitor.find_claude_windows()
            if claude_windows:
                hwnd = claude_windows[0].get('hwnd')
                if hwnd:
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        except Exception as e:
            print(f"Focus error: {e}")
    
    def detect_confirmations(self, text, session_id, window_info):
        """Text'te onay soruları tespit et"""
        confirmations = []
        
        for pattern in self.confirmation_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # Onay sorusunun etrafındaki bağlamı al
                start_pos = max(0, match.start() - 200)
                end_pos = min(len(text), match.end() + 200)
                context = text[start_pos:end_pos].strip()
                
                confirmation = {
                    'type': 'confirmation',
                    'content': context,
                    'session_id': session_id,
                    'window_info': window_info,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'pattern_matched': pattern
                }
                confirmations.append(confirmation)
        
        return confirmations
    
    def detect_limit_warnings(self, text, session_id, window_info):
        """Limit uyarılarını tespit et"""
        warnings = []
        
        for pattern in self.limit_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(text), match.end() + 100)
                context = text[start_pos:end_pos].strip()
                
                warning = {
                    'type': 'limit_warning',
                    'content': context,
                    'session_id': session_id,
                    'window_info': window_info,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'severity': 'high'
                }
                warnings.append(warning)
        
        return warnings
    
    def detect_time_info(self, text, session_id, window_info):
        """Zaman bilgilerini tespit et"""
        time_infos = []
        
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                time_str = match.group(1) if match.groups() else match.group(0)
                start_pos = max(0, match.start() - 100)
                end_pos = min(len(text), match.end() + 100)
                context = text[start_pos:end_pos].strip()
                
                time_info = {
                    'type': 'time_info',
                    'content': context,
                    'time_value': time_str,
                    'session_id': session_id,
                    'window_info': window_info,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                time_infos.append(time_info)
        
        return time_infos
    
    def process_text(self, text, session_id, window_info):
        """Text'i tüm pattern'ler için işle"""
        results = {
            'confirmations': self.detect_confirmations(text, session_id, window_info),
            'limit_warnings': self.detect_limit_warnings(text, session_id, window_info),
            'time_infos': self.detect_time_info(text, session_id, window_info)
        }
        
        # Onay sorularını göster
        for confirmation in results['confirmations']:
            if not self.is_duplicate_confirmation(confirmation):
                window_title = window_info.get('title', 'Unknown')
                self.show_confirmation_dialog(confirmation['content'], session_id, window_title)
                self.main_monitor.add_alert('confirmation_detected', 
                                          f"Onay sorusu tespit edildi: {confirmation['content'][:50]}...", 
                                          session_id)
        
        # Limit uyarılarını işle
        for warning in results['limit_warnings']:
            self.main_monitor.add_alert('limit_warning', 
                                      f"Limit uyarısı: {warning['content'][:100]}...", 
                                      session_id)
        
        # Zaman bilgilerini işle
        for time_info in results['time_infos']:
            self.main_monitor.add_alert('time_info', 
                                      f"Zaman bilgisi: {time_info['content'][:100]}...", 
                                      session_id)
        
        return results
    
    def is_duplicate_confirmation(self, confirmation):
        """Aynı onay sorusunun tekrar tespit edilip edilmediğini kontrol et"""
        current_time = datetime.datetime.now()
        
        for existing in self.confirmation_history[-10:]:  # Son 10 onay
            existing_time = datetime.datetime.fromisoformat(existing['timestamp'])
            
            # 5 dakika içinde aynı session'dan benzer onay var mı?
            if (existing['session_id'] == confirmation['session_id'] and
                (current_time - existing_time).total_seconds() < 300 and
                self.similarity_score(existing['content'], confirmation['content']) > 0.8):
                return True
        
        return False
    
    def similarity_score(self, text1, text2):
        """İki text arasındaki benzerlik skorunu hesapla"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def log_confirmation(self, session_id, message, window_title):
        """Onay sorusunu log'a kaydet"""
        log_entry = {
            'session_id': session_id,
            'message': message,
            'window_title': window_title,
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.confirmation_history.append(log_entry)
        
        # Dosyaya kaydet
        log_file = f"claude_session_data/confirmations_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')

class AutoResponseSystem:
    def __init__(self, confirmation_detector):
        self.confirmation_detector = confirmation_detector
        self.auto_responses = {
            'continue': ['yes', 'continue', 'proceed', '1'],
            'abort': ['no', 'abort', 'stop', '2'],
            'default': ['3', 'maybe', 'not sure']
        }
        
        self.auto_response_enabled = False
        self.response_delay = 5  # 5 saniye bekle
    
    def enable_auto_response(self, response_type='continue'):
        """Otomatik yanıt sistemini etkinleştir"""
        self.auto_response_enabled = True
        self.default_response = response_type
    
    def disable_auto_response(self):
        """Otomatik yanıt sistemini devre dışı bırak"""
        self.auto_response_enabled = False
    
    def send_auto_response(self, response_text, window_hwnd):
        """Otomatik yanıt gönder"""
        try:
            # Pencereye focus yap
            win32gui.SetForegroundWindow(window_hwnd)
            time.sleep(0.5)
            
            # Yanıtı gönder (bu kısım tarayıcı tipine göre özelleştirilebilir)
            # Şimdilik sadece log'a kaydedelim
            print(f"Auto response sent: {response_text}")
            
        except Exception as e:
            print(f"Auto response error: {e}")

if __name__ == "__main__":
    # Test için
    class MockMonitor:
        def add_alert(self, alert_type, message, session_id=None):
            print(f"Alert: {alert_type} - {message}")
        
        def find_claude_windows(self):
            return []
    
    mock_monitor = MockMonitor()
    detector = ConfirmationDetector(mock_monitor)
    
    # Test text
    test_text = "Do you want me to continue with this task? Please type 'yes' or 'no'."
    results = detector.process_text(test_text, "test_session", {"title": "Test Window"})
    print(f"Results: {results}")