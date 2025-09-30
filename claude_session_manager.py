#!/usr/bin/env python3
import subprocess
import threading
import time
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import schedule

class ClaudeSessionManager:
    def __init__(self):
        self.config_file = "config.json"
        self.session_file = "session_data.json"
        self.config = self.load_config()
        self.session_data = self.load_session_data()
        self.is_running = False
        self.scheduler_thread = None
        self.current_session_id = None
        self.tokens_remaining = None
        self.session_end_time = None
        
    def load_config(self) -> Dict[str, Any]:
        default_config = {
            "auto_prompt": "x",
            "session_interval_hours": 5,
            "enable_auto_session": True,
            "start_time": "08:00",
            "claude_executable": "claude"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        self.config = config
    
    def load_session_data(self) -> Dict[str, Any]:
        default_data = {
            "last_session_start": None,
            "next_session_time": None,
            "session_count": 0
        }
        
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_data
        return default_data
    
    def save_session_data(self):
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
    
    def send_claude_prompt(self, prompt: str = None) -> tuple[bool, str]:
        if prompt is None:
            prompt = self.config["auto_prompt"]
        
        try:
            cmd = [self.config["claude_executable"], "--print", prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.session_data["last_session_start"] = datetime.now().isoformat()
                self.session_data["session_count"] += 1
                self.calculate_next_session_time()
                self.save_session_data()
                return True, result.stdout
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Claude komutu zaman aşımına uğradı"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def calculate_next_session_time(self):
        if self.session_data["last_session_start"]:
            last_start = datetime.fromisoformat(self.session_data["last_session_start"])
            next_time = last_start + timedelta(hours=self.config["session_interval_hours"])
            self.session_data["next_session_time"] = next_time.isoformat()
        else:
            now = datetime.now()
            start_time = datetime.strptime(self.config["start_time"], "%H:%M").time()
            next_time = datetime.combine(now.date(), start_time)
            
            if next_time <= now:
                next_time += timedelta(days=1)
            
            self.session_data["next_session_time"] = next_time.isoformat()
    
    def get_session_status(self) -> Dict[str, Any]:
        status = {
            "is_running": self.is_running,
            "last_session": self.session_data.get("last_session_start"),
            "next_session": self.session_data.get("next_session_time"),
            "session_count": self.session_data.get("session_count", 0),
            "tokens_remaining": self.tokens_remaining,
            "session_end_time": self.session_end_time
        }
        
        if status["next_session"]:
            next_time = datetime.fromisoformat(status["next_session"])
            now = datetime.now()
            if next_time > now:
                time_diff = next_time - now
                hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                status["time_until_next"] = f"{hours}s {minutes}d"
            else:
                status["time_until_next"] = "Zamanı geldi"
        
        return status
    
    def auto_session_job(self):
        if not self.config["enable_auto_session"]:
            return
        
        success, response = self.send_claude_prompt()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if success:
            print(f"[{timestamp}] Otomatik session başlatıldı")
        else:
            print(f"[{timestamp}] Otomatik session hatası: {response}")
    
    def start_scheduler(self):
        if self.is_running:
            return
        
        self.is_running = True
        schedule.clear()
        
        next_session = self.session_data.get("next_session_time")
        if next_session:
            next_time = datetime.fromisoformat(next_session)
            schedule.every().day.at(next_time.strftime("%H:%M")).do(self.auto_session_job)
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        self.is_running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1)
    
    def manual_session_start(self, custom_prompt: str = None):
        return self.send_claude_prompt(custom_prompt)

class ClaudeSessionGUI:
    def __init__(self):
        self.manager = ClaudeSessionManager()
        self.root = tk.Tk()
        self.root.title("Claude Session Manager")
        self.root.geometry("600x500")
        self.setup_ui()
        self.update_status()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        ttk.Label(main_frame, text="Claude Session Manager", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        ttk.Label(main_frame, text="Durum:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.status_label = ttk.Label(main_frame, text="Durumu kontrol ediliyor...")
        self.status_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Son Session:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.last_session_label = ttk.Label(main_frame, text="-")
        self.last_session_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Sonraki Session:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.next_session_label = ttk.Label(main_frame, text="-")
        self.next_session_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Kalan Süre:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.time_remaining_label = ttk.Label(main_frame, text="-")
        self.time_remaining_label.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Session Sayısı:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.session_count_label = ttk.Label(main_frame, text="0")
        self.session_count_label.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(buttons_frame, text="Otomatik Başlat", 
                                      command=self.toggle_auto_session)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Manuel Session", 
                  command=self.manual_session).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Ayarlar", 
                  command=self.show_settings).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Durum Yenile", 
                  command=self.update_status).pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, width=50)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        main_frame.rowconfigure(7, weight=1)
        
        self.root.after(5000, self.auto_update_status)
    
    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_status(self):
        status = self.manager.get_session_status()
        
        if status["is_running"]:
            self.status_label.config(text="Aktif", foreground="green")
            self.start_button.config(text="Durdur")
        else:
            self.status_label.config(text="Pasif", foreground="red")
            self.start_button.config(text="Otomatik Başlat")
        
        if status["last_session"]:
            last_time = datetime.fromisoformat(status["last_session"])
            self.last_session_label.config(text=last_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.last_session_label.config(text="Henüz başlatılmadı")
        
        if status["next_session"]:
            next_time = datetime.fromisoformat(status["next_session"])
            self.next_session_label.config(text=next_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.next_session_label.config(text="Planlanmadı")
        
        self.time_remaining_label.config(text=status.get("time_until_next", "-"))
        self.session_count_label.config(text=str(status["session_count"]))
    
    def auto_update_status(self):
        self.update_status()
        self.root.after(5000, self.auto_update_status)
    
    def toggle_auto_session(self):
        if self.manager.is_running:
            self.manager.stop_scheduler()
            self.log_message("Otomatik session durduruldu")
        else:
            self.manager.start_scheduler()
            self.log_message("Otomatik session başlatıldı")
        self.update_status()
    
    def manual_session(self):
        prompt = simpledialog.askstring("Manuel Session", 
                                       "Göndermek istediğiniz prompt (boş bırakırsanız varsayılan kullanılır):")
        if prompt is not None:
            success, response = self.manager.manual_session_start(prompt if prompt.strip() else None)
            if success:
                self.log_message(f"Manuel session başarılı: {prompt or self.manager.config['auto_prompt']}")
                messagebox.showinfo("Başarılı", "Session başarıyla başlatıldı!")
            else:
                self.log_message(f"Manuel session hatası: {response}")
                messagebox.showerror("Hata", f"Session başlatılamadı: {response}")
            self.update_status()
    
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Ayarlar")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        frame = ttk.Frame(settings_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Otomatik Prompt:").grid(row=0, column=0, sticky=tk.W, pady=5)
        auto_prompt_var = tk.StringVar(value=self.manager.config["auto_prompt"])
        ttk.Entry(frame, textvariable=auto_prompt_var, width=30).grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Session Aralığı (saat):").grid(row=1, column=0, sticky=tk.W, pady=5)
        interval_var = tk.StringVar(value=str(self.manager.config["session_interval_hours"]))
        ttk.Entry(frame, textvariable=interval_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Başlangıç Saati (HH:MM):").grid(row=2, column=0, sticky=tk.W, pady=5)
        start_time_var = tk.StringVar(value=self.manager.config["start_time"])
        ttk.Entry(frame, textvariable=start_time_var, width=30).grid(row=2, column=1, pady=5)
        
        auto_enable_var = tk.BooleanVar(value=self.manager.config["enable_auto_session"])
        ttk.Checkbutton(frame, text="Otomatik session etkin", 
                       variable=auto_enable_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        def save_settings():
            try:
                new_config = self.manager.config.copy()
                new_config["auto_prompt"] = auto_prompt_var.get()
                new_config["session_interval_hours"] = int(interval_var.get())
                new_config["start_time"] = start_time_var.get()
                new_config["enable_auto_session"] = auto_enable_var.get()
                
                datetime.strptime(start_time_var.get(), "%H:%M")
                
                self.manager.save_config(new_config)
                self.log_message("Ayarlar kaydedildi")
                settings_window.destroy()
                
                if self.manager.is_running:
                    self.manager.stop_scheduler()
                    self.manager.start_scheduler()
                    
            except ValueError as e:
                messagebox.showerror("Hata", "Geçersiz değer girdiniz!")
        
        ttk.Button(frame, text="Kaydet", command=save_settings).grid(row=4, column=0, pady=20)
        ttk.Button(frame, text="İptal", command=settings_window.destroy).grid(row=4, column=1, pady=20)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.manager.is_running:
            self.manager.stop_scheduler()
        self.root.destroy()

if __name__ == "__main__":
    app = ClaudeSessionGUI()
    app.run()