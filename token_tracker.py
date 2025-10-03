import re
import json
import datetime
import threading
import time
import os
from collections import defaultdict, deque
import tkinter as tk
from tkinter import ttk, messagebox

class TokenTracker:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.token_usage = defaultdict(list)
        self.session_tokens = {}
        self.daily_limits = {}
        
        # Token patterns - Claude'un token kullanımı hakkında verdiği bilgileri yakalamak için
        self.token_patterns = [
            r'(?i)(\d+)\s*tokens?\s*used',
            r'(?i)tokens?\s*used:?\s*(\d+)',
            r'(?i)(\d+)\s*tokens?\s*remaining',
            r'(?i)tokens?\s*remaining:?\s*(\d+)',
            r'(?i)(\d+)\s*tokens?\s*consumed',
            r'(?i)token\s*usage:?\s*(\d+)',
            r'(?i)(\d+)\s*tokens?\s*processed',
            r'(?i)total\s*tokens?:?\s*(\d+)',
        ]
        
        # Mesaj uzunluğu patterns
        self.message_patterns = [
            r'(?i)(\d+)\s*characters?',
            r'(?i)message\s*length:?\s*(\d+)',
            r'(?i)(\d+)\s*words?',
        ]
        
        # Limit patterns
        self.limit_patterns = [
            r'(?i)daily\s*limit:?\s*(\d+)',
            r'(?i)monthly\s*limit:?\s*(\d+)',
            r'(?i)usage\s*limit:?\s*(\d+)',
            r'(?i)(\d+)\s*requests?\s*per\s*day',
        ]
        
        self.token_estimates = deque(maxlen=1000)  # Son 1000 mesaj için token tahmini
        self.create_token_ui()
        
    def create_token_ui(self):
        """Token tracking UI'si"""
        self.token_window = None
        
    def show_token_dashboard(self):
        """Token dashboard'unu göster"""
        if self.token_window and self.token_window.winfo_exists():
            self.token_window.lift()
            return
        
        self.token_window = tk.Toplevel()
        self.token_window.title("Token & Usage Tracker")
        self.token_window.geometry("900x700")
        
        # Ana notebook
        notebook = ttk.Notebook(self.token_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Session Token Usage
        session_frame = ttk.Frame(notebook)
        notebook.add(session_frame, text="Session Token Kullanımı")
        self.create_session_token_ui(session_frame)
        
        # Daily Limits
        daily_frame = ttk.Frame(notebook)
        notebook.add(daily_frame, text="Günlük Limitler")
        self.create_daily_limits_ui(daily_frame)
        
        # Token Estimator
        estimator_frame = ttk.Frame(notebook)
        notebook.add(estimator_frame, text="Token Tahmini")
        self.create_token_estimator_ui(estimator_frame)
        
        # Usage Analytics
        analytics_frame = ttk.Frame(notebook)
        notebook.add(analytics_frame, text="Kullanım Analizi")
        self.create_usage_analytics_ui(analytics_frame)
        
        self.update_token_dashboard()
    
    def create_session_token_ui(self, parent):
        """Session token kullanımı UI'si"""
        # Session token listesi
        self.session_token_tree = ttk.Treeview(parent, 
                                              columns=("tokens_used", "messages", "avg_tokens", "status"), 
                                              show="tree headings")
        self.session_token_tree.heading("#0", text="Session ID")
        self.session_token_tree.heading("tokens_used", text="Kullanılan Token")
        self.session_token_tree.heading("messages", text="Mesaj Sayısı")
        self.session_token_tree.heading("avg_tokens", text="Ort. Token/Mesaj")
        self.session_token_tree.heading("status", text="Durum")
        
        self.session_token_tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Token istatistikleri
        stats_frame = ttk.LabelFrame(parent, text="Token İstatistikleri", padding="10")
        stats_frame.pack(fill="x")
        
        self.token_stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        self.token_stats_text.pack(fill="x")
    
    def create_daily_limits_ui(self, parent):
        """Günlük limitler UI'si"""
        # Günlük kullanım özeti
        summary_frame = ttk.LabelFrame(parent, text="Günlük Özet", padding="10")
        summary_frame.pack(fill="x", pady=(0, 10))
        
        self.daily_summary_text = tk.Text(summary_frame, height=6, wrap=tk.WORD)
        self.daily_summary_text.pack(fill="x")
        
        # Limit uyarıları
        limits_frame = ttk.LabelFrame(parent, text="Limit Uyarıları", padding="5")
        limits_frame.pack(fill="both", expand=True)
        
        self.limits_tree = ttk.Treeview(limits_frame, 
                                       columns=("date", "type", "current", "limit", "percentage"), 
                                       show="headings")
        self.limits_tree.heading("date", text="Tarih")
        self.limits_tree.heading("type", text="Tip")
        self.limits_tree.heading("current", text="Mevcut")
        self.limits_tree.heading("limit", text="Limit")
        self.limits_tree.heading("percentage", text="%")
        
        self.limits_tree.pack(fill="both", expand=True)
    
    def create_token_estimator_ui(self, parent):
        """Token tahmini UI'si"""
        # Metin girişi
        input_frame = ttk.LabelFrame(parent, text="Token Tahmini", padding="10")
        input_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(input_frame, text="Metni yapıştırın:").pack(anchor="w")
        
        self.estimate_text = tk.Text(input_frame, height=6, wrap=tk.WORD)
        self.estimate_text.pack(fill="x", pady=(5, 10))
        
        estimate_btn_frame = ttk.Frame(input_frame)
        estimate_btn_frame.pack(fill="x")
        
        ttk.Button(estimate_btn_frame, text="Token Tahmin Et", 
                  command=self.estimate_tokens).pack(side="left", padx=(0, 10))
        ttk.Button(estimate_btn_frame, text="Temizle", 
                  command=lambda: self.estimate_text.delete(1.0, tk.END)).pack(side="left")
        
        # Sonuçlar
        results_frame = ttk.LabelFrame(parent, text="Tahmin Sonuçları", padding="10")
        results_frame.pack(fill="both", expand=True)
        
        self.estimate_results = tk.Text(results_frame, wrap=tk.WORD)
        self.estimate_results.pack(fill="both", expand=True)
    
    def create_usage_analytics_ui(self, parent):
        """Kullanım analizi UI'si"""
        # Analiz kontrolleri
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(control_frame, text="Analiz Periyodu:").pack(side="left")
        
        self.analysis_period = tk.StringVar(value="bugün")
        period_combo = ttk.Combobox(control_frame, textvariable=self.analysis_period,
                                   values=["bugün", "bu hafta", "bu ay", "tümü"])
        period_combo.pack(side="left", padx=(5, 10))
        
        ttk.Button(control_frame, text="Analiz Et", 
                  command=self.analyze_usage).pack(side="left")
        
        # Analiz sonuçları
        self.analytics_text = tk.Text(parent, wrap=tk.WORD)
        analytics_scrollbar = ttk.Scrollbar(parent, orient="vertical", 
                                           command=self.analytics_text.yview)
        self.analytics_text.configure(yscrollcommand=analytics_scrollbar.set)
        
        self.analytics_text.pack(side="left", fill="both", expand=True)
        analytics_scrollbar.pack(side="right", fill="y")
    
    def track_token_usage(self, session_id, text, message_type):
        """Token kullanımını takip et"""
        # Explicit token bilgisi varsa yakala
        explicit_tokens = self.extract_explicit_tokens(text)
        
        # Token tahmini yap
        estimated_tokens = self.estimate_tokens_from_text(text)
        
        timestamp = datetime.datetime.now()
        
        token_entry = {
            'timestamp': timestamp.isoformat(),
            'session_id': session_id,
            'message_type': message_type,
            'text_length': len(text),
            'word_count': len(text.split()),
            'estimated_tokens': estimated_tokens,
            'explicit_tokens': explicit_tokens,
            'text_preview': text[:100] + "..." if len(text) > 100 else text
        }
        
        # Session token'larını güncelle
        if session_id not in self.session_tokens:
            self.session_tokens[session_id] = {
                'total_estimated': 0,
                'total_explicit': 0,
                'message_count': 0,
                'start_time': timestamp,
                'last_activity': timestamp,
                'entries': []
            }
        
        session_data = self.session_tokens[session_id]
        session_data['total_estimated'] += estimated_tokens
        if explicit_tokens:
            session_data['total_explicit'] += explicit_tokens
        session_data['message_count'] += 1
        session_data['last_activity'] = timestamp
        session_data['entries'].append(token_entry)
        
        # Günlük kullanım güncelle
        today = timestamp.strftime('%Y-%m-%d')
        if today not in self.daily_limits:
            self.daily_limits[today] = {
                'estimated_tokens': 0,
                'explicit_tokens': 0,
                'message_count': 0,
                'sessions': set()
            }
        
        daily_data = self.daily_limits[today]
        daily_data['estimated_tokens'] += estimated_tokens
        if explicit_tokens:
            daily_data['explicit_tokens'] += explicit_tokens
        daily_data['message_count'] += 1
        daily_data['sessions'].add(session_id)
        
        # Token estimate buffer'a ekle
        self.token_estimates.append(token_entry)
        
        # Dosyaya kaydet
        self.save_token_data(token_entry)
        
        return token_entry
    
    def extract_explicit_tokens(self, text):
        """Claude'un verdiği explicit token bilgilerini çıkar"""
        for pattern in self.token_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except (ValueError, IndexError):
                    continue
        return None
    
    def estimate_tokens_from_text(self, text):
        """Metinden token tahmini yap"""
        # Basit tahmin: 
        # - Ortalama 4 karakter = 1 token
        # - Özel karakterler ve boşluklar dikkate alınır
        
        # Kelime sayısı bazlı tahmin
        words = text.split()
        word_based_estimate = len(words) * 1.3  # Ortalama 1.3 token per word
        
        # Karakter sayısı bazlı tahmin
        char_based_estimate = len(text) / 4  # 4 char per token
        
        # İki tahminin ortalaması
        estimated_tokens = int((word_based_estimate + char_based_estimate) / 2)
        
        return max(1, estimated_tokens)  # En az 1 token
    
    def estimate_tokens(self):
        """UI'den token tahmini yap"""
        text = self.estimate_text.get(1.0, tk.END).strip()
        if not text:
            return
        
        estimated = self.estimate_tokens_from_text(text)
        char_count = len(text)
        word_count = len(text.split())
        
        results = f"""📊 TOKEN TAHMİNİ SONUÇLARI
{'='*40}

📝 METİN İSTATİSTİKLERİ:
• Karakter Sayısı: {char_count:,}
• Kelime Sayısı: {word_count:,}
• Satır Sayısı: {text.count(chr(10)) + 1}

🎯 TOKEN TAHMİNLERİ:
• Tahmini Token: {estimated:,}
• Kelime Bazlı: {int(word_count * 1.3):,}
• Karakter Bazlı: {int(char_count / 4):,}

💰 MALİYET TAHMİNİ (yaklaşık):
• GPT-4 Input: ${estimated * 0.00003:.4f}
• GPT-4 Output: ${estimated * 0.00006:.4f}

⚠️  NOT: Bu tahminler yaklaşıktır. Gerçek token 
kullanımı model ve içeriğe göre değişebilir."""
        
        self.estimate_results.delete(1.0, tk.END)
        self.estimate_results.insert(1.0, results)
    
    def analyze_usage(self):
        """Kullanım analizi yap"""
        period = self.analysis_period.get()
        current_time = datetime.datetime.now()
        
        # Periyot hesapla
        if period == "bugün":
            start_date = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "bu hafta":
            days_since_monday = current_time.weekday()
            start_date = current_time - datetime.timedelta(days=days_since_monday)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "bu ay":
            start_date = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # tümü
            start_date = datetime.datetime.min
        
        # Veri filtrele
        relevant_entries = []
        for session_data in self.session_tokens.values():
            for entry in session_data['entries']:
                entry_time = datetime.datetime.fromisoformat(entry['timestamp'])
                if entry_time >= start_date:
                    relevant_entries.append(entry)
        
        if not relevant_entries:
            self.analytics_text.delete(1.0, tk.END)
            self.analytics_text.insert(1.0, "Seçilen periyot için veri bulunamadı.")
            return
        
        # Analiz yap
        total_estimated = sum(e['estimated_tokens'] for e in relevant_entries)
        total_explicit = sum(e['explicit_tokens'] for e in relevant_entries if e['explicit_tokens'])
        total_messages = len(relevant_entries)
        unique_sessions = len(set(e['session_id'] for e in relevant_entries))
        
        avg_tokens_per_message = total_estimated / total_messages if total_messages > 0 else 0
        
        # Mesaj tipi analizi
        message_types = defaultdict(int)
        for entry in relevant_entries:
            message_types[entry['message_type']] += 1
        
        # En aktif session'lar
        session_usage = defaultdict(int)
        for entry in relevant_entries:
            session_usage[entry['session_id']] += entry['estimated_tokens']
        
        top_sessions = sorted(session_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        analysis_result = f"""📈 KULLANIM ANALİZİ - {period.upper()}
{'='*50}

📊 GENEL İSTATİSTİKLER:
• Toplam Mesaj: {total_messages:,}
• Unique Session: {unique_sessions}
• Tahmini Token: {total_estimated:,}
• Explicit Token: {total_explicit:,} ({total_explicit/total_estimated*100 if total_estimated > 0 else 0:.1f}%)
• Ort. Token/Mesaj: {avg_tokens_per_message:.1f}

📝 MESAJ TİPİ DAĞILIMI:
"""
        
        for msg_type, count in message_types.items():
            percentage = count / total_messages * 100 if total_messages > 0 else 0
            analysis_result += f"• {msg_type}: {count:,} (%{percentage:.1f})\n"
        
        analysis_result += f"""
🏆 EN AKTİF SESSION'LAR:
"""
        
        for i, (session_id, tokens) in enumerate(top_sessions, 1):
            analysis_result += f"{i}. {session_id}: {tokens:,} token\n"
        
        # Günlük trend
        daily_usage = defaultdict(int)
        for entry in relevant_entries:
            date = datetime.datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d')
            daily_usage[date] += entry['estimated_tokens']
        
        if len(daily_usage) > 1:
            analysis_result += f"""
📅 GÜNLİK TREND:
"""
            for date in sorted(daily_usage.keys())[-7:]:  # Son 7 gün
                analysis_result += f"• {date}: {daily_usage[date]:,} token\n"
        
        self.analytics_text.delete(1.0, tk.END)
        self.analytics_text.insert(1.0, analysis_result)
    
    def check_daily_limits(self):
        """Günlük limitleri kontrol et"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if today not in self.daily_limits:
            return
        
        daily_data = self.daily_limits[today]
        estimated_tokens = daily_data['estimated_tokens']
        
        # Varsayılan günlük limitler (tahmin)
        WARNING_THRESHOLD = 50000  # 50K token
        CRITICAL_THRESHOLD = 80000  # 80K token
        
        if estimated_tokens > CRITICAL_THRESHOLD:
            self.main_monitor.add_alert('token_critical', 
                                      f"CRITICAL: Günlük token kullanımı {estimated_tokens:,} (Limit: {CRITICAL_THRESHOLD:,})")
        elif estimated_tokens > WARNING_THRESHOLD:
            self.main_monitor.add_alert('token_warning', 
                                      f"WARNING: Günlük token kullanımı {estimated_tokens:,} (Uyarı: {WARNING_THRESHOLD:,})")
    
    def save_token_data(self, token_entry):
        """Token verisini dosyaya kaydet"""
        date = datetime.datetime.now().strftime('%Y%m%d')
        token_file = f"claude_session_data/tokens/token_usage_{date}.json"
        
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
        
        with open(token_file, 'a', encoding='utf-8') as f:
            json.dump(token_entry, f, ensure_ascii=False)
            f.write('\n')
    
    def load_token_data(self):
        """Token verilerini yükle"""
        token_dir = "claude_session_data/tokens"
        if not os.path.exists(token_dir):
            return
        
        for filename in os.listdir(token_dir):
            if filename.startswith('token_usage_') and filename.endswith('.json'):
                file_path = os.path.join(token_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                entry = json.loads(line)
                                # Restore session data
                                session_id = entry['session_id']
                                if session_id not in self.session_tokens:
                                    self.session_tokens[session_id] = {
                                        'total_estimated': 0,
                                        'total_explicit': 0,
                                        'message_count': 0,
                                        'entries': []
                                    }
                                
                                self.session_tokens[session_id]['entries'].append(entry)
                                self.token_estimates.append(entry)
                except Exception as e:
                    print(f"Token data load error: {e}")
    
    def update_token_dashboard(self):
        """Token dashboard'unu güncelle"""
        if not self.token_window or not self.token_window.winfo_exists():
            return
        
        # Session token tree güncelle
        for item in self.session_token_tree.get_children():
            self.session_token_tree.delete(item)
        
        for session_id, session_data in self.session_tokens.items():
            total_tokens = session_data['total_estimated']
            message_count = session_data['message_count']
            avg_tokens = total_tokens / message_count if message_count > 0 else 0
            
            # Session durumu
            status = "Aktif" if session_id in [s for s in self.main_monitor.sessions.keys() 
                                             if self.main_monitor.sessions[s]['status'] == 'active'] else "Kapalı"
            
            self.session_token_tree.insert('', 'end',
                                          text=session_id,
                                          values=(f"{total_tokens:,}",
                                                 message_count,
                                                 f"{avg_tokens:.1f}",
                                                 status))
        
        # Token istatistikleri güncelle
        total_estimated = sum(data['total_estimated'] for data in self.session_tokens.values())
        total_messages = sum(data['message_count'] for data in self.session_tokens.values())
        total_sessions = len(self.session_tokens)
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_data = self.daily_limits.get(today, {'estimated_tokens': 0, 'message_count': 0})
        
        stats_text = f"""🎯 TOKEN İSTATİSTİKLERİ
{'='*30}

📊 TOPLAM:
• Sessions: {total_sessions}
• Mesajlar: {total_messages:,}
• Tahmini Token: {total_estimated:,}

📅 BUGÜN:
• Mesajlar: {today_data['message_count']:,}
• Tahmini Token: {today_data['estimated_tokens']:,}

📈 ORTALAMALAR:
• Token/Session: {total_estimated/total_sessions if total_sessions > 0 else 0:.1f}
• Token/Mesaj: {total_estimated/total_messages if total_messages > 0 else 0:.1f}

🕐 Son Güncelleme: {datetime.datetime.now().strftime('%H:%M:%S')}"""
        
        self.token_stats_text.delete(1.0, tk.END)
        self.token_stats_text.insert(1.0, stats_text)
        
        # Günlük limitler kontrol et
        self.check_daily_limits()
        
        # 10 saniye sonra tekrar güncelle
        self.token_window.after(10000, self.update_token_dashboard)
    
    def start_monitoring(self):
        """Token monitoring'i başlat"""
        # Load existing data
        self.load_token_data()
        
        # Her dakika limit kontrolü yap
        def limit_check_loop():
            while True:
                self.check_daily_limits()
                time.sleep(60)  # 1 dakika
        
        limit_thread = threading.Thread(target=limit_check_loop, daemon=True)
        limit_thread.start()

if __name__ == "__main__":
    # Test için
    class MockMonitor:
        def __init__(self):
            self.sessions = {}
        
        def add_alert(self, alert_type, message, session_id=None):
            print(f"Alert: {alert_type} - {message}")
    
    mock_monitor = MockMonitor()
    tracker = TokenTracker(mock_monitor)
    
    # Test data
    test_text = "Bu bir test mesajıdır. Token tahmini için kullanılacaktır. Claude'un verdiği yanıtları takip etmek için kullanıyoruz."
    tracker.track_token_usage("test_session", test_text, "user_prompt")
    
    tracker.show_token_dashboard()
    tracker.start_monitoring()
    
    # Ana loop
    root = tk.Tk()
    root.withdraw()
    root.mainloop()