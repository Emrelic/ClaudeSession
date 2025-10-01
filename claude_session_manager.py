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
from dataclasses import dataclass

@dataclass
class ScheduledCommand:
    time: str
    command: str
    description: str
    enabled: bool = True

class ClaudeSessionManager:
    def __init__(self):
        self.config_file = "config.json"
        self.session_file = "session_data.json"
        self.scheduled_commands_file = "scheduled_commands.json"
        self.usage_log_file = "usage_log.json"
        self.chat_history_file = "chat_history.json"
        self.config = self.load_config()
        self.session_data = self.load_session_data()
        self.scheduled_commands = self.load_scheduled_commands()
        self.usage_log = self.load_usage_log()
        self.chat_history = self.load_chat_history()
        self.is_running = False
        self.scheduler_thread = None
        self.current_session_id = None
        self.tokens_remaining = None
        self.session_end_time = None
        self.last_usage_check = None
        
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
    
    def load_scheduled_commands(self) -> list[ScheduledCommand]:
        if os.path.exists(self.scheduled_commands_file):
            try:
                with open(self.scheduled_commands_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [ScheduledCommand(**cmd) for cmd in data]
            except:
                return []
        return []
    
    def save_scheduled_commands(self):
        with open(self.scheduled_commands_file, 'w', encoding='utf-8') as f:
            data = [{
                'time': cmd.time,
                'command': cmd.command,
                'description': cmd.description,
                'enabled': cmd.enabled
            } for cmd in self.scheduled_commands]
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_usage_log(self) -> Dict[str, Any]:
        default_log = {
            "hourly_reports": [],
            "daily_summary": {},
            "last_check_time": None
        }
        
        if os.path.exists(self.usage_log_file):
            try:
                with open(self.usage_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_log
        return default_log
    
    def save_usage_log(self):
        with open(self.usage_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.usage_log, f, indent=2, ensure_ascii=False)
    
    def load_chat_history(self) -> list:
        if os.path.exists(self.chat_history_file):
            try:
                with open(self.chat_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_chat_history(self):
        with open(self.chat_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.chat_history, f, indent=2, ensure_ascii=False)
    
    def add_chat_entry(self, prompt: str, response: str, command_type: str = "manual"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "type": command_type,  # manual, scheduled, auto
            "success": True
        }
        
        self.chat_history.append(entry)
        
        # Son 1000 sohbet kaydı tut
        if len(self.chat_history) > 1000:
            self.chat_history = self.chat_history[-1000:]
        
        self.save_chat_history()
    
    def add_chat_error(self, prompt: str, error: str, command_type: str = "manual"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": f"HATA: {error}",
            "type": command_type,
            "success": False
        }
        
        self.chat_history.append(entry)
        
        if len(self.chat_history) > 1000:
            self.chat_history = self.chat_history[-1000:]
        
        self.save_chat_history()
    
    def send_claude_prompt(self, prompt: str = None) -> tuple[bool, str]:
        if prompt is None:
            prompt = self.config["auto_prompt"]
        
        try:
            if prompt.startswith("/"):
                return self.handle_special_command(prompt)
            
            cmd = [self.config["claude_executable"], "--print", prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.session_data["last_session_start"] = datetime.now().isoformat()
                self.session_data["session_count"] += 1
                self.calculate_next_session_time()
                self.save_session_data()
                
                # Sohbet geçmişine ekle
                self.add_chat_entry(prompt, result.stdout, "auto")
                
                return True, result.stdout
            else:
                # Hata durumunu da kaydet
                self.add_chat_error(prompt, result.stderr, "auto")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Claude komutu zaman aşımına uğradı"
        except Exception as e:
            return False, f"Hata: {str(e)}"
    
    def handle_special_command(self, command: str) -> tuple[bool, str]:
        command = command.lower().strip()
        
        if command == "/status":
            return self.get_claude_status()
        elif command == "/usage":
            return self.get_claude_usage()
        elif command == "/cost":
            return self.get_claude_cost()
        else:
            return False, f"Bilinmeyen komut: {command}"
    
    def get_claude_status(self) -> tuple[bool, str]:
        try:
            cmd = [self.config["claude_executable"], "--help"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            status_info = {
                "claude_available": result.returncode == 0,
                "last_check": datetime.now().isoformat(),
                "session_count": self.session_data.get("session_count", 0),
                "auto_session_running": self.is_running
            }
            
            return True, json.dumps(status_info, indent=2, ensure_ascii=False)
        except Exception as e:
            return False, f"Status kontrolü başarısız: {str(e)}"
    
    def get_claude_usage(self) -> tuple[bool, str]:
        try:
            now = datetime.now()
            if self.last_usage_check is None or (now - self.last_usage_check).total_seconds() > 300:
                self.check_and_log_usage()
                self.last_usage_check = now
            
            recent_reports = self.usage_log["hourly_reports"][-24:] if self.usage_log["hourly_reports"] else []
            
            usage_info = {
                "last_24_hours": recent_reports,
                "total_sessions_today": sum(1 for r in recent_reports if r.get("date") == now.strftime("%Y-%m-%d")),
                "last_update": self.usage_log.get("last_check_time")
            }
            
            return True, json.dumps(usage_info, indent=2, ensure_ascii=False)
        except Exception as e:
            return False, f"Usage bilgisi alınamadı: {str(e)}"
    
    def get_claude_cost(self) -> tuple[bool, str]:
        try:
            cost_info = {
                "estimated_cost": "Maliyet bilgisi API'den alınamıyor",
                "session_count": self.session_data.get("session_count", 0),
                "last_session": self.session_data.get("last_session_start"),
                "note": "Gerçek maliyet bilgisi için Claude hesabınızı kontrol edin"
            }
            
            return True, json.dumps(cost_info, indent=2, ensure_ascii=False)
        except Exception as e:
            return False, f"Cost bilgisi alınamadı: {str(e)}"
    
    def check_and_log_usage(self):
        now = datetime.now()
        report = {
            "timestamp": now.isoformat(),
            "hour": now.hour,
            "date": now.strftime("%Y-%m-%d"),
            "session_count": self.session_data.get("session_count", 0),
            "auto_session_active": self.is_running
        }
        
        self.usage_log["hourly_reports"].append(report)
        self.usage_log["last_check_time"] = now.isoformat()
        
        if len(self.usage_log["hourly_reports"]) > 168:
            self.usage_log["hourly_reports"] = self.usage_log["hourly_reports"][-168:]
        
        self.save_usage_log()
    
    def add_scheduled_command(self, time_str: str, command: str, description: str = ""):
        try:
            datetime.strptime(time_str, "%H:%M")
            new_cmd = ScheduledCommand(time_str, command, description)
            self.scheduled_commands.append(new_cmd)
            self.save_scheduled_commands()
            return True, "Zamanlı komut eklendi"
        except ValueError:
            return False, "Geçersiz saat formatı (HH:MM kullanın)"
    
    def remove_scheduled_command(self, index: int):
        try:
            if 0 <= index < len(self.scheduled_commands):
                removed = self.scheduled_commands.pop(index)
                self.save_scheduled_commands()
                return True, f"Komut silindi: {removed.description}"
            else:
                return False, "Geçersiz komut index'i"
        except Exception as e:
            return False, f"Komut silinemedi: {str(e)}"
    
    def toggle_scheduled_command(self, index: int):
        try:
            if 0 <= index < len(self.scheduled_commands):
                self.scheduled_commands[index].enabled = not self.scheduled_commands[index].enabled
                self.save_scheduled_commands()
                status = "etkin" if self.scheduled_commands[index].enabled else "pasif"
                return True, f"Komut {status} edildi"
            else:
                return False, "Geçersiz komut index'i"
        except Exception as e:
            return False, f"Komut durumu değiştirilemedi: {str(e)}"
    
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
    
    def scheduled_command_job(self, command: str):
        try:
            success, response = self.send_claude_prompt(command)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if success:
                print(f"[{timestamp}] Zamanlı komut çalıştırıldı: {command}")
                # Yanıtı da logla
                response_preview = response[:200] + "..." if len(response) > 200 else response
                print(f"[{timestamp}] Claude yanıtı: {response_preview}")
                
                # Sohbet geçmişine kaydet
                self.add_chat_entry(command, response, "scheduled")
            else:
                print(f"[{timestamp}] Zamanlı komut hatası: {response}")
                self.add_chat_error(command, response, "scheduled")
        except Exception as e:
            error_msg = str(e)
            print(f"Zamanlı komut çalıştırma hatası: {error_msg}")
            self.add_chat_error(command, error_msg, "scheduled")
    
    def hourly_usage_report(self):
        try:
            self.check_and_log_usage()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saatlik kullanım raporu oluşturuldu")
        except Exception as e:
            print(f"Saatlik rapor hatası: {str(e)}")
    
    def start_scheduler(self):
        if self.is_running:
            return
        
        self.is_running = True
        schedule.clear()
        
        next_session = self.session_data.get("next_session_time")
        if next_session:
            next_time = datetime.fromisoformat(next_session)
            schedule.every().day.at(next_time.strftime("%H:%M")).do(self.auto_session_job)
        
        for cmd in self.scheduled_commands:
            if cmd.enabled:
                schedule.every().day.at(cmd.time).do(self.scheduled_command_job, cmd.command)
        
        schedule.every().hour.do(self.hourly_usage_report)
        
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
        success, response = self.send_claude_prompt(custom_prompt)
        
        # Manuel sohbeti kaydet
        if success:
            prompt = custom_prompt or self.config["auto_prompt"]
            self.add_chat_entry(prompt, response, "manual")
        else:
            prompt = custom_prompt or self.config["auto_prompt"]
            self.add_chat_error(prompt, response, "manual")
        
        return success, response

class ClaudeSessionGUI:
    def __init__(self):
        self.manager = ClaudeSessionManager()
        self.root = tk.Tk()
        self.root.title("Claude Session Manager")
        self.root.geometry("700x600")
        self.setup_ui()
        self.update_status()
        self.update_clock()
        
        # Scheduler'ı otomatik başlat
        if not self.manager.is_running:
            self.manager.start_scheduler()
            self.log_message("Scheduler otomatik başlatıldı")
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="Claude Session Manager", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, sticky=tk.W)
        
        self.clock_label = ttk.Label(header_frame, text="", 
                                    font=("Arial", 14, "bold"), foreground="blue")
        self.clock_label.grid(row=0, column=1, sticky=tk.E)
        
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
        
        ttk.Label(main_frame, text="Token Kalan:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.tokens_label = ttk.Label(main_frame, text="-")
        self.tokens_label.grid(row=6, column=1, sticky=tk.W, pady=2)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=7, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(buttons_frame, text="Otomatik Başlat", 
                                      command=self.toggle_auto_session)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Manuel Session", 
                  command=self.manual_session).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Ayarlar", 
                  command=self.show_settings).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Durum Yenile", 
                  command=self.update_status).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Zamanlı Komutlar", 
                  command=self.show_scheduled_commands).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Kullanım Raporu", 
                  command=self.show_usage_report).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Sohbet Geçmişi", 
                  command=self.show_chat_history).pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, width=50)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        main_frame.rowconfigure(8, weight=1)
        
        self.root.after(5000, self.auto_update_status)
        self.root.after(1000, self.update_clock)
    
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
        self.tokens_label.config(text=str(status.get("tokens_remaining", "-")))
    
    def auto_update_status(self):
        self.update_status()
        self.root.after(5000, self.auto_update_status)
    
    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)
    
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
                                       "Göndermek istediğiniz prompt (boş bırakırsanız varsayılan kullanılır):\n\nÖzel komutlar: /status, /usage, /cost")
        if prompt is not None:
            success, response = self.manager.manual_session_start(prompt if prompt.strip() else None)
            if success:
                self.log_message(f"Manuel session başarılı: {prompt or self.manager.config['auto_prompt']}")
                if prompt and prompt.startswith("/"):
                    messagebox.showinfo("Komut Sonuçu", response)
                else:
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
    
    def show_scheduled_commands(self):
        commands_window = tk.Toplevel(self.root)
        commands_window.title("Zamanlı Komutlar")
        commands_window.geometry("600x400")
        commands_window.transient(self.root)
        commands_window.grab_set()
        
        frame = ttk.Frame(commands_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Zamanlı Komutlar", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("Saat", "Komut", "Açıklama", "Durum")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_list():
            for item in tree.get_children():
                tree.delete(item)
            
            for i, cmd in enumerate(self.manager.scheduled_commands):
                status = "Etkin" if cmd.enabled else "Pasif"
                tree.insert("", "end", values=(cmd.time, cmd.command[:30], cmd.description[:30], status))
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        def add_command():
            add_window = tk.Toplevel(commands_window)
            add_window.title("Komut Ekle")
            add_window.geometry("400x200")
            add_window.transient(commands_window)
            
            add_frame = ttk.Frame(add_window, padding="10")
            add_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(add_frame, text="Saat (HH:MM):").grid(row=0, column=0, sticky=tk.W, pady=5)
            time_var = tk.StringVar()
            ttk.Entry(add_frame, textvariable=time_var, width=20).grid(row=0, column=1, pady=5)
            
            ttk.Label(add_frame, text="Komut:").grid(row=1, column=0, sticky=tk.W, pady=5)
            command_var = tk.StringVar()
            ttk.Entry(add_frame, textvariable=command_var, width=30).grid(row=1, column=1, pady=5)
            
            ttk.Label(add_frame, text="Açıklama:").grid(row=2, column=0, sticky=tk.W, pady=5)
            desc_var = tk.StringVar()
            ttk.Entry(add_frame, textvariable=desc_var, width=30).grid(row=2, column=1, pady=5)
            
            def save_command():
                success, message = self.manager.add_scheduled_command(
                    time_var.get(), command_var.get(), desc_var.get()
                )
                if success:
                    refresh_list()
                    self.log_message(message)
                    add_window.destroy()
                else:
                    messagebox.showerror("Hata", message)
            
            ttk.Button(add_frame, text="Ekle", command=save_command).grid(row=3, column=0, pady=20)
            ttk.Button(add_frame, text="İptal", command=add_window.destroy).grid(row=3, column=1, pady=20)
        
        def remove_command():
            selection = tree.selection()
            if selection:
                index = tree.index(selection[0])
                success, message = self.manager.remove_scheduled_command(index)
                if success:
                    refresh_list()
                    self.log_message(message)
                else:
                    messagebox.showerror("Hata", message)
        
        def toggle_command():
            selection = tree.selection()
            if selection:
                index = tree.index(selection[0])
                success, message = self.manager.toggle_scheduled_command(index)
                if success:
                    refresh_list()
                    self.log_message(message)
                else:
                    messagebox.showerror("Hata", message)
        
        ttk.Button(button_frame, text="Ekle", command=add_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sil", command=remove_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Etkin/Pasif", command=toggle_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Yenile", command=refresh_list).pack(side=tk.LEFT, padx=5)
        
        refresh_list()
    
    def show_usage_report(self):
        report_window = tk.Toplevel(self.root)
        report_window.title("Kullanım Raporu")
        report_window.geometry("500x400")
        report_window.transient(self.root)
        report_window.grab_set()
        
        frame = ttk.Frame(report_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Claude Kullanım Raporu", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        report_text = tk.Text(frame, height=20, width=60)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=report_text.yview)
        report_text.configure(yscrollcommand=scrollbar.set)
        
        report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_report():
            report_text.delete(1.0, tk.END)
            
            success, usage_data = self.manager.get_claude_usage()
            if success:
                try:
                    usage_info = json.loads(usage_data)
                    report_text.insert(tk.END, "=== CLAUDE KULLANIM RAPORU ===\n\n")
                    report_text.insert(tk.END, f"Son Güncelleme: {usage_info.get('last_update', 'Bilinmiyor')}\n")
                    report_text.insert(tk.END, f"Bugünkü Session Sayısı: {usage_info.get('total_sessions_today', 0)}\n\n")
                    
                    report_text.insert(tk.END, "=== SON 24 SAAT ===\n")
                    recent_reports = usage_info.get('last_24_hours', [])
                    
                    if recent_reports:
                        for report in recent_reports[-10:]:
                            timestamp = report.get('timestamp', 'Bilinmiyor')
                            session_count = report.get('session_count', 0)
                            active = "Evet" if report.get('auto_session_active', False) else "Hayır"
                            report_text.insert(tk.END, f"{timestamp}: {session_count} session, Otomatik: {active}\n")
                    else:
                        report_text.insert(tk.END, "Henüz veri yok\n")
                        
                except json.JSONDecodeError:
                    report_text.insert(tk.END, f"Veri parse hatası: {usage_data}")
            else:
                report_text.insert(tk.END, f"Rapor alınamadı: {usage_data}")
        
        ttk.Button(frame, text="Yenile", command=refresh_report).pack(pady=10)
        refresh_report()
    
    def show_chat_history(self):
        chat_window = tk.Toplevel(self.root)
        chat_window.title("Claude Sohbet Geçmişi")
        chat_window.geometry("800x600")
        chat_window.transient(self.root)
        chat_window.grab_set()
        
        frame = ttk.Frame(chat_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Claude Sohbet Geçmişi", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Arama çubuğu
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Arama:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Sohbet listesi frame
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Sohbet metni için Text widget
        chat_text = tk.Text(list_frame, height=25, width=80, wrap=tk.WORD, font=("Consolas", 9))
        chat_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=chat_text.yview)
        chat_text.configure(yscrollcommand=chat_scrollbar.set)
        
        chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Renk etiketleri
        chat_text.tag_configure("timestamp", foreground="gray")
        chat_text.tag_configure("prompt", foreground="blue", font=("Consolas", 9, "bold"))
        chat_text.tag_configure("response", foreground="green")
        chat_text.tag_configure("error", foreground="red")
        chat_text.tag_configure("type_manual", background="#e6f3ff")
        chat_text.tag_configure("type_scheduled", background="#fff2e6")
        chat_text.tag_configure("type_auto", background="#f0f8f0")
        
        def refresh_chat():
            chat_text.delete(1.0, tk.END)
            
            # Sohbet geçmişini yükle
            history = self.manager.chat_history
            search_term = search_var.get().lower()
            
            if not history:
                chat_text.insert(tk.END, "Henüz sohbet kaydı bulunmuyor.\n\n")
                chat_text.insert(tk.END, "Sohbet kayıtları şunları içerir:\n")
                chat_text.insert(tk.END, "- Manuel session'lar\n")
                chat_text.insert(tk.END, "- Zamanlı komutlar\n")
                chat_text.insert(tk.END, "- Otomatik session'lar\n")
                return
            
            # Son kayıtları göster (en yeni üstte)
            for entry in reversed(history[-100:]):
                # Arama filtresi
                if search_term and search_term not in entry.get('prompt', '').lower() and search_term not in entry.get('response', '').lower():
                    continue
                
                timestamp = entry.get('timestamp', '')
                prompt = entry.get('prompt', '')
                response = entry.get('response', '')
                cmd_type = entry.get('type', 'manual')
                success = entry.get('success', True)
                
                # Zaman damgası
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = timestamp
                
                # Komut tipi işareti
                type_indicator = {
                    'manual': '[MANUEL]',
                    'scheduled': '[ZAMANLI]', 
                    'auto': '[OTOMATIK]'
                }.get(cmd_type, '[BELİRSİZ]')
                
                # Header
                chat_text.insert(tk.END, f"{'='*80}\n")
                chat_text.insert(tk.END, f"{time_str} {type_indicator}\n", "timestamp")
                
                # Prompt
                chat_text.insert(tk.END, f"\n➜ PROMPT: {prompt}\n", "prompt")
                
                # Response
                if success:
                    chat_text.insert(tk.END, f"\n✓ CLAUDE: {response}\n\n", "response")
                else:
                    chat_text.insert(tk.END, f"\n✗ HATA: {response}\n\n", "error")
            
            # En üste scroll et
            chat_text.see(1.0)
        
        def search_chat(*args):
            refresh_chat()
        
        search_var.trace('w', search_chat)
        
        # Butonlar
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Yenile", command=refresh_chat).pack(side=tk.LEFT, padx=5)
        
        def clear_history():
            if messagebox.askyesno("Onay", "Tüm sohbet geçmişini silmek istediğinizden emin misiniz?"):
                self.manager.chat_history = []
                self.manager.save_chat_history()
                refresh_chat()
                self.log_message("Sohbet geçmişi temizlendi")
        
        ttk.Button(button_frame, text="Geçmişi Temizle", command=clear_history).pack(side=tk.LEFT, padx=5)
        
        def export_history():
            try:
                export_file = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(export_file, 'w', encoding='utf-8') as f:
                    f.write("Claude Session Manager - Sohbet Geçmişi\n")
                    f.write(f"Export Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*80 + "\n\n")
                    
                    for entry in self.manager.chat_history:
                        timestamp = entry.get('timestamp', '')
                        prompt = entry.get('prompt', '')
                        response = entry.get('response', '')
                        cmd_type = entry.get('type', 'manual')
                        success = entry.get('success', True)
                        
                        f.write(f"Zaman: {timestamp}\n")
                        f.write(f"Tip: {cmd_type.upper()}\n")
                        f.write(f"Prompt: {prompt}\n")
                        f.write(f"Yanıt: {response}\n")
                        f.write(f"Başarılı: {success}\n")
                        f.write("-"*80 + "\n\n")
                
                messagebox.showinfo("Başarılı", f"Sohbet geçmişi {export_file} dosyasına aktarıldı")
                self.log_message(f"Sohbet geçmişi {export_file} dosyasına aktarıldı")
            except Exception as e:
                messagebox.showerror("Hata", f"Export hatası: {str(e)}")
        
        ttk.Button(button_frame, text="Export Et", command=export_history).pack(side=tk.LEFT, padx=5)
        
        # İlk yükleme
        refresh_chat()
    
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