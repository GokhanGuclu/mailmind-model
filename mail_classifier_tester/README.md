# Mail Classifier Tester

Bu klasör, MailMind modelini test etmek için kullanılan araçları içerir. Gemini API ile test maili oluşturma ve MailHog üzerinden mail kategorizasyonu yapma özelliklerini sağlar.

## Gereksinimler

1. **MailHog**: Mail test ortamı için
   - İndirme: https://github.com/mailhog/MailHog
   - Veya Docker ile: `docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog`

2. **Gemini API Key**: Google Gemini API anahtarı
   - Alma: https://makersuite.google.com/app/apikey
   - `.env` dosyasına eklenmeli

## Kurulum

1. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyası oluşturun (proje kök dizininde):
```env
GEMINI_API_KEY=your_gemini_api_key_here
MAILHOG_SMTP_HOST=localhost
MAILHOG_SMTP_PORT=1025
```

3. MailHog'u başlatın:
```bash
# Windows/Mac/Linux - İndirilen dosyayı çalıştırın
# Veya Docker ile:
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

## Kullanım

### 1. Test Maili Oluşturma (Tek Seferlik)

Gemini API kullanarak test maili oluşturur ve MailHog'a gönderir:

```bash
# Rastgele kategori ile
python mail_classifier_tester/mail_olusturucu.py

# Belirli bir kategori ile
python mail_classifier_tester/mail_olusturucu.py --kategori "Pazarlama"
```

**Desteklenen Kategoriler:**
- İş/Acil
- Güvenlik/Uyarı
- Pazarlama
- Sosyal Medya
- Spam
- Abonelik/Fatura
- Kişisel
- Eğitim/Öğretim
- Sağlık
- Diğer

### 2. Mail İzleyici (Sürekli Çalışan)

MailHog'u dinler ve yeni mail geldiğinde modeli kullanarak kategorize eder:

```bash
# Varsayılan ayarlarla (localhost:8025, 2 saniye aralık)
python mail_classifier_tester/mail_izleyici.py

# Özel ayarlarla
python mail_classifier_tester/mail_izleyici.py --host localhost --port 8025 --aralik 3
```

**Özellikler:**
- MailHog'u sürekli dinler
- Yeni mail geldiğinde otomatik kategorize eder
- Sonuçları ekrana yazdırır
- Sonuçları `sonuclar.jsonl` dosyasına kaydeder

### Çalışma Senaryosu

1. **Terminal 1**: Mail izleyiciyi başlatın:
```bash
python mail_classifier_tester/mail_izleyici.py
```

2. **Terminal 2**: Test maili oluşturun:
```bash
python mail_classifier_tester/mail_olusturucu.py
```

3. Mail izleyici otomatik olarak yeni maili tespit eder, kategorize eder ve sonuçları gösterir.

## MailHog Web Arayüzü

MailHog'un web arayüzüne şu adresten erişebilirsiniz:
- http://localhost:8025

Buradan gönderilen mailleri görüntüleyebilir ve kontrol edebilirsiniz.

## Sonuçlar

Kategorizasyon sonuçları `mail_classifier_tester/sonuclar.jsonl` dosyasına kaydedilir. Her satır bir JSON objesi içerir:

```json
{
  "zaman": "2024-01-01T12:00:00",
  "mail_id": "mailhog_id",
  "baslik": "Mail başlığı",
  "icerik": "Mail içeriği...",
  "tahmin": "Pazarlama",
  "olasiliklar": {
    "Pazarlama": 0.85,
    "İş/Acil": 0.10,
    "Diğer": 0.05
  }
}
```

## Sorun Giderme

### MailHog'a bağlanılamıyor
- MailHog'un çalıştığından emin olun
- Port 8025'in açık olduğunu kontrol edin
- `--host` ve `--port` parametrelerini kontrol edin

### Gemini API hatası
- `.env` dosyasında `GEMINI_API_KEY` tanımlı olduğundan emin olun
- API anahtarının geçerli olduğunu kontrol edin
- İnternet bağlantınızı kontrol edin

### Model yüklenemiyor
- Modelin eğitilmiş olduğundan emin olun (`python mail_classifier_advanced.py`)
- `model/` klasöründe gerekli dosyaların bulunduğunu kontrol edin

