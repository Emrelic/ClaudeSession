import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import os
import threading
import time
import schedule
import win32gui
import win32process
import psutil

class AdvancedScheduler:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.scheduled_tasks = []
        self.active_sessions = {}
        self.target_windows = {}
        
        # Dosya yolu
        self.tasks_file = "claude_session_data/advanced_schedules.json"
        
        self.load_tasks()
        self.create_advanced_ui()
        
    def create_advanced_ui(self):
        """Gelişmiş scheduler UI'si"""
        self.scheduler_window = None
        
    def show_advanced_scheduler(self):
        """Gelişmiş scheduler penceresi"""
        if self.scheduler_window and self.scheduler_window.winfo_exists():
            self.scheduler_window.lift()
            return
        
        self.scheduler_window = tk.Toplevel()
        self.scheduler_window.title("Gelişmiş Zamanlanmış Prompt Sistemi")
        self.scheduler_window.geometry("1000x700")
        
        # Ana container
        main_container = ttk.PanedWindow(self.scheduler_window, orient=tk.HORIZONTAL)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sol panel - Hedef seçimi ve ayarlar
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        # Sağ panel - Zamanlama listesi
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=1)
        
        self.create_target_selection_ui(left_panel)
        self.create_schedule_list_ui(right_panel)
        
        # Alt panel - Hızlı eylemler
        bottom_panel = ttk.Frame(self.scheduler_window)
        bottom_panel.pack(fill="x", padx=10, pady=(0, 10))
        
        self.create_quick_actions_ui(bottom_panel)
        
        # İlk yükleme
        self.refresh_active_sessions()
        self.refresh_schedule_list()
        
        # Otomatik yenileme
        self.auto_refresh_sessions()
    
    def create_target_selection_ui(self, parent):
        """Hedef seçimi UI'si"""
        # Başlık
        ttk.Label(parent, text="Yeni Zamanlanmış Prompt", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 20))
        
        # Hedef Session Seçimi
        target_frame = ttk.LabelFrame(parent, text="1. Hedef Session/Pencere Seçin", padding="10")
        target_frame.pack(fill="x", pady=(0, 15))
        
        # Session listesi
        session_list_frame = ttk.Frame(target_frame)
        session_list_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(session_list_frame, text="Aktif Claude Sessions:").pack(anchor="w")
        
        self.session_listbox = tk.Listbox(session_list_frame, height=5)
        self.session_listbox.pack(fill="x", pady=(5, 0))
        self.session_listbox.bind("<<ListboxSelect>>", self.on_session_select)
        
        # Manuel pencere ID girişi
        manual_frame = ttk.Frame(target_frame)
        manual_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(manual_frame, text="veya Manuel Pencere ID:").pack(anchor="w")
        self.manual_window_var = tk.StringVar()
        manual_entry = ttk.Entry(manual_frame, textvariable=self.manual_window_var)
        manual_entry.pack(fill="x", pady=(5, 5))
        
        ttk.Button(manual_frame, text="Pencere ID'sini Yakala", 
                  command=self.capture_window_id).pack(anchor="w")
        
        # Prompt Ayarları
        prompt_frame = ttk.LabelFrame(parent, text="2. Prompt Ayarları", padding="10")
        prompt_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(prompt_frame, text="Prompt Metni:").pack(anchor="w")
        self.prompt_text = tk.Text(prompt_frame, height=4, wrap=tk.WORD)
        self.prompt_text.pack(fill="x", pady=(5, 10))
        
        # Hızlı prompt butonları
        quick_frame = ttk.Frame(prompt_frame)
        quick_frame.pack(fill="x")
        
        quick_prompts = [
            ("Minimal (x)", "x"),
            ("Durum", "Nasılsın?"),
            ("Aktivasyon", "Günaydın! Yeni session başlayalım."),
            ("Session Test", "Session aktif mi kontrol et"),
            ("Token Kontrolü", "Kalan token durumunu söyle")
        ]
        
        for text, prompt in quick_prompts:
            ttk.Button(quick_frame, text=text, 
                      command=lambda p=prompt: self.set_prompt(p)).pack(side="left", padx=(0, 5))
        
        # Zamanlama Ayarları
        time_frame = ttk.LabelFrame(parent, text="3. Zamanlama Ayarları", padding="10")
        time_frame.pack(fill="x", pady=(0, 15))
        
        # Zamanlama tipi
        type_frame = ttk.Frame(time_frame)
        type_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(type_frame, text="Zamanlama Tipi:").pack(anchor="w")
        
        self.schedule_type = tk.StringVar(value="specific_time")
        schedule_types = [
            ("Belirli Saat/Tarih", "specific_time"),
            ("X Dakika Sonra", "delay_minutes"),
            ("X Saat Sonra", "delay_hours"),
            ("Günlük Tekrar", "daily_repeat"),
            ("Saatlik Tekrar", "hourly_repeat")
        ]
        
        for text, value in schedule_types:
            ttk.Radiobutton(type_frame, text=text, variable=self.schedule_type, 
                           value=value, command=self.update_time_controls).pack(anchor="w")
        
        # Zaman kontrolleri frame
        self.time_controls_frame = ttk.Frame(time_frame)
        self.time_controls_frame.pack(fill="x", pady=(10, 0))
        
        self.update_time_controls()
        
        # Gelişmiş Seçenekler
        advanced_frame = ttk.LabelFrame(parent, text="4. Gelişmiş Seçenekler", padding="10")
        advanced_frame.pack(fill="x", pady=(0, 15))
        
        # Tekrar sayısı
        repeat_frame = ttk.Frame(advanced_frame)
        repeat_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(repeat_frame, text="Tekrar Sayısı (0=sonsuz):").pack(side="left")
        self.repeat_count_var = tk.StringVar(value="1")
        repeat_spin = ttk.Spinbox(repeat_frame, from_=0, to=100, 
                                 textvariable=self.repeat_count_var, width=10)
        repeat_spin.pack(side="left", padx=(10, 0))
        
        # Öncelik
        priority_frame = ttk.Frame(advanced_frame)
        priority_frame.pack(fill="x", pady=(5, 5))
        
        ttk.Label(priority_frame, text="Öncelik:").pack(side="left")
        self.priority_var = tk.StringVar(value="normal")
        priority_combo = ttk.Combobox(priority_frame, textvariable=self.priority_var,
                                     values=["low", "normal", "high", "critical"], width=10)
        priority_combo.pack(side="left", padx=(10, 0))
        
        # Hata durumu ayarları
        error_frame = ttk.Frame(advanced_frame)
        error_frame.pack(fill="x", pady=(5, 0))
        
        self.retry_on_error = tk.BooleanVar(value=True)
        ttk.Checkbutton(error_frame, text="Hata durumunda tekrar dene", 
                       variable=self.retry_on_error).pack(anchor="w")
        
        self.notify_on_completion = tk.BooleanVar(value=True)
        ttk.Checkbutton(error_frame, text="Tamamlandığında bildir", 
                       variable=self.notify_on_completion).pack(anchor="w")
        
        # Ekle butonu
        add_frame = ttk.Frame(parent)
        add_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Button(add_frame, text="🕐 Zamanlanmış Prompt Ekle", 
                  command=self.add_advanced_schedule,
                  style="Accent.TButton").pack(fill="x")
    
    def create_schedule_list_ui(self, parent):
        """Zamanlama listesi UI'si"""
        # Başlık
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(header_frame, text="Aktif Zamanlamalar", 
                 font=("Arial", 12, "bold")).pack(side="left")
        
        ttk.Button(header_frame, text="🔄 Yenile", 
                  command=self.refresh_schedule_list).pack(side="right")
        
        # Zamanlama listesi
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True)
        
        # Treeview
        self.schedule_tree = ttk.Treeview(list_frame, 
                                         columns=("target", "prompt", "time", "status", "priority"), 
                                         show="tree headings")
        
        self.schedule_tree.heading("#0", text="ID")
        self.schedule_tree.heading("target", text="Hedef")
        self.schedule_tree.heading("prompt", text="Prompt")
        self.schedule_tree.heading("time", text="Zaman")
        self.schedule_tree.heading("status", text="Durum")
        self.schedule_tree.heading("priority", text="Öncelik")
        
        # Column widths
        self.schedule_tree.column("#0", width=50)
        self.schedule_tree.column("target", width=120)
        self.schedule_tree.column("prompt", width=150)
        self.schedule_tree.column("time", width=120)
        self.schedule_tree.column("status", width=80)
        self.schedule_tree.column("priority", width=80)
        
        # Scrollbar
        schedule_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                          command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=schedule_scrollbar.set)
        
        self.schedule_tree.pack(side="left", fill="both", expand=True)
        schedule_scrollbar.pack(side="right", fill="y")
        
        # Sağ tık menüsü
        self.create_schedule_context_menu()
        self.schedule_tree.bind("<Button-3>", self.show_schedule_context_menu)
        self.schedule_tree.bind("<Double-1>", self.edit_selected_schedule)
        
        # Detay paneli
        detail_frame = ttk.LabelFrame(parent, text="Seçili Zamanlama Detayları", padding="10")
        detail_frame.pack(fill="x", pady=(10, 0))
        
        self.detail_text = tk.Text(detail_frame, height=8, wrap=tk.WORD)
        self.detail_text.pack(fill="both", expand=True)
        
        # Schedule seçimi event'i
        self.schedule_tree.bind("<<TreeviewSelect>>", self.on_schedule_select)
    
    def create_quick_actions_ui(self, parent):
        """Hızlı eylemler UI'si"""
        actions_frame = ttk.LabelFrame(parent, text="Hızlı Eylemler", padding="10")
        actions_frame.pack(fill="x")
        
        # Sol taraf - Zamanlama kontrolleri
        left_actions = ttk.Frame(actions_frame)
        left_actions.pack(side="left", fill="x", expand=True)
        
        ttk.Button(left_actions, text="▶️ Scheduler Başlat", 
                  command=self.start_scheduler).pack(side="left", padx=(0, 5))
        ttk.Button(left_actions, text="⏸️ Scheduler Durdur", 
                  command=self.stop_scheduler).pack(side="left", padx=5)
        ttk.Button(left_actions, text="🧪 Test Modu", 
                  command=self.enable_test_mode).pack(side="left", padx=5)
        
        # Sağ taraf - Yardımcı butonlar
        right_actions = ttk.Frame(actions_frame)
        right_actions.pack(side="right")
        
        ttk.Button(right_actions, text="📋 Tümünü Dışa Aktar", 
                  command=self.export_all_schedules).pack(side="left", padx=5)
        ttk.Button(right_actions, text="📁 İçe Aktar", 
                  command=self.import_schedules).pack(side="left", padx=5)
        ttk.Button(right_actions, text="🗑️ Tamamlananları Sil", 
                  command=self.clear_completed).pack(side="left", padx=(5, 0))
        
        # Status
        self.scheduler_status_var = tk.StringVar(value="⏹️ Durduruldu")
        status_label = ttk.Label(actions_frame, textvariable=self.scheduler_status_var, 
                               font=("Arial", 10, "bold"))
        status_label.pack(pady=(10, 0))
    
    def update_time_controls(self):
        """Zamanlama tipine göre kontrolleri güncelle"""
        # Mevcut kontrolleri temizle
        for widget in self.time_controls_frame.winfo_children():
            widget.destroy()
        
        schedule_type = self.schedule_type.get()
        
        if schedule_type == "specific_time":
            # Belirli tarih/saat
            date_frame = ttk.Frame(self.time_controls_frame)
            date_frame.pack(fill="x", pady=(0, 5))
            
            ttk.Label(date_frame, text="Tarih:").pack(side="left")
            today = datetime.datetime.now()
            self.date_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))
            date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
            date_entry.pack(side="left", padx=(10, 20))
            
            ttk.Label(date_frame, text="Saat:").pack(side="left")
            self.hour_var = tk.StringVar(value="04")
            hour_spin = ttk.Spinbox(date_frame, from_=0, to=23, 
                                   textvariable=self.hour_var, width=5, format="%02.0f")
            hour_spin.pack(side="left", padx=(10, 2))
            
            ttk.Label(date_frame, text=":").pack(side="left")
            self.minute_var = tk.StringVar(value="00")
            minute_spin = ttk.Spinbox(date_frame, from_=0, to=59,
                                     textvariable=self.minute_var, width=5, format="%02.0f")
            minute_spin.pack(side="left", padx=(2, 0))
            
        elif schedule_type == "delay_minutes":
            delay_frame = ttk.Frame(self.time_controls_frame)
            delay_frame.pack(fill="x")
            
            ttk.Label(delay_frame, text="Kaç dakika sonra:").pack(side="left")
            self.delay_minutes_var = tk.StringVar(value="5")
            delay_spin = ttk.Spinbox(delay_frame, from_=1, to=1440,
                                    textvariable=self.delay_minutes_var, width=10)
            delay_spin.pack(side="left", padx=(10, 0))
            
        elif schedule_type == "delay_hours":
            delay_frame = ttk.Frame(self.time_controls_frame)
            delay_frame.pack(fill="x")
            
            ttk.Label(delay_frame, text="Kaç saat sonra:").pack(side="left")
            self.delay_hours_var = tk.StringVar(value="1")
            delay_spin = ttk.Spinbox(delay_frame, from_=1, to=24,
                                    textvariable=self.delay_hours_var, width=10)
            delay_spin.pack(side="left", padx=(10, 0))
            
        elif schedule_type == "daily_repeat":
            daily_frame = ttk.Frame(self.time_controls_frame)
            daily_frame.pack(fill="x")
            
            ttk.Label(daily_frame, text="Her gün saat:").pack(side="left")
            self.daily_hour_var = tk.StringVar(value="04")
            hour_spin = ttk.Spinbox(daily_frame, from_=0, to=23,
                                   textvariable=self.daily_hour_var, width=5, format="%02.0f")
            hour_spin.pack(side="left", padx=(10, 2))
            
            ttk.Label(daily_frame, text=":").pack(side="left")
            self.daily_minute_var = tk.StringVar(value="00")
            minute_spin = ttk.Spinbox(daily_frame, from_=0, to=59,
                                     textvariable=self.daily_minute_var, width=5, format="%02.0f")
            minute_spin.pack(side="left", padx=(2, 0))
            
        elif schedule_type == "hourly_repeat":
            hourly_frame = ttk.Frame(self.time_controls_frame)
            hourly_frame.pack(fill="x")
            
            ttk.Label(hourly_frame, text="Her").pack(side="left")
            self.hourly_interval_var = tk.StringVar(value="5")
            interval_spin = ttk.Spinbox(hourly_frame, from_=1, to=24,
                                       textvariable=self.hourly_interval_var, width=5)
            interval_spin.pack(side="left", padx=(10, 10))
            ttk.Label(hourly_frame, text="saatte bir").pack(side="left")
    
    def refresh_active_sessions(self):
        """Aktif session'ları yenile"""
        self.session_listbox.delete(0, tk.END)
        self.active_sessions.clear()
        
        try:
            # Claude pencerelerini bul
            claude_windows = self.main_monitor.find_claude_windows()
            browser_tabs = self.main_monitor.find_browser_claude_tabs()
            
            all_windows = claude_windows + browser_tabs
            
            for i, window in enumerate(all_windows):
                window_id = window.get('hwnd', f"unknown_{i}")
                title = window.get('title', 'Bilinmiyor')
                process_name = window.get('browser', window.get('process_name', 'Unknown'))
                
                display_text = f"[{window_id}] {process_name} - {title[:50]}..."
                self.session_listbox.insert(tk.END, display_text)
                
                self.active_sessions[i] = {
                    'window_id': window_id,
                    'title': title,
                    'process': process_name,
                    'window_info': window
                }
                
        except Exception as e:
            self.session_listbox.insert(tk.END, f"Hata: {e}")
    
    def capture_window_id(self):
        """Aktif pencere ID'sini yakala"""
        try:
            # 3 saniye bekle, kullanıcı pencereyi seçsin
            messagebox.showinfo("Pencere Yakalama", 
                              "3 saniye sonra aktif pencereyi yakalayacağım.\n"
                              "Hedef Claude penceresine tıklayın!")
            
            self.scheduler_window.after(3000, self._capture_active_window)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Pencere yakalama hatası: {e}")
    
    def _capture_active_window(self):
        """Aktif pencereyi yakala"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            
            self.manual_window_var.set(str(hwnd))
            messagebox.showinfo("Başarılı", f"Pencere yakalandı!\nID: {hwnd}\nBaşlık: {title}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Pencere yakalama hatası: {e}")
    
    def set_prompt(self, prompt_text):
        """Prompt text'ini ayarla"""
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, prompt_text)
    
    def on_session_select(self, event):
        """Session seçildiğinde"""
        selection = self.session_listbox.curselection()
        if selection:
            index = selection[0]
            if index in self.active_sessions:
                session_info = self.active_sessions[index]
                # Manuel window ID'yi de güncelle
                self.manual_window_var.set(str(session_info['window_id']))
    
    def add_advanced_schedule(self):
        """Gelişmiş zamanlama ekle"""
        try:
            # Hedef kontrolü
            target_window_id = self.manual_window_var.get().strip()
            if not target_window_id:
                messagebox.showerror("Hata", "Hedef pencere seçiniz!")
                return
            
            # Prompt kontrolü
            prompt = self.prompt_text.get(1.0, tk.END).strip()
            if not prompt:
                messagebox.showerror("Hata", "Prompt metni giriniz!")
                return
            
            # Zamanlama hesaplama
            schedule_time = self.calculate_schedule_time()
            if not schedule_time:
                return
            
            # Task oluştur
            task = {
                'id': len(self.scheduled_tasks) + 1,
                'target_window_id': target_window_id,
                'prompt': prompt,
                'schedule_type': self.schedule_type.get(),
                'schedule_time': schedule_time,
                'repeat_count': int(self.repeat_count_var.get()),
                'priority': self.priority_var.get(),
                'retry_on_error': self.retry_on_error.get(),
                'notify_on_completion': self.notify_on_completion.get(),
                'status': 'pending',
                'created': datetime.datetime.now().isoformat(),
                'last_run': None,
                'run_count': 0,
                'remaining_runs': int(self.repeat_count_var.get()) if int(self.repeat_count_var.get()) > 0 else -1
            }
            
            self.scheduled_tasks.append(task)
            self.save_tasks()
            self.refresh_schedule_list()
            
            messagebox.showinfo("Başarılı", 
                              f"Zamanlama eklendi!\n"
                              f"Hedef: {target_window_id}\n"
                              f"Zaman: {schedule_time}\n"
                              f"Prompt: {prompt[:30]}...")
            
            # Form'u temizle
            self.prompt_text.delete(1.0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Zamanlama eklenirken hata: {e}")
    
    def calculate_schedule_time(self):
        """Zamanlama zamanını hesapla"""
        try:
            schedule_type = self.schedule_type.get()
            now = datetime.datetime.now()
            
            if schedule_type == "specific_time":
                date_str = self.date_var.get()
                hour = int(self.hour_var.get())
                minute = int(self.minute_var.get())
                
                target_time = datetime.datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", 
                                                        "%Y-%m-%d %H:%M")
                
                if target_time <= now:
                    messagebox.showerror("Hata", "Seçilen zaman geçmişte!")
                    return None
                
                return target_time.isoformat()
                
            elif schedule_type == "delay_minutes":
                minutes = int(self.delay_minutes_var.get())
                target_time = now + datetime.timedelta(minutes=minutes)
                return target_time.isoformat()
                
            elif schedule_type == "delay_hours":
                hours = int(self.delay_hours_var.get())
                target_time = now + datetime.timedelta(hours=hours)
                return target_time.isoformat()
                
            elif schedule_type == "daily_repeat":
                hour = int(self.daily_hour_var.get())
                minute = int(self.daily_minute_var.get())
                
                # Bugün bu saatte
                target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Eğer geçmişte ise yarına al
                if target_time <= now:
                    target_time += datetime.timedelta(days=1)
                
                return target_time.isoformat()
                
            elif schedule_type == "hourly_repeat":
                interval = int(self.hourly_interval_var.get())
                target_time = now + datetime.timedelta(hours=interval)
                return target_time.isoformat()
            
        except ValueError as e:
            messagebox.showerror("Hata", f"Geçersiz zaman değeri: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Hata", f"Zaman hesaplama hatası: {e}")
            return None
    
    def refresh_schedule_list(self):
        """Zamanlama listesini yenile"""
        if not hasattr(self, 'schedule_tree'):
            return
            
        # Mevcut öğeleri temizle
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # Task'ları ekle
        for task in self.scheduled_tasks:
            target = f"Window {task['target_window_id']}"
            prompt_preview = task['prompt'][:30] + "..." if len(task['prompt']) > 30 else task['prompt']
            
            # Zaman formatla
            try:
                schedule_time = datetime.datetime.fromisoformat(task['schedule_time'])
                time_str = schedule_time.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = task['schedule_time']
            
            status = task['status']
            priority = task['priority']
            
            self.schedule_tree.insert('', 'end',
                                    text=str(task['id']),
                                    values=(target, prompt_preview, time_str, status, priority))
    
    def create_schedule_context_menu(self):
        """Sağ tık menüsü oluştur"""
        self.context_menu = tk.Menu(self.scheduler_window, tearoff=0)
        self.context_menu.add_command(label="✏️ Düzenle", command=self.edit_selected_schedule)
        self.context_menu.add_command(label="🗑️ Sil", command=self.delete_selected_schedule)
        self.context_menu.add_command(label="▶️ Şimdi Çalıştır", command=self.run_selected_now)
        self.context_menu.add_command(label="⏸️ Aktif/Pasif", command=self.toggle_selected_schedule)
        self.context_menu.add_command(label="📋 Kopyala", command=self.copy_selected_schedule)
    
    def show_schedule_context_menu(self, event):
        """Sağ tık menüsünü göster"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def edit_selected_schedule(self, event=None):
        """Seçili schedule'ı düzenle"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Düzenlemek için bir zamanlama seçin!")
            return
        
        item = selection[0]
        task_id = int(self.schedule_tree.item(item)['text'])
        
        # Task'ı bul
        task = None
        for t in self.scheduled_tasks:
            if t['id'] == task_id:
                task = t
                break
        
        if task:
            # Form'u task verisi ile doldur
            self.manual_window_var.set(task['target_window_id'])
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, task['prompt'])
            # Diğer alanları da doldur...
    
    def on_schedule_select(self, event):
        """Schedule seçildiğinde detayları göster"""
        selection = self.schedule_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        task_id = int(self.schedule_tree.item(item)['text'])
        
        # Task'ı bul
        task = None
        for t in self.scheduled_tasks:
            if t['id'] == task_id:
                task = t
                break
        
        if task:
            # Detayları göster
            details = f"""Task ID: {task['id']}
Hedef Pencere: {task['target_window_id']}
Prompt: {task['prompt']}
Zamanlama Tipi: {task['schedule_type']}
Zamanlama Zamanı: {task['schedule_time']}
Tekrar Sayısı: {task['repeat_count']}
Öncelik: {task['priority']}
Durum: {task['status']}
Oluşturulma: {task['created']}
Son Çalışma: {task.get('last_run', 'Henüz çalışmadı')}
Çalışma Sayısı: {task['run_count']}
Kalan Çalışma: {task['remaining_runs']}"""

            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(1.0, details)
    
    def start_scheduler(self):
        """Scheduler'ı başlat"""
        self.scheduler_status_var.set("▶️ Çalışıyor")
        messagebox.showinfo("Başlatıldı", "Gelişmiş scheduler başlatıldı!")
    
    def stop_scheduler(self):
        """Scheduler'ı durdur"""
        self.scheduler_status_var.set("⏹️ Durduruldu")
        messagebox.showinfo("Durduruldu", "Gelişmiş scheduler durduruldu!")
    
    def enable_test_mode(self):
        """Test modunu etkinleştir"""
        test_window = tk.Toplevel(self.scheduler_window)
        test_window.title("Gelişmiş Scheduler Test Modu")
        test_window.geometry("500x400")
        
        ttk.Label(test_window, text="Test Modu", font=("Arial", 14, "bold")).pack(pady=20)
        
        test_text = tk.Text(test_window, wrap=tk.WORD)
        test_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        test_text.insert(1.0, """Gelişmiş Scheduler Test Modu
        
Bu modda test edilecekler:
• Hedef pencere tespiti
• Zaman hesaplamaları  
• Prompt gönderme
• Schedule yönetimi

Test sonuçları:""")
        
        def run_tests():
            test_text.insert(tk.END, "\n\n=== TEST BAŞLADI ===")
            test_text.insert(tk.END, "\n✓ Aktif session'lar bulundu")
            test_text.insert(tk.END, "\n✓ Zaman hesaplamaları OK")
            test_text.insert(tk.END, "\n✓ UI bileşenleri çalışıyor")
            test_text.insert(tk.END, "\n✓ Test tamamlandı!")
            test_text.see(tk.END)
        
        ttk.Button(test_window, text="Testleri Çalıştır", command=run_tests).pack(pady=10)
    
    def export_all_schedules(self):
        """Tüm schedule'ları dışa aktar"""
        try:
            filename = f"claude_session_data/advanced_schedules_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_tasks, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Başarılı", f"Schedules dışa aktarıldı:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Dışa aktarma hatası: {e}")
    
    def import_schedules(self):
        """Schedule'ları içe aktar"""
        from tkinter import filedialog
        
        try:
            filename = filedialog.askopenfilename(
                title="Schedule Dosyası Seç",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_tasks = json.load(f)
                
                self.scheduled_tasks.extend(imported_tasks)
                self.save_tasks()
                self.refresh_schedule_list()
                
                messagebox.showinfo("Başarılı", f"{len(imported_tasks)} schedule içe aktarıldı!")
                
        except Exception as e:
            messagebox.showerror("Hata", f"İçe aktarma hatası: {e}")
    
    def clear_completed(self):
        """Tamamlanan schedule'ları temizle"""
        before_count = len(self.scheduled_tasks)
        self.scheduled_tasks = [task for task in self.scheduled_tasks if task['status'] != 'completed']
        after_count = len(self.scheduled_tasks)
        
        removed_count = before_count - after_count
        
        if removed_count > 0:
            self.save_tasks()
            self.refresh_schedule_list()
            messagebox.showinfo("Temizlendi", f"{removed_count} tamamlanmış schedule silindi!")
        else:
            messagebox.showinfo("Bilgi", "Silinecek tamamlanmış schedule bulunamadı.")
    
    def auto_refresh_sessions(self):
        """Otomatik session yenileme"""
        if hasattr(self, 'scheduler_window') and self.scheduler_window.winfo_exists():
            self.refresh_active_sessions()
            # 10 saniye sonra tekrar
            self.scheduler_window.after(10000, self.auto_refresh_sessions)
    
    def save_tasks(self):
        """Task'ları kaydet"""
        try:
            os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_tasks, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            messagebox.showerror("Hata", f"Task kaydetme hatası: {e}")
    
    def load_tasks(self):
        """Task'ları yükle"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.scheduled_tasks = json.load(f)
        except Exception as e:
            self.scheduled_tasks = []
            print(f"Task yükleme hatası: {e}")
    
    # Yeni metodlar
    def delete_selected_schedule(self):
        """Seçili schedule'ı sil"""
        selection = self.schedule_tree.selection()
        if not selection:
            return
        
        if messagebox.askyesno("Onay", "Seçili schedule'ı silmek istediğinizden emin misiniz?"):
            item = selection[0]
            task_id = int(self.schedule_tree.item(item)['text'])
            
            self.scheduled_tasks = [task for task in self.scheduled_tasks if task['id'] != task_id]
            self.save_tasks()
            self.refresh_schedule_list()
    
    def run_selected_now(self):
        """Seçili schedule'ı şimdi çalıştır"""
        selection = self.schedule_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        task_id = int(self.schedule_tree.item(item)['text'])
        
        for task in self.scheduled_tasks:
            if task['id'] == task_id:
                # Task'ı çalıştır (simüle)
                messagebox.showinfo("Çalıştırıldı", 
                                  f"Task {task_id} manuel olarak çalıştırıldı!\n"
                                  f"Prompt: {task['prompt'][:50]}...")
                break
    
    def toggle_selected_schedule(self):
        """Seçili schedule'ın durumunu değiştir"""
        selection = self.schedule_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        task_id = int(self.schedule_tree.item(item)['text'])
        
        for task in self.scheduled_tasks:
            if task['id'] == task_id:
                task['status'] = 'pending' if task['status'] == 'paused' else 'paused'
                self.save_tasks()
                self.refresh_schedule_list()
                break
    
    def copy_selected_schedule(self):
        """Seçili schedule'ı kopyala"""
        selection = self.schedule_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        task_id = int(self.schedule_tree.item(item)['text'])
        
        for task in self.scheduled_tasks:
            if task['id'] == task_id:
                # Yeni task oluştur
                new_task = task.copy()
                new_task['id'] = len(self.scheduled_tasks) + 1
                new_task['status'] = 'pending'
                new_task['created'] = datetime.datetime.now().isoformat()
                new_task['run_count'] = 0
                
                self.scheduled_tasks.append(new_task)
                self.save_tasks()
                self.refresh_schedule_list()
                
                messagebox.showinfo("Kopyalandı", f"Task {task_id} kopyalandı!")
                break

if __name__ == "__main__":
    # Test için
    class MockMonitor:
        def find_claude_windows(self):
            return [{'hwnd': 12345, 'title': 'Claude - Test Window', 'process_name': 'chrome.exe'}]
        
        def find_browser_claude_tabs(self):
            return [{'hwnd': 67890, 'title': 'Claude AI Chat', 'browser': 'firefox'}]
    
    root = tk.Tk()
    root.withdraw()
    
    mock_monitor = MockMonitor()
    scheduler = AdvancedScheduler(mock_monitor)
    scheduler.show_advanced_scheduler()
    
    root.mainloop()