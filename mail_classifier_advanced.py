"""
MailMind - Mail Kategori Sınıflandırma Modeli Eğitimi

Bu script, mail_classifier_model paketini kullanarak
gelişmiş makine öğrenmesi modelini eğitir.
"""

import argparse

from mail_classifier_model import (
    veri_yukle,
    model_karsilastir,
    model_kaydet
)


def _parse_args():
    p = argparse.ArgumentParser(description="MailMind model eğitimi")
    p.add_argument("--csv", default=None, help="Eğitim CSV yolu (varsayılan: config.CSV_DOSYASI)")
    return p.parse_args()


def main():
    """Ana fonksiyon"""
    args = _parse_args()
    print("="*70)
    print("MAILMIND - GELİŞMİŞ MAIL KATEGORİ SINIFLANDIRMA MODELİ EĞİTİMİ")
    print("="*70)
    
    # Veriyi yükle
    X, y, X_metrikler, temizleyici, metrik_cikarici = veri_yukle(csv_dosyasi=args.csv)
    
    # Model karşılaştırması
    en_iyi_isim, en_iyi_model, vectorizer, scaler, _, _ = model_karsilastir(
        X, y, X_metrikler, temizleyici, metrik_cikarici
    )
    
    # Modeli kaydet
    model_kaydet(en_iyi_model, vectorizer, scaler, temizleyici, metrik_cikarici)
    
    print("\n" + "="*70)
    print("EĞİTİM TAMAMLANDI!")
    print("="*70)
    print(f"\nEn iyi model: {en_iyi_isim}")
    print("\nTahmin yapmak için 'test_model_advanced.py' komutunu çalıştırın.")


if __name__ == "__main__":
    main()
