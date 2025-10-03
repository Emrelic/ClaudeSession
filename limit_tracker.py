import datetime
import threading
import time
import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
import win32api
import winsound

class LimitTracker:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.session_limits = {}
        self.daily_usage = {}
        self.limit_warnings = []
        
        # Limit ayarları
        self.DEFAULT_SESSION_LIMIT = 5 * 60 * 60  # 5 saat (saniye)
        self.WARNING_THRESHOLDS = [0.8, 0.9, 0.95]  # %80, %90, %95
        
        # Alarm sistemi
        self.alarm_enabled = True
        self.notification_sent = set()
        
        self.load_usage_data()
        self.create_limit_ui()
        
    def create_limit_ui(self):
        """Limit takip UI'si oluştur"""
        self.limit_window = None
        
    def show_limit_dashboard(self):
        """Limit dashboard'unu göster"""
        if self.limit_window and self.limit_window.winfo_exists():
            self.limit_window.lift()
            return
        
        self.limit_window = tk.Toplevel()
        self.limit_window.title("Claude Limit Tracker")
        self.limit_window.geometry("800x600")
        
        # Ana notebook
        notebook = ttk.Notebook(self.limit_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Session Limits sekmesi
        session_frame = ttk.Frame(notebook)
        notebook.add(session_frame, text="Session Limitleri")
        
        self.create_session_limits_ui(session_frame)
        
        # Daily Usage sekmesi
        daily_frame = ttk.Frame(notebook)
        notebook.add(daily_frame, text="Günlük Kullanım")
        
        self.create_daily_usage_ui(daily_frame)
        
        # Warnings sekmesi
        warnings_frame = ttk.Frame(notebook)
        notebook.add(warnings_frame, text="Uyarılar")
        
        self.create_warnings_ui(warnings_frame)
        
        # Settings sekmesi
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Ayarlar")
        
        self.create_settings_ui(settings_frame)
        
        self.update_limit_dashboard()
    
    def create_session_limits_ui(self, parent):
        """Session limits UI'si"""
        # Session listesi
        self.session_tree = ttk.Treeview(parent, columns=("start_time", "duration", "remaining", "status"), show="tree headings")
        self.session_tree.heading("#0", text="Session ID")
        self.session_tree.heading("start_time", text="Başlama")
        self.session_tree.heading("duration", text="Süre")
        self.session_tree.heading("remaining", text="Kalan")
        self.session_tree.heading("status", text="Durum")
        self.session_tree.pack(fill="both", expand=True)
        
        # Progress bar'lar için frame
        progress_frame = ttk.LabelFrame(parent, text="Session Progress", padding="5")
        progress_frame.pack(fill="x", pady=(10, 0))
        
        self.session_progress_bars = {}
    
    def create_daily_usage_ui(self, parent):
        """Günlük kullanım UI'si"""
        # Günlük istatistikler
        stats_frame = ttk.LabelFrame(parent, text="Günlük İstatistikler", padding="10")
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.daily_stats_label = ttk.Label(stats_frame, text="İstatistikler yükleniyor...")
        self.daily_stats_label.pack()
        
        # Günlük kullanım grafiği (basit text gösterim)
        usage_frame = ttk.LabelFrame(parent, text="Kullanım Detayları", padding="5")
        usage_frame.pack(fill="both", expand=True)
        
        self.usage_text = tk.Text(usage_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(usage_frame, orient="vertical", command=self.usage_text.yview)
        self.usage_text.configure(yscrollcommand=scrollbar.set)
        
        self.usage_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_warnings_ui(self, parent):
        """Uyarılar UI'si"""
        self.warnings_tree = ttk.Treeview(parent, columns=("time", "session", "type", "message"), show="headings")
        self.warnings_tree.heading("time", text="Zaman")
        self.warnings_tree.heading("session", text="Session")
        self.warnings_tree.heading("type", text="Tip")
        self.warnings_tree.heading("message", text="Mesaj")
        self.warnings_tree.pack(fill="both", expand=True)
    
    def create_settings_ui(self, parent):
        """Ayarlar UI'si"""
        # Limit ayarları
        limit_frame = ttk.LabelFrame(parent, text="Limit Ayarları", padding="10")
        limit_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(limit_frame, text="Session Limit (saat):").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.session_limit_var = tk.StringVar(value=str(self.DEFAULT_SESSION_LIMIT // 3600))
        session_limit_entry = ttk.Entry(limit_frame, textvariable=self.session_limit_var, width=10)
        session_limit_entry.grid(row=0, column=1, sticky="w")
        
        # Uyarı ayarları
        warning_frame = ttk.LabelFrame(parent, text="Uyarı Ayarları", padding="10")
        warning_frame.pack(fill="x", pady=(0, 10))
        
        self.alarm_var = tk.BooleanVar(value=self.alarm_enabled)
        alarm_check = ttk.Checkbutton(warning_frame, text="Sesli Alarm", variable=self.alarm_var)
        alarm_check.pack(anchor="w")
        
        # Kaydet butonu
        save_btn = ttk.Button(parent, text="Ayarları Kaydet", command=self.save_settings)
        save_btn.pack(pady=10)
    
    def track_session_time(self, session_id, start_time):
        """Session süresini takip et"""
        if session_id not in self.session_limits:
            self.session_limits[session_id] = {
                'start_time': start_time,
                'limit': self.DEFAULT_SESSION_LIMIT,
                'warnings_sent': set(),
                'status': 'active'
            }
    
    def check_session_limits(self):
        """Tüm session'ların limitlerini kontrol et"""
        current_time = datetime.datetime.now()
        
        for session_id, limit_info in self.session_limits.items():
            if limit_info['status'] != 'active':
                continue
            
            # Geçen süreyi hesapla
            elapsed_time = (current_time - limit_info['start_time']).total_seconds()
            limit = limit_info['limit']
            
            # Limit aşıldı mı?
            if elapsed_time >= limit:
                self.handle_limit_exceeded(session_id, elapsed_time, limit)
                continue
            
            # Uyarı eşikleri kontrol et
            for threshold in self.WARNING_THRESHOLDS:
                if elapsed_time >= limit * threshold:
                    warning_key = f"{session_id}_{threshold}"
                    if warning_key not in limit_info['warnings_sent']:
                        self.send_limit_warning(session_id, threshold, elapsed_time, limit)
                        limit_info['warnings_sent'].add(warning_key)
    
    def handle_limit_exceeded(self, session_id, elapsed_time, limit):
        """Limit aşıldığında yapılacaklar"""
        self.session_limits[session_id]['status'] = 'exceeded'
        
        # Uyarı gönder
        self.add_limit_warning(session_id, 'limit_exceeded', 
                             f"Session {session_id} 5 saat limitini aştı! ({elapsed_time/3600:.1f} saat)")
        
        # Alarm çal
        if self.alarm_enabled:
            self.play_alarm()
        
        # Bildiri göster
        self.show_limit_notification(session_id, "LİMİT AŞILDI!", 
                                   f"Session {session_id} 5 saat limitini aştı!")
    
    def send_limit_warning(self, session_id, threshold, elapsed_time, limit):
        """Limit uyarısı gönder"""
        percentage = int(threshold * 100)
        remaining_time = limit - elapsed_time
        
        message = f"Session {session_id} {percentage}% limitine ulaştı! Kalan: {remaining_time/3600:.1f} saat"
        
        self.add_limit_warning(session_id, f'warning_{percentage}', message)
        
        # Ciddi uyarılar için alarm
        if threshold >= 0.9 and self.alarm_enabled:
            self.play_alarm()
        
        self.show_limit_notification(session_id, f"{percentage}% Limit Uyarısı", message)
    
    def add_limit_warning(self, session_id, warning_type, message):
        """Limit uyarısı ekle"""
        warning = {
            'timestamp': datetime.datetime.now().isoformat(),
            'session_id': session_id,
            'type': warning_type,
            'message': message
        }
        
        self.limit_warnings.append(warning)
        
        # Ana monitöre de bildir
        self.main_monitor.add_alert('limit_tracking', message, session_id)
        
        # Dosyaya kaydet
        self.save_warning_to_file(warning)
    
    def save_warning_to_file(self, warning):
        """Uyarıyı dosyaya kaydet"""
        warnings_file = f"claude_session_data/limit_warnings_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        os.makedirs(os.path.dirname(warnings_file), exist_ok=True)
        
        with open(warnings_file, 'a', encoding='utf-8') as f:
            json.dump(warning, f, ensure_ascii=False)
            f.write('\n')
    
    def play_alarm(self):
        """Alarm sesi çal"""
        try:
            winsound.Beep(1000, 500)  # 1000 Hz, 500ms
            time.sleep(0.2)
            winsound.Beep(1500, 500)
            time.sleep(0.2)
            winsound.Beep(1000, 500)
        except Exception as e:
            print(f"Alarm error: {e}")
    
    def show_limit_notification(self, session_id, title, message):
        """Limit bildirimi göster"""
        notification_key = f"{session_id}_{title}"
        if notification_key in self.notification_sent:
            return
        
        self.notification_sent.add(notification_key)
        
        # Windows toast notification
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(title, message, duration=10, threaded=True)
        except ImportError:
            # Fallback: tkinter messagebox
            def show_msgbox():
                messagebox.showwarning(title, message)
            
            threading.Thread(target=show_msgbox, daemon=True).start()
    
    def parse_claude_time_messages(self, text, session_id):
        """Claude'un zaman mesajlarını parse et"""
        time_patterns = [
            r'approaching.*5.*hour.*limit',
            r'until.*(\d{1,2}:\d{2}).*limit',
            r'reset.*at.*(\d{1,2}:\d{2})',
            r'(\d+).*minutes?.*remaining',
            r'(\d+).*hours?.*remaining'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                self.process_claude_time_info(session_id, pattern, matches[0])
    
    def process_claude_time_info(self, session_id, pattern, time_info):
        """Claude'dan gelen zaman bilgisini işle"""
        current_time = datetime.datetime.now()
        
        if 'approaching' in pattern.lower():
            # 5 saat limitine yaklaşıyor
            self.add_limit_warning(session_id, 'claude_approaching_limit', 
                                 "Claude 5 saat limitine yaklaştığını bildirdi")
        
        elif 'until' in pattern.lower() or 'at' in pattern.lower():
            # Belirli bir saatte reset
            try:
                reset_time = datetime.datetime.strptime(time_info, '%H:%M').time()
                today = current_time.date()
                reset_datetime = datetime.datetime.combine(today, reset_time)
                
                # Eğer reset zamanı geçmişse, yarın olarak kabul et
                if reset_datetime < current_time:
                    reset_datetime += datetime.timedelta(days=1)
                
                time_until_reset = (reset_datetime - current_time).total_seconds()
                self.add_limit_warning(session_id, 'claude_reset_time', 
                                     f"Claude limiti {time_info} saatinde resetlenecek")
                
            except ValueError:
                pass
        
        elif 'minutes' in pattern.lower():
            # Dakika cinsinden kalan süre
            try:
                minutes = int(time_info)
                self.add_limit_warning(session_id, 'claude_minutes_remaining', 
                                     f"Claude {minutes} dakika kaldığını bildirdi")
            except ValueError:
                pass
        
        elif 'hours' in pattern.lower():
            # Saat cinsinden kalan süre
            try:
                hours = int(time_info)
                self.add_limit_warning(session_id, 'claude_hours_remaining', 
                                     f"Claude {hours} saat kaldığını bildirdi")
            except ValueError:
                pass
    
    def update_daily_usage(self, session_id, usage_data):
        """Günlük kullanımı güncelle"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if today not in self.daily_usage:
            self.daily_usage[today] = {}
        
        self.daily_usage[today][session_id] = usage_data
        self.save_usage_data()
    
    def load_usage_data(self):
        """Kullanım verilerini yükle"""
        usage_file = "claude_session_data/usage_data.json"
        try:
            if os.path.exists(usage_file):
                with open(usage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.daily_usage = data.get('daily_usage', {})
                    self.session_limits = data.get('session_limits', {})
        except Exception as e:
            print(f"Usage data load error: {e}")
    
    def save_usage_data(self):
        """Kullanım verilerini kaydet"""
        usage_file = "claude_session_data/usage_data.json"
        os.makedirs(os.path.dirname(usage_file), exist_ok=True)
        
        try:
            data = {
                'daily_usage': self.daily_usage,
                'session_limits': {k: {**v, 'start_time': v['start_time'].isoformat() if isinstance(v['start_time'], datetime.datetime) else v['start_time']} 
                                 for k, v in self.session_limits.items()},
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            with open(usage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Usage data save error: {e}")
    
    def save_settings(self):
        """Ayarları kaydet"""
        try:
            new_limit = float(self.session_limit_var.get()) * 3600  # Saat'i saniyeye çevir
            self.DEFAULT_SESSION_LIMIT = int(new_limit)
            self.alarm_enabled = self.alarm_var.get()
            
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz limit değeri!")
    
    def update_limit_dashboard(self):
        """Dashboard'u güncelle"""
        if not self.limit_window or not self.limit_window.winfo_exists():
            return
        
        # Session limits güncelle
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)
        
        current_time = datetime.datetime.now()
        for session_id, limit_info in self.session_limits.items():
            start_time = limit_info['start_time']
            if isinstance(start_time, str):
                start_time = datetime.datetime.fromisoformat(start_time)
            
            elapsed = (current_time - start_time).total_seconds()
            remaining = max(0, limit_info['limit'] - elapsed)
            
            self.session_tree.insert('', 'end',
                                   text=session_id,
                                   values=(start_time.strftime('%H:%M:%S'),
                                          f"{elapsed/3600:.1f}h",
                                          f"{remaining/3600:.1f}h",
                                          limit_info['status']))
        
        # Warnings güncelle
        for item in self.warnings_tree.get_children():
            self.warnings_tree.delete(item)
        
        for warning in self.limit_warnings[-50:]:
            timestamp = datetime.datetime.fromisoformat(warning['timestamp'])
            self.warnings_tree.insert('', 'end',
                                     values=(timestamp.strftime('%H:%M:%S'),
                                            warning['session_id'],
                                            warning['type'],
                                            warning['message']))
        
        # 5 saniye sonra tekrar güncelle
        self.limit_window.after(5000, self.update_limit_dashboard)
    
    def start_monitoring(self):
        """Limit monitoring'i başlat"""
        def monitor_loop():
            while True:
                self.check_session_limits()
                time.sleep(30)  # 30 saniyede bir kontrol
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

if __name__ == "__main__":
    # Test için
    class MockMonitor:
        def add_alert(self, alert_type, message, session_id=None):
            print(f"Alert: {alert_type} - {message}")
    
    mock_monitor = MockMonitor()
    tracker = LimitTracker(mock_monitor)
    
    # Test session ekle
    test_session = "test_session_1"
    start_time = datetime.datetime.now() - datetime.timedelta(hours=4, minutes=30)
    tracker.track_session_time(test_session, start_time)
    
    tracker.show_limit_dashboard()
    tracker.start_monitoring()
    
    # Ana loop
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    root.mainloop()