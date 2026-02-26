"""
CSV veri seti ön-işleme aracı (veri madenciliği / rapor için).

Yapar:
1) Gürültülü karakter temizliği (URL/e-posta/sayı/noktalama/özel karakter)
2) Küçük harfe çevirme (Türkçe I/İ uyumlu)
3) Stopword kaldırma
4) Opsiyonel: TF-IDF matrisi üretme ve kaydetme

Kullanım örnekleri:
  python preprocess_dataset.py --input "mailler copy.csv" --output "mailler_clean.csv"
  python preprocess_dataset.py --input mailler.csv --output mailler_clean.csv --export-tfidf --tfidf-dir model
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import joblib
from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer

from mail_classifier_model.preprocessing import MetinTemizleyici
from mail_classifier_model.config import (
    CSV_DOSYASI,
    DEFAULT_MAX_DF,
    DEFAULT_MAX_FEATURES,
    DEFAULT_MIN_DF,
    DEFAULT_NGRAM_RANGE,
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mail veri seti temizleme ve TF-IDF hazırlama aracı")
    p.add_argument("--input", default=CSV_DOSYASI, help="Girdi CSV yolu (varsayılan: config.CSV_DOSYASI)")
    p.add_argument("--output", default="mailler_clean.csv", help="Temizlenmiş CSV çıktı yolu")
    p.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (varsayılan: utf-8-sig)")
    p.add_argument("--min-word-len", type=int, default=3, help="Minimum kelime uzunluğu (stopword filtresinde)")
    p.add_argument("--min-words", type=int, default=3, help="Minimum kelime sayısı (satırı tutmak için)")
    p.add_argument("--no-stopwords", action="store_true", help="Stopword kaldırmayı kapat")
    p.add_argument("--keep-empty", action="store_true", help="Boş/çok kısa metinleri de tut (önerilmez)")

    p.add_argument("--export-tfidf", action="store_true", help="TF-IDF matrisi ve vectorizer kaydet")
    p.add_argument("--tfidf-dir", default="model", help="TF-IDF çıktı klasörü (varsayılan: model/)")
    p.add_argument("--tfidf-max-features", type=int, default=DEFAULT_MAX_FEATURES)
    p.add_argument("--tfidf-min-df", type=float, default=DEFAULT_MIN_DF)
    p.add_argument("--tfidf-max-df", type=float, default=DEFAULT_MAX_DF)
    p.add_argument(
        "--tfidf-ngram-min",
        type=int,
        default=DEFAULT_NGRAM_RANGE[0],
        help="TF-IDF ngram min (varsayılan: config.DEFAULT_NGRAM_RANGE)",
    )
    p.add_argument(
        "--tfidf-ngram-max",
        type=int,
        default=DEFAULT_NGRAM_RANGE[1],
        help="TF-IDF ngram max (varsayılan: config.DEFAULT_NGRAM_RANGE)",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Girdi CSV bulunamadı: {input_path}")

    df = pd.read_csv(input_path, encoding=args.encoding)
    required_cols = ["Kategori", "Başlık", "İçerik"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"CSV kolonları eksik: {missing}. Beklenen kolonlar: {required_cols}")

    # NaN temizliği
    df = df.dropna(subset=required_cols).copy()

    temizleyici = MetinTemizleyici(
        remove_stopwords=not args.no_stopwords,
        min_length=args.min_word_len,
        turkce_lowercase=True,
    )

    # Temiz metin üret
    df["Mail_Metni"] = df["Başlık"].astype(str) + " " + df["İçerik"].astype(str)
    df["Mail_Metni_Temiz"] = temizleyici.transform(df["Mail_Metni"].values)

    if not args.keep_empty:
        df = df[df["Mail_Metni_Temiz"].str.strip() != ""]
        df = df[df["Mail_Metni_Temiz"].str.split().str.len() >= int(args.min_words)]

    # Çıktı klasörü
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("=" * 70)
    print("VERİSETİ TEMİZLEME TAMAMLANDI")
    print("=" * 70)
    print(f"Girdi:  {input_path}  (satır: {len(pd.read_csv(input_path, encoding=args.encoding))})")
    print(f"Çıktı:  {output_path}  (satır: {len(df)})")
    print(f"Stopword: {'kapalı' if args.no_stopwords else 'açık'} | min_word_len={args.min_word_len} | min_words={args.min_words}")

    if args.export_tfidf:
        tfidf_dir = Path(args.tfidf_dir)
        tfidf_dir.mkdir(parents=True, exist_ok=True)

        vectorizer = TfidfVectorizer(
            max_features=args.tfidf_max_features,
            ngram_range=(args.tfidf_ngram_min, args.tfidf_ngram_max),
            min_df=args.tfidf_min_df,
            max_df=args.tfidf_max_df,
            sublinear_tf=True,
        )
        X_tfidf = vectorizer.fit_transform(df["Mail_Metni_Temiz"].values)

        vec_path = tfidf_dir / "tfidf_vectorizer_preproc.pkl"
        mat_path = tfidf_dir / "tfidf_matrix_preproc.npz"
        feats_path = tfidf_dir / "tfidf_feature_names_preproc.txt"

        joblib.dump(vectorizer, vec_path)
        save_npz(mat_path, X_tfidf)
        feats_path.write_text("\n".join(vectorizer.get_feature_names_out()), encoding="utf-8")

        print("\nTF-IDF çıktıları kaydedildi:")
        print(f"- Vectorizer: {vec_path}")
        print(f"- Matrix:     {mat_path}  (shape={X_tfidf.shape})")
        print(f"- Features:   {feats_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


