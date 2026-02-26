"""
Mail İzleyici - MailHog'u Dinleyen ve Mail Geldiğinde Modeli Çalıştıran Script

Bu script sürekli çalışır ve MailHog'u dinler.
Yeni mail geldiğinde modeli kullanarak kategorize eder.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Optional

# Üst dizini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mail_classifier_model import tahmin_yap


class MailHogIzleyici:
    """MailHog'u izleyen ve mail geldiğinde işlem yapan sınıf"""
    
    def __init__(self, api_host="localhost", api_port=8025, kontrol_araligi=2):
        """
        Args:
            api_host: MailHog API host adresi
            api_port: MailHog API port numarası
            kontrol_araligi: Her kaç saniyede bir kontrol edilecek
        """
        self.api_base_url = f"http://{api_host}:{api_port}/api/v2"
        self.kontrol_araligi = kontrol_araligi
        self.islenmis_mail_ids = set()  # İşlenmiş mail ID'lerini tut
        
        # Modeli başlangıçta yükle (performans için)
        print("🤖 Model yükleniyor...")
        self.model, self.vectorizer, self.scaler, self.temizleyici, self.metrik_cikarici = self._model_yukle()
        if self.model is None:
            raise RuntimeError("Model yüklenemedi!")
        print("✓ Model yüklendi")
    
    def _model_yukle(self):
        """Modeli yükle"""
        try:
            from mail_classifier_model.model_manager import model_yukle
            result = model_yukle()
            # model_yukle may now return optional label mappings as additional items.
            # Old callers expect 5 items, so return only the first five to preserve behavior.
            if isinstance(result, tuple) and len(result) >= 5:
                return result[0], result[1], result[2], result[3], result[4]
            else:
                return result
        except Exception as e:
            print(f"✗ Model yükleme hatası: {e}")
            return None, None, None, None, None
    
    def _mailhoga_baglan(self) -> bool:
        """MailHog bağlantısını test et"""
        try:
            response = requests.get(f"{self.api_base_url}/messages", timeout=5)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def _mailleri_al(self) -> list:
        """MailHog'dan tüm mailleri al"""
        try:
            response = requests.get(f"{self.api_base_url}/messages", timeout=5)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                # Debug: İlk maili göster
                if items and len(self.islenmis_mail_ids) == 0:
                    first_mail = items[0]
                    print(f"🔍 Debug - İlk mail yapısı: {list(first_mail.keys())}")
                    print(f"🔍 Debug - İlk mail ID: {first_mail.get('ID', 'YOK')}")
                return items
            return []
        except Exception as e:
            print(f"✗ Mail alma hatası: {e}")
            return []
    
    def _mail_detay_al(self, mail_id: str) -> Optional[Dict]:
        """Belirli bir mailin detaylarını al"""
        try:
            # MailHog API v2 için ID'yi encode et (URL-safe)
            import urllib.parse
            encoded_id = urllib.parse.quote(mail_id, safe='')
            
            # Önce ID ile dene
            response = requests.get(f"{self.api_base_url}/messages/{encoded_id}", timeout=5)
            
            if response.status_code != 200:
                # Eğer başarısız olursa, direkt ID ile dene
                response = requests.get(f"{self.api_base_url}/messages/{mail_id}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # MailHog v2 API yapısı: { "Content": {...}, "Raw": {...}, ... }
                return data
            else:
                print(f"✗ Mail detay HTTP hatası: {response.status_code}")
                print(f"   Denenen URL: {self.api_base_url}/messages/{encoded_id}")
                return None
        except Exception as e:
            print(f"✗ Mail detay alma hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _mail_icerik_cikar(self, mail_data: Dict) -> tuple:
        """
        Mail verisinden başlık ve içeriği çıkar
        
        Returns:
            tuple: (baslik, icerik)
        """
        try:
            import re
            import base64
            from email.header import decode_header
            from email.utils import parsedate_to_datetime
            
            # MailHog API v2 yapısı: { "Content": { "Headers": {...}, "Body": "...", "MIME": {...} } }
            content = mail_data.get("Content", {})
            if not content:
                # Alternatif yapı denemesi
                content = mail_data
            
            headers = content.get("Headers", {})
            if not headers:
                # Headers doğrudan content içinde olmayabilir
                headers = content
            
            # Başlık - RFC 2047 decode et
            subject = headers.get("Subject", [""])
            if isinstance(subject, list):
                baslik_raw = subject[0] if subject and len(subject) > 0 else ""
            else:
                baslik_raw = str(subject) if subject else ""
            
            # RFC 2047 decode (örnek: =?utf-8?q?Size_=C3=96zel?= -> Size Özel)
            baslik = ""
            try:
                decoded_parts = decode_header(baslik_raw)
                decoded_strings = []
                for part, encoding in decoded_parts:
                    if isinstance(part, bytes):
                        if encoding:
                            decoded_strings.append(part.decode(encoding))
                        else:
                            decoded_strings.append(part.decode('utf-8', errors='ignore'))
                    else:
                        decoded_strings.append(part)
                baslik = ''.join(decoded_strings)
            except Exception as e:
                # Decode başarısız olursa orijinali kullan
                baslik = baslik_raw
                print(f"  ⚠️  Başlık decode hatası: {e}")
            
            # İçerik - Birden fazla yöntem dene
            body = content.get("Body", "")
            
            # Body'yi decode et - Base64 ve multipart MIME yapısını handle et
            if body:
                # Multipart MIME yapısı kontrolü (--=============== ile başlıyorsa)
                if body.strip().startswith("--") or "Content-Transfer-Encoding: base64" in body:
                    # MIME multipart - base64 içeriği çıkar
                    lines = body.split('\n')
                    base64_lines = []
                    in_base64 = False
                    found_base64_section = False
                    
                    for i, line in enumerate(lines):
                        # Base64 section başladı mı?
                        if "Content-Transfer-Encoding: base64" in line or "Content-Type: text/plain" in line:
                            in_base64 = True
                            found_base64_section = True
                            continue
                        # Boş satır sonrası base64 başlar
                        if in_base64 and line.strip() == "":
                            continue
                        # Boundary veya yeni section başladı mı?
                        if line.strip().startswith("--") and in_base64:
                            # Base64 decode et
                            if base64_lines:
                                base64_content = ''.join(base64_lines).replace('\n', '').replace('\r', '').replace(' ', '')
                                try:
                                    decoded = base64.b64decode(base64_content).decode('utf-8', errors='ignore')
                                    if decoded.strip() and len(decoded.strip()) > 10:
                                        body = decoded.strip()
                                        break
                                except Exception as e:
                                    pass
                            base64_lines = []
                            in_base64 = False
                        elif in_base64 and line.strip() and not line.strip().startswith("Content-") and not line.strip().startswith("MIME-"):
                            # Base64 satırı
                            cleaned_line = line.strip().replace(' ', '').replace('\n', '').replace('\r', '')
                            if cleaned_line:
                                base64_lines.append(cleaned_line)
                    
                    # Son base64 bloğunu da decode et
                    if base64_lines and found_base64_section:
                        base64_content = ''.join(base64_lines).replace('\n', '').replace('\r', '').replace(' ', '')
                        if base64_content:
                            try:
                                decoded = base64.b64decode(base64_content).decode('utf-8', errors='ignore')
                                if decoded.strip() and len(decoded.strip()) > 10:
                                    body = decoded.strip()
                            except Exception as e:
                                pass
                
                # Eğer hala base64 görünüyorsa (direkt base64 string)
                if body and len(body) > 20 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r ' for c in body[:200].replace(' ', '').replace('\n', '').replace('\r', '')[:100]):
                    try:
                        # Tüm whitespace'i temizle
                        base64_clean = ''.join([c for c in body if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='])
                        if len(base64_clean) > 20:
                            decoded = base64.b64decode(base64_clean).decode('utf-8', errors='ignore')
                            if decoded.strip() and len(decoded.strip()) > 10:
                                body = decoded.strip()
                    except:
                        pass
            
            # Eğer Body boşsa veya hala encoded görünüyorsa, MIME Parts'ı kontrol et
            if not body or len(body.strip()) == 0 or ("Content-Type:" in body and "base64" in body.lower()):
                # Multipart mailler için
                parts = content.get("MIME", {}).get("Parts", [])
                if parts:
                    for part in parts:
                        content_type = part.get("ContentType", "")
                        part_body = part.get("Body", "")
                        
                        # Base64 decode denemesi
                        if part_body and content_type.startswith("text/"):
                            try:
                                # Base64 decode dene
                                decoded = base64.b64decode(part_body).decode('utf-8', errors='ignore')
                                if decoded.strip():
                                    part_body = decoded
                            except:
                                pass
                        
                        if content_type.startswith("text/plain") and part_body:
                            body = part_body
                            break
                        elif content_type.startswith("text/html") and not body and part_body:
                            # HTML'i fallback olarak kullan
                            body = part_body
            
            # HTML etiketlerini temizle
            if body and ("<html" in body.lower() or "<body" in body.lower() or "<div" in body.lower()):
                # HTML içeriğini temizle
                body = re.sub('<[^<]+?>', '', body)
                # Fazla boşlukları temizle
                body = re.sub(r'\s+', ' ', body).strip()
            
            # Eğer hala içerik yoksa, Raw Data'yı kontrol et
            if not body or len(body.strip()) == 0:
                raw_data = content.get("Raw", {})
                if raw_data:
                    body = str(raw_data)
                    # Raw data'dan text çıkar
                    if isinstance(raw_data, dict):
                        body = raw_data.get("Data", str(raw_data))
            
            # Son kontrol: Eğer hala boşsa, Content'in kendisini string'e çevir
            if not body or len(body.strip()) == 0:
                body = str(content).replace('{', '').replace('}', '').strip()
            
            return baslik.strip(), body.strip() if body else ""
            
        except Exception as e:
            print(f"✗ Mail içerik çıkarma hatası: {e}")
            import traceback
            traceback.print_exc()
            return "", ""
    
    def _maili_kategorize_et(self, baslik: str, icerik: str) -> tuple:
        """
        Maili model kullanarak kategorize et
        
        Returns:
            tuple: (tahmin, olasiliklar)
        """
        try:
            # Boş kontrolü
            if not baslik and not icerik:
                print("  ⚠️  Başlık ve içerik boş!")
                return None, None
            
            # En az birini doldur
            if not baslik:
                baslik = "Test"
            if not icerik:
                icerik = baslik
            
            tahmin, olasiliklar = tahmin_yap(
                baslik, icerik,
                model=self.model,
                vectorizer=self.vectorizer,
                scaler=self.scaler,
                temizleyici=self.temizleyici,
                metrik_cikarici=self.metrik_cikarici
            )
            
            # Debug: Eğer None dönerse
            if tahmin is None or olasiliklar is None:
                print(f"  ⚠️  Model None döndü!")
                print(f"     Model: {self.model is not None}")
                print(f"     Vectorizer: {self.vectorizer is not None}")
                
            return tahmin, olasiliklar
        except Exception as e:
            print(f"✗ Kategorizasyon hatası: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def _yeni_mailleri_isle(self):
        """Yeni gelen mailleri işle"""
        # Tüm mailleri al
        mailler = self._mailleri_al()
        
        if not mailler:
            return
        
        # Yeni mailleri bul ve işle
        for mail in mailler:
            mail_id = mail.get("ID")
            
            if not mail_id:
                continue
            
            # Daha önce işlenmiş mi kontrol et
            if mail_id in self.islenmis_mail_ids:
                continue
            
            # Maili işle
            print(f"\n{'='*70}")
            print(f"📧 YENİ MAİL TESPİT EDİLDİ!")
            print(f"{'='*70}")
            print(f"📋 Mail ID: {mail_id[:50]}...")
            
            # MailHog API v2'de bazen mail detayları zaten mail objesi içinde olabilir
            # Önce mail objesinin kendisini kontrol et
            mail_detay = None
            
            # Eğer mail objesi içinde Content varsa, detay API'sine gerek yok
            if "Content" in mail or "Raw" in mail:
                print("📌 Mail detayları zaten mevcut (API çağrısına gerek yok)")
                mail_detay = mail
            else:
                # Mail detaylarını al
                mail_detay = self._mail_detay_al(mail_id)
            
            if not mail_detay:
                print(f"✗ Mail detayları alınamadı (ID: {mail_id})")
                # Eğer mail objesi varsa onu kullan
                if mail:
                    print("📌 Mail objesi kullanılıyor...")
                    mail_detay = mail
                else:
                    self.islenmis_mail_ids.add(mail_id)
                    print(f"{'='*70}\n")
                    continue
            
            # Debug: Mail yapısını göster
            print(f"🔍 Mail yapısı anahtarları: {list(mail_detay.keys())}")
            if "Content" in mail_detay:
                content_keys = list(mail_detay['Content'].keys()) if isinstance(mail_detay['Content'], dict) else "Content dict değil"
                print(f"🔍 Content anahtarları: {content_keys}")
            
            # Başlık ve içeriği çıkar
            baslik, icerik = self._mail_icerik_cikar(mail_detay)
            
            print(f"📌 Başlık: {baslik}")
            print(f"📄 İçerik uzunluğu: {len(icerik)} karakter")
            if icerik:
                print(f"📄 İçerik (ilk 150 karakter): {icerik[:150]}...")
            else:
                print(f"⚠️  İçerik boş!")
            
            # İçerik kontrolü - En az bir şey olsun
            if not baslik and not icerik:
                print(f"✗ Mail içeriği alınamadı! Mail yapısını kontrol edin.")
                # Debug için mail yapısını göster
                print(f"🔍 Debug - mail_detay tipi: {type(mail_detay)}")
                if isinstance(mail_detay, dict):
                    print(f"🔍 Debug - mail_detay anahtarları: {list(mail_detay.keys())[:10]}")
                self.islenmis_mail_ids.add(mail_id)
                print(f"{'='*70}\n")
                continue
            
            # En az içerik varsa devam et
            if not icerik and baslik:
                icerik = baslik  # Başlığı içerik olarak kullan
            
            # Kategorize et
            print(f"\n🤖 Model kategorize ediliyor...")
            print(f"   Başlık: '{baslik[:50]}...' ({len(baslik)} karakter)")
            print(f"   İçerik: '{icerik[:50]}...' ({len(icerik)} karakter)")
            try:
                tahmin, olasiliklar = self._maili_kategorize_et(baslik, icerik)
                
                if tahmin and olasiliklar:
                    # Sonuçları göster
                    print(f"\n✓ KATEGORİZASYON SONUCU:")
                    print(f"  📊 Tahmin: {tahmin}")
                    print(f"  📈 Güven: %{olasiliklar.get(tahmin, 0) * 100:.2f}")
                    
                    # En yüksek 3 olasılığı göster
                    sirali_olasiliklar = sorted(olasiliklar.items(), key=lambda x: x[1], reverse=True)[:3]
                    print(f"\n  En olası kategoriler:")
                    for kategori, prob in sirali_olasiliklar:
                        emoji = "🏆" if kategori == tahmin else "  "
                        print(f"    {emoji} {kategori}: %{prob * 100:.2f}")
                    
                    # Sonuçları kaydet (opsiyonel)
                    self._sonuc_kaydet(mail_id, baslik, icerik, tahmin, olasiliklar)
                else:
                    print(f"✗ Kategorizasyon başarısız!")
                    print(f"  Tahmin: {tahmin}")
                    print(f"  Olasılıklar: {olasiliklar}")
            except Exception as e:
                print(f"✗ Kategorizasyon hatası: {e}")
                import traceback
                traceback.print_exc()
            
            # İşlenmiş olarak işaretle
            self.islenmis_mail_ids.add(mail_id)
            
            print(f"{'='*70}\n")
    
    def _sonuc_kaydet(self, mail_id: str, baslik: str, icerik: str, tahmin: str, olasiliklar: Dict):
        """Sonuçları dosyaya kaydet (opsiyonel)"""
        try:
            sonuc_dosyasi = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "mail_classifier_tester",
                "sonuclar.jsonl"
            )
            
            sonuc = {
                "zaman": datetime.now().isoformat(),
                "mail_id": mail_id,
                "baslik": baslik,
                "icerik": icerik[:500],  # İlk 500 karakter
                "tahmin": tahmin,
                "olasiliklar": {k: float(v) for k, v in olasiliklar.items()}
            }
            
            with open(sonuc_dosyasi, "a", encoding="utf-8") as f:
                f.write(json.dumps(sonuc, ensure_ascii=False) + "\n")
                
        except Exception as e:
            # Hata olsa bile devam et
            pass
    
    def baslat(self):
        """İzlemeyi başlat"""
        print("="*70)
        print("MAIL İZLEYİCİ - MAILHOG DİNLEME BAŞLATIYOR")
        print("="*70)
        
        # MailHog bağlantısını test et
        print("\n🔍 MailHog bağlantısı kontrol ediliyor...")
        if not self._mailhoga_baglan():
            print("✗ MailHog'a bağlanılamadı!")
            print("  Lütfen MailHog'un çalıştığından emin olun:")
            print("  - SMTP: localhost:1025")
            print("  - API: localhost:8025")
            sys.exit(1)
        
        print("✓ MailHog bağlantısı başarılı")
        print(f"\n⏰ Her {self.kontrol_araligi} saniyede bir kontrol edilecek")
        print("  Çıkmak için Ctrl+C basın\n")
        
        try:
            while True:
                # Yeni mailleri işle
                self._yeni_mailleri_isle()
                
                # Bekle
                time.sleep(self.kontrol_araligi)
                
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("👋 İzleyici durduruldu")
            print("="*70)


def main():
    """Ana fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MailHog\'u dinle ve mailleri kategorize et')
    parser.add_argument('--host', type=str, default="localhost", help='MailHog API host (varsayılan: localhost)')
    parser.add_argument('--port', type=int, default=8025, help='MailHog API port (varsayılan: 8025)')
    parser.add_argument('--aralik', type=int, default=2, help='Kontrol aralığı saniye (varsayılan: 2)')
    
    args = parser.parse_args()
    
    # İzleyiciyi oluştur ve başlat
    izleyici = MailHogIzleyici(
        api_host=args.host,
        api_port=args.port,
        kontrol_araligi=args.aralik
    )
    
    izleyici.baslat()


if __name__ == "__main__":
    main()

