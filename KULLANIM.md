# Claude Session Manager - Hızlı Başlangıç

## Kurulum ve Başlatma

### 1. Hızlı Başlatma (Önerilen)
```bash
python start.py
```
Bu komut otomatik olarak:
- Gereksinimleri kontrol eder ve yükler
- Sistem testlerini çalıştırır
- GUI'yi başlatır

### 2. Manuel Başlatma
```bash
# Gereksinimleri yükle
pip install -r requirements.txt

# Sistemi test et
python test_system.py

# Programı başlat
python claude_session_manager.py
```

### 3. Windows Batch Dosyası
Windows'ta `start.bat` dosyasına çift tıklayarak da başlatabilirsiniz.

## İlk Kurulum Sonrası

1. **Ayarları Kontrol Edin**
   - "Ayarlar" butonuna tıklayın
   - Başlangıç saatini ayarlayın (örn: 08:00)
   - Session aralığını kontrol edin (varsayılan: 5 saat)
   - Otomatik prompt'u ayarlayın (varsayılan: "x")

2. **Sistemi Aktif Hale Getirin**
   - "Otomatik Başlat" butonuna tıklayın
   - Sistem artık belirlenen saatlerde otomatik çalışacak

3. **İlk Test**
   - "Manuel Session" butonuna tıklayarak test edin
   - Log alanından sonuçları kontrol edin

## Önemli Özellikler

### Otomatik Zamanlama
- İlk session: Belirlediğiniz saat (örn: 08:00)
- Sonraki sessionlar: Her 5 saatte bir
- Örnek: 08:00 → 13:00 → 18:00 → 23:00 → 04:00 → 09:00...

### Durum Takibi
- **Durum**: Sistem aktif/pasif
- **Son Session**: En son session zamanı
- **Sonraki Session**: Bir sonraki otomatik session
- **Kalan Süre**: Sonraki session'a kadar kalan süre
- **Session Sayısı**: Toplam session sayısı

### Manuel Kontrol
- **Otomatik Başlat/Durdur**: Otomatik sistemi aç/kapat
- **Manuel Session**: Anında yeni session başlat
- **Durum Yenile**: Anlık durumu güncelle

## Sorun Giderme

### Claude Komutu Bulunamıyor
```bash
# Claude'un kurulu olup olmadığını kontrol edin
claude --version

# PATH'e ekli olup olmadığını kontrol edin
where claude
```

### GUI Açılmıyor
```bash
# tkinter kurulu mu kontrol edin
python -m tkinter
```

### Session Başlatılamıyor
- Internet bağlantınızı kontrol edin
- Claude hesabınızın aktif olduğunu doğrulayın
- Claude Code'un güncel olduğundan emin olun

## Log Mesajları

- **[HH:MM:SS] Otomatik session başlatıldı**: Başarılı otomatik session
- **[HH:MM:SS] Manuel session başarılı: x**: Başarılı manuel session
- **[HH:MM:SS] Otomatik session hatası**: Session başlatılamadı
- **[HH:MM:SS] Otomatik session başlatıldı/durduruldu**: Sistem durumu değişti

## Dosya Yapısı

- `claude_session_manager.py`: Ana program
- `config.json`: Kullanıcı ayarları (otomatik oluşur)
- `session_data.json`: Session geçmişi (otomatik oluşur)
- `requirements.txt`: Python gereksinimleri
- `test_system.py`: Sistem test scripti
- `start.py`: Başlatma scripti

## Ayarları Özelleştirme

`config.json` dosyasını doğrudan düzenleyebilirsiniz:

```json
{
  "auto_prompt": "x",
  "session_interval_hours": 5,
  "enable_auto_session": true,
  "start_time": "08:00",
  "claude_executable": "claude"
}
```

## Güvenlik

- Sistem sadece minimal prompt gönderir
- Hiçbir hassas veri saklanmaz
- Claude Code'un kendi güvenlik önlemlerini kullanır
- Sadece session başlatma işlemi yapar

## Sistem Gereksinimleri

- Windows, macOS veya Linux
- Python 3.7+
- Claude Code kurulu ve PATH'te tanımlı
- Internet bağlantısı
- tkinter (GUI için)

Bu dokümanda yer alan tüm bilgiler ilk kullanım için yeterlidir. Detaylı bilgi için README.md dosyasını inceleyin.