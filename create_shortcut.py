#!/usr/bin/env python3
"""
Masaüstü kısayolu oluşturucu
"""

import os
import sys
from pathlib import Path

def create_windows_shortcut():
    """Windows için .bat kısayolu oluştur"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Claude Session Manager.lnk")
        target = os.path.join(os.getcwd(), "start.bat")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.Description = "Claude Session Manager - Otomatik Session Yönetimi"
        shortcut.save()
        
        print(f"OK Windows kısayolu oluşturuldu: {path}")
        return True
        
    except ImportError:
        # winshell yoksa manuel .bat oluştur
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        bat_path = os.path.join(desktop, "Claude Session Manager.bat")
        
        current_dir = os.getcwd()
        bat_content = f"""@echo off
cd /d "{current_dir}"
python start.py
pause"""
        
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        print(f"OK Masaüstü kısayolu oluşturuldu: {bat_path}")
        return True
    
    except Exception as e:
        print(f"HATA Windows kısayolu oluşturulamadı: {e}")
        return False

def create_python_shortcut():
    """Python script kısayolu oluştur"""
    try:
        # Windows'ta farklı masaüstü konumlarını dene
        possible_desktops = [
            os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Masaüstü"),
            os.path.join(os.path.expanduser("~"), "Masaüstü")
        ]
        
        desktop = None
        for path in possible_desktops:
            if os.path.exists(path):
                desktop = path
                break
        
        if not desktop:
            desktop = possible_desktops[0]  # Varsayılan olarak ilkini kullan
        
        if os.name == 'nt':  # Windows
            shortcut_path = os.path.join(desktop, "Claude Session Manager.bat")
            current_dir = os.getcwd()
            
            content = f"""@echo off
title Claude Session Manager
cd /d "{current_dir}"
python start.py
if %errorlevel% neq 0 (
    echo Program hata ile sonlandi.
    pause
)"""
            
        else:  # Linux/macOS
            shortcut_path = os.path.join(desktop, "claude_session_manager.sh")
            current_dir = os.getcwd()
            
            content = f"""#!/bin/bash
cd "{current_dir}"
python3 start.py
if [ $? -ne 0 ]; then
    echo "Program hata ile sonlandı."
    read -p "Devam etmek için Enter'a basın..."
fi"""
        
        with open(shortcut_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Linux/macOS için executable yap
        if os.name != 'nt':
            os.chmod(shortcut_path, 0o755)
        
        print(f"Masaüstü kısayolu oluşturuldu: {shortcut_path}")
        return True
        
    except Exception as e:
        print(f"Kısayol oluşturulamadı: {e}")
        return False

def create_desktop_icon():
    """Windows için gelişmiş ikon oluştur"""
    try:
        # Masaüstü klasörünü bul
        possible_desktops = [
            os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Masaüstü"),
            os.path.join(os.path.expanduser("~"), "Masaüstü")
        ]
        
        desktop = None
        for path in possible_desktops:
            if os.path.exists(path):
                desktop = path
                break
        
        if not desktop:
            desktop = possible_desktops[0]
        
        # Icon dosyası oluştur (basit text-based)
        icon_content = """@echo off
title Claude Session Manager
echo.
echo  ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
echo ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
echo ██║     ██║     ███████║██║   ██║██║  ██║█████╗  
echo ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝  
echo ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
echo  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
echo.
echo        SESSION MANAGER - Yukleniyor...
echo.
timeout /t 2 >nul
""" + f'cd /d "{os.getcwd()}"\npython start.py\nif %errorlevel% neq 0 pause'
        
        icon_path = os.path.join(desktop, "Claude Session Manager.bat")
        
        with open(icon_path, 'w', encoding='utf-8') as f:
            f.write(icon_content)
        
        print(f"Özel masaüstü ikonu oluşturuldu: {icon_path}")
        return True
        
    except Exception as e:
        print(f"Özel ikon oluşturulamadı: {e}")
        return create_python_shortcut()

def main():
    print("Claude Session Manager - Masaüstü Kısayolu Oluşturucu")
    print("=" * 55)
    
    success = False
    
    if os.name == 'nt':  # Windows
        print("Windows sistemi tespit edildi...")
        
        # Önce gelişmiş kısayol dene
        try:
            success = create_desktop_icon()
        except:
            pass
        
        # Başarısız olursa basit kısayol
        if not success:
            success = create_python_shortcut()
    
    else:  # Linux/macOS
        print("Unix sistemi tespit edildi...")
        success = create_python_shortcut()
    
    print("\n" + "=" * 55)
    if success:
        print("BASARILI! BAŞARILI! Masaüstü kısayolu oluşturuldu.")
        print("\nKısayola çift tıklayarak Claude Session Manager'ı başlatabilirsiniz.")
    else:
        print("HATA! Kısayol oluşturulamadı.")
        print("\nManuel başlatma:")
        print("python start.py")
    
    print("\nDevam etmek için Enter'a basın...")
    input()

if __name__ == "__main__":
    main()