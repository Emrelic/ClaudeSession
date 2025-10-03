import schedule
import time
import threading
import datetime
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import win32gui
import win32api
import win32con

class ScheduledPromptSystem:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.scheduled_prompts = []
        self.running_schedules = {}
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Dosya yolları
        self.schedules_file = "claude_session_data/scheduled_prompts.json"
        
        self.load_schedules()
        self.create_scheduler_ui()
        
    def create_scheduler_ui(self):
        """Scheduler UI penceresi"""
        self.scheduler_window = None
        
    def show_scheduler_dashboard(self):
        """Scheduler dashboard'unu göster"""
        if self.scheduler_window and self.scheduler_window.winfo_exists():
            self.scheduler_window.lift()
            return
        
        self.scheduler_window = tk.Toplevel()
        self.scheduler_window.title("Zamanlanmış Prompt Sistemi")
        self.scheduler_window.geometry("800x700")
        
        # Ana notebook
        notebook = ttk.Notebook(self.scheduler_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Mevcut Schedullar
        current_frame = ttk.Frame(notebook)
        notebook.add(current_frame, text="Mevcut Zamanlamalar")
        self.create_current_schedules_ui(current_frame)
        
        # Yeni Schedule Ekle
        new_frame = ttk.Frame(notebook)
        notebook.add(new_frame, text="Yeni Zamanlama Ekle")
        self.create_new_schedule_ui(new_frame)
        
        # Günlük Program
        daily_frame = ttk.Frame(notebook)
        notebook.add(daily_frame, text="Günlük Program")
        self.create_daily_program_ui(daily_frame)
        
        # Schedule Geçmişi
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="Geçmiş")
        self.create_history_ui(history_frame)
        
        self.update_scheduler_dashboard()
    
    def create_current_schedules_ui(self, parent):
        """Mevcut schedule'lar UI'si"""
        # Kontrol butonları
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=(0, 10))
        
        self.scheduler_status_var = tk.StringVar(value="Durduruldu")
        status_label = ttk.Label(control_frame, textvariable=self.scheduler_status_var, font=("Arial", 10, "bold"))
        status_label.pack(side="left")
        
        ttk.Button(control_frame, text="Başlat", command=self.start_scheduler).pack(side="left", padx=(10, 5))
        ttk.Button(control_frame, text="Durdur", command=self.stop_scheduler).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Yenile", command=self.refresh_schedules).pack(side="left", padx=5)
        
        # Schedule listesi
        self.schedules_tree = ttk.Treeview(parent, 
                                          columns=("time", "prompt", "status", "next_run", "last_run"), 
                                          show="tree headings")
        
        self.schedules_tree.heading("#0", text="ID")
        self.schedules_tree.heading("time", text="Zaman")
        self.schedules_tree.heading("prompt", text="Prompt")
        self.schedules_tree.heading("status", text="Durum")
        self.schedules_tree.heading("next_run", text="Sonraki Çalışma")
        self.schedules_tree.heading("last_run", text="Son Çalışma")
        
        # Column widths
        self.schedules_tree.column("#0", width=50)
        self.schedules_tree.column("time", width=100)
        self.schedules_tree.column("prompt", width=200)
        self.schedules_tree.column("status", width=80)
        self.schedules_tree.column("next_run", width=120)
        self.schedules_tree.column("last_run", width=120)
        
        schedules_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.schedules_tree.yview)
        self.schedules_tree.configure(yscrollcommand=schedules_scrollbar.set)
        
        self.schedules_tree.pack(side="left", fill="both", expand=True)
        schedules_scrollbar.pack(side="right", fill="y")
        
        # Sağ tık menüsü
        self.create_context_menu()
        self.schedules_tree.bind("<Button-3>", self.show_context_menu)
    
    def create_new_schedule_ui(self, parent):
        """Yeni schedule ekleme UI'si"""
        # Prompt bilgileri
        prompt_frame = ttk.LabelFrame(parent, text="Prompt Bilgileri", padding="10")
        prompt_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(prompt_frame, text="Prompt Metni:").pack(anchor="w")
        self.prompt_text = tk.Text(prompt_frame, height=4, wrap=tk.WORD)
        self.prompt_text.pack(fill="x", pady=(5, 10))
        
        # Örnek promptlar
        examples_frame = ttk.Frame(prompt_frame)
        examples_frame.pack(fill="x")
        
        ttk.Label(examples_frame, text="Hızlı Örnekler:").pack(side="left")
        ttk.Button(examples_frame, text="Minimal (x)", 
                  command=lambda: self.set_prompt_text("x")).pack(side="left", padx=(10, 5))
        ttk.Button(examples_frame, text="Durum Kontrolü", 
                  command=lambda: self.set_prompt_text("Merhaba, nasılsın?")).pack(side="left", padx=5)
        ttk.Button(examples_frame, text="Sistem Durumu", 
                  command=lambda: self.set_prompt_text("Sistem durumunu kontrol et")).pack(side="left", padx=5)
        
        # Zamanlama ayarları
        time_frame = ttk.LabelFrame(parent, text="Zamanlama Ayarları", padding="10")
        time_frame.pack(fill="x", pady=(0, 10))
        
        # Zamanlama tipi
        schedule_type_frame = ttk.Frame(time_frame)
        schedule_type_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(schedule_type_frame, text="Zamanlama Tipi:").pack(side="left")
        
        self.schedule_type = tk.StringVar(value="daily")
        schedule_types = [
            ("Günlük", "daily"),
            ("Haftalık", "weekly"), 
            ("Tek Seferlik", "once"),
            ("Her X Saatte", "hourly")
        ]
        
        for text, value in schedule_types:
            ttk.Radiobutton(schedule_type_frame, text=text, variable=self.schedule_type, 
                           value=value, command=self.update_time_options).pack(side="left", padx=(10, 0))
        
        # Zaman seçimi
        self.time_options_frame = ttk.Frame(time_frame)
        self.time_options_frame.pack(fill="x", pady=(10, 0))
        
        self.update_time_options()
        
        # Ekle butonu
        add_frame = ttk.Frame(parent)
        add_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(add_frame, text="Zamanlama Ekle", command=self.add_schedule).pack(side="right")
        ttk.Button(add_frame, text="Önizleme", command=self.preview_schedule).pack(side="right", padx=(0, 10))
    
    def create_daily_program_ui(self, parent):
        """Günlük program UI'si"""
        # Hızlı program şablonları
        templates_frame = ttk.LabelFrame(parent, text="Program Şablonları", padding="10")
        templates_frame.pack(fill="x", pady=(0, 10))
        
        template_buttons = [
            ("Sabah Aktivasyonu (08:00)", self.create_morning_activation),
            ("İş Günü Programı (09:00-18:00)", self.create_work_day_program),
            ("Gece Sessiz Modu (23:00-07:00)", self.create_night_program),
            ("5 Saatlik Döngü", self.create_5hour_cycle)
        ]
        
        for text, command in template_buttons:
            ttk.Button(templates_frame, text=text, command=command).pack(side="left", padx=(0, 10))
        
        # Program önizlemesi
        preview_frame = ttk.LabelFrame(parent, text="Program Önizlemesi", padding="5")
        preview_frame.pack(fill="both", expand=True)
        
        self.program_preview = tk.Text(preview_frame, wrap=tk.WORD)
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.program_preview.yview)
        self.program_preview.configure(yscrollcommand=preview_scrollbar.set)
        
        self.program_preview.pack(side="left", fill="both", expand=True)
        preview_scrollbar.pack(side="right", fill="y")
    
    def create_history_ui(self, parent):
        """Geçmiş UI'si"""
        # Filtreler
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(filter_frame, text="Tarih Aralığı:").pack(side="left")
        
        self.history_period = tk.StringVar(value="bugün")
        period_combo = ttk.Combobox(filter_frame, textvariable=self.history_period,
                                   values=["bugün", "bu hafta", "bu ay", "tümü"])
        period_combo.pack(side="left", padx=(5, 10))
        
        ttk.Button(filter_frame, text="Filtrele", command=self.filter_history).pack(side="left")
        ttk.Button(filter_frame, text="Geçmişi Temizle", command=self.clear_history).pack(side="right")
        
        # Geçmiş listesi
        self.history_tree = ttk.Treeview(parent, 
                                        columns=("time", "prompt", "status", "response"), 
                                        show="headings")
        
        self.history_tree.heading("time", text="Zaman")
        self.history_tree.heading("prompt", text="Prompt")
        self.history_tree.heading("status", text="Durum")
        self.history_tree.heading("response", text="Yanıt")
        
        history_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
    
    def update_time_options(self):
        """Zamanlama tipine göre zaman seçeneklerini güncelle"""
        # Mevcut widget'ları temizle
        for widget in self.time_options_frame.winfo_children():
            widget.destroy()
        
        schedule_type = self.schedule_type.get()
        
        if schedule_type == "daily":
            ttk.Label(self.time_options_frame, text="Saat:").pack(side="left")
            
            self.hour_var = tk.StringVar(value="08")
            hour_spin = ttk.Spinbox(self.time_options_frame, from_=0, to=23, 
                                   textvariable=self.hour_var, width=5, format="%02.0f")
            hour_spin.pack(side="left", padx=(5, 2))
            
            ttk.Label(self.time_options_frame, text=":").pack(side="left")
            
            self.minute_var = tk.StringVar(value="00")
            minute_spin = ttk.Spinbox(self.time_options_frame, from_=0, to=59,
                                     textvariable=self.minute_var, width=5, format="%02.0f")
            minute_spin.pack(side="left", padx=(2, 5))
            
        elif schedule_type == "weekly":
            ttk.Label(self.time_options_frame, text="Gün:").pack(side="left")
            
            self.day_var = tk.StringVar(value="monday")
            day_combo = ttk.Combobox(self.time_options_frame, textvariable=self.day_var,
                                    values=["monday", "tuesday", "wednesday", "thursday", 
                                           "friday", "saturday", "sunday"])
            day_combo.pack(side="left", padx=(5, 10))
            
            ttk.Label(self.time_options_frame, text="Saat:").pack(side="left")
            
            self.hour_var = tk.StringVar(value="08")
            hour_spin = ttk.Spinbox(self.time_options_frame, from_=0, to=23, 
                                   textvariable=self.hour_var, width=5, format="%02.0f")
            hour_spin.pack(side="left", padx=(5, 2))
            
            ttk.Label(self.time_options_frame, text=":").pack(side="left")
            
            self.minute_var = tk.StringVar(value="00")
            minute_spin = ttk.Spinbox(self.time_options_frame, from_=0, to=59,
                                     textvariable=self.minute_var, width=5, format="%02.0f")
            minute_spin.pack(side="left", padx=(2, 5))
            
        elif schedule_type == "once":
            ttk.Label(self.time_options_frame, text="Tarih:").pack(side="left")
            
            today = datetime.datetime.now()
            self.date_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))
            date_entry = ttk.Entry(self.time_options_frame, textvariable=self.date_var, width=12)
            date_entry.pack(side="left", padx=(5, 10))
            
            ttk.Label(self.time_options_frame, text="Saat:").pack(side="left")
            
            self.hour_var = tk.StringVar(value="08")
            hour_spin = ttk.Spinbox(self.time_options_frame, from_=0, to=23, 
                                   textvariable=self.hour_var, width=5, format="%02.0f")
            hour_spin.pack(side="left", padx=(5, 2))
            
            ttk.Label(self.time_options_frame, text=":").pack(side="left")
            
            self.minute_var = tk.StringVar(value="00")
            minute_spin = ttk.Spinbox(self.time_options_frame, from_=0, to=59,
                                     textvariable=self.minute_var, width=5, format="%02.0f")
            minute_spin.pack(side="left", padx=(2, 5))
            
        elif schedule_type == "hourly":
            ttk.Label(self.time_options_frame, text="Her").pack(side="left")
            
            self.interval_var = tk.StringVar(value="5")
            interval_spin = ttk.Spinbox(self.time_options_frame, from_=1, to=24,
                                       textvariable=self.interval_var, width=5)
            interval_spin.pack(side="left", padx=(5, 5))
            
            ttk.Label(self.time_options_frame, text="saatte bir").pack(side="left")
    
    def set_prompt_text(self, text):
        """Prompt text'ini ayarla"""
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, text)
    
    def add_schedule(self):
        """Yeni schedule ekle"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showerror("Hata", "Prompt metni boş olamaz!")
            return
        
        schedule_type = self.schedule_type.get()
        
        try:
            schedule_data = {
                'id': len(self.scheduled_prompts) + 1,
                'prompt': prompt,
                'type': schedule_type,
                'status': 'active',
                'created': datetime.datetime.now().isoformat(),
                'last_run': None,
                'next_run': None,
                'run_count': 0
            }
            
            # Zamanlama parametrelerini ekle
            if schedule_type == "daily":
                schedule_data['hour'] = int(self.hour_var.get())
                schedule_data['minute'] = int(self.minute_var.get())
                
            elif schedule_type == "weekly":
                schedule_data['day'] = self.day_var.get()
                schedule_data['hour'] = int(self.hour_var.get())
                schedule_data['minute'] = int(self.minute_var.get())
                
            elif schedule_type == "once":
                schedule_data['date'] = self.date_var.get()
                schedule_data['hour'] = int(self.hour_var.get())
                schedule_data['minute'] = int(self.minute_var.get())
                
            elif schedule_type == "hourly":
                schedule_data['interval'] = int(self.interval_var.get())
            
            self.scheduled_prompts.append(schedule_data)
            self.save_schedules()
            self.refresh_schedules()
            
            messagebox.showinfo("Başarılı", "Zamanlama başarıyla eklendi!")
            
            # Form'u temizle
            self.prompt_text.delete(1.0, tk.END)
            
        except ValueError as e:
            messagebox.showerror("Hata", f"Geçersiz zaman değeri: {e}")
        except Exception as e:
            messagebox.showerror("Hata", f"Zamanlama eklenirken hata: {e}")
    
    def preview_schedule(self):
        """Schedule önizlemesi göster"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        schedule_type = self.schedule_type.get()
        
        preview_text = f"Prompt: {prompt}\n"
        preview_text += f"Tip: {schedule_type}\n"
        
        try:
            if schedule_type == "daily":
                preview_text += f"Zaman: Her gün {self.hour_var.get()}:{self.minute_var.get()}\n"
            elif schedule_type == "weekly":
                preview_text += f"Zaman: Her {self.day_var.get()} {self.hour_var.get()}:{self.minute_var.get()}\n"
            elif schedule_type == "once":
                preview_text += f"Zaman: {self.date_var.get()} {self.hour_var.get()}:{self.minute_var.get()}\n"
            elif schedule_type == "hourly":
                preview_text += f"Zaman: Her {self.interval_var.get()} saatte bir\n"
            
            messagebox.showinfo("Zamanlama Önizlemesi", preview_text)
        except Exception as e:
            messagebox.showerror("Hata", f"Önizleme oluşturulamadı: {e}")
    
    def create_context_menu(self):
        """Sağ tık menüsü oluştur"""
        self.context_menu = tk.Menu(self.scheduler_window, tearoff=0)
        self.context_menu.add_command(label="Düzenle", command=self.edit_schedule)
        self.context_menu.add_command(label="Sil", command=self.delete_schedule)
        self.context_menu.add_command(label="Aktif/Pasif", command=self.toggle_schedule)
        self.context_menu.add_command(label="Şimdi Çalıştır", command=self.run_now)
    
    def show_context_menu(self, event):
        """Sağ tık menüsünü göster"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def send_prompt_to_claude(self, prompt):
        """Claude'a prompt gönder"""
        try:
            # Claude pencerelerini bul
            claude_windows = self.main_monitor.find_claude_windows()
            browser_tabs = self.main_monitor.find_browser_claude_tabs()
            
            if not claude_windows and not browser_tabs:
                self.main_monitor.add_alert('scheduler_error', 
                                          "Claude penceresi bulunamadı! Prompt gönderilemedi.")
                return False
            
            # İlk bulduğu Claude penceresini kullan
            target_window = claude_windows[0] if claude_windows else browser_tabs[0]
            hwnd = target_window.get('hwnd')
            
            if hwnd:
                # Pencereyi aktif yap
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.5)
                
                # Prompt'u gönder (şimdilik simule edelim)
                self.main_monitor.add_alert('scheduled_prompt_sent', 
                                          f"Zamanlanmış prompt gönderildi: {prompt[:50]}...")
                
                # Gerçek implementation için keyboard simulation eklenebilir
                return True
            
        except Exception as e:
            self.main_monitor.add_alert('scheduler_error', 
                                      f"Prompt gönderme hatası: {str(e)}")
            return False
        
        return False
    
    def execute_scheduled_prompt(self, schedule_data):
        """Zamanlanmış prompt'u çalıştır"""
        try:
            prompt = schedule_data['prompt']
            success = self.send_prompt_to_claude(prompt)
            
            # Çalışma kayıtlarını güncelle
            schedule_data['last_run'] = datetime.datetime.now().isoformat()
            schedule_data['run_count'] += 1
            
            if success:
                schedule_data['last_status'] = 'success'
            else:
                schedule_data['last_status'] = 'failed'
            
            # Tek seferlik schedule'ları deaktive et
            if schedule_data['type'] == 'once':
                schedule_data['status'] = 'completed'
            
            self.save_schedules()
            
            # Log kaydet
            self.log_scheduled_execution(schedule_data, success)
            
        except Exception as e:
            self.main_monitor.add_alert('scheduler_error', 
                                      f"Schedule çalıştırma hatası: {str(e)}")
    
    def log_scheduled_execution(self, schedule_data, success):
        """Zamanlanmış çalıştırma logunu kaydet"""
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'schedule_id': schedule_data['id'],
            'prompt': schedule_data['prompt'],
            'success': success,
            'type': schedule_data['type']
        }
        
        log_file = f"claude_session_data/scheduled_executions_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
    
    def run_scheduler(self):
        """Ana scheduler döngüsü"""
        while self.scheduler_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.main_monitor.add_alert('scheduler_error', 
                                          f"Scheduler döngü hatası: {str(e)}")
                time.sleep(10)
    
    def start_scheduler(self):
        """Scheduler'ı başlat"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.setup_schedules()
        
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.scheduler_status_var.set("Çalışıyor")
        self.main_monitor.add_alert('scheduler_started', "Zamanlanmış prompt sistemi başlatıldı")
    
    def stop_scheduler(self):
        """Scheduler'ı durdur"""
        self.scheduler_running = False
        schedule.clear()
        
        self.scheduler_status_var.set("Durduruldu")
        self.main_monitor.add_alert('scheduler_stopped', "Zamanlanmış prompt sistemi durduruldu")
    
    def setup_schedules(self):
        """Schedule'ları sistem schedule'ına ekle"""
        schedule.clear()
        
        for schedule_data in self.scheduled_prompts:
            if schedule_data['status'] != 'active':
                continue
            
            schedule_type = schedule_data['type']
            
            if schedule_type == "daily":
                time_str = f"{schedule_data['hour']:02d}:{schedule_data['minute']:02d}"
                schedule.every().day.at(time_str).do(self.execute_scheduled_prompt, schedule_data)
                
            elif schedule_type == "weekly":
                day = schedule_data['day']
                time_str = f"{schedule_data['hour']:02d}:{schedule_data['minute']:02d}"
                getattr(schedule.every(), day).at(time_str).do(self.execute_scheduled_prompt, schedule_data)
                
            elif schedule_type == "hourly":
                interval = schedule_data['interval']
                schedule.every(interval).hours.do(self.execute_scheduled_prompt, schedule_data)
                
            elif schedule_type == "once":
                # Tek seferlik schedule için özel kontrol gerekli
                target_date = datetime.datetime.fromisoformat(
                    f"{schedule_data['date']} {schedule_data['hour']:02d}:{schedule_data['minute']:02d}:00"
                )
                
                if target_date > datetime.datetime.now():
                    # Şimdilik daily olarak ekle, gelecekte daha sophisticated bir sistem yapılabilir
                    time_str = f"{schedule_data['hour']:02d}:{schedule_data['minute']:02d}"
                    schedule.every().day.at(time_str).do(self.execute_scheduled_prompt, schedule_data)
    
    def save_schedules(self):
        """Schedule'ları dosyaya kaydet"""
        try:
            os.makedirs(os.path.dirname(self.schedules_file), exist_ok=True)
            
            with open(self.schedules_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_prompts, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.main_monitor.add_alert('scheduler_error', 
                                      f"Schedule kaydetme hatası: {str(e)}")
    
    def load_schedules(self):
        """Schedule'ları dosyadan yükle"""
        try:
            if os.path.exists(self.schedules_file):
                with open(self.schedules_file, 'r', encoding='utf-8') as f:
                    self.scheduled_prompts = json.load(f)
        except Exception as e:
            self.scheduled_prompts = []
            self.main_monitor.add_alert('scheduler_error', 
                                      f"Schedule yükleme hatası: {str(e)}")
    
    def refresh_schedules(self):
        """Schedule listesini yenile"""
        if not hasattr(self, 'schedules_tree'):
            return
        
        # Mevcut öğeleri temizle
        for item in self.schedules_tree.get_children():
            self.schedules_tree.delete(item)
        
        # Schedule'ları ekle
        for schedule_data in self.scheduled_prompts:
            schedule_id = schedule_data['id']
            schedule_type = schedule_data['type']
            prompt_preview = schedule_data['prompt'][:30] + "..." if len(schedule_data['prompt']) > 30 else schedule_data['prompt']
            status = schedule_data['status']
            
            # Zaman bilgisi oluştur
            if schedule_type == "daily":
                time_info = f"Günlük {schedule_data['hour']:02d}:{schedule_data['minute']:02d}"
            elif schedule_type == "weekly":
                time_info = f"{schedule_data['day']} {schedule_data['hour']:02d}:{schedule_data['minute']:02d}"
            elif schedule_type == "once":
                time_info = f"{schedule_data['date']} {schedule_data['hour']:02d}:{schedule_data['minute']:02d}"
            elif schedule_type == "hourly":
                time_info = f"Her {schedule_data['interval']} saatte"
            else:
                time_info = "Bilinmiyor"
            
            next_run = schedule_data.get('next_run', 'Hesaplanıyor...')
            last_run = schedule_data.get('last_run', 'Henüz çalışmadı')
            if last_run != 'Henüz çalışmadı':
                try:
                    last_run_dt = datetime.datetime.fromisoformat(last_run)
                    last_run = last_run_dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            self.schedules_tree.insert('', 'end',
                                     text=str(schedule_id),
                                     values=(time_info, prompt_preview, status, next_run, last_run))
    
    def update_scheduler_dashboard(self):
        """Scheduler dashboard'unu güncelle"""
        if not self.scheduler_window or not self.scheduler_window.winfo_exists():
            return
        
        self.refresh_schedules()
        
        # 5 saniye sonra tekrar güncelle
        self.scheduler_window.after(5000, self.update_scheduler_dashboard)
    
    # Template metodları
    def create_morning_activation(self):
        """Sabah aktivasyon programı oluştur"""
        self.scheduled_prompts.append({
            'id': len(self.scheduled_prompts) + 1,
            'prompt': 'Günaydın! Yeni gün başlıyor.',
            'type': 'daily',
            'hour': 8,
            'minute': 0,
            'status': 'active',
            'created': datetime.datetime.now().isoformat(),
            'last_run': None,
            'run_count': 0
        })
        self.save_schedules()
        messagebox.showinfo("Başarılı", "Sabah aktivasyon programı eklendi!")
    
    def create_work_day_program(self):
        """İş günü programı oluştur"""
        work_schedules = [
            {'hour': 9, 'minute': 0, 'prompt': 'İş gününe başlıyoruz!'},
            {'hour': 12, 'minute': 0, 'prompt': 'Öğle arası kontrol'},
            {'hour': 15, 'minute': 0, 'prompt': 'Öğleden sonra kontrol'},
            {'hour': 18, 'minute': 0, 'prompt': 'İş günü sonu'}
        ]
        
        for schedule in work_schedules:
            self.scheduled_prompts.append({
                'id': len(self.scheduled_prompts) + 1,
                'prompt': schedule['prompt'],
                'type': 'daily',
                'hour': schedule['hour'],
                'minute': schedule['minute'],
                'status': 'active',
                'created': datetime.datetime.now().isoformat(),
                'last_run': None,
                'run_count': 0
            })
        
        self.save_schedules()
        messagebox.showinfo("Başarılı", "İş günü programı eklendi!")
    
    def create_night_program(self):
        """Gece programı oluştur"""
        self.scheduled_prompts.append({
            'id': len(self.scheduled_prompts) + 1,
            'prompt': 'İyi geceler! Gece modu aktif.',
            'type': 'daily',
            'hour': 23,
            'minute': 0,
            'status': 'active',
            'created': datetime.datetime.now().isoformat(),
            'last_run': None,
            'run_count': 0
        })
        self.save_schedules()
        messagebox.showinfo("Başarılı", "Gece programı eklendi!")
    
    def create_5hour_cycle(self):
        """5 saatlik döngü oluştur"""
        self.scheduled_prompts.append({
            'id': len(self.scheduled_prompts) + 1,
            'prompt': 'x',
            'type': 'hourly',
            'interval': 5,
            'status': 'active',
            'created': datetime.datetime.now().isoformat(),
            'last_run': None,
            'run_count': 0
        })
        self.save_schedules()
        messagebox.showinfo("Başarılı", "5 saatlik döngü eklendi!")
    
    # Placeholder metodlar (UI event'leri için)
    def edit_schedule(self): pass
    def delete_schedule(self): pass
    def toggle_schedule(self): pass
    def run_now(self): pass
    def filter_history(self): pass
    def clear_history(self): pass

if __name__ == "__main__":
    # Test için
    class MockMonitor:
        def add_alert(self, alert_type, message, session_id=None):
            print(f"Alert: {alert_type} - {message}")
        
        def find_claude_windows(self):
            return []
        
        def find_browser_claude_tabs(self):
            return []
    
    mock_monitor = MockMonitor()
    scheduler = ScheduledPromptSystem(mock_monitor)
    
    scheduler.show_scheduler_dashboard()
    
    # Ana loop
    root = tk.Tk()
    root.withdraw()
    root.mainloop()