import os
import csv
import pandas as pd
import google.generativeai as genai
from datetime import datetime, date
import random
import time
import re
import json
from dotenv import load_dotenv
import argparse

# .env dosyasından environment variables'ları yükle
load_dotenv()

# Gemini API Key'i .env dosyasından veya environment variable'dan al
API_KEY = os.getenv('GEMINI_API_KEY')

# Kategoriler
KATEGORILER = [
    "İş/Acil",
    "Güvenlik/Uyarı",
    "Pazarlama",
    "Sosyal Medya",
    "Spam",
    "Abonelik/Fatura",
    "Kişisel",
    "Eğitim/Öğretim",
    "Sağlık",
    "Diğer"

]

# CSV dosya adı
CSV_DOSYASI = "mailler.csv"
# Günlük istek sayacı dosyası
RPD_DOSYASI = "rpd_counter.json"
# Günlük maksimum istek limiti (Peak Requests Per Day) - varsayılan 1500
MAX_DAILY_REQUESTS = 1500
# Her kategoride hedeflenen mail sayısı (min-max)
HEDEF_MIN = 2000
HEDEF_MAX = 2000
# Her çalıştırmada bir kategoriden üretilecek mail sayısı
BATCH_SIZE = 100

# Farklı prompt varyasyonları (her çalıştırmada farklı konulardan mail üretmek için)
PROMPT_TEMPLATES = [
    "günlük iş rutinleri",
    "önemli duyurular",
    "acil durum bildirimleri",
    "özelleştirilmiş içerikler",
    "profesyonel yazışmalar",
    "kişisel mesajlaşma",
    "türlü senaryolar",
    "farklı durumlar",
    "çeşitli bağlamlar",
    "değişik konular"
]

"""
KARIŞTIRMA (CONFUSION) ODAKLI VERİ ÜRETİMİ

Modelin karıştırdığı kategori çiftleri için veriyi daha ayırt edici yapmak üzere:
- Bazı kelimeleri "mutlaka kullan" (pozitif sinyal)
- Bazı kelimeleri "asla kullanma" (negatif sinyal / karışma önleme)

Not: Bu kurallar verinin sınıflar arası örtüşmesini azaltmak için tasarlanmıştır.
"""

# En çok karışan kategori çiftleri (eğitim çıktısındaki örnek listeye göre)
CONFUSION_PAIRS = [
    ("Sosyal Medya", "Güvenlik/Uyarı"),
    ("Kişisel", "İş/Acil"),
    ("Pazarlama", "Abonelik/Fatura"),
    ("Diğer", "Kişisel"),
    ("Eğitim/Öğretim", "Diğer"),
    ("Güvenlik/Uyarı", "İş/Acil"),
    ("Abonelik/Fatura", "Pazarlama"),
    ("Kişisel", "Diğer"),
    ("Sağlık", "Diğer"),
    ("Spam", "Pazarlama"),
]

# Kategori bazlı pozitif/negatif ipuçları
CATEGORY_HINTS = {
    "Sosyal Medya": {
        "must_include_any": [
            "instagram", "linkedin", "facebook", "tiktok", "twitter", "x",
            "beğeni", "yorum", "takip", "mesaj", "bildirim", "etkileşim", "hikaye"
        ],
        "must_avoid_any": [
            "şifre", "doğrulama", "güvenlik", "şüpheli giriş", "hesabınız", "otp", "kod",
            "oturum", "kilitlendi", "kimlik doğrulama"
        ],
    },
    "Güvenlik/Uyarı": {
        "must_include_any": [
            "şüpheli", "giriş", "doğrulama", "şifre", "güvenlik", "kod", "otp",
            "hesabınız", "oturum", "kilit", "koruma"
        ],
        "must_avoid_any": [
            "takip etti", "beğendi", "yorum yaptı", "instagram", "linkedin", "facebook", "tiktok",
            "kampanya", "indirim", "kupon"
        ],
    },
    "Pazarlama": {
        "must_include_any": [
            "kampanya", "indirim", "fırsat", "kupon", "sepette", "son gün", "%", "hediye", "çek"
        ],
        "must_avoid_any": [
            "fatura", "ödeme", "abonelik", "yenileme", "tahsilat", "son ödeme", "dekont", "tutar"
        ],
    },
    "Abonelik/Fatura": {
        "must_include_any": [
            "fatura", "ödeme", "abonelik", "yenileme", "tutar", "son ödeme", "işlem", "dekont"
        ],
        "must_avoid_any": [
            "kupon", "kampanya", "flash sale", "kaçırma", "sepete ekle", "hediye çek"
        ],
    },
    "Kişisel": {
        "must_include_any": [
            "nasılsın", "görüşürüz", "özledim", "selam", "akşam", "hafta sonu", "buluşalım"
        ],
        "must_avoid_any": [
            "toplantı", "deadline", "müşteri", "rapor", "proje", "acil görev", "saygılarımla"
        ],
    },
    "İş/Acil": {
        "must_include_any": [
            "toplantı", "acil", "proje", "müşteri", "rapor", "deadline", "aksiyon", "güncelleme"
        ],
        "must_avoid_any": [
            "özledim", "buluşalım", "canım", "hadi", "hafta sonu", "kanka"
        ],
    },
    "Eğitim/Öğretim": {
        "must_include_any": [
            "ödev", "sınav", "ders", "not", "program", "kayıt", "öğrenci", "öğretmen", "akademik"
        ],
        "must_avoid_any": [
            "kampanya", "kupon", "satın al", "sepete", "indirim"
        ],
    },
    "Sağlık": {
        "must_include_any": [
            "randevu", "muayene", "test sonucu", "tetkik", "doktor", "hastane", "reçete", "tahlil"
        ],
        "must_avoid_any": [
            "kampanya", "kupon", "takip etti", "beğendi", "fatura numarası"
        ],
    },
    "Spam": {
        "must_include_any": [
            "kazandınız", "hemen tıkla", "acil", "son uyarı", "bedava", "ödül", "şanslı"
        ],
        "must_avoid_any": [
            "saygılarımla", "resmi", "dekont", "randevu onayı"
        ],
    },
    "Diğer": {
        "must_include_any": [
            "etkinlik", "duyuru", "hobi", "bülten", "gönüllü", "topluluk", "atölye", "kulüp"
        ],
        "must_avoid_any": [
            "ödev", "sınav", "fatura", "ödeme", "kupon", "kampanya", "şifre sıfırla"
        ],
    },
}


def build_karsima_kurallari(kategori: str) -> str:
    """Kategori için karışma önleyici kuralları prompt'a ekle."""
    hints = CATEGORY_HINTS.get(kategori, {})
    must_include = hints.get("must_include_any", [])
    must_avoid = hints.get("must_avoid_any", [])

    # Bu kategori hangi kategorilerle daha çok karışıyor?
    confusing_with = []
    for a, b in CONFUSION_PAIRS:
        if a == kategori:
            confusing_with.append(b)
        elif b == kategori:
            confusing_with.append(a)

    lines = []
    if confusing_with:
        lines.append("KARIŞMA ÖNLEME: Aşağıdaki kategorilerle karışmamalı: " + ", ".join(confusing_with))
    if must_include:
        # Model sinyalini güçlendirmek için: "en az 2 tanesi geçsin"
        lines.append("MUTLAKA: Aşağıdaki ifadelerden EN AZ 2 tanesi metinde geçsin: " + ", ".join(must_include))
    if must_avoid:
        lines.append("ASLA: Aşağıdaki ifadeleri kullanma (bu kelimeler başka kategori çağrıştırır): " + ", ".join(must_avoid))

    if not lines:
        return ""
    return "\n" + "\n".join(f"- {ln}" for ln in lines) + "\n"


def _parse_args():
    p = argparse.ArgumentParser(description="Gemini API Mail Üretici")
    p.add_argument("--hard-mode", action="store_true", help="Karışma önleyici kuralları prompt'a ekle")
    p.add_argument(
        "--focus-confusions",
        action="store_true",
        help="Karışması muhtemel kategorileri önceliklendir (confusion pairs içinden)",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Her turda üretilecek mail sayısı (varsayılan: BATCH_SIZE)",
    )
    return p.parse_args()


def gemini_api_baslat(api_key):
    """Gemini API'yi başlat"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    return model


def rpd_kontrol_et():
    """Günlük istek sayacını kontrol et ve gerekirse sıfırla"""
    bugun = str(date.today())
    
    if os.path.exists(RPD_DOSYASI):
        with open(RPD_DOSYASI, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Eğer farklı bir gündeyse sayacı sıfırla
                if data.get('tarih') != bugun:
                    data = {'tarih': bugun, 'istek_sayisi': 0}
                    with open(RPD_DOSYASI, 'w', encoding='utf-8') as f_write:
                        json.dump(data, f_write, indent=2, ensure_ascii=False)
                return data
            except json.JSONDecodeError:
                # Dosya bozuksa sıfırla
                data = {'tarih': bugun, 'istek_sayisi': 0}
                with open(RPD_DOSYASI, 'w', encoding='utf-8') as f_write:
                    json.dump(data, f_write, indent=2, ensure_ascii=False)
                return data
    else:
        # Yeni dosya oluştur
        data = {'tarih': bugun, 'istek_sayisi': 0}
        with open(RPD_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data


def rpd_artir():
    """Günlük istek sayacını 1 artır"""
    data = rpd_kontrol_et()
    data['istek_sayisi'] += 1
    with open(RPD_DOSYASI, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data['istek_sayisi']


def rpd_limit_kontrol():
    """Günlük istek limiti kontrolü"""
    data = rpd_kontrol_et()
    mevcut = data['istek_sayisi']
    return mevcut, mevcut >= MAX_DAILY_REQUESTS


def csv_kontrol_et():
    """CSV dosyasını kontrol et, yoksa oluştur, varsa mevcut verileri oku"""
    if os.path.exists(CSV_DOSYASI):
        df = pd.read_csv(CSV_DOSYASI)
        return df
    else:
        # Yeni CSV oluştur
        df = pd.DataFrame(columns=['Kategori', 'Başlık', 'İçerik', 'Tarih'])
        df.to_csv(CSV_DOSYASI, index=False, encoding='utf-8-sig')
        return df


def kategori_istatistikleri(df):
    """Her kategoride kaç mail olduğunu hesapla"""
    if df.empty:
        return {kategori: 0 for kategori in KATEGORILER}
    
    istatistik = {}
    for kategori in KATEGORILER:
        sayi = len(df[df['Kategori'] == kategori])
        istatistik[kategori] = sayi
    
    return istatistik


def hangi_kategoriler_gerekli(istatistik):
    """Hangi kategorilerde daha fazla mail gerektiğini belirle"""
    gerekli_kategoriler = []
    
    for kategori in KATEGORILER:
        mevcut_sayi = istatistik[kategori]
        # Eğer hedef minimum sayıya ulaşmadıysa gerekli
        if mevcut_sayi < HEDEF_MIN:
            gerekli_kategoriler.append({
                'kategori': kategori,
                'mevcut': mevcut_sayi,
                'gerekli': HEDEF_MIN - mevcut_sayi
            })
    
    # Eğer tüm kategoriler minimum sayıya ulaştıysa, maksimuma ulaşmayanları seç
    if not gerekli_kategoriler:
        for kategori in KATEGORILER:
            mevcut_sayi = istatistik[kategori]
            if mevcut_sayi < HEDEF_MAX:
                gerekli_kategoriler.append({
                    'kategori': kategori,
                    'mevcut': mevcut_sayi,
                    'gerekli': min(BATCH_SIZE, HEDEF_MAX - mevcut_sayi)
                })
    
    return gerekli_kategoriler


def mail_uret(model, kategori, sayi, varyasyon_indeksi, max_retries=3, hard_mode=False):
    """Gemini API'den belirli bir kategori için mail üret (retry mekanizması ile)"""
    
    # Her çalıştırmada farklı prompt varyasyonu kullan
    varyasyon = PROMPT_TEMPLATES[varyasyon_indeksi % len(PROMPT_TEMPLATES)]
    
    # Kategoriye özel detaylı açıklamalar (makine öğrenmesi için istikrar artırıcı)
    KATEGORI_DETAYLARI = {
        "İş/Acil": """
KATEGORİ DETAYI: Profesyonel iş ortamında gerçekleşen acil veya önemli konular.
İÇERİK KURALLARI:
- İş dünyası terminolojisi kullan (toplantı, rapor, müşteri, proje, deadline, vs.)
- Acil durumlar veya önemli iş konuları olsun
- Saygılı ve profesyonel dil kullan
- Tarih, saat, yer bilgileri içerebilir
- E-posta imzası içerir ("Saygılarımla", "İyi çalışmalar" vs.)
ÖRNEKLER: Toplantı davetleri, acil görev atamaları, müşteri şikayetleri, proje güncellemeleri
DİKKAT: Kişisel veya sosyal içerikli değil, iş hayatı merkezli olmalı""",

        "Güvenlik/Uyarı": """
KATEGORİ DETAYI: Güvenlik tehditleri, hesap uyarıları, sistem bildirimleri.
İÇERİK KURALLARI:
- Hesap güvenliği, veri koruma, şifre değişikliği vurgusu
- İşlem onayı isteği, şüpheli etkinlik uyarısı
- Önemli güvenlik bilgileri aktarımı
- Net ve anlaşılır dil kullan
ÖRNEKLER: Şifre sıfırlama istekleri, yeni giriş uyarıları, güvenlik güncellemeleri, şüpheli etkinlik bildirimleri
DİKKAT: Kompleks içerik değil, basit ve yönlendirici olmalı""",

        "Pazarlama": """
KATEGORİ DETAYI: Ürün tanıtımları, kampanyalar, özel indirimler, reklamlar.
İÇERİK KURALLARI:
- Çekici başlıklar, indirim oranları, kampanya vurgusu
- Alışveriş çağrısı (CTA: Call to Action)
- Ürün/hizmet özellikleri anlatımı
- Aciliyet hissi ("Son günler!", "Kaçırma!" vs.)
ÖRNEKLER: Flash sale duyuruları, yeni ürün lansmanları, özel fırsatlar, kupon kodları
DİKKAT: Gerçek pazarlama stratejilerine uygun, alıcıyı ikna edici olmalı""",

        "Sosyal Medya": """
KATEGORİ DETAYI: Sosyal medya platformlarından gelen bildirimler ve etkileşimler.
İÇERİK KURALLARI:
- Platform isimleri kullan (Instagram, LinkedIn, Facebook, Twitter, X, TikTok)
- Beğeni, yorum, mesaj, takip bildirimleri
- Günlük dil, samimi ton
- Emoji veya sosyal medya jargonu kullanılabilir
ÖRNEKLER: Yeni beğeni bildirimleri, mesaj hatırlatmaları, arkadaş istekleri, etkileşim özetleri
DİKKAT: Sosyal medya üslubunda, resmiyetten uzak olmalı""",

        "Spam": """
KATEGORİ DETAYI: İstenmeyen, şüpheli, aldatıcı veya spam e-postalar.
İÇERİK KURALLARI:
- Abartılı başlıklar, şüpheli diller, gramer hataları
- Acil eylem çağrıları, kazanç veya zor durumdan kurtulma vadeden içerikler
- Rastgele karakterler, garip içerik düzeni
- Şüpheli link veya ek istekleri
ÖRNEKLER: "Kazandınız!" aldatmacaları, sahte faturalar, şifre sıfırlama istekleri, şüpheli bağlantılar
DİKKAT: Kasıtlı olarak yanıltıcı ve düşük kaliteli olmalı""",

        "Abonelik/Fatura": """
KATEGORİ DETAYI: Hizmet abonelikleri, ödeme bildirimleri, fatura detayları.
İÇERİK KURALLARI:
- Ödeme miktarları, tarihler, ödeme yöntemleri
- Hizmet süresi, yenileme bilgileri
- Fatura numarası, müşteri referans numaraları
- Ödeme hatırlatmaları veya onay mesajları
ÖRNEKLER: Aylık fatura bildirimleri, abonelik yenilemeleri, ödeme onay mesajları, ödeme hatırlatmaları
DİKKAT: Yapılandırılmış, sayısal veri içeren, resmi olmalı""",

        "Kişisel": """
KATEGORİ DETAYI: Arkadaşlar, aile, yakın çevre arasındaki kişisel iletişim.
İÇERİK KURALLARI:
- Samimi dil, kişisel ton
- Gündelik konuşma, tebrik, davet, haber paylaşımı
- Duygusal ifadeler, yakınlık göstergeleri
- Resmi olmayan üslup
ÖRNEKLER: Doğum günü kutlamaları, yemek davetleri, kişisel haberler, arkadaş sohbetleri
DİKKAT: İş dünyasından uzak, samimi ve özel olmalı""",

        "Eğitim/Öğretim": """
KATEGORİ DETAYI: Okul, kurs, eğitim kurumlarından gelen bilgilendirmeler.
İÇERİK KURALLARI:
- Ders programları, sınav tarihleri, ödev bildirimleri
- Akademik terimler, eğitim jargonu
- Öğrenci/öğretmen odaklı dil
- Eğitim içerik ve aktiviteleri hakkında bilgi
ÖRNEKLER: Sınav sonuç bildirimleri, ödev hatırlatmaları, kurs duyuruları, eğitim materyalleri
DİKKAT: Eğitimsel odağı koruyan, bilgilendirici olmalı""",

        "Sağlık": """
KATEGORİ DETAYI: Hastane, doktor, sağlık kurumlarından gelen bildirimler.
İÇERİK KURALLARI:
- Randevu hatırlatmaları, muayene bilgileri
- Sağlık raporları, test sonuçları
- Sağlık tavsiyeleri, tedavi bilgileri
- Hasta odaklı, bilgilendirici dil
ÖRNEKLER: Randevu onayları, tetkik sonuçları, ilaç hatırlatmaları, sağlık kampanyaları
DİKKAT: Profesyonel, net ve sağlık alanına özgü olmalı""",

        "Diğer": """
KATEGORİ DETAYI: Yukarıdaki kategorilere girmeyen her türlü e-posta içeriği.
İÇERİK KURALLARI:
- Hobiler, etkinlikler, ilgi alanları
- Genel bilgilendirmeler, haber bültenleri
- Organizasyon duyuruları, gönüllülük çağrıları
- Herhangi bir konu olabilir
ÖRNEKLER: Etkinlik davetleri, hobi kulüpleri, güncel haberler, genel ilanlar
DİKKAT: Diğer kategorilere benzemeyecek kadar farklı ve çeşitli olmalı"""
    }
    
    # Kategori açıklamasını al
    kategori_aciklamasi = KATEGORI_DETAYLARI.get(kategori, "")
    karsima_kurallari = build_karsima_kurallari(kategori) if hard_mode else ""
    
    prompt = f"""Sen bir e-posta üretim asistanısın. Makine öğrenmesi modeli eğitimi için yüksek kaliteli, tutarlı ve gerçekçi Türkçe e-postalar üreteceksin.

AMAÇ: {kategori} kategorisine özgü, diğer kategorilerden net bir şekilde ayrışan, gerçek dünyada görülebilecek e-postalar üretmek.

KALİTE STANDARTLARI:
✓ Her e-posta kategori özelliklerini %100 yansıtmalı
✓ Doğal Türkçe dilbilgisi kurallarına uymalı
✓ Gerçekçi senaryo ve içerik kullanmalı
✓ Makine öğrenmesi için istikrarlı ve öngörülebilir olmalı
✓ Başka kategorilerle karışabilecek belirsiz ifadelerden kaçınmalı
{karsima_kurallari}

{kategori_aciklamasi}

FORMAT:
Kategori: {kategori}
Başlık: "[başlık metni]"  (5-15 kelime, net ve kategoriye uygun)
İçerik: "[içerik metni]"  (30-80 kelime, anlamlı ve tutarlı)

ÖRNEK (Referans İçin):
Kategori: İş/Acil
Başlık: "Acil: Müşteri Şikayeti - Acilen İncelenmesi Gerekiyor"
İçerik: "Merhaba, bugün sabah büyük bir müşterimizden ciddi bir şikayet aldık. Ürün tesliminde gecikme yaşanmış ve müşteri çok rahatsız. Acilen bu konuyla ilgilenilmesi gerekiyor. Lütfen en geç bu akşama kadar bir çözüm sunalım. Müşteri ile iletişime geçip durumu açıklayalım. Saygılarımla."

ŞİMDİ GÖREVİN:
"{kategori}" kategorisinde, {varyasyon} temasında TAM OLARAK {sayi} ADET birbirinden farklı, kaliteli ve kategorinin özelliklerini yansıtan Türkçe e-posta üret.

Her e-posta için TAM OLARAK şu formatta ver:
Kategori: {kategori}
Başlık: "[başlık]"
İçerik: "[içerik]"

E-postalar tamamen farklı senaryolar, farklı tonlar ve farklı içeriklerde olsun. Kategori özelliklerinden asla sapma!"""

    # Günlük istek limiti kontrolü
    mevcut_rpd, limit_asildi = rpd_limit_kontrol()
    if limit_asildi:
        print(f"⚠ Günlük istek limiti aşıldı! (Mevcut: {mevcut_rpd}/{MAX_DAILY_REQUESTS})")
        print("   Yarına kadar beklemelisiniz veya limiti artırın.")
        return None
    
    # API çağrısından önce kısa bir bekleme (rate limit için)
    time.sleep(2)
    
    for deneme in range(max_retries):
        try:
            response = model.generate_content(prompt)
            # Başarılı API çağrısı sonrası sayacı artır
            rpd_artir()
            return response.text
        except Exception as e:
            hata_mesaji = str(e)
            if '429' in hata_mesaji or 'Resource exhausted' in hata_mesaji:
                bekleme_suresi = (deneme + 1) * 10  # Her denemede daha uzun bekle
                print(f"⚠ Rate limit hatası (429). {bekleme_suresi} saniye bekleniyor... (Deneme {deneme + 1}/{max_retries})")
                time.sleep(bekleme_suresi)
            else:
                print(f"Hata: Gemini API'den veri alınırken sorun oluştu: {e}")
                if deneme < max_retries - 1:
                    bekleme_suresi = 5
                    print(f"{bekleme_suresi} saniye bekleniyor ve tekrar denenecek...")
                    time.sleep(bekleme_suresi)
                else:
                    return None
    
    print(f"✗ {max_retries} deneme sonrası başarısız oldu.")
    return None


def mail_parse_et(metin, kategori):
    """Gemini'den gelen metni parse edip mail listesi oluştur"""
    mailler = []
    satirlar = metin.split('\n')
    
    current_mail = {}
    icerik_bekleniyor = False
    
    for satir in satirlar:
        satir = satir.strip()
        
        # Boş satırları atla
        if not satir:
            icerik_bekleniyor = False
            continue
        
        # Markdown bold temizle (**Başlık:** -> Başlık:)
        satir_temiz = re.sub(r'\*\*', '', satir)
        
        # Başlık için: "Başlık:" veya "**Başlık:**" formatlarını destekle
        if 'Başlık' in satir_temiz and ':' in satir_temiz:
            # Önceki maili kaydet (yeni mail başlıyor)
            if 'Başlık' in current_mail and 'İçerik' in current_mail:
                current_mail['Kategori'] = kategori
                current_mail['Tarih'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                mailler.append(current_mail.copy())
                current_mail = {}
            
            baslik = satir_temiz.split(':', 1)[1].strip()
            baslik = baslik.strip('"').strip("'")
            if baslik:
                current_mail['Başlık'] = baslik
                icerik_bekleniyor = False
        
        # İçerik için: "İçerik:" veya "**İçerik:**" formatlarını destekle
        elif 'İçerik' in satir_temiz and ':' in satir_temiz:
            icerik = satir_temiz.split(':', 1)[1].strip()
            icerik = icerik.strip('"').strip("'")
            if icerik:
                current_mail['İçerik'] = icerik
                icerik_bekleniyor = True
            else:
                icerik_bekleniyor = True
        
        # İçerik devamı (önceki satırda İçerik varsa ve bu satır yeni bir alan değilse)
        elif icerik_bekleniyor and 'İçerik' in current_mail:
            # Eğer yeni bir mail başlıyorsa (numaralı liste veya Kategori/Başlık varsa) durdur
            if re.match(r'^\d+\.', satir) or 'Kategori' in satir or ('Başlık' in satir and ':' in satir):
                icerik_bekleniyor = False
                # Eğer önceki mail tamamlandıysa kaydet
                if 'Başlık' in current_mail and 'İçerik' in current_mail:
                    current_mail['Kategori'] = kategori
                    current_mail['Tarih'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    mailler.append(current_mail.copy())
                    current_mail = {}
            else:
                # İçeriğe devam et
                current_mail['İçerik'] += ' ' + satir
        
        # Kategori için: Yeni mail başlıyor (eğer zaten bir mail varsa öncekini kaydet)
        elif 'Kategori' in satir_temiz and ':' in satir_temiz and current_mail:
            icerik_bekleniyor = False
    
    # Son maili de kaydet
    if current_mail and 'Başlık' in current_mail and 'İçerik' in current_mail:
        current_mail['Kategori'] = kategori
        current_mail['Tarih'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mailler.append(current_mail)
    
    return mailler


def csv_ye_ekle(mailler):
    """Mail listesini CSV dosyasına ekle (append mode)"""
    if not mailler:
        return
    
    # Mevcut CSV'yi oku
    df_mevcut = pd.read_csv(CSV_DOSYASI, encoding='utf-8-sig')
    
    # Yeni mailleri DataFrame'e çevir
    df_yeni = pd.DataFrame(mailler)
    
    # Birleştir
    df_birlesik = pd.concat([df_mevcut, df_yeni], ignore_index=True)
    
    # Duplikasyon kontrolü (aynı başlık ve içerik varsa ekleme)
    df_birlesik = df_birlesik.drop_duplicates(subset=['Başlık', 'İçerik'], keep='first')
    
    # CSV'ye kaydet
    df_birlesik.to_csv(CSV_DOSYASI, index=False, encoding='utf-8-sig')
    print(f"✓ {len(df_yeni)} yeni mail CSV'ye eklendi.")


def main():
    """Ana fonksiyon"""
    args = _parse_args()
    print("=" * 60)
    print("Gemini API Mail Üretici")
    print("=" * 60)
    
    # API key kontrolü
    if not API_KEY:
        print("⚠ HATA: API key ayarlanmamış!")
        print("Lütfen .env dosyasında GEMINI_API_KEY değerini ayarlayın.")
        return
    
    # Gemini API'yi başlat
    print("Gemini API başlatılıyor...")
    try:
        model = gemini_api_baslat(API_KEY)
        print("✓ API bağlantısı başarılı!")
    except Exception as e:
        print(f"✗ API bağlantı hatası: {e}")
        return
    
    # CSV'yi kontrol et
    print(f"\nCSV dosyası kontrol ediliyor: {CSV_DOSYASI}")
    
    # Günlük istek limiti bilgisini göster
    mevcut_rpd, limit_asildi = rpd_limit_kontrol()
    print(f"\n📊 Günlük İstek Durumu (RPD): {mevcut_rpd}/{MAX_DAILY_REQUESTS}")
    if limit_asildi:
        print("⚠ UYARI: Günlük istek limitine ulaşıldı!")
        print("   Program çalışmayacak, yarını bekleyin veya limiti artırın.")
        return
    
    # Ana döngü - tüm kategoriler tamamlanana kadar devam et
    tur_sayisi = 0
    while True:
        tur_sayisi += 1
        print(f"\n{'='*60}")
        print(f"Tur {tur_sayisi}")
        print(f"{'='*60}")
        
        # Her tur başında RPD kontrolü
        mevcut_rpd, limit_asildi = rpd_limit_kontrol()
        print(f"\n📊 Günlük İstek (RPD): {mevcut_rpd}/{MAX_DAILY_REQUESTS} "
              f"({(mevcut_rpd/MAX_DAILY_REQUESTS*100):.1f}%)")
        if limit_asildi:
            print("⚠ Günlük istek limitine ulaşıldı! Program durduruluyor...")
            break
        
        df = csv_kontrol_et()
        
        # İstatistikleri göster
        istatistik = kategori_istatistikleri(df)
        print("\nMevcut Durum:")
        print("-" * 60)
        for kategori, sayi in istatistik.items():
            durum = "✓" if sayi >= HEDEF_MIN else "○"
            print(f"{durum} {kategori}: {sayi} mail")
        
        # Hangi kategorilerde mail üretilmesi gerektiğini belirle
        gerekli_kategoriler = hangi_kategoriler_gerekli(istatistik)

        # Karışan kategorileri önceliklendir (opsiyonel)
        if args.focus_confusions and gerekli_kategoriler:
            confusion_set = set()
            for a, b in CONFUSION_PAIRS:
                confusion_set.add(a)
                confusion_set.add(b)
            oncelikli = [k for k in gerekli_kategoriler if k["kategori"] in confusion_set]
            if oncelikli:
                gerekli_kategoriler = oncelikli
        
        if not gerekli_kategoriler:
            print("\n✓ Tüm kategoriler hedef sayıya ulaştı!")
            break
        
        # Rastgele bir kategori seç
        secilen = random.choice(gerekli_kategoriler) if gerekli_kategoriler else None
        if not secilen:
            print("\n✓ Tüm kategoriler tamamlandı!")
            break
        
        kategori = secilen['kategori']
        mevcut_sayi = secilen['mevcut']
        uretilecek_sayi = min(int(args.batch_size), secilen['gerekli'])
        
        print(f"\n🔄 Üretiliyor: {kategori} kategorisi için {uretilecek_sayi} mail...")
        print(f"   (Mevcut: {mevcut_sayi}, Hedef: {HEDEF_MIN}-{HEDEF_MAX})")
        
        # Rastgele bir prompt varyasyonu seç
        varyasyon_indeksi = random.randint(0, len(PROMPT_TEMPLATES) - 1)
        
        # Mail üret
        print("Gemini API'den mail üretiliyor...")
        raw_response = mail_uret(model, kategori, uretilecek_sayi, varyasyon_indeksi, hard_mode=args.hard_mode)
        
        if not raw_response:
            print("✗ Mail üretilemedi! Sonraki kategoriye geçiliyor...")
            # Hata durumunda kısa bir bekleme sonrası devam et
            time.sleep(5)
            continue
        
        # Mail'leri parse et
        print("Mail'ler işleniyor...")
        mailler = mail_parse_et(raw_response, kategori)
        
        if not mailler:
            print("⚠ Uyarı: Hiç mail parse edilemedi. API yanıtı:")
            print(raw_response[:500])
            time.sleep(5)
            continue
        
        print(f"✓ {len(mailler)} mail başarıyla parse edildi.")
        
        # CSV'ye ekle
        csv_ye_ekle(mailler)
        
        # Son durumu göster
        df_yeni = csv_kontrol_et()
        istatistik_yeni = kategori_istatistikleri(df_yeni)
        
        print(f"\n📊 Güncel Durum - {kategori}:")
        print(f"   Önce: {mevcut_sayi} → Şimdi: {istatistik_yeni[kategori]}")
        
        # Her 20 mail sonrası 6 saniye bekle (API rate limit için)
        if len(mailler) >= 20:
            print("\n⏳ 6 saniye bekleniyor (API rate limit)...")
            time.sleep(6)
        else:
            # 20'den az mail üretildiyse de kısa bir bekleme yap
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("Tüm işlemler tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()

