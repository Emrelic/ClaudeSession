import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import datetime
import json
import os
from claude_monitor import ClaudeMonitor
from advanced_text_monitor import AdvancedTextMonitor, ClipboardMonitor
from confirmation_detector import ConfirmationDetector
from limit_tracker import LimitTracker
from token_tracker import TokenTracker
from scheduler_system import ScheduledPromptSystem

class ClaudeSessionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Session Manager - Gelişmiş İzleme Sistemi")
        self.root.geometry("1400x900")
        self.root.state('zoomed')  # Tam ekran başlat
        
        # Tema ayarı
        style = ttk.Style()
        style.theme_use('clam')
        
        # Ana bileşenler
        self.base_monitor = ClaudeMonitor()
        self.text_monitor = AdvancedTextMonitor(self.base_monitor)
        self.clipboard_monitor = ClipboardMonitor(self.base_monitor)
        self.confirmation_detector = ConfirmationDetector(self.base_monitor)
        self.limit_tracker = LimitTracker(self.base_monitor)
        self.token_tracker = TokenTracker(self.base_monitor)
        self.scheduler_system = ScheduledPromptSystem(self.base_monitor)
        
        # UI bileşenleri
        self.create_main_ui()
        self.create_status_bar()
        self.create_menu_bar()
        
        # Monitoring başlat
        self.start_all_monitoring()
        
        # Auto-save
        self.setup_auto_save()
        
    def create_main_ui(self):
        """Ana UI'yi oluştur"""
        # Ana container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sol panel - Session listesi ve kontroller
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        self.create_left_panel(left_panel)
        
        # Sağ panel - Detay ve log'lar
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)
        
        self.create_right_panel(right_panel)
    
    def create_left_panel(self, parent):
        """Sol panel - Session yönetimi"""
        # Başlık
        title_label = ttk.Label(parent, text="Claude Session Manager", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Kontrol butonları
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(control_frame, text="Yenile", 
                  command=self.refresh_sessions).pack(side="left", padx=(0, 5))
        ttk.Button(control_frame, text="Limit Dashboard", 
                  command=self.limit_tracker.show_limit_dashboard).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Token Dashboard", 
                  command=self.token_tracker.show_token_dashboard).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Zamanlanmış Prompt", 
                  command=self.scheduler_system.show_scheduler_dashboard).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Ayarlar", 
                  command=self.show_settings).pack(side="left", padx=5)
        
        # Session listesi
        session_frame = ttk.LabelFrame(parent, text="Aktif Claude Session'ları", padding="5")
        session_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Treeview
        self.session_tree = ttk.Treeview(session_frame, 
                                        columns=("status", "start_time", "duration", "alerts", "prompts"), 
                                        show="tree headings")
        
        self.session_tree.heading("#0", text="Session ID")
        self.session_tree.heading("status", text="Durum")
        self.session_tree.heading("start_time", text="Başlama")
        self.session_tree.heading("duration", text="Süre")
        self.session_tree.heading("alerts", text="Uyarılar")
        self.session_tree.heading("prompts", text="Prompt'lar")
        
        # Column widths
        self.session_tree.column("#0", width=150)
        self.session_tree.column("status", width=80)
        self.session_tree.column("start_time", width=100)
        self.session_tree.column("duration", width=80)
        self.session_tree.column("alerts", width=60)
        self.session_tree.column("prompts", width=60)
        
        # Scrollbar
        session_scrollbar = ttk.Scrollbar(session_frame, orient="vertical", 
                                         command=self.session_tree.yview)
        self.session_tree.configure(yscrollcommand=session_scrollbar.set)
        
        self.session_tree.pack(side="left", fill="both", expand=True)
        session_scrollbar.pack(side="right", fill="y")
        
        # Session tıklama event'i
        self.session_tree.bind("<<TreeviewSelect>>", self.on_session_select)
        
        # Hızlı istatistikler
        stats_frame = ttk.LabelFrame(parent, text="Hızlı İstatistikler", padding="5")
        stats_frame.pack(fill="x")
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        self.stats_text.pack(fill="x")
    
    def create_right_panel(self, parent):
        """Sağ panel - Detaylar ve log'lar"""
        # Notebook
        self.detail_notebook = ttk.Notebook(parent)
        self.detail_notebook.pack(fill="both", expand=True)
        
        # Session Detayları
        detail_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(detail_frame, text="Session Detayları")
        self.create_session_detail_ui(detail_frame)
        
        # Prompt Günlüğü
        prompt_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(prompt_frame, text="Prompt Günlüğü")
        self.create_prompt_log_ui(prompt_frame)
        
        # Uyarılar
        alerts_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(alerts_frame, text="Uyarılar")
        self.create_alerts_ui(alerts_frame)
        
        # Canlı İzleme
        live_frame = ttk.Frame(self.detail_notebook)
        self.detail_notebook.add(live_frame, text="Canlı İzleme")
        self.create_live_monitoring_ui(live_frame)
    
    def create_session_detail_ui(self, parent):
        """Session detay UI'si"""
        # Seçili session bilgileri
        info_frame = ttk.LabelFrame(parent, text="Session Bilgileri", padding="10")
        info_frame.pack(fill="x", pady=(0, 10))
        
        self.session_info_text = scrolledtext.ScrolledText(info_frame, height=8, wrap=tk.WORD)
        self.session_info_text.pack(fill="x")
        
        # Session işlemleri
        actions_frame = ttk.LabelFrame(parent, text="İşlemler", padding="5")
        actions_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(actions_frame, text="Session'a Odaklan", 
                  command=self.focus_selected_session).pack(side="left", padx=(0, 5))
        ttk.Button(actions_frame, text="Prompt'ları Dışa Aktar", 
                  command=self.export_session_prompts).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Session Kapatma Alarmı", 
                  command=self.set_session_alarm).pack(side="left", padx=5)
        
        # Session timeline
        timeline_frame = ttk.LabelFrame(parent, text="Session Timeline", padding="5")
        timeline_frame.pack(fill="both", expand=True)
        
        self.timeline_tree = ttk.Treeview(timeline_frame, 
                                         columns=("time", "event", "details"), 
                                         show="headings")
        self.timeline_tree.heading("time", text="Zaman")
        self.timeline_tree.heading("event", text="Event")
        self.timeline_tree.heading("details", text="Detaylar")
        
        timeline_scrollbar = ttk.Scrollbar(timeline_frame, orient="vertical", 
                                          command=self.timeline_tree.yview)
        self.timeline_tree.configure(yscrollcommand=timeline_scrollbar.set)
        
        self.timeline_tree.pack(side="left", fill="both", expand=True)
        timeline_scrollbar.pack(side="right", fill="y")
    
    def create_prompt_log_ui(self, parent):
        """Prompt log UI'si"""
        # Filtreler
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filtrele:").pack(side="left")
        
        self.filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                   values=["Tümü", "User Prompts", "Claude Responses", "Confirmations"])
        filter_combo.set("Tümü")
        filter_combo.pack(side="left", padx=(5, 0))
        filter_combo.bind("<<ComboboxSelected>>", self.filter_prompts)
        
        # Search
        ttk.Label(filter_frame, text="Ara:").pack(side="left", padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.pack(side="left", padx=(0, 5))
        search_entry.bind("<KeyRelease>", self.search_prompts)
        
        ttk.Button(filter_frame, text="Temizle", 
                  command=self.clear_search).pack(side="left", padx=5)
        
        # Prompt listesi
        self.prompt_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD)
        self.prompt_text.pack(fill="both", expand=True)
        
        # Text formatting tags
        self.prompt_text.tag_configure("user_prompt", foreground="blue", font=("Arial", 10, "bold"))
        self.prompt_text.tag_configure("claude_response", foreground="green")
        self.prompt_text.tag_configure("confirmation", foreground="red", font=("Arial", 10, "bold"))
        self.prompt_text.tag_configure("timestamp", foreground="gray", font=("Arial", 8))
    
    def create_alerts_ui(self, parent):
        """Uyarılar UI'si"""
        # Uyarı filtreleri
        alert_filter_frame = ttk.Frame(parent)
        alert_filter_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(alert_filter_frame, text="Uyarı Tipi:").pack(side="left")
        
        self.alert_filter_var = tk.StringVar()
        alert_filter_combo = ttk.Combobox(alert_filter_frame, textvariable=self.alert_filter_var,
                                         values=["Tümü", "Confirmations", "Limits", "Errors", "Sessions"])
        alert_filter_combo.set("Tümü")
        alert_filter_combo.pack(side="left", padx=(5, 0))
        
        ttk.Button(alert_filter_frame, text="Uyarıları Temizle", 
                  command=self.clear_alerts).pack(side="right")
        
        # Uyarı listesi
        self.alerts_tree = ttk.Treeview(parent, 
                                       columns=("time", "session", "type", "message"), 
                                       show="headings")
        self.alerts_tree.heading("time", text="Zaman")
        self.alerts_tree.heading("session", text="Session")
        self.alerts_tree.heading("type", text="Tip")
        self.alerts_tree.heading("message", text="Mesaj")
        
        alerts_scrollbar = ttk.Scrollbar(parent, orient="vertical", 
                                        command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_tree.pack(side="left", fill="both", expand=True)
        alerts_scrollbar.pack(side="right", fill="y")
    
    def create_live_monitoring_ui(self, parent):
        """Canlı izleme UI'si"""
        # Monitoring kontrolü
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=(0, 10))
        
        self.monitoring_var = tk.BooleanVar(value=True)
        monitoring_check = ttk.Checkbutton(control_frame, text="Canlı İzleme Aktif", 
                                          variable=self.monitoring_var,
                                          command=self.toggle_monitoring)
        monitoring_check.pack(side="left")
        
        ttk.Button(control_frame, text="İzleme Logunu Temizle", 
                  command=self.clear_monitoring_log).pack(side="right")
        
        # Canlı log
        self.live_log = scrolledtext.ScrolledText(parent, wrap=tk.WORD)
        self.live_log.pack(fill="both", expand=True)
        
        # Log formatting
        self.live_log.tag_configure("info", foreground="blue")
        self.live_log.tag_configure("warning", foreground="orange")
        self.live_log.tag_configure("error", foreground="red")
        self.live_log.tag_configure("success", foreground="green")
    
    def create_status_bar(self):
        """Status bar oluştur"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side="bottom", fill="x")
        
        self.status_text = tk.StringVar()
        self.status_text.set("Claude Session Manager hazır")
        
        status_label = ttk.Label(self.status_frame, textvariable=self.status_text)
        status_label.pack(side="left", padx=5)
        
        # Sistem durumu
        self.system_status = tk.StringVar()
        self.system_status.set("●")  # Yeşil nokta
        
        system_label = ttk.Label(self.status_frame, textvariable=self.system_status, 
                                foreground="green", font=("Arial", 12))
        system_label.pack(side="right", padx=5)
        
        ttk.Label(self.status_frame, text="Sistem:").pack(side="right")
    
    def create_menu_bar(self):
        """Menu bar oluştur"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Dosya menüsü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Verileri Dışa Aktar", command=self.export_data)
        file_menu.add_command(label="Verileri İçe Aktar", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.on_closing)
        
        # Görünüm menüsü
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        view_menu.add_command(label="Limit Dashboard", 
                             command=self.limit_tracker.show_limit_dashboard)
        view_menu.add_command(label="Onay Detektörü", 
                             command=self.confirmation_detector.show_confirmation_dialog)
        
        # Araçlar menüsü
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Araçlar", menu=tools_menu)
        tools_menu.add_command(label="Ayarlar", command=self.show_settings)
        tools_menu.add_command(label="Log Dosyaları", command=self.open_log_folder)
        tools_menu.add_command(label="Test Modu", command=self.enable_test_mode)
        
        # Yardım menüsü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Kullanım Kılavuzu", command=self.show_help)
        help_menu.add_command(label="Hakkında", command=self.show_about)
    
    def start_all_monitoring(self):
        """Tüm monitoring sistemlerini başlat"""
        self.text_monitor.start_monitoring()
        self.clipboard_monitor.start_monitoring()
        self.limit_tracker.start_monitoring()
        self.token_tracker.start_monitoring()
        
        # GUI güncelleme döngüsü
        self.update_gui()
    
    def update_gui(self):
        """GUI'yi düzenli olarak güncelle"""
        try:
            self.update_session_list()
            self.update_stats()
            self.update_alerts_display()
            self.update_live_log()
            
            # System status güncelle
            active_sessions = len([s for s in self.base_monitor.sessions.values() 
                                 if s['status'] == 'active'])
            self.status_text.set(f"Aktif session: {active_sessions} | "
                               f"Toplam prompt: {len(self.base_monitor.prompt_logs)} | "
                               f"Uyarılar: {len(self.base_monitor.alerts)}")
            
        except Exception as e:
            self.log_to_live_monitor(f"GUI güncelleme hatası: {e}", "error")
        
        # 2 saniye sonra tekrar güncelle
        self.root.after(2000, self.update_gui)
    
    def update_session_list(self):
        """Session listesini güncelle"""
        # Mevcut öğeleri temizle
        for item in self.session_tree.get_children():
            self.session_tree.delete(item)
        
        # Session'ları ekle
        for session_id, session in self.base_monitor.sessions.items():
            duration = datetime.datetime.now() - session['start_time']
            duration_str = str(duration).split('.')[0]
            
            alert_count = len([a for a in self.base_monitor.alerts 
                             if a.get('session_id') == session_id])
            prompt_count = len([p for p in self.base_monitor.prompt_logs 
                              if p.get('session_id') == session_id])
            
            # Durum rengi
            status_color = {"active": "green", "closed": "red", "error": "orange"}.get(session['status'], "black")
            
            item = self.session_tree.insert('', 'end', 
                                           text=session_id,
                                           values=(session['status'], 
                                                  session['start_time'].strftime('%H:%M:%S'),
                                                  duration_str,
                                                  alert_count,
                                                  prompt_count))
            
            # Durum rengini ayarla
            self.session_tree.set(item, "status", session['status'])
    
    def update_stats(self):
        """İstatistikleri güncelle"""
        total_sessions = len(self.base_monitor.sessions)
        active_sessions = len([s for s in self.base_monitor.sessions.values() if s['status'] == 'active'])
        total_prompts = len(self.base_monitor.prompt_logs)
        total_alerts = len(self.base_monitor.alerts)
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_prompts = len([p for p in self.base_monitor.prompt_logs 
                            if p['timestamp'].startswith(today)])
        
        stats_text = f"""📊 SESSION İSTATİSTİKLERİ
─────────────────────
Toplam Session: {total_sessions}
Aktif Session: {active_sessions}
Kapalı Session: {total_sessions - active_sessions}

💬 PROMPT İSTATİSTİKLERİ
─────────────────────
Toplam Prompt: {total_prompts}
Bugünkü Prompt: {today_prompts}

⚠️  UYARI İSTATİSTİKLERİ
─────────────────────
Toplam Uyarı: {total_alerts}
Aktif Uyarılar: {len([a for a in self.base_monitor.alerts[-10:]])}

🕐 SON GÜNCELLEMe
─────────────────────
{datetime.datetime.now().strftime('%H:%M:%S')}"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def log_to_live_monitor(self, message, level="info"):
        """Canlı monitöre log ekle"""
        if not hasattr(self, 'live_log'):
            return
        
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.live_log.insert(tk.END, formatted_message, level)
        self.live_log.see(tk.END)
        
        # Çok fazla log birikirse temizle
        if len(self.live_log.get(1.0, tk.END).split('\n')) > 1000:
            lines = self.live_log.get(1.0, tk.END).split('\n')
            self.live_log.delete(1.0, tk.END)
            self.live_log.insert(1.0, '\n'.join(lines[-500:]))
    
    def setup_auto_save(self):
        """Otomatik kaydetme ayarla"""
        def auto_save():
            try:
                self.save_session_data()
                self.log_to_live_monitor("Veriler otomatik kaydedildi", "success")
            except Exception as e:
                self.log_to_live_monitor(f"Otomatik kaydetme hatası: {e}", "error")
        
        # Her 5 dakikada bir kaydet
        def schedule_auto_save():
            auto_save()
            self.root.after(300000, schedule_auto_save)  # 5 dakika
        
        schedule_auto_save()
    
    def save_session_data(self):
        """Session verilerini kaydet"""
        def serialize_datetime(obj):
            """Datetime objelerini serialize et"""
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            else:
                return obj
        
        data = {
            'sessions': serialize_datetime(self.base_monitor.sessions),
            'prompt_logs': serialize_datetime(self.base_monitor.prompt_logs),
            'alerts': serialize_datetime(self.base_monitor.alerts),
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        os.makedirs("claude_session_data/backups", exist_ok=True)
        filename = f"claude_session_data/backups/session_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Event handler'lar
    def on_session_select(self, event):
        """Session seçildiğinde"""
        selection = self.session_tree.selection()
        if selection:
            session_id = self.session_tree.item(selection[0])['text']
            self.show_session_details(session_id)
    
    def show_session_details(self, session_id):
        """Session detaylarını göster"""
        if session_id in self.base_monitor.sessions:
            session = self.base_monitor.sessions[session_id]
            
            details = f"""Session ID: {session_id}
Durum: {session['status']}
Başlama Zamanı: {session['start_time']}
Son Görülme: {session.get('last_seen', 'N/A')}
Window Bilgisi: {session.get('window_info', {})}
Prompt Sayısı: {session.get('prompt_count', 0)}
Uyarı Sayısı: {len(session.get('warnings', []))}"""
            
            self.session_info_text.delete(1.0, tk.END)
            self.session_info_text.insert(1.0, details)
    
    def refresh_sessions(self):
        """Session'ları yenile"""
        self.log_to_live_monitor("Session'lar yenileniyor...", "info")
        # Force refresh
        self.update_session_list()
    
    def show_settings(self):
        """Ayarlar penceresini göster"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ayarlar")
        settings_window.geometry("400x300")
        
        # Placeholder
        ttk.Label(settings_window, text="Ayarlar (Geliştirme aşamasında)").pack(pady=20)
    
    def on_closing(self):
        """Uygulama kapatılırken"""
        try:
            self.save_session_data()
            self.log_to_live_monitor("Veriler kaydedildi, uygulama kapatılıyor...", "info")
        except Exception as e:
            print(f"Kapanış hatası: {e}")
        
        self.root.destroy()
    
    # Placeholder metodlar
    def filter_prompts(self, event=None): pass
    def search_prompts(self, event=None): pass
    def clear_search(self): pass
    def update_alerts_display(self): pass
    def update_live_log(self): pass
    def clear_alerts(self): pass
    def toggle_monitoring(self): pass
    def clear_monitoring_log(self): pass
    def focus_selected_session(self): pass
    def export_session_prompts(self): pass
    def set_session_alarm(self): pass
    def export_data(self): pass
    def import_data(self): pass
    def open_log_folder(self): pass
    def enable_test_mode(self): pass
    def show_help(self): pass
    def show_about(self): pass
    
    def run(self):
        """Uygulamayı çalıştır"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = ClaudeSessionApp()
        app.run()
    except Exception as e:
        print(f"Uygulama başlatma hatası: {e}")
        input("Devam etmek için Enter'a basın...")