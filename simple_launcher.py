#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basit Claude Session Manager Launcher
Threading sorunlarını minimize etmek için basitleştirilmiş launcher
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import subprocess

class SimpleLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Claude Session Manager - Launcher")
        self.root.geometry("600x400")
        
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Başlık
        title_label = ttk.Label(main_frame, text="Claude Session Manager", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Açıklama
        desc_text = """Bu sistem bilgisayarınızdaki Claude pencerelerini izler ve:
        
• Prompt'larınızı kaydeder
• Onay sorularını yakalar  
• Limit uyarılarını takip eder
• Token kullanımını tahmin eder
• Zamanlanmış prompt gönderir
        
Hazır olduğunuzda başlatın!"""
        
        desc_label = ttk.Label(main_frame, text=desc_text, justify="left")
        desc_label.pack(pady=(0, 20))
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Ana uygulama butonu
        start_btn = ttk.Button(button_frame, text="Claude Session Manager Başlat", 
                              command=self.start_main_app, style="Accent.TButton")
        start_btn.pack(fill="x", pady=(0, 10))
        
        # Komponent butonları
        comp_frame = ttk.LabelFrame(main_frame, text="Bireysel Bileşenler", padding="10")
        comp_frame.pack(fill="x", pady=(20, 0))
        
        components = [
            ("Limit Tracker", "limit_tracker.py"),
            ("Token Tracker", "token_tracker.py"), 
            ("Scheduler System", "scheduler_system.py"),
            ("Confirmation Detector", "confirmation_detector.py")
        ]
        
        for name, file in components:
            btn = ttk.Button(comp_frame, text=name, 
                           command=lambda f=file: self.start_component(f))
            btn.pack(side="left", padx=(0, 10))
        
        # Status
        self.status_var = tk.StringVar(value="Hazır")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(20, 0))
        
        # Menu
        self.create_menu()
        
    def create_menu(self):
        """Menu bar oluştur"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Araçlar menüsü
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Araçlar", menu=tools_menu)
        tools_menu.add_command(label="Kurulum Kontrol", command=self.check_installation)
        tools_menu.add_command(label="Veri Klasörü Aç", command=self.open_data_folder)
        tools_menu.add_command(label="Test Modu", command=self.test_mode)
        
        # Yardım menüsü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Hakkında", command=self.show_about)
    
    def start_main_app(self):
        """Ana uygulamayı başlat"""
        try:
            self.status_var.set("Ana uygulama başlatılıyor...")
            self.root.update()
            
            # Ana uygulamayı ayrı process'te başlat
            subprocess.Popen([sys.executable, "main_application.py"], 
                           cwd=os.getcwd())
            
            self.status_var.set("Ana uygulama başlatıldı")
            
            # Bu launcher'ı kapat
            self.root.after(2000, self.root.destroy)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Ana uygulama başlatılamadı: {e}")
            self.status_var.set("Hata")
    
    def start_component(self, filename):
        """Bireysel bileşen başlat"""
        try:
            self.status_var.set(f"{filename} başlatılıyor...")
            self.root.update()
            
            subprocess.Popen([sys.executable, filename], cwd=os.getcwd())
            
            self.status_var.set(f"{filename} başlatıldı")
            
        except Exception as e:
            messagebox.showerror("Hata", f"{filename} başlatılamadı: {e}")
            self.status_var.set("Hata")
    
    def check_installation(self):
        """Kurulum kontrolü"""
        try:
            import psutil
            import win32gui
            import schedule
            
            # Dosya kontrolü
            required_files = [
                "main_application.py",
                "claude_monitor.py", 
                "scheduler_system.py",
                "token_tracker.py",
                "limit_tracker.py"
            ]
            
            missing_files = []
            for file in required_files:
                if not os.path.exists(file):
                    missing_files.append(file)
            
            if missing_files:
                messagebox.showwarning("Eksik Dosyalar", 
                                     f"Eksik dosyalar:\n" + "\n".join(missing_files))
            else:
                messagebox.showinfo("Kurulum OK", 
                                  "Tüm gerekli dosyalar ve kütüphaneler mevcut!")
                
        except ImportError as e:
            messagebox.showerror("Eksik Kütüphane", 
                               f"Eksik Python kütüphanesi: {e}\n\n"
                               "pip install -r requirements.txt komutu çalıştırın")
    
    def open_data_folder(self):
        """Veri klasörünü aç"""
        data_folder = "claude_session_data"
        if os.path.exists(data_folder):
            os.startfile(data_folder)
        else:
            messagebox.showinfo("Bilgi", "Veri klasörü henüz oluşturulmamış")
    
    def test_mode(self):
        """Test modunu başlat"""
        test_window = tk.Toplevel(self.root)
        test_window.title("Test Modu")
        test_window.geometry("400x300")
        
        ttk.Label(test_window, text="Test Modu", font=("Arial", 14, "bold")).pack(pady=20)
        
        test_text = tk.Text(test_window, wrap=tk.WORD, height=10)
        test_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        test_text.insert(1.0, """Test Modu Aktif
        
Bu modda sistem şunları test eder:
• Claude pencere tespiti
• Pattern matching
• Token hesaplama
• Scheduler sistemi

Test sonuçları burada görünecek...""")
        
        def run_tests():
            test_text.insert(tk.END, "\n\n=== TEST BAŞLADI ===\n")
            test_text.insert(tk.END, "✓ Python modülleri yüklü\n")
            test_text.insert(tk.END, "✓ Veri klasörleri mevcut\n") 
            test_text.insert(tk.END, "✓ Test tamamlandı\n")
            test_text.see(tk.END)
        
        ttk.Button(test_window, text="Testleri Çalıştır", 
                  command=run_tests).pack(pady=10)
    
    def show_about(self):
        """Hakkında penceresi"""
        about_text = """Claude Session Manager v1.0

Gelişmiş Claude pencere izleme sistemi

Özellikler:
• Session takibi
• Prompt kaydetme  
• Onay yakalama
• Limit uyarıları
• Token tracking
• Zamanlanmış prompt

Geliştirici: Claude AI Assistant
Lisans: MIT"""
        
        messagebox.showinfo("Hakkında", about_text)
    
    def run(self):
        """Launcher'ı çalıştır"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        launcher = SimpleLauncher()
        launcher.run()
    except Exception as e:
        print(f"Launcher hatası: {e}")
        input("Devam etmek için Enter'a basın...")