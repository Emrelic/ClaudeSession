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
import tempfile

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
            "claude_executable": "claude",
            "auto_response_enabled": True,
            "default_choice": "1",
            "auto_execute_code": True,
            "allowed_languages": ["python", "bash", "cmd", "powershell"],
            "work_protocols": """● 🔧 ÇALIŞMA PROTOKOLLERI

📝 NOT DEFTERLERİ PROTOKOLÜ

- "ntk" komutu: Tüm .md uzantılı not defterlerini okur
- Dosyalar: CLAUDE.md + diğer tüm .md dosyaları projeye dahil
- "Not defterleri" = .md dosyaları: Markdown uzantılı tüm dokümanlar

📋 YAPILACAKLAR NOT DEFTERİ

- "ynd" komutu: Yeni madde ekle (Yapılacaklar Not Defteri)
- Dosya: YAPILACAKLAR.md
- Format: [Kullanıcı madde] + ynd → otomatik kayıt
- Otomatik tarih: Her maddeye tarih damgası eklenir

📝 PROMPT GÜNLÜĞÜ SİSTEMİ

ZORUNLU KURAL: Her kullanıcı promptu PROMPT_GUNLUGU.md dosyasına otomatik kaydedilmeli. Manuel "promptu ekle"
talebi beklemeden, her prompt otomatik olarak günlüğe işlenmelidir.
- Dosya: PROMPT_GUNLUGU.md
- Format: [Tarih-Saat] Prompt İçeriği
- Otomatik: Kullanıcı talebi olmadan tüm promptlar kaydedilir
- Kronolojik: En yeni promptlar en üstte

🔄 BERABER ÇALIŞMA PROTOKOLÜ

1. 🔧 Otomatik Build & Deploy:
  - Her yenilik → APK build → telefona yükleme
  - Kullanıcı sorgulamaz, otomatik yapılır
2. 🔊 SİSTEM BEEP PROTOKOLÜ:
  - Temel kurallar:
      - Soru sorulacağı zaman → 3x beep
    - Onay alınacağı zaman → 3x beep
    - Sonuç sunulacağı zaman → 3x beep
    - Etkileşim gerekince → 3x beep
    - Görev bitirip sunacağı zaman → 3x beep
    - 1,2,3 tuş seçenekleri sunacağı zaman → 3x beep
  - Ses Formatı:
powershell -c "[Console]::Beep(800,300); [Console]::Beep(800,300); [Console]::Beep(800,300)"
3. 💾 Hızlı Commit Protokolü:
  - "tmm" diyince → anında commit + push
  - "[özellik adı] tamam" diyince → commit + push

🔥 YILDIZLI KOMUT SİSTEMİ (*)

- *"p" = Bu prompt'u günlüğe ekle
- *"btş" = Beep protokolü uyguladığın için teşekkür
- *"btk" = Beep protokolünü uygulamadığın için tenkid
- *"tmm" = Bu özellik tamam, commit + push yap
- *"ab" = APK build et
- *"bty" = Build et telefona yükle
- *"ty" = Telefona yükle (APK install)
- *"mo" = md uzantılı not defterlerini oku

📋 HER AÇILIŞTA YAPILACAKLAR:

1. CLAUDE.md dosyasını oku ve projeyi anla
2. Önceki konuşmaları ve gelişmeleri kontrol et
3. Güncel proje durumunu değerlendir
4. Sistem sesi protokolü: Görev tamamlandığında 3 kere beep sesi çıkar
5. Otomatik onay protokolü: Kullanıcıdan onay almadan işlemlere devam et"""
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
    
    def analyze_claude_response(self, response: str) -> Dict[str, Any]:
        """Claude yanıtını analiz eder ve otomatik aksiyonlar önerir"""
        analysis = {
            "has_choices": False,
            "choices": [],
            "has_code": False,
            "code_blocks": [],
            "needs_response": False,
            "suggested_action": None
        }
        
        # Seçenek kontrolü (1, 2, 3 / yes, no vb.)
        choice_patterns = [
            r'(?:^|\n)\s*([1-3])[.)]\s*(.+?)(?=\n|$)',
            r'(?:^|\n)\s*(yes|no|y|n)\s*[:-]?\s*(.+?)(?=\n|$)',
            r'(?:^|\n)\s*([abc])[.)]\s*(.+?)(?=\n|$)'
        ]
        
        for pattern in choice_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            if len(matches) >= 2:
                analysis["has_choices"] = True
                analysis["choices"] = [(match[0], match[1].strip()) for match in matches]
                analysis["needs_response"] = True
                analysis["suggested_action"] = self.config.get("default_choice", "1")
                break
        
        # Kod bloğu kontrolü
        code_patterns = [
            r'```(\w+)?\n(.*?)\n```',
            r'`([^`\n]+)`',
            r'(?:^|\n)\s*(\$|>)\s*(.+?)(?=\n|$)'
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.MULTILINE)
            if matches:
                for match in matches:
                    if len(match) == 2:
                        lang = match[0] if match[0] else "unknown"
                        code = match[1].strip()
                        if len(code) > 3:  # Çok kısa kod bloklarını görmezden gel
                            analysis["has_code"] = True
                            analysis["code_blocks"].append({
                                "language": lang,
                                "code": code
                            })
        
        return analysis
    
    def auto_respond_to_claude(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Otomatik Claude yanıtı oluşturur"""
        if not self.config.get("auto_response_enabled", False):
            return None
        
        if analysis["has_choices"] and analysis["needs_response"]:
            return analysis["suggested_action"]
        
        return None
    
    def execute_code_from_response(self, code_blocks: list) -> str:
        """Claude yanıtındaki kod bloklarını çalıştırır"""
        if not self.config.get("auto_execute_code", False):
            return "Otomatik kod çalıştırma devre dışı"
        
        results = []
        allowed_langs = self.config.get("allowed_languages", [])
        
        for block in code_blocks:
            lang = block["language"].lower()
            code = block["code"]
            
            if lang not in allowed_langs:
                results.append(f"❌ {lang} dili otomatik çalıştırma için izinli değil")
                continue
            
            try:
                if lang in ["python", "py"]:
                    result = self.execute_python_code(code)
                elif lang in ["bash", "sh"]:
                    result = self.execute_bash_code(code)
                elif lang in ["cmd", "bat"]:
                    result = self.execute_cmd_code(code)
                elif lang in ["powershell", "ps1"]:
                    result = self.execute_powershell_code(code)
                else:
                    result = f"❓ {lang} dili için executor bulunamadı"
                
                results.append(f"✅ {lang}: {result}")
            except Exception as e:
                results.append(f"❌ {lang} hatası: {str(e)}")
        
        return "\n".join(results) if results else "Çalıştırılabilir kod bulunamadı"
    
    def execute_python_code(self, code: str) -> str:
        """Python kodunu güvenli şekilde çalıştırır"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return result.stdout or "Kod başarıyla çalıştırıldı"
            else:
                return f"Hata: {result.stderr}"
                
        except Exception as e:
            return f"Python execution hatası: {str(e)}"
    
    def execute_bash_code(self, code: str) -> str:
        """Bash kodunu çalıştırır"""
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout or "Komut başarıyla çalıştırıldı"
            else:
                return f"Hata: {result.stderr}"
                
        except Exception as e:
            return f"Bash execution hatası: {str(e)}"
    
    def execute_cmd_code(self, code: str) -> str:
        """CMD kodunu çalıştırır"""
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                return result.stdout or "Komut başarıyla çalıştırıldı"
            else:
                return f"Hata: {result.stderr}"
                
        except Exception as e:
            return f"CMD execution hatası: {str(e)}"
    
    def execute_powershell_code(self, code: str) -> str:
        """PowerShell kodunu çalıştırır"""
        try:
            ps_command = f'powershell -Command "{code}"'
            result = subprocess.run(
                ps_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout or "PowerShell komutu başarıyla çalıştırıldı"
            else:
                return f"Hata: {result.stderr}"
                
        except Exception as e:
            return f"PowerShell execution hatası: {str(e)}"
    
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
                
                response = result.stdout
                
                # Claude yanıtını analiz et
                analysis = self.analyze_claude_response(response)
                
                # Otomatik yanıt kontrolü
                auto_response = self.auto_respond_to_claude(analysis)
                if auto_response:
                    # Otomatik yanıt gönder
                    follow_up_success, follow_up_response = self.send_claude_prompt(auto_response)
                    if follow_up_success:
                        response += f"\n\n[AUTO-RESPONSE: {auto_response}]\n{follow_up_response}"
                    else:
                        response += f"\n\n[AUTO-RESPONSE FAILED: {auto_response}]\n{follow_up_response}"
                
                # Kod çalıştırma kontrolü
                if analysis["has_code"] and analysis["code_blocks"]:
                    execution_result = self.execute_code_from_response(analysis["code_blocks"])
                    response += f"\n\n[CODE EXECUTION]\n{execution_result}"
                
                # Sohbet geçmişine ekle
                self.add_chat_entry(prompt, response, "auto")
                
                return True, response
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
        self.root.title("🤖 Claude Session Manager - Professional Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(True, True)
        
        # Modern renkler ve tema
        self.colors = {
            'bg_primary': '#1a1a1a',       # Ana arkaplan - koyu siyah
            'bg_secondary': '#2d2d2d',     # İkincil arkaplan - koyu gri
            'bg_tertiary': '#3a3a3a',      # Üçüncül arkaplan - orta gri
            'accent_blue': '#4A9EFF',      # Mavi vurgu
            'accent_green': '#00C851',     # Yeşil vurgu
            'accent_orange': '#FF8A00',    # Turuncu vurgu
            'accent_red': '#FF4444',       # Kırmızı vurgu
            'text_primary': '#FFFFFF',     # Ana metin - beyaz
            'text_secondary': '#B0B0B0',   # İkincil metin - açık gri
            'text_muted': '#808080',       # Soluk metin - orta gri
            'button_primary': '#4A9EFF',   # Ana buton rengi
            'button_hover': '#66B2FF',     # Hover rengi
            'success': '#00C851',          # Başarı rengi
            'warning': '#FF8A00',          # Uyarı rengi
            'error': '#FF4444'             # Hata rengi
        }
        
        # Modern fontlar
        self.fonts = {
            'title': ('Segoe UI', 18, 'bold'),
            'subtitle': ('Segoe UI', 14, 'bold'),
            'body': ('Segoe UI', 10),
            'button': ('Segoe UI', 9, 'bold'),
            'mono': ('Consolas', 10),
            'mono_small': ('Consolas', 9)
        }
        
        self.setup_ui()
        self.update_status()
        self.update_clock()
        
        # Scheduler'ı otomatik başlat
        if not self.manager.is_running:
            self.manager.start_scheduler()
            self.log_message("Scheduler otomatik başlatıldı")
        
    def create_modern_button(self, parent, text, command, bg_color=None, width=15):
        """Modern buton oluşturur"""
        if bg_color is None:
            bg_color = self.colors['button_primary']
        
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.fonts['button'],
            bg=bg_color,
            fg=self.colors['text_primary'],
            activebackground=self.colors['button_hover'],
            activeforeground=self.colors['text_primary'],
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            width=width,
            height=2
        )
        return button
    
    def create_status_card(self, parent, title, value, color=None):
        """Modern durum kartı oluşturur"""
        if color is None:
            color = self.colors['text_secondary']
        
        card_frame = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        card_frame.pack(fill=tk.X, pady=2, padx=5)
        
        title_label = tk.Label(
            card_frame, 
            text=title,
            font=self.fonts['body'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_muted'],
            anchor='w'
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        value_label = tk.Label(
            card_frame,
            text=value,
            font=self.fonts['body'],
            bg=self.colors['bg_secondary'],
            fg=color,
            anchor='e'
        )
        value_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        return value_label
    
    def setup_ui(self):
        # Ana container
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header bölümü - gradient görünüm
        header_frame = tk.Frame(main_container, bg=self.colors['bg_secondary'], height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Header içeriği
        header_content = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sol taraf - Başlık ve alt başlık
        left_header = tk.Frame(header_content, bg=self.colors['bg_secondary'])
        left_header.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = tk.Label(
            left_header,
            text="🤖 Claude Session Manager",
            font=self.fonts['title'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['accent_blue']
        )
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(
            left_header,
            text="Professional AI Session Management",
            font=self.fonts['body'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Sağ taraf - Saat
        right_header = tk.Frame(header_content, bg=self.colors['bg_secondary'])
        right_header.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.clock_label = tk.Label(
            right_header,
            text="",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['accent_green']
        )
        self.clock_label.pack(anchor='e', pady=(10, 0))
        
        # Ana içerik bölümü
        content_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sol panel - Durum bilgileri
        left_panel = tk.Frame(content_frame, bg=self.colors['bg_tertiary'], width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0)
        left_panel.pack_propagate(False)
        
        # Durum başlığı
        status_header = tk.Label(
            left_panel,
            text="📊 Sistem Durumu",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            pady=15
        )
        status_header.pack(fill=tk.X)
        
        # Durum kartları
        self.status_label = self.create_status_card(left_panel, "🔄 Sistem Durumu", "Kontrol ediliyor...", self.colors['warning'])
        self.last_session_label = self.create_status_card(left_panel, "⏰ Son Session", "Henüz başlatılmadı", self.colors['text_secondary'])
        self.next_session_label = self.create_status_card(left_panel, "⏭️ Sonraki Session", "Planlanmadı", self.colors['text_secondary'])
        self.time_remaining_label = self.create_status_card(left_panel, "⏳ Kalan Süre", "-", self.colors['text_secondary'])
        self.session_count_label = self.create_status_card(left_panel, "📈 Session Sayısı", "0", self.colors['accent_blue'])
        self.tokens_label = self.create_status_card(left_panel, "🎯 Token Kalan", "-", self.colors['text_secondary'])
        
        # Sağ panel - Kontroller ve log
        right_panel = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Buton bölümü
        buttons_section = tk.Frame(right_panel, bg=self.colors['bg_primary'])
        buttons_section.pack(fill=tk.X, pady=(0, 20))
        
        # Buton başlığı
        buttons_header = tk.Label(
            buttons_section,
            text="🎮 Kontrol Paneli",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary']
        )
        buttons_header.pack(anchor='w', pady=(0, 15))
        
        # Ana butonlar (birinci satır)
        main_buttons_frame = tk.Frame(buttons_section, bg=self.colors['bg_primary'])
        main_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = self.create_modern_button(
            main_buttons_frame, "🚀 Otomatik Başlat", self.toggle_auto_session, 
            self.colors['accent_green'], 18
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        manual_button = self.create_modern_button(
            main_buttons_frame, "⚡ Manuel Session", self.manual_session,
            self.colors['accent_blue'], 18
        )
        manual_button.pack(side=tk.LEFT, padx=(0, 10))
        
        terminal_button = self.create_modern_button(
            main_buttons_frame, "🖥️ Terminal", self.show_terminal,
            self.colors['bg_tertiary'], 15
        )
        terminal_button.pack(side=tk.LEFT)
        
        # Yönetim butonları (ikinci satır)
        mgmt_buttons_frame = tk.Frame(buttons_section, bg=self.colors['bg_primary'])
        mgmt_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        settings_button = self.create_modern_button(
            mgmt_buttons_frame, "⚙️ Ayarlar", self.show_settings,
            self.colors['bg_tertiary'], 12
        )
        settings_button.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_button = self.create_modern_button(
            mgmt_buttons_frame, "🔄 Yenile", self.update_status,
            self.colors['bg_tertiary'], 12
        )
        refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        scheduled_button = self.create_modern_button(
            mgmt_buttons_frame, "⏰ Zamanlı", self.show_scheduled_commands,
            self.colors['accent_orange'], 12
        )
        scheduled_button.pack(side=tk.LEFT, padx=(0, 5))
        
        protocols_button = self.create_modern_button(
            mgmt_buttons_frame, "📋 Protokoller", self.show_work_protocols,
            self.colors['accent_orange'], 12
        )
        protocols_button.pack(side=tk.LEFT)
        
        # Raporlar (üçüncü satır)
        reports_buttons_frame = tk.Frame(buttons_section, bg=self.colors['bg_primary'])
        reports_buttons_frame.pack(fill=tk.X)
        
        usage_button = self.create_modern_button(
            reports_buttons_frame, "📊 Kullanım", self.show_usage_report,
            self.colors['bg_tertiary'], 12
        )
        usage_button.pack(side=tk.LEFT, padx=(0, 5))
        
        chat_button = self.create_modern_button(
            reports_buttons_frame, "💬 Sohbet", self.show_chat_history,
            self.colors['bg_tertiary'], 12
        )
        chat_button.pack(side=tk.LEFT)
        
        # Log bölümü
        log_section = tk.Frame(right_panel, bg=self.colors['bg_primary'])
        log_section.pack(fill=tk.BOTH, expand=True)
        
        # Log başlığı
        log_header = tk.Label(
            log_section,
            text="📝 Sistem Günlüğü",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary']
        )
        log_header.pack(anchor='w', pady=(0, 10))
        
        # Log frame
        log_frame = tk.Frame(log_section, bg=self.colors['bg_tertiary'], relief='flat', bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text widget
        self.log_text = tk.Text(
            log_frame,
            height=12,
            font=self.fonts['mono_small'],
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            selectbackground=self.colors['accent_blue'],
            relief='flat',
            borderwidth=5,
            wrap=tk.WORD
        )
        
        log_scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview,
                                    bg=self.colors['bg_secondary'], troughcolor=self.colors['bg_primary'])
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # Log renk etiketleri
        self.log_text.tag_configure("info", foreground=self.colors['accent_blue'])
        self.log_text.tag_configure("success", foreground=self.colors['success'])
        self.log_text.tag_configure("warning", foreground=self.colors['warning'])
        self.log_text.tag_configure("error", foreground=self.colors['error'])
        
        self.root.after(5000, self.auto_update_status)
        self.root.after(1000, self.update_clock)
    
    def log_message(self, message: str, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Mesaj tipine göre renk belirle
        if "başarı" in message.lower() or "başlatıldı" in message.lower():
            tag = "success"
        elif "hata" in message.lower() or "fail" in message.lower():
            tag = "error"
        elif "uyarı" in message.lower() or "warning" in message.lower():
            tag = "warning"
        else:
            tag = "info"
            
        self.log_text.insert(tk.END, log_entry, tag)
        self.log_text.see(tk.END)
    
    def update_status(self):
        status = self.manager.get_session_status()
        
        # Sistem durumu güncelle
        if status["is_running"]:
            self.status_label.config(text="🟢 Aktif", fg=self.colors['success'])
            self.start_button.config(text="⏹️ Durdur", bg=self.colors['accent_red'])
        else:
            self.status_label.config(text="🔴 Pasif", fg=self.colors['error'])
            self.start_button.config(text="🚀 Otomatik Başlat", bg=self.colors['accent_green'])
        
        # Son session güncelle
        if status["last_session"]:
            last_time = datetime.fromisoformat(status["last_session"])
            self.last_session_label.config(text=last_time.strftime("%d/%m/%Y %H:%M"), fg=self.colors['text_primary'])
        else:
            self.last_session_label.config(text="Henüz başlatılmadı", fg=self.colors['text_muted'])
        
        # Sonraki session güncelle
        if status["next_session"]:
            next_time = datetime.fromisoformat(status["next_session"])
            self.next_session_label.config(text=next_time.strftime("%d/%m/%Y %H:%M"), fg=self.colors['accent_blue'])
        else:
            self.next_session_label.config(text="Planlanmadı", fg=self.colors['text_muted'])
        
        # Kalan süre güncelle
        time_remaining = status.get("time_until_next", "-")
        if time_remaining != "-" and "Zamanı geldi" not in time_remaining:
            self.time_remaining_label.config(text=time_remaining, fg=self.colors['accent_orange'])
        else:
            self.time_remaining_label.config(text=time_remaining, fg=self.colors['text_muted'])
        
        # Session sayısı güncelle
        self.session_count_label.config(text=str(status["session_count"]), fg=self.colors['accent_blue'])
        
        # Token bilgisi güncelle
        tokens = status.get("tokens_remaining", "-")
        self.tokens_label.config(text=str(tokens), fg=self.colors['text_secondary'])
    
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
        settings_window.title("⚙️ Gelişmiş Ayarlar")
        settings_window.geometry("500x600")
        settings_window.configure(bg=self.colors['bg_primary'])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Ana frame
        main_frame = tk.Frame(settings_window, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = tk.Label(
            main_frame,
            text="⚙️ Sistem Ayarları",
            font=self.fonts['title'],
            bg=self.colors['bg_primary'],
            fg=self.colors['accent_blue']
        )
        title_label.pack(pady=(0, 20))
        
        # Temel ayarlar bölümü
        basic_frame = tk.LabelFrame(
            main_frame,
            text="📋 Temel Ayarlar",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief='flat',
            bd=1
        )
        basic_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Otomatik prompt
        prompt_frame = tk.Frame(basic_frame, bg=self.colors['bg_secondary'])
        prompt_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(prompt_frame, text="Otomatik Prompt:", font=self.fonts['body'],
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        auto_prompt_var = tk.StringVar(value=self.manager.config["auto_prompt"])
        tk.Entry(prompt_frame, textvariable=auto_prompt_var, width=25, font=self.fonts['body']).pack(side=tk.RIGHT)
        
        # Session aralığı
        interval_frame = tk.Frame(basic_frame, bg=self.colors['bg_secondary'])
        interval_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(interval_frame, text="Session Aralığı (saat):", font=self.fonts['body'],
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        interval_var = tk.StringVar(value=str(self.manager.config["session_interval_hours"]))
        tk.Entry(interval_frame, textvariable=interval_var, width=25, font=self.fonts['body']).pack(side=tk.RIGHT)
        
        # Başlangıç saati
        time_frame = tk.Frame(basic_frame, bg=self.colors['bg_secondary'])
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(time_frame, text="Başlangıç Saati (HH:MM):", font=self.fonts['body'],
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        start_time_var = tk.StringVar(value=self.manager.config["start_time"])
        tk.Entry(time_frame, textvariable=start_time_var, width=25, font=self.fonts['body']).pack(side=tk.RIGHT)
        
        # Temel checkboxlar
        auto_enable_var = tk.BooleanVar(value=self.manager.config["enable_auto_session"])
        tk.Checkbutton(
            basic_frame, text="🚀 Otomatik session etkin", variable=auto_enable_var,
            font=self.fonts['body'], bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_tertiary'], activebackground=self.colors['bg_secondary']
        ).pack(anchor='w', padx=10, pady=5)
        
        # Otomatik yanıt bölümü
        auto_frame = tk.LabelFrame(
            main_frame,
            text="🤖 Otomatik Yanıt Sistemi",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief='flat',
            bd=1
        )
        auto_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Otomatik yanıt etkinleştir
        auto_response_var = tk.BooleanVar(value=self.manager.config.get("auto_response_enabled", True))
        tk.Checkbutton(
            auto_frame, text="🔄 Otomatik yanıt sistemi etkin", variable=auto_response_var,
            font=self.fonts['body'], bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_tertiary'], activebackground=self.colors['bg_secondary']
        ).pack(anchor='w', padx=10, pady=5)
        
        # Varsayılan seçim
        choice_frame = tk.Frame(auto_frame, bg=self.colors['bg_secondary'])
        choice_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(choice_frame, text="Varsayılan Seçim (1,2,3):", font=self.fonts['body'],
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        default_choice_var = tk.StringVar(value=self.manager.config.get("default_choice", "1"))
        choice_combo = ttk.Combobox(choice_frame, textvariable=default_choice_var, 
                                   values=["1", "2", "3", "yes", "no"], width=10)
        choice_combo.pack(side=tk.RIGHT)
        
        # Kod çalıştırma bölümü
        code_frame = tk.LabelFrame(
            main_frame,
            text="💻 Kod Çalıştırma Sistemi",
            font=self.fonts['subtitle'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief='flat',
            bd=1
        )
        code_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Otomatik kod çalıştırma
        auto_code_var = tk.BooleanVar(value=self.manager.config.get("auto_execute_code", True))
        tk.Checkbutton(
            code_frame, text="⚡ Otomatik kod çalıştırma etkin", variable=auto_code_var,
            font=self.fonts['body'], bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_tertiary'], activebackground=self.colors['bg_secondary']
        ).pack(anchor='w', padx=10, pady=5)
        
        # İzinli diller
        lang_label = tk.Label(
            code_frame, text="💡 İzinli Diller: Python, Bash, CMD, PowerShell",
            font=self.fonts['mono_small'], bg=self.colors['bg_secondary'], 
            fg=self.colors['text_muted']
        )
        lang_label.pack(anchor='w', padx=10, pady=2)
        
        # Butonlar
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_settings():
            try:
                new_config = self.manager.config.copy()
                new_config["auto_prompt"] = auto_prompt_var.get()
                new_config["session_interval_hours"] = int(interval_var.get())
                new_config["start_time"] = start_time_var.get()
                new_config["enable_auto_session"] = auto_enable_var.get()
                new_config["auto_response_enabled"] = auto_response_var.get()
                new_config["default_choice"] = default_choice_var.get()
                new_config["auto_execute_code"] = auto_code_var.get()
                
                # Saat formatını kontrol et
                datetime.strptime(start_time_var.get(), "%H:%M")
                
                self.manager.save_config(new_config)
                self.log_message("✅ Gelişmiş ayarlar kaydedildi", "success")
                
                # Başarı mesajı
                messagebox.showinfo("Başarılı", 
                    "🎉 Ayarlar başarıyla kaydedildi!\n\n"
                    f"🤖 Otomatik yanıt: {'Açık' if auto_response_var.get() else 'Kapalı'}\n"
                    f"⚡ Kod çalıştırma: {'Açık' if auto_code_var.get() else 'Kapalı'}\n"
                    f"🎯 Varsayılan seçim: {default_choice_var.get()}")
                
                settings_window.destroy()
                
                if self.manager.is_running:
                    self.manager.stop_scheduler()
                    self.manager.start_scheduler()
                    
            except ValueError as e:
                messagebox.showerror("Hata", "⚠️ Geçersiz saat formatı! (HH:MM kullanın)")
            except Exception as e:
                messagebox.showerror("Hata", f"⚠️ Ayarlar kaydedilemedi: {str(e)}")
        
        def reset_to_defaults():
            if messagebox.askyesno("Onay", "🔄 Tüm ayarları varsayılan değerlere döndürmek istediğinizden emin misiniz?"):
                auto_prompt_var.set("x")
                interval_var.set("5")
                start_time_var.set("08:00")
                auto_enable_var.set(True)
                auto_response_var.set(True)
                default_choice_var.set("1")
                auto_code_var.set(True)
                self.log_message("🔄 Ayarlar varsayılana döndürüldü", "warning")
        
        save_button = self.create_modern_button(
            button_frame, "💾 Kaydet", save_settings, 
            self.colors['success'], 15
        )
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_button = self.create_modern_button(
            button_frame, "🔄 Varsayılan", reset_to_defaults,
            self.colors['warning'], 15
        )
        reset_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = self.create_modern_button(
            button_frame, "❌ İptal", settings_window.destroy,
            self.colors['bg_tertiary'], 15
        )
        cancel_button.pack(side=tk.RIGHT)
    
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
    
    def show_work_protocols(self):
        protocols_window = tk.Toplevel(self.root)
        protocols_window.title("Çalışma Protokolleri")
        protocols_window.geometry("800x700")
        protocols_window.transient(self.root)
        protocols_window.grab_set()
        
        frame = ttk.Frame(protocols_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Çalışma Protokolleri", font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        # Bilgi metni
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = ttk.Label(info_frame, 
                             text="Bu bölümde çalışma protokollerinizi düzenleyebilirsiniz. Protokoller otomatik olarak kaydedilir.",
                             foreground="gray", font=("Arial", 9))
        info_text.pack(anchor=tk.W)
        
        # Metin editörü
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        protocols_text = tk.Text(text_frame, height=30, width=80, wrap=tk.WORD, 
                                font=("Consolas", 10), undo=True, maxundo=20)
        protocols_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=protocols_text.yview)
        protocols_text.configure(yscrollcommand=protocols_scrollbar.set)
        
        protocols_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        protocols_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mevcut protokolleri yükle
        current_protocols = self.manager.config.get("work_protocols", "")
        protocols_text.insert(1.0, current_protocols)
        
        # Butonlar
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_protocols():
            new_protocols = protocols_text.get(1.0, tk.END).strip()
            config = self.manager.config.copy()
            config["work_protocols"] = new_protocols
            self.manager.save_config(config)
            self.log_message("Çalışma protokolleri kaydedildi")
            messagebox.showinfo("Başarılı", "Çalışma protokolleri başarıyla kaydedildi!")
        
        def reset_protocols():
            if messagebox.askyesno("Onay", "Protokolleri varsayılan haline döndürmek istediğinizden emin misiniz?"):
                default_protocols = """● 🔧 ÇALIŞMA PROTOKOLLERI

📝 NOT DEFTERLERİ PROTOKOLÜ

- "ntk" komutu: Tüm .md uzantılı not defterlerini okur
- Dosyalar: CLAUDE.md + diğer tüm .md dosyaları projeye dahil
- "Not defterleri" = .md dosyaları: Markdown uzantılı tüm dokümanlar

📋 YAPILACAKLAR NOT DEFTERİ

- "ynd" komutu: Yeni madde ekle (Yapılacaklar Not Defteri)
- Dosya: YAPILACAKLAR.md
- Format: [Kullanıcı madde] + ynd → otomatik kayıt
- Otomatik tarih: Her maddeye tarih damgası eklenir

📝 PROMPT GÜNLÜĞÜ SİSTEMİ

ZORUNLU KURAL: Her kullanıcı promptu PROMPT_GUNLUGU.md dosyasına otomatik kaydedilmeli. Manuel "promptu ekle"
talebi beklemeden, her prompt otomatik olarak günlüğe işlenmelidir.
- Dosya: PROMPT_GUNLUGU.md
- Format: [Tarih-Saat] Prompt İçeriği
- Otomatik: Kullanıcı talebi olmadan tüm promptlar kaydedilir
- Kronolojik: En yeni promptlar en üstte

🔄 BERABER ÇALIŞMA PROTOKOLÜ

1. 🔧 Otomatik Build & Deploy:
  - Her yenilik → APK build → telefona yükleme
  - Kullanıcı sorgulamaz, otomatik yapılır
2. 🔊 SİSTEM BEEP PROTOKOLÜ:
  - Temel kurallar:
      - Soru sorulacağı zaman → 3x beep
    - Onay alınacağı zaman → 3x beep
    - Sonuç sunulacağı zaman → 3x beep
    - Etkileşim gerekince → 3x beep
    - Görev bitirip sunacağı zaman → 3x beep
    - 1,2,3 tuş seçenekleri sunacağı zaman → 3x beep
  - Ses Formatı:
powershell -c "[Console]::Beep(800,300); [Console]::Beep(800,300); [Console]::Beep(800,300)"
3. 💾 Hızlı Commit Protokolü:
  - "tmm" diyince → anında commit + push
  - "[özellik adı] tamam" diyince → commit + push

🔥 YILDIZLI KOMUT SİSTEMİ (*)

- *"p" = Bu prompt'u günlüğe ekle
- *"btş" = Beep protokolü uyguladığın için teşekkür
- *"btk" = Beep protokolünü uygulamadığın için tenkid
- *"tmm" = Bu özellik tamam, commit + push yap
- *"ab" = APK build et
- *"bty" = Build et telefona yükle
- *"ty" = Telefona yükle (APK install)
- *"mo" = md uzantılı not defterlerini oku

📋 HER AÇILIŞTA YAPILACAKLAR:

1. CLAUDE.md dosyasını oku ve projeyi anla
2. Önceki konuşmaları ve gelişmeleri kontrol et
3. Güncel proje durumunu değerlendir
4. Sistem sesi protokolü: Görev tamamlandığında 3 kere beep sesi çıkar
5. Otomatik onay protokolü: Kullanıcıdan onay almadan işlemlere devam et"""
                protocols_text.delete(1.0, tk.END)
                protocols_text.insert(1.0, default_protocols)
                self.log_message("Protokoller varsayılan haline döndürüldü")
        
        def export_protocols():
            try:
                protocols_content = protocols_text.get(1.0, tk.END).strip()
                export_file = f"work_protocols_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(export_file, 'w', encoding='utf-8') as f:
                    f.write("Claude Session Manager - Çalışma Protokolleri\n")
                    f.write(f"Export Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*80 + "\n\n")
                    f.write(protocols_content)
                
                messagebox.showinfo("Başarılı", f"Çalışma protokolleri {export_file} dosyasına aktarıldı")
                self.log_message(f"Çalışma protokolleri {export_file} dosyasına aktarıldı")
            except Exception as e:
                messagebox.showerror("Hata", f"Export hatası: {str(e)}")
        
        ttk.Button(button_frame, text="Kaydet", command=save_protocols).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Varsayılana Döndür", command=reset_protocols).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Et", command=export_protocols).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=protocols_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Otomatik kayıt (her 30 saniyede bir)
        def auto_save():
            try:
                if protocols_window.winfo_exists():
                    new_protocols = protocols_text.get(1.0, tk.END).strip()
                    if new_protocols != self.manager.config.get("work_protocols", ""):
                        config = self.manager.config.copy()
                        config["work_protocols"] = new_protocols
                        self.manager.save_config(config)
                    protocols_window.after(30000, auto_save)
            except:
                pass
        
        protocols_window.after(30000, auto_save)
    
    def show_terminal(self):
        terminal_window = tk.Toplevel(self.root)
        terminal_window.title("Claude Session Manager - Terminal")
        terminal_window.geometry("900x600")
        terminal_window.transient(self.root)
        terminal_window.grab_set()
        
        # Terminal için değişkenler
        self.current_directory = os.getcwd()
        self.command_history = []
        self.history_index = -1
        
        frame = ttk.Frame(terminal_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🖥️ Gömülü Terminal", font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        
        # Mevcut dizin göstergesi
        self.current_dir_label = ttk.Label(header_frame, text=f"📁 {self.current_directory}", 
                                          foreground="blue", font=("Consolas", 9))
        self.current_dir_label.pack(side=tk.RIGHT)
        
        # Terminal çıktı alanı
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.terminal_output = tk.Text(output_frame, height=25, width=100, 
                                      font=("Consolas", 10), bg="black", fg="white",
                                      insertbackground="white", wrap=tk.WORD)
        terminal_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.terminal_output.yview)
        self.terminal_output.configure(yscrollcommand=terminal_scrollbar.set)
        
        self.terminal_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        terminal_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Renk etiketleri
        self.terminal_output.tag_configure("prompt", foreground="lime")
        self.terminal_output.tag_configure("command", foreground="yellow")
        self.terminal_output.tag_configure("output", foreground="white")
        self.terminal_output.tag_configure("error", foreground="red")
        self.terminal_output.tag_configure("info", foreground="cyan")
        
        # Komut giriş alanı
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Komut:", font=("Consolas", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.command_entry = ttk.Entry(input_frame, font=("Consolas", 10), width=80)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Butonlar
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Çalıştır", 
                  command=lambda: self.execute_terminal_command()).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Temizle", 
                  command=self.clear_terminal).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Dizin Değiştir", 
                  command=self.change_directory).pack(side=tk.LEFT, padx=2)
        
        # Kısayol tuşları
        def on_enter(event):
            self.execute_terminal_command()
            return "break"
        
        def on_up_arrow(event):
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, self.command_history[-(self.history_index + 1)])
            return "break"
        
        def on_down_arrow(event):
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, self.command_history[-(self.history_index + 1)])
            elif self.history_index == 0:
                self.history_index = -1
                self.command_entry.delete(0, tk.END)
            return "break"
        
        self.command_entry.bind("<Return>", on_enter)
        self.command_entry.bind("<Up>", on_up_arrow)
        self.command_entry.bind("<Down>", on_down_arrow)
        
        # Alt bilgi
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X)
        
        info_text = ttk.Label(info_frame, 
                             text="💡 claude [prompt]: AI session | auto [on|off|status]: Otomatik özellikler | ↑↓: Geçmiş",
                             foreground="gray", font=("Arial", 8))
        info_text.pack(anchor=tk.W)
        
        # Hoşgeldin mesajı
        self.terminal_output.insert(tk.END, "🤖 Claude Session Manager - Akıllı Terminal\n", "info")
        self.terminal_output.insert(tk.END, f"📁 Mevcut dizin: {self.current_directory}\n", "info")
        self.terminal_output.insert(tk.END, "🚀 Özel komutlar:\n", "info")
        self.terminal_output.insert(tk.END, "  • claude [mesaj]     → AI session başlat\n", "info")
        self.terminal_output.insert(tk.END, "  • auto on/off/status → Otomatik özellikler\n", "info")
        self.terminal_output.insert(tk.END, "  • cd [dizin]        → Dizin değiştir\n", "info")
        self.terminal_output.insert(tk.END, "\n✨ Otomatik özellikler aktif - Claude kodları çalıştırılacak!\n\n", "info")
        
        # Focus'u komut giriş alanına ver
        self.command_entry.focus()
    
    def execute_terminal_command(self):
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Komut geçmişine ekle
        if command not in self.command_history:
            self.command_history.append(command)
        if len(self.command_history) > 50:  # Son 50 komutu sakla
            self.command_history = self.command_history[-50:]
        self.history_index = -1
        
        # Prompt göster
        prompt = f"{os.path.basename(self.current_directory)}> "
        self.terminal_output.insert(tk.END, prompt, "prompt")
        self.terminal_output.insert(tk.END, f"{command}\n", "command")
        
        # Özel komutları kontrol et
        if command.lower().startswith("claude "):
            # Claude'a özel prompt gönder
            prompt = command[7:].strip()  # "claude " kısmını kaldır
            if prompt:
                self.terminal_output.insert(tk.END, f"Claude session başlatılıyor: '{prompt}'\n", "info")
                self.start_claude_session_from_terminal(prompt)
            else:
                self.terminal_output.insert(tk.END, "Claude session başlatılıyor...\n", "info")
                self.start_claude_session_from_terminal()
            self.command_entry.delete(0, tk.END)
            self.terminal_output.see(tk.END)
            return
        
        if command.lower() in ["claude", "claude --help"]:
            self.terminal_output.insert(tk.END, "Claude session başlatılıyor...\n", "info")
            self.start_claude_session_from_terminal()
            self.command_entry.delete(0, tk.END)
            self.terminal_output.see(tk.END)
            return
        
        if command.lower().startswith("auto "):
            # Otomatik ayarları kontrol et
            auto_command = command[5:].strip()
            if auto_command == "on":
                self.manager.config["auto_response_enabled"] = True
                self.manager.config["auto_execute_code"] = True
                self.manager.save_config(self.manager.config)
                self.terminal_output.insert(tk.END, "✅ Otomatik özellikler AÇILDI\n", "info")
            elif auto_command == "off":
                self.manager.config["auto_response_enabled"] = False
                self.manager.config["auto_execute_code"] = False
                self.manager.save_config(self.manager.config)
                self.terminal_output.insert(tk.END, "❌ Otomatik özellikler KAPATILDI\n", "warning")
            elif auto_command == "status":
                auto_resp = self.manager.config.get("auto_response_enabled", False)
                auto_code = self.manager.config.get("auto_execute_code", False)
                default_choice = self.manager.config.get("default_choice", "1")
                self.terminal_output.insert(tk.END, f"🤖 Otomatik yanıt: {'AÇIK' if auto_resp else 'KAPALI'}\n", "info")
                self.terminal_output.insert(tk.END, f"⚡ Otomatik kod: {'AÇIK' if auto_code else 'KAPALI'}\n", "info")
                self.terminal_output.insert(tk.END, f"🎯 Varsayılan seçim: {default_choice}\n", "info")
            else:
                self.terminal_output.insert(tk.END, "❓ Kullanım: auto [on|off|status]\n", "warning")
            self.command_entry.delete(0, tk.END)
            self.terminal_output.see(tk.END)
            return
        
        if command.lower().startswith("cd "):
            self.change_directory_command(command[3:].strip())
            self.command_entry.delete(0, tk.END)
            self.terminal_output.see(tk.END)
            return
        
        # Normal komut çalıştır
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.current_directory
            )
            
            stdout, stderr = process.communicate(timeout=30)
            
            if stdout:
                self.terminal_output.insert(tk.END, stdout, "output")
            if stderr:
                self.terminal_output.insert(tk.END, stderr, "error")
            
            if process.returncode != 0:
                self.terminal_output.insert(tk.END, f"Exit code: {process.returncode}\n", "error")
                
        except subprocess.TimeoutExpired:
            self.terminal_output.insert(tk.END, "Komut zaman aşımına uğradı (30s)\n", "error")
        except Exception as e:
            self.terminal_output.insert(tk.END, f"Hata: {str(e)}\n", "error")
        
        self.terminal_output.insert(tk.END, "\n")
        self.command_entry.delete(0, tk.END)
        self.terminal_output.see(tk.END)
    
    def start_claude_session_from_terminal(self, custom_prompt=None):
        def run_claude():
            try:
                prompt = custom_prompt or "Terminal'den başlatıldı"
                success, response = self.manager.manual_session_start(prompt)
                if success:
                    self.terminal_output.insert(tk.END, "✅ Claude session başarıyla başlatıldı!\n", "info")
                    
                    # Yanıtı göster
                    self.terminal_output.insert(tk.END, f"\n📝 Claude Yanıtı:\n{response}\n\n", "output")
                    
                    # Yanıtı analiz et ve kod varsa çalıştır
                    analysis = self.manager.analyze_claude_response(response)
                    if analysis["has_code"] and analysis["code_blocks"]:
                        self.terminal_output.insert(tk.END, "🔍 Kod blokları tespit edildi, çalıştırılıyor...\n", "info")
                        execution_result = self.manager.execute_code_from_response(analysis["code_blocks"])
                        self.terminal_output.insert(tk.END, f"💻 Kod Çalıştırma Sonucu:\n{execution_result}\n\n", "output")
                    
                    # Seçenekler varsa otomatik yanıtla
                    if analysis["has_choices"]:
                        auto_response = self.manager.auto_respond_to_claude(analysis)
                        if auto_response:
                            self.terminal_output.insert(tk.END, f"🤖 Otomatik yanıt gönderiliyor: {auto_response}\n", "info")
                            # Recursive call - otomatik yanıtı gönder
                            self.start_claude_session_from_terminal(auto_response)
                        else:
                            self.terminal_output.insert(tk.END, "❓ Seçenekler mevcut ama otomatik yanıt kapalı\n", "warning")
                else:
                    self.terminal_output.insert(tk.END, f"❌ Claude session hatası: {response}\n", "error")
                self.terminal_output.see(tk.END)
            except Exception as e:
                self.terminal_output.insert(tk.END, f"❌ Beklenmeyen hata: {str(e)}\n", "error")
                self.terminal_output.see(tk.END)
        
        # Claude session'ı ayrı thread'de çalıştır
        threading.Thread(target=run_claude, daemon=True).start()
    
    def change_directory_command(self, path):
        try:
            if not path:
                path = os.path.expanduser("~")  # Home directory
            
            new_path = os.path.abspath(os.path.join(self.current_directory, path))
            
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.current_directory = new_path
                self.current_dir_label.config(text=f"📁 {self.current_directory}")
                self.terminal_output.insert(tk.END, f"Dizin değiştirildi: {self.current_directory}\n", "info")
            else:
                self.terminal_output.insert(tk.END, f"Dizin bulunamadı: {path}\n", "error")
        except Exception as e:
            self.terminal_output.insert(tk.END, f"Dizin değiştirme hatası: {str(e)}\n", "error")
    
    def change_directory(self):
        new_dir = simpledialog.askstring("Dizin Değiştir", f"Yeni dizin (mevcut: {self.current_directory}):")
        if new_dir:
            self.change_directory_command(new_dir)
    
    def clear_terminal(self):
        self.terminal_output.delete(1.0, tk.END)
        self.terminal_output.insert(tk.END, "Terminal temizlendi.\n\n", "info")
    
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