# Claude Session Manager

Claude Code için otomatik session yönetim sistemi. Bu program, Claude Code'un günlük token limitlerinden maksimum verim almak için otomatik olarak belirli aralıklarla yeni sessionlar başlatır.

## Özellikler

- **Otomatik Session Başlatma**: Belirlenen saatlerde otomatik olarak minimal prompt gönderir
- **5 Saatlik Döngü**: Varsayılan olarak her 5 saatte bir yeni session başlatır
- **GUI Arayüz**: Kolay kullanım için grafik arayüz
- **Durum Takibi**: Anlık session durumu, kalan süre ve token bilgileri
- **Özelleştirilebilir Ayarlar**: Prompt, zaman aralığı ve başlangıç saati ayarlanabilir
- **Manuel Kontrol**: İsteğe bağlı manuel session başlatma

## Kurulum

1. Python 3.7+ yüklü olduğundan emin olun
2. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

3. Claude Code'un sisteminizde kurulu ve çalışır durumda olduğundan emin olun

## Kullanım

### GUI ile Başlatma
```bash
python claude_session_manager.py
```

### Ana Özellikler

#### Otomatik Session Sistemi
- Belirlediğiniz saatte ilk session başlar
- Her 5 saatte bir otomatik olarak yeni session açar
- Sistem arka planda çalışır ve belirlenen saatlerde minimal prompt gönderir

#### Zamanlama Mantığı
Örnek senaryo:
- İlk başlangıç: 08:00
- Sonraki sessionlar: 13:00, 18:00, 23:00, 04:00, 09:00...
- Her session 5 saat süreyle kullanılabilir

#### Avantajları
- Gece 2'de tokeniniz biterse, sistem sabah 5'te yeni session başlatır
- Siz sabah 8'de kalktığınızda fresh tokenlerle çalışmaya başlarsınız
- Günlük token limitlerinden maksimum verim alırsınız

### GUI Kontrolleri

- **Otomatik Başlat/Durdur**: Otomatik session sistemini açar/kapatır
- **Manuel Session**: Anında yeni session başlatır
- **Ayarlar**: Konfigürasyonu değiştirme
- **Durum Yenile**: Mevcut durumu günceller

### Ayarlar

- **Otomatik Prompt**: Session başlatmak için gönderilecek minimal mesaj (varsayılan: "x")
- **Session Aralığı**: Sessionlar arası süre (varsayılan: 5 saat)
- **Başlangıç Saati**: İlk session zamanı (varsayılan: 08:00)
- **Otomatik Session**: Sistemin otomatik çalışması

## Konfigürasyon Dosyaları

- `config.json`: Program ayarları
- `session_data.json`: Session geçmişi ve zamanlama bilgileri

## Sistem Gereksinimleri

- Python 3.7+
- Claude Code kurulu ve PATH'te tanımlı
- tkinter (genellikle Python ile birlikte gelir)
- schedule kütüphanesi

## Güvenlik Notları

- Sistem sadece minimal prompt ("x") gönderir
- Hiçbir hassas veri işlenmez veya saklanmaz
- Sadece session başlatma için kullanılır

## Sorun Giderme

### Claude komutu bulunamıyor
Claude Code'un doğru kurulduğundan ve terminal/cmd'den `claude --help` komutunun çalıştığından emin olun.

### Session başlatılamıyor
- Claude Code'un güncel olduğundan emin olun
- Internet bağlantınızı kontrol edin
- Claude hesabınızın aktif olduğunu doğrulayın

### GUI açılmıyor
tkinter kütüphanesinin kurulu olduğundan emin olun:
```bash
python -m tkinter
```

## Gelişmiş Kullanım

### Komut Satırından Test
```bash
# Manuel session test
claude --print "test"

# Sistem durumu kontrolü
python -c "from claude_session_manager import ClaudeSessionManager; print(ClaudeSessionManager().get_session_status())"
```

### Özelleştirme
`config.json` dosyasını doğrudan düzenleyerek gelişmiş ayarlar yapabilirsiniz.

## Sık Sorulan Sorular

**S: Sistem kapalıyken session zamanı gelirse ne olur?**
C: Program açıldığında kaçırılan sessionları tespit eder ve hemen yeni session başlatır.

**S: Birden fazla session aynı anda çalışır mı?**
C: Hayır, her seferinde sadece bir session aktif olur.

**S: Token sayısını takip edebilir miyim?**
C: Şu anda basic takip var, gelecek sürümlerde detaylı token takibi eklenecek.

## Lisans

Bu proje açık kaynak kodludur ve kişisel kullanım için tasarlanmıştır.