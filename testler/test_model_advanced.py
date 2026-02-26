import numpy as np
import sys
import os
# Üst dizini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Modüler yapıdan import et
from mail_classifier_model import tahmin_yap

def main():
    """Test için örnek mail tahminleri"""
    print("="*70)
    print("MAILMIND - GELİŞMİŞ MAİL KATEGORİ TAHMİN TESTİ")
    print("="*70)
    
    # Örnek mailler (10 kategori x 10 örnek = 100 test)
    ornek_mailler = [
        # Pazarlama (Alışveriş + Reklam) - 10 örnek
        {
            'baslik': 'Siparişiniz onaylandı',
            'icerik': 'Merhaba, siparişiniz başarıyla alınmıştır. Sipariş numaranız: 12345. En kısa sürede hazırlanıp kargoya verilecektir.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Muhteşem fırsat!',
            'icerik': 'Sadece bugün! Kaçırılmayacak indirimler! Hemen tıklayın!',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Yeni koleksiyon geldi',
            'icerik': 'Sezonun en yeni koleksiyonu artık sitemizde! Erkenden göz atmak için indirim fırsatını yakalayın.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Kampanya son günü',
            'icerik': 'Flash sale son günleri! Seçili ürünlerde %70\'e varan indirimler. Stoklar tükenmeden alışveriş yapın.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Kargo bedava kapınızda',
            'icerik': 'Bugün tüm alışverişlerinizde kargo ücretsiz! 500 TL üzeri alışverişe ekstra indirim kuponu hediye.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Özel indirim kuponunuz',
            'icerik': 'Sadece sizin için özel: İLK20 kupon kodu ile %20 indirim kazanın. Son gün: Bu akşam!',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Sepetinizdeki ürünler indirime girdi',
            'icerik': 'Sepetinizde bekleyen ürünler indirime girdi! Son 24 saatte stokta kalacağı garantisi. Hemen tamamlayın.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'VIP müşteri özel fırsatı',
            'icerik': 'Değerli VIP müşterimiz, sizin için özel erken erişim hakkı. Yeni ürünleri herkesten önce keşfedin.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Takım elbise koleksiyonu',
            'icerik': 'Profesyonel kıyafetleriniz hazır! İş dünyası için özel tasarlanmış takım elbise koleksiyonumuz sizlerle.',
            'beklenen': 'Pazarlama'
        },
        {
            'baslik': 'Elektronik ürünlerde bomba fiyatlar',
            'icerik': 'Teknoloji tutkunları buraya! Bilgisayar, telefon ve aksesuarlarda kaçırılmayacak kampanya başladı.',
            'beklenen': 'Pazarlama'
        },
        # Eğitim/Öğretim - 10 örnek
        {
            'baslik': 'Sınav sonuçları açıklandı',
            'icerik': 'Sınav sonuçlarınız öğrenci bilgi sistemine yüklenmiştir. Başarılarınızı dilerim.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Ödev teslim hatırlatması',
            'icerik': 'Merhaba öğrenciler, ödev teslim tarihiniz yaklaşıyor. Son gün: 15 Kasım. Lütfen unutmayın!',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Kurs kayıtları başladı',
            'icerik': '2024 yılı kurs kayıtları açıldı. Profesyonel gelişim için online ve yüz yüze eğitim seçenekleri.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Seminer daveti',
            'icerik': 'Değerli öğrenciler, gelecek hafta "Yapay Zeka ve Gelecek" konulu seminerimiz var. Katılımınızı bekliyoruz.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Ders programı güncellemesi',
            'icerik': 'Sayın öğrenciler, ders programında değişiklik yapılmıştır. Güncel programı öğrenci portalından kontrol edin.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Lisansüstü başvuru hatırlatması',
            'icerik': 'Yüksek lisans başvuruları son 5 gün! Başvuru belgelerinizi eksiksiz tamamlamayı unutmayın.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Kütüphane yeni kitaplar',
            'icerik': 'Kütüphanemize yeni kitaplar eklendi. Akademik kaynaklara daha kolay ulaşım için online sistem aktif.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Staj başvuru sonuçları',
            'icerik': 'Değerli öğrenciler, staj başvuru sonuçları ilan edilmiştir. Başvuru sonucunuzu online sistemden kontrol edebilirsiniz.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Dönem ödevi bildirimi',
            'icerik': 'Dönem ödevi konuları belirlenmiştir. En geç 20 Aralık\'a kadar öğretim üyenize konu seçiminizi iletin.',
            'beklenen': 'Eğitim/Öğretim'
        },
        {
            'baslik': 'Mezuniyet töreni bilgisi',
            'icerik': 'Tüm mezun adayları için mezuniyet töreni 15 Haziran\'da yapılacaktır. Detaylı bilgi için web sayfamızı ziyaret edin.',
            'beklenen': 'Eğitim/Öğretim'
        },
        # Kişisel - 10 örnek
        {
            'baslik': 'Akşam yemeğine ne dersin?',
            'icerik': 'Merhaba, bu akşam yemeğe çıkmaya ne dersin? Uzun zamandır görüşemedik, biraz sohbet ederiz.',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Doğum günü partisi daveti',
            'icerik': 'Cumartesi akşamı doğum günü partim var. Gelmek ister misin? Saat 20:00\'da başlıyor.',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Hafta sonu piknik planı',
            'icerik': 'Hafta sonu ormanda piknik yapmaya gidiyoruz. Sen de gelmek ister misin? Eş ve çocuklar da davetli!',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Düğün davetiyesi',
            'icerik': 'Sevgili arkadaşım, evleniyoruz! Seni de kutlama törenimizde aramızda görmekten mutluluk duyarız.',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Yolculuk planı',
            'icerik': 'Bahara özel tatil planı yaptık. Kapadokya turuna gitmeyi düşünüyoruz, sen de katılmak ister misin?',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Konser biletleri aldım',
            'icerik': 'Sevdiğimiz grubun konseri var! İkimiz için bilet aldım, gidelim mi?',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Yeni işimi aldım',
            'icerik': 'Hey dostum, harika bir haber! İstediğim şirketten teklif aldım, Pazartesi başlıyorum. Sana söylemek istedim.',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Bebek haberimiz var',
            'icerik': 'Sevgili ailemiz, büyük bir sevinçle paylaşıyoruz: Hamileyiz! Ekim ayında bebeğimizi kucaklamayı bekliyoruz.',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Annem ameliyat oldu',
            'icerik': 'Merhaba, annem bugün başarıyla ameliyat oldu. Şimdi iyileşme sürecinde. Dualarınızı bekliyoruz.',
            'beklenen': 'Kişisel'
        },
        {
            'baslik': 'Yıllar sonra buluşalım',
            'icerik': 'Okul günlerinden kalma arkadaşlarla birleşiyoruz. Geçmişe yolculuk yapmak ister misin? Tüm arkadaşlar geliyor.',
            'beklenen': 'Kişisel'
        },
        # İş/Acil (İş + Acil birleşti) - 10 örnek
        {
            'baslik': 'Toplantı daveti - Proje sunumu',
            'icerik': 'Yarın saat 14:00\'te proje sunumu toplantısı yapılacaktır. Tüm ekip üyelerinin katılımı önemlidir.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Acil: Toplantı iptal',
            'icerik': 'Acil duyuru: Bugünkü toplantı iptal edilmiştir. Yeni tarih paylaşılacaktır.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Müşteri şikayeti - Acil',
            'icerik': 'Büyük bir müşterimizden ciddi şikayet geldi. Acilen konuyla ilgilenilmesi ve çözüm sunulması gerekiyor.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Sunum materyalleri hazır mı?',
            'icerik': 'Yarınki müşteri sunumuna az kaldı. Tüm materyallerin ve demo\'nun hazır olduğunu doğrulayabilir misiniz?',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Proje deadline yaklaşıyor',
            'icerik': 'Kritik proje teslim tarihi yarın! Son kontrolleri yapın ve kesinlikle gecikme olmamalı. Ekip toplantısı bu akşam.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Sistem arızası bildirimi',
            'icerik': 'Üretim hatasında sistem arızası tespit edildi. Acil teknik destek gerekiyor. Durum raporu gönderin.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Müdür toplantısı',
            'icerik': 'Tüm müdürlere acil toplantı çağrısı. Hemen toplantı salonunda buluşuyoruz. Kritik kararlar alınacak.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'İş teklifi değerlendirme',
            'icerik': 'Sayın aday, size yönelik iş teklifimizi değerlendirmek için en geç Cuma akşamına kadar dönüş bekliyoruz.',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Çeyreklik rapor teslimi',
            'icerik': 'Q4 raporlarınız bugün teslim edilmeli. Son kontrolleri yapıp doğrulama için gönderebilir misiniz?',
            'beklenen': 'İş/Acil'
        },
        {
            'baslik': 'Workshop organizasyonu',
            'icerik': 'Müşteri workshop\'u için koordinasyon yapılması gerekiyor. Malzeme listesi ve teknik gereksinimleri paylaşın.',
            'beklenen': 'İş/Acil'
        },
        # Abonelik/Fatura (Üyelik + Fatura birleşti) - 10 örnek
        {
            'baslik': 'Faturalama hatırlatması',
            'icerik': 'Sayın müşterimiz, faturanızı ödemeyi unutmayın. Son tarih yaklaşıyor.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Üyelik yenileme',
            'icerik': 'Sayın üyemiz, üyeliğiniz yakında sona erecek. Yenilemek için tıklayın.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Ödeme onayı',
            'icerik': 'Sayın müşteri, ödemeniz başarıyla alınmıştır. Teşekkür ederiz. Fiş ve makbuz e-posta ekindedir.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Aylık fatura eklendi',
            'icerik': 'Merhaba, Ocak ayı faturanız hazırdır. Toplam tutar: 350 TL. Son ödeme tarihi: 15 Şubat.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Abonelik otomatik yenilendi',
            'icerik': 'Aboneliğiniz otomatik olarak yenilenmiştir. Yeni dönem: 3 Ocak - 3 Mart. İptal için son 24 saat.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Ödeme başarısız',
            'icerik': 'Otomatik ödeme işleminiz başarısız oldu. Lütfen kart bilgilerinizi güncelleyin veya manuel ödeme yapın.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Üyelik fırsatı',
            'icerik': 'Premium üyeliğe geçin, ilk ay %50 indirimli! Tüm özelliklere sınırsız erişim. Süre sonu bu gece.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Fatura özeti - Ekim ayı',
            'icerik': 'Ekim ayı harcama özetiniz: Toplam 890 TL. Detaylı fatura ekte. Sorularınız için destek hattımızı arayın.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'İade işlemi tamamlandı',
            'icerik': 'İade işleminiz tamamlandı. Tutar 3-5 iş günü içinde kartınıza yansıtılacaktır. Teşekkür ederiz.',
            'beklenen': 'Abonelik/Fatura'
        },
        {
            'baslik': 'Subscription renewal reminder',
            'icerik': 'Your annual subscription will renew automatically next week. Current plan: Professional. Amount: $199/year.',
            'beklenen': 'Abonelik/Fatura'
        },
        # Sosyal Medya - 10 örnek
        {
            'baslik': 'Sosyal medya bildirimi',
            'icerik': 'Beğendiğiniz sayfada yeni bir gönderi paylaşıldı. Hemen bakın!',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'Yeni takipçi',
            'icerik': 'Instagram\'da size yeni bir kişi takip etmeye başladı. Kontrol edin!',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'Twitter\'da bahsedildiniz',
            'icerik': 'Twitter\'da size bir bahsetme var. Yeni bildiriminizi görmek için tıklayın.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'LinkedIn yorum bildirimi',
            'icerik': 'LinkedIn\'de gönderinize bir yorum geldi. Profesyonel ağınızdan yeni etkileşim.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'TikTok\'ta yeni beğeni',
            'icerik': 'Videolarınızdan biri 100 beğeni aldı! Daha fazlası için içerik üretmeye devam edin.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'Facebook arkadaş isteği',
            'icerik': 'Size yeni bir arkadaşlık isteği geldi. İstekleri görmek için profilinizi ziyaret edin.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'WhatsApp durum güncellemesi',
            'icerik': 'Arkadaşınız WhatsApp durumunda yeni bir gönderi paylaştı. Hemen görün.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'YouTube abonelik hatırlatması',
            'icerik': 'Abone olduğunuz kanalda yeni video yayınlandı. Hemen izleyin ve yorum yapın.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'Pinterest yeni pim',
            'icerik': 'Takip ettiğiniz kullanıcılar yeni içerikler paylaştı. İlham almak için keşfedin.',
            'beklenen': 'Sosyal Medya'
        },
        {
            'baslik': 'Reddit mesajınız var',
            'icerik': 'Reddit\'te size yeni bir özel mesaj geldi. Oyuncu topluluğundan geri bildirim.',
            'beklenen': 'Sosyal Medya'
        },
        # Güvenlik/Uyarı - 10 örnek
        {
            'baslik': 'Güvenlik uyarısı',
            'icerik': 'Şüpheli giriş tespit edildi. Lütfen şifrenizi kontrol edin.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Yeni cihaz girişi',
            'icerik': 'Hesabınıza yeni bir cihazdan giriş yapıldı. Siz misiniz?',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Şifre değişiklik onayı',
            'icerik': 'Hesabınızın şifresi başarıyla değiştirildi. Değişikliği siz yapmadıysanız lütfen derhal iletişime geçin.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Çift doğrulama etkinleştirildi',
            'icerik': 'Hesabınız için iki faktörlü kimlik doğrulama aktif edildi. Güvenliğiniz için önemli bir adım attınız.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Şüpheli e-posta aktivitesi',
            'icerik': 'Hesabınızdan şüpheli bir e-posta gönderimi tespit edildi. Lütfen hesabınızı kontrol edin.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Veri sızıntısı uyarısı',
            'icerik': 'Olası bir veri güvenliği olayı tespit edildi. Lütfen şifrenizi değiştirin ve hesap güvenlik ayarlarınızı gözden geçirin.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Bilinmeyen konum girişi',
            'icerik': 'Hesabınıza bilinmeyen bir konumdan giriş yapıldı. IP: 192.168.1.100. Eğer bu siz değilseniz hesabı koruyun.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Oturum sonlandırma',
            'icerik': 'Güvenlik nedenleriyle bazı oturumlarınız sonlandırıldı. Yeni giriş için şifre gerekli.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'API anahtarı yenileme',
            'icerik': 'Eski API anahtarlarınızın süresi doldu. Güvenlik için yeni anahtarlar oluşturmanız gerekiyor.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        {
            'baslik': 'Virüs taraması sonucu',
            'icerik': 'Sisteminizde tehlikeli bir yazılım tespit edildi. Acilen temizleme işlemi yapın ve destek alın.',
            'beklenen': 'Güvenlik/Uyarı'
        },
        # Spam - 10 örnek
        {
            'baslik': 'Kazanmak için tıkla!',
            'icerik': '10 milyon dolar kazandınız! Hemen tıklayın ve ödülünüzü alın!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'BEDAVA BEDAVA BEDAVA!',
            'icerik': 'HİÇ DURMA BEDAVA İPHONE KAZANDINIZ TIKLAMAN YETER!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'JACKPOT KAZANDIN!',
            'icerik': '1 BILYON DOLAR KAZANDINIZ! HEMEN TIKLAYIN PARA HESABINIZA GEÇECEK! DİKKAT: SON 24 SAAT!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'İŞTE FIRSAT ZAMANI!',
            'icerik': 'Hiç şakayla karıştırmadan gerçek! Fırsat kaçırmayın! HEMEN HEMEN HERŞEY BEDAVA!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'BAYRAM İKRAMI SİZİN İÇİN!',
            'icerik': 'Bayram hediyemiz sadece sizler için! Bu linke tıklayın ve altın madalya kazanın!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'Hesap kapatılıyor mu?',
            'icerik': 'Hesabınız kapatılacak! Acil işlem yapın! Verilerinizi kaybetmemek için hemen tıklayın!!1!',
            'beklenen': 'Spam'
        },
        {
            'baslik': '12345***',
            'icerik': '$$$$$ YOUR BEST $$FRIEND$$ SENT YOU $$$$ MONEY $$$$$$$ CLICK NOW $$$$$ WON!!!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'Mirakül çözüm',
            'icerik': 'Doktorların keşfettiklerini gizlediği formül! İlaç kullanmadan 1 haftada %100 sonuç garantili!',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'Çok acil mesaj',
            'icerik': 'Bu mesajı görüyorsanız çok şanslısınız. Ancak 3 saat içinde yanıt vermezseniz şansınız kaybolacak.',
            'beklenen': 'Spam'
        },
        {
            'baslik': 'yOu WiN pRiZe!!!11',
            'icerik': 'CONGRATULATIONS!!!111!!! you woN mONEy priZe!!! cLIck heRE NOW!!!!!!!!!!!!!!!!!! winner!!!!!!!!!!!!!!!',
            'beklenen': 'Spam'
        },
        # Sağlık - 10 örnek
        {
            'baslik': 'Randevu hatırlatması',
            'icerik': 'Sayın hastamız, yarın saat 10:00\'da doktor randevunuzu hatırlatmak isteriz.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Check-up sonuçlarınız hazır',
            'icerik': 'Sayın hastamız, check-up sonuçlarınız hazırdır. Sonuçları görmek için hastanemize gelebilirsiniz.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Ameliyat hazırlık talimatları',
            'icerik': 'Sayın hastamız, ameliyatınız için önemli talimatlar: Sabah 08:00\'da aç karnına gelin. Son yemek saat 00:00.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'İlaç dozaj hatırlatması',
            'icerik': 'Reçetenizdeki antibiyotik tedavisini tamamladınız mı? Erken bırakmak bakteri direncine neden olabilir.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Kan veri sonuçları',
            'icerik': 'Tahlil sonuçlarınız normal aralıkta. Ancak D vitamini seviyesi düşük. Destek takviyesi önerilir.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Fizyoterapi seansı',
            'icerik': 'Fizyoterapi randevunuz yarın saat 14:00\'te. Ortopedik yatırım cihazınızı getirmeyi unutmayın.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Aşı randevusu',
            'icerik': 'COVID-19 aşınızın 6. dozu yapılabilir. En yakın sağlık kuruluşundan randevu alabilirsiniz.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Diş kontrolü hatırlatması',
            'icerik': '6 aylık diş kontrolünüzü yaptırdınız mı? Düzenli kontroller ağız sağlığınız için önemli.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Beslenme danışmanlığı',
            'icerik': 'Beslenme uzmanımız sizinle görüşmek istiyor. Kişiselleştirilmiş diyet programı için randevu alın.',
            'beklenen': 'Sağlık'
        },
        {
            'baslik': 'Göz muayenesi sonuçları',
            'icerik': 'Göz muayene sonuçlarınız normal. Gözlük numaranızda değişiklik yok. Sonraki kontrol 1 yıl sonra.',
            'beklenen': 'Sağlık'
        },
        # Diğer - 10 örnek
        {
            'baslik': 'Genel duyuru',
            'icerik': 'Merhaba, bu hafta genel bakım nedeniyle sistem geçici olarak kapanacaktır.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Sistem güncellemesi',
            'icerik': 'Yeni sürüm kullanıma hazır. Lütfen sistemi güncellemeyi unutmayın.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Haber bülteni',
            'icerik': 'Bu haftanın önemli haberlerini derledik. Teknoloji, spor ve dünya gündeminden özetler.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Etkinlik duyurusu',
            'icerik': 'Yaklaşan kitap fuarında yazar imza günü düzenleniyor. Katılımcı olmak ister misiniz?',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Günlük hava durumu',
            'icerik': 'Bugün için hava durumu: Parçalı bulutlu, sıcaklık 18 derece. Yağmur ihtimali %20. İyi günler dileriz.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Kültürel etkinlik takvimi',
            'icerik': 'Kasım ayı kültürel etkinlikler: Tiyatro gösterileri, sergi açılışları ve konser programları.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Gönüllülük çağrısı',
            'icerik': 'Çevre temizliği etkinliğine katılmak ister misiniz? Cumartesi sabahı parkta buluşuyoruz.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Hobi kulübü daveti',
            'icerik': 'Fotoğrafçılık tutkunları bir araya geliyor. İlk buluşmamız bu Pazar günü doğada. Katılın!',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Topluluk toplantısı',
            'icerik': 'Topluluk üyeleri için aylık bilgilendirme toplantısı düzenleniyor. Katılımınızı bekliyoruz.',
            'beklenen': 'Diğer'
        },
        {
            'baslik': 'Genel arşiv uyarısı',
            'icerik': 'Eski e-postalarınız otomatik olarak arşivlendi. İstediğiniz zaman geri getirebilirsiniz.',
            'beklenen': 'Diğer'
        }
    ]
    
    print("\n✓ Model modülü hazır!\n")
    
    # Tahminler
    dogru_tahmin = 0
    toplam = len(ornek_mailler)
    
    for idx, ornek in enumerate(ornek_mailler, 1):
        baslik = ornek['baslik']
        icerik = ornek['icerik']
        beklenen = ornek['beklenen']
        
        tahmin, olasiliklar = tahmin_yap(baslik, icerik)
        
        if tahmin:
            # Olasılıkları sırala
            olasiliklar_sirali = sorted(olasiliklar.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Sonuç
            dogru_mu = "✓" if tahmin == beklenen else "✗"
            if dogru_mu == "✓":
                dogru_tahmin += 1
            
            print(f"{idx}. {dogru_mu} Başlık: '{baslik[:50]}...'")
            print(f"   Beklenen: {beklenen}")
            print(f"   Tahmin: {tahmin} (%{olasiliklar[tahmin]*100:.2f})")
            print(f"   Diğer olasılıklar:")
            for kategori, prob in olasiliklar_sirali[1:3]:
                print(f"     - {kategori}: %{prob*100:.2f}")
            print()
    
    # Genel sonuç
    accuracy = dogru_tahmin / toplam
    print("="*70)
    print(f"GENEL SONUÇ: {dogru_tahmin}/{toplam} doğru (%{accuracy*100:.2f})")
    print("="*70)


if __name__ == "__main__":
    main()

