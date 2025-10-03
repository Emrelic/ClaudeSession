import tkinter as tk
from tkinter import ttk, scrolledtext
import psutil
import time
import threading
import json
import datetime
import os
import re
from collections import defaultdict
import win32gui
import win32process
import win32con

class ClaudeMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Session Monitor")
        self.root.geometry("1200x800")
        
        # Data storage
        self.sessions = {}
        self.prompt_logs = []
        self.alerts = []
        
        # Create data directories
        self.data_dir = "claude_session_data"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/logs", exist_ok=True)
        os.makedirs(f"{self.data_dir}/sessions", exist_ok=True)
        
        self.create_widgets()
        self.start_monitoring()
        
    def create_widgets(self):
        # Ana notebook
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ana sayfa
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Ana Sayfa")
        
        # Session listesi
        self.session_tree = ttk.Treeview(main_frame, columns=("status", "start_time", "duration", "warnings"), show="tree headings")
        self.session_tree.heading("#0", text="Session")
        self.session_tree.heading("status", text="Durum")
        self.session_tree.heading("start_time", text="Başlama Saati")
        self.session_tree.heading("duration", text="Süre")
        self.session_tree.heading("warnings", text="Uyarılar")
        self.session_tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Prompt günlüğü
        prompt_frame = ttk.Frame(notebook)
        notebook.add(prompt_frame, text="Prompt Günlüğü")
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD)
        self.prompt_text.pack(fill="both", expand=True)
        
        # Uyarılar
        alerts_frame = ttk.Frame(notebook)
        notebook.add(alerts_frame, text="Uyarılar")
        
        self.alerts_tree = ttk.Treeview(alerts_frame, columns=("time", "type", "message"), show="headings")
        self.alerts_tree.heading("time", text="Zaman")
        self.alerts_tree.heading("type", text="Tip")
        self.alerts_tree.heading("message", text="Mesaj")
        self.alerts_tree.pack(fill="both", expand=True)
        
        # İstatistikler
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="İstatistikler")
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD)
        self.stats_text.pack(fill="both", expand=True)
        
    def find_claude_windows(self):
        """Claude pencerelerini bul"""
        claude_windows = []
        
        def enum_window_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if "claude" in window_title.lower() or "anthropic" in window_title.lower():
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        windows.append({
                            'hwnd': hwnd,
                            'title': window_title,
                            'pid': pid,
                            'process_name': process.name(),
                            'create_time': process.create_time()
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            return True
        
        win32gui.EnumWindows(enum_window_callback, claude_windows)
        return claude_windows
    
    def find_browser_claude_tabs(self):
        """Tarayıcılardaki Claude sekmelerini bul"""
        claude_tabs = []
        
        # Chrome, Edge, Firefox gibi tarayıcıları kontrol et
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in ['chrome.exe', 'msedge.exe', 'firefox.exe']:
                    # Pencere başlıklarını kontrol et
                    def enum_callback(hwnd, tabs):
                        if win32gui.GetParent(hwnd) == 0:
                            title = win32gui.GetWindowText(hwnd)
                            if "claude" in title.lower():
                                tabs.append({
                                    'hwnd': hwnd,
                                    'title': title,
                                    'browser': proc.info['name'],
                                    'pid': proc.info['pid']
                                })
                        return True
                    
                    win32gui.EnumWindows(enum_callback, claude_tabs)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return claude_tabs
    
    def detect_claude_prompts(self, window_text):
        """Claude promptlarını ve yanıtlarını tespit et"""
        patterns = {
            'user_prompt': r'Human: (.+?)(?=Assistant:|$)',
            'claude_response': r'Assistant: (.+?)(?=Human:|$)',
            'confirmation': r'(yes|no|1|2|3|continue|abort|proceed)',
            'approach_limit': r'approaching.*5.*hour.*limit',
            'time_limit': r'until.*\d{1,2}:\d{2}.*limit',
            'token_usage': r'token.*usage|usage.*token'
        }
        
        results = {}
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, window_text, re.IGNORECASE | re.DOTALL)
            if matches:
                results[pattern_name] = matches
        
        return results
    
    def log_prompt(self, session_id, prompt_type, content):
        """Prompt günlüğüne kaydet"""
        timestamp = datetime.datetime.now()
        log_entry = {
            'timestamp': timestamp.isoformat(),
            'session_id': session_id,
            'type': prompt_type,
            'content': content[:500] + "..." if len(content) > 500 else content
        }
        
        self.prompt_logs.append(log_entry)
        
        # Dosyaya kaydet
        log_file = f"{self.data_dir}/logs/prompts_{timestamp.strftime('%Y%m%d')}.json"
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
        
        # GUI'yi güncelle
        self.update_prompt_display()
    
    def add_alert(self, alert_type, message, session_id=None):
        """Uyarı ekle"""
        timestamp = datetime.datetime.now()
        alert = {
            'timestamp': timestamp.isoformat(),
            'type': alert_type,
            'message': message,
            'session_id': session_id
        }
        
        self.alerts.append(alert)
        
        # GUI'yi thread-safe bir şekilde güncelle
        try:
            if hasattr(self, 'root'):
                self.root.after_idle(self.safe_update_alerts_display)
        except (tk.TclError, RuntimeError):
            pass  # GUI kapalıysa ignore et
    
    def monitor_sessions(self):
        """Session'ları sürekli izle"""
        while True:
            try:
                # Claude pencerelerini bul
                claude_windows = self.find_claude_windows()
                browser_tabs = self.find_browser_claude_tabs()
                
                current_time = datetime.datetime.now()
                
                # Mevcut session'ları güncelle
                active_sessions = set()
                
                for window in claude_windows + browser_tabs:
                    session_id = f"{window['pid']}_{window.get('hwnd', 0)}"
                    active_sessions.add(session_id)
                    
                    if session_id not in self.sessions:
                        # Yeni session
                        self.sessions[session_id] = {
                            'id': session_id,
                            'start_time': current_time,
                            'last_seen': current_time,
                            'window_info': window,
                            'prompt_count': 0,
                            'warnings': [],
                            'status': 'active'
                        }
                        
                        self.add_alert('session_start', f"Yeni Claude session başladı: {window['title']}", session_id)
                    else:
                        # Mevcut session'ı güncelle
                        self.sessions[session_id]['last_seen'] = current_time
                
                # Kapanmış session'ları işaretle
                for session_id in list(self.sessions.keys()):
                    if session_id not in active_sessions and self.sessions[session_id]['status'] == 'active':
                        self.sessions[session_id]['status'] = 'closed'
                        self.add_alert('session_end', f"Claude session kapandı: {session_id}", session_id)
                
                # GUI'yi thread-safe bir şekilde güncelle
                try:
                    if hasattr(self, 'root'):
                        self.root.after_idle(self.safe_update_session_display)
                except (tk.TclError, RuntimeError):
                    pass  # GUI kapalıysa ignore et
                
                time.sleep(5)  # 5 saniyede bir kontrol et
                
            except Exception as e:
                self.add_alert('error', f"Monitoring hatası: {str(e)}")
                time.sleep(10)
    
    def safe_update_session_display(self):
        """Thread-safe session listesi güncelleme"""
        try:
            self.update_session_display()
        except Exception as e:
            print(f"Session display update error: {e}")
    
    def update_session_display(self):
        """Session listesini güncelle"""
        if not hasattr(self, 'session_tree') or not self.session_tree.winfo_exists():
            return
            
        # Mevcut öğeleri temizle
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)
        
        # Session'ları ekle
        for session_id, session in self.sessions.items():
            try:
                duration = datetime.datetime.now() - session['start_time']
                duration_str = str(duration).split('.')[0]  # Mikrosaniyeleri çıkar
                
                warnings_count = len(session.get('warnings', []))
                
                self.session_tree.insert('', 'end', 
                                       text=session_id,
                                       values=(session['status'], 
                                              session['start_time'].strftime('%H:%M:%S'),
                                              duration_str,
                                              warnings_count))
            except Exception as e:
                print(f"Error adding session {session_id}: {e}")
    
    def update_prompt_display(self):
        """Prompt günlüğünü güncelle"""
        self.prompt_text.delete(1.0, tk.END)
        
        for log in self.prompt_logs[-100:]:  # Son 100 log
            timestamp = datetime.datetime.fromisoformat(log['timestamp'])
            self.prompt_text.insert(tk.END, 
                                  f"[{timestamp.strftime('%H:%M:%S')}] {log['type']}: {log['content']}\n\n")
        
        self.prompt_text.see(tk.END)
    
    def safe_update_alerts_display(self):
        """Thread-safe alerts listesi güncelleme"""
        try:
            self.update_alerts_display()
        except Exception as e:
            print(f"Alerts display update error: {e}")
    
    def update_alerts_display(self):
        """Uyarılar listesini güncelle"""
        if not hasattr(self, 'alerts_tree') or not self.alerts_tree.winfo_exists():
            return
            
        # Mevcut öğeleri temizle
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
        
        # Uyarıları ekle
        for alert in self.alerts[-50:]:  # Son 50 uyarı
            try:
                timestamp = datetime.datetime.fromisoformat(alert['timestamp'])
                self.alerts_tree.insert('', 'end',
                                      values=(timestamp.strftime('%H:%M:%S'),
                                             alert['type'],
                                             alert['message']))
            except Exception as e:
                print(f"Error adding alert: {e}")
    
    def update_stats_display(self):
        """İstatistikleri güncelle"""
        stats = f"""
Claude Session Monitor İstatistikleri
=====================================

Toplam Session: {len(self.sessions)}
Aktif Session: {len([s for s in self.sessions.values() if s['status'] == 'active'])}
Kapanmış Session: {len([s for s in self.sessions.values() if s['status'] == 'closed'])}

Toplam Prompt: {len(self.prompt_logs)}
Toplam Uyarı: {len(self.alerts)}

Son Güncelleme: {datetime.datetime.now().strftime('%H:%M:%S')}
"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
    
    def start_monitoring(self):
        """İzlemeyi başlat"""
        # Monitoring thread'ini başlat
        monitor_thread = threading.Thread(target=self.monitor_sessions, daemon=True)
        monitor_thread.start()
        
        # GUI güncelleme döngüsü
        def update_gui():
            self.update_stats_display()
            self.root.after(2000, update_gui)  # 2 saniyede bir güncelle
        
        update_gui()
    
    def run(self):
        """Uygulamayı çalıştır"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        monitor = ClaudeMonitor()
        monitor.run()
    except Exception as e:
        print(f"Uygulama başlatma hatası: {e}")
        input("Devam etmek için Enter'a basın...")