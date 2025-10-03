# Claude Session Manager

Gelişmiş Claude pencere izleme ve yönetim sistemi. Bu uygulama bilgisayarınızdaki tüm Claude pencerelerini izler ve çeşitli analitik bilgiler sağlar.

## 🚀 Özellikler

### 1. 📊 Session İzleme
- Açık Claude pencerelerini otomatik tespit
- Session başlama zamanları ve süreleri
- Aktif/kapalı session durumları
- Gerçek zamanlı session listesi

### 2. 💬 Prompt Günlüğü
- Kullanıcı prompt'larını izleme ve kaydetme
- Claude yanıtlarını takip etme
- Conversation geçmişi
- Prompt filtreleme ve arama

### 3. ❓ Onay Sorusu Takibi
- Claude'un sorduğu yes/no sorularını tespit
- 1/2/3 şeklindeki seçim sorularını yakalama
- Otomatik popup uyarıları
- Onay geçmişi ve kayıtları

### 4. ⏰ Limit Uyarıları
- 5 saat limit yaklaştığında uyarı
- "Approach 5 hour limit" mesajlarını yakalama
- Limit süresi bilgilerini takip
- Sesli ve görsel uyarılar

### 5. 🎯 Token Takibi
- Token kullanım tahmini
- Günlük token limitleri
- Mesaj başına ortalama token
- Token kullanım analizi

### 6. 📈 Canlı İzleme
- Gerçek zamanlı sistem durumu
- Log akışı
- Hata ve uyarı takibi
- Sistem performans metrikleri

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