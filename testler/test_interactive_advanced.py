import numpy as np
import sys
import os
# Üst dizini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Modüler yapıdan import et
from mail_classifier_model import tahmin_yap

def main():
    """İnteraktif mail tahmin testi"""
    print("="*70)
    print("MAILMIND - İNTERAKTİF MAİL KATEGORİ TAHMİN SİSTEMİ")
    print("="*70)
    
    print("✓ Model modülü hazır!")
    
    print("\n" + "="*70)
    print("KULLANIM NOTLARI:")
    print("- Mail başlığı ve içeriğini girin")
    print("- 'çıkış' yazarsanız program sonlanır")
    print("- Boş bırakırsanız örnek test çalıştırılır")
    print("="*70)
    
    # Olası kategoriler
    print("\n📋 Olabilecek Kategoriler:")
    print("1. İş/Acil")
    print("2. Güvenlik/Uyarı")
    print("3. Pazarlama")
    print("4. Sosyal Medya")
    print("5. Spam")
    print("6. Abonelik/Fatura")
    print("7. Kişisel")
    print("8. Eğitim/Öğretim")
    print("9. Sağlık")
    print("10. Diğer")
    
    while True:
        print("\n" + "-"*70)
        
        # Başlık alma
        baslik = input("\n📧 Mail Başlığı (boş bırakın: örnek test / 'çıkış': programdan çık): ").strip()
        
        if baslik.lower() == 'çıkış' or baslik.lower() == 'exit':
            print("\n👋 İyi günler!")
            break
        
        # Örnek test
        if not baslik:
            print("\n🔄 Örnek test modu...")
            baslik = "Bugünkü proje toplantısı ertelendi"
            icerik = "Merhaba, bugün yapılması planlanan proje toplantısı ertelenmiştir. Yeni tarih duyurulacaktır."
            print(f"Başlık: {baslik}")
            print(f"İçerik: {icerik}\n")
        else:
            # İçerik alma
            icerik = input("📝 Mail İçeriği: ").strip()
            
            if not icerik:
                print("\n⚠️  İçerik boş olamaz! Tekrar deneyin.")
                continue
        
        # Tahmin yap
        try:
            tahmin, olasiliklar = tahmin_yap(baslik, icerik)
            
            if tahmin:
                # Olasılıkları sırala ve en üst 3'ü al
                olasiliklar_sirali = sorted(olasiliklar.items(), key=lambda x: x[1], reverse=True)[:3]
                
                # İlk 3'ün toplam olasılığını hesapla
                toplam_olasilik = sum(prob for _, prob in olasiliklar_sirali)
                
                # Sonuç göster
                print("\n" + "="*70)
                print("🎯 TAHMİN SONUCU")
                print("="*70)
                print(f"\n✅ Tahmin Edilen Kategori: {tahmin}")
                print(f"📊 Güven Skoru: %{olasiliklar[tahmin]*100:.2f}")
                
                print("\n📈 En Olası 3 Kategori:")
                for i, (kategori, prob) in enumerate(olasiliklar_sirali, 1):
                    # İlk 3'e göre normalize et
                    normalized_prob = prob / toplam_olasilik if toplam_olasilik > 0 else 0
                    bar_length = int(normalized_prob * 50)  # Bar için uzunluk
                    bar = "█" * bar_length + "░" * (50 - bar_length)
                    
                    marker = "🏆" if i == 1 else "🥈" if i == 2 else "🥉"
                    print(f"  {marker} {i}. {kategori:25s} %{normalized_prob*100:5.2f}  [{bar}]")
                
                print("\n" + "="*70)
                
                # Güven uyarısı
                if olasiliklar[tahmin] < 0.5:
                    print("⚠️  DÜŞÜK GÜVEN: Bu tahmin %50'nin altında güven skoruna sahip!")
                elif olasiliklar[tahmin] < 0.7:
                    print("ℹ️  ORTA GÜVEN: Bu tahmin orta seviye güven skoruna sahip.")
                else:
                    print("✓  YÜKSEK GÜVEN: Bu tahmin güvenilir görünüyor!")
                
            else:
                print("\n❌ Tahmin yapılamadı! Model hatası.")
        
        except Exception as e:
            print(f"\n❌ Hata oluştu: {e}")
            print("Lütfen tekrar deneyin.")


if __name__ == "__main__":
    main()

