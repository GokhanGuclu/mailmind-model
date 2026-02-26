<p align="center">
  <img alt="Python Version" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-1.3%2B-F7931E?logo=scikitlearn&logoColor=white">
  <img alt="XGBoost" src="https://img.shields.io/badge/XGBoost-2.x-EB5E28">
  <img alt="PyTorch" src="https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white">
  <img alt="Transformers" src="https://img.shields.io/badge/Transformers-4.30%2B-FFD21E">
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey">
</p>

<p align="center">
  <b>MailMind – Intelligent Email Category Classification</b>
</p>

---

MailMind is a production‑oriented machine learning project that **classifies Turkish emails into meaningful categories** (e.g. İş/Acil, Güvenlik/Uyarı, Pazarlama, Sosyal Medya, Spam, Abonelik/Fatura, Kişisel, Eğitim/Öğretim, Sağlık, Diğer).

The repository contains:

- A reusable Python package `mail_classifier_model` for **training, saving, loading and serving the model**
- A training entrypoint `mail_classifier_advanced.py`
- Testing utilities under `testler/`
- A MailHog + Gemini‑based tester under `mail_classifier_tester/`
- Pre‑trained models and result artifacts under `model/` and `model_result/`

---

## Project Structure

- **`mail_classifier_advanced.py`**: CLI script to train the advanced email classification model using the `mail_classifier_model` package.
- **`mail_classifier_model/`**: Core model package.
  - `config.py`: Global configuration (paths, hyper‑parameters, Turkish stopwords).
  - `data_loader.py`: Loads the labeled email dataset from CSV, performs cleaning and label encoding.
  - `preprocessing.py`: `MetinTemizleyici` (text cleaner/normalizer) and `MetrikCikarici` (feature/metric extractor for emails).
  - `vectorizers.py`: `DualTfidfVectorizer` that combines **word n‑gram** and **character n‑gram** TF‑IDF features.
  - `model_trainer.py`: Builds TF‑IDF + numeric features, compares multiple models, saves metrics, reports and plots.
  - `model_manager.py`: Saves and loads the trained model, vectorizer, scaler and preprocessing objects.
  - `predictor.py`: High‑level `tahmin_yap` API to classify a single email (subject + body) and return probabilities.
- **`mail_classifier_tester/`**: Integration testing utilities (see its own `README.md`).
  - `mail_olusturucu.py`: Uses Google Gemini to generate synthetic test emails and sends them to MailHog.
  - `mail_izleyici.py`: Polls MailHog, classifies incoming emails with MailMind and logs results.
- **`testler/`**:
  - `test_model_advanced.py`: Batch test with curated examples across all categories.
  - `test_interactive_advanced.py`: Interactive CLI where you type an email and see predicted categories with confidence bars.
  - `preprocess_dataset.py`: Helper for dataset preprocessing experiments.
- **`datasets/`**: Source CSV datasets for training (e.g. `mailler.csv`, cleaned variants).
- **`model/`**: Serialized trained artifacts (model, vectorizer, scaler, cleaner, label mappings, feature importance, etc.).
- **`model_result/`**: Evaluation reports and plots (classification report, confusion matrix, per‑class F1, model comparison).
- **`requirements.txt`**: Python dependencies.

---

## Features

- **Turkish‑aware preprocessing**
  - Robust lower‑casing for Turkish characters (İ/ı handling)
  - URL, email and number removal
  - Punctuation and noise filtering while keeping Turkish letters
  - Custom Turkish stopword list
  - Minimum token length and minimum word count filtering

- **Rich Feature Engineering**
  - Cleaned text through `MetinTemizleyici`
  - **Dual TF‑IDF** (`DualTfidfVectorizer`):
    - Word n‑grams with configurable `ngram_range` and `max_features`
    - Character n‑grams (`char_wb`) to capture suffixes, misspellings and spam patterns
  - Additional numeric metrics from `MetrikCikarici`, such as:
    - Word count, character count, sentence count
    - Uppercase character count
    - Number of exclamation and question marks
    - Average word length
  - Numeric metrics normalized with `StandardScaler` and concatenated to TF‑IDF features.

- **Model Comparison**
  - Trains and evaluates a set of models:
    - Multinomial Naive Bayes (TF‑IDF only)
    - Logistic Regression
    - Linear SVM
    - XGBoost
  - Uses **F1‑macro** (and accuracy, precision, recall) to select the best model.
  - Saves:
    - `model_comparison_metrics.csv` / `.json`
    - `model_comparison_f1_macro.png`
    - Confusion matrix CSV + heatmap (`confusion_matrix_normalized.png`)
    - Per‑class F1 bar chart (`per_class_f1.png`)
    - Overall best‑model metrics JSON (`metrikler_advanced.json`)

- **Production‑oriented Artifacts**
  - Model, vectorizer, scaler, text cleaner, metric extractor and label mappings are saved under `model/`:
    - `mail_model_advanced.pkl`
    - `mail_vectorizer_advanced.pkl`
    - `scaler_advanced.pkl`
    - `temizleyici_advanced.pkl`
    - `metrik_cikarici_advanced.pkl`
    - `label_to_id_advanced.npy`, `id_to_label_advanced.npy`
  - `predictor.tahmin_yap` unifies loading and prediction for external integrations.

---

## Installation

### 1. Clone the repository

```bash
git clone <this-repo-url>
cd mailmind-model
```

### 2. (Optional) Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate  # on Windows
# source .venv/bin/activate  # on macOS / Linux
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> Note: Some models (e.g. XGBoost, PyTorch/Transformers) may require a C++ build toolchain and can take time to install.

---

## Data

The main training dataset is expected as a CSV file with Turkish column names:

- **Required columns**
  - `Kategori`: Target label (one of the supported categories)
  - `Başlık`: Email subject
  - `İçerik`: Email body

During loading (`data_loader.veri_yukle`):

- Rows with missing `Kategori`, `Başlık` or `İçerik` are dropped.
- `Başlık` and `İçerik` are concatenated into `Mail_Metni`.
- Cleaned text is stored in `Mail_Metni_Temiz`.
- Extremely short or empty texts are removed (minimum 3 tokens).
- Label mappings (`label_to_id`, `id_to_label`) are created and saved under `model/`.

By default the CSV path is configured in `mail_classifier_model/config.py` (`CSV_DOSYASI`).  
You can override it from the CLI with `--csv`.

---

## Training the Model

Run the following command in the project root:

```bash
python mail_classifier_advanced.py
```

Optional arguments:

- **`--csv PATH`**: Custom training CSV path. If omitted, the default in `config.CSV_DOSYASI` is used.

The script will:

1. Load and preprocess data via `veri_yukle`.
2. Build TF‑IDF + numeric features.
3. Train and compare candidate models.
4. Select the **best** model by F1‑macro.
5. Save:
   - The best model and all preprocessing components (under `model/`).
   - Evaluation metrics and plots (under `model_result/`).

Console output includes:

- Dataset size and label distribution
- Total feature counts (TF‑IDF features vs numeric metrics)
- Training and total time per model
- Accuracy, F1‑macro, precision‑macro, recall‑macro
- Detailed classification report and confusion matrix summary

---

## Using the Model Programmatically

The main prediction API lives in `mail_classifier_model/predictor.py`:

```python
from mail_classifier_model import tahmin_yap

subject = "Bugünkü proje toplantısı ertelendi"
body = "Merhaba, bugün yapılması planlanan proje toplantısı ertelenmiştir. Yeni tarih duyurulacaktır."

predicted_label, probabilities = tahmin_yap(subject, body)

print("Predicted:", predicted_label)
print("Probabilities:", probabilities)
```

Behavior:

- On first call (or when you pass `model=None`), `tahmin_yap` will:
  - Load the saved model and components via `model_manager.model_yukle`.
  - Load optional label mappings when available.
- It:
  - Cleans the concatenated text (`subject + " " + body`) with `MetinTemizleyici`.
  - Transforms it with the saved `DualTfidfVectorizer`.
  - Computes numeric metrics with `MetrikCikarici` and scales them with the saved `StandardScaler`.
  - Concatenates and feeds features to the model.
  - Returns:
    - **`tahmin`**: best category label.
    - **`olasiliklar`**: dictionary `label -> probability`.
- If the underlying model does not expose `predict_proba` (e.g. LinearSVC), it approximates probabilities via a calibrated decision function / softmax.

You can optionally pass a **confidence threshold**:

```python
predicted_label, probabilities = tahmin_yap(
    subject,
    body,
    min_guven=0.6,
    fallback_label="Diğer"
)
```

If the best class probability is below `min_guven`, the function will return the `fallback_label`.

---

## CLI Testing Utilities

### Batch Advanced Test (`test_model_advanced.py`)

Runs a large curated suite of emails (10 categories × 10 examples each) through the model and reports accuracy:

```bash
python testler/test_model_advanced.py
```

It prints, for each example:

- Expected category (`beklenen`)
- Predicted category and confidence
- Top‑N alternative categories with probabilities

At the end it prints overall accuracy.

### Interactive CLI (`test_interactive_advanced.py`)

An interactive console where you can manually type email subject + body and see predicted categories with a simple bar visualization:

```bash
python testler/test_interactive_advanced.py
```

Features:

- Lists all supported categories.
- Special commands:
  - Typing **`çıkış`** or **`exit`** quits.
  - Leaving the subject empty runs a built‑in demo example.
- Shows:
  - Predicted category
  - Raw confidence
  - Top 3 categories with normalized probabilities and ASCII bar chart
  - A qualitative confidence message (low / medium / high).

---

## MailHog & Gemini‑Based Testing

The `mail_classifier_tester` package allows you to test the model on **live emails** captured via MailHog and synthetic messages generated by Google Gemini.

For detailed instructions, see `mail_classifier_tester/README.md`. In summary:

- Requires:
  - **MailHog** running locally.
  - **Gemini API key** in a `.env` file in the project root.
- Provides:
  - `mail_olusturucu.py`: generates and sends categorized test emails to MailHog.
  - `mail_izleyici.py`: continuously polls MailHog, classifies new messages with the model, logs JSON lines to `sonuclar.jsonl`.

---

## Configuration

Key configuration is in `mail_classifier_model/config.py`:

- **Paths**
  - `CSV_DOSYASI`: Default training CSV.
  - `MODEL_DIR`, `RESULT_DIR`: Directories where models and evaluation artifacts are saved.
  - File paths for all persisted components.
- **Turkish stopwords**
  - `TURKCE_STOPWORDS`: A curated Turkish stopword set used by `MetinTemizleyici`.
- **Vectorizer hyper‑parameters**
  - `DEFAULT_NGRAM_RANGE`, `DEFAULT_MAX_FEATURES`, `DEFAULT_MIN_DF`, `DEFAULT_MAX_DF`.

You can change these values to tune performance/size trade‑offs or adapt to new datasets.

---

## Dependencies

Main libraries (see `requirements.txt` for exact versions):

- `pandas`, `numpy`, `scikit-learn`, `scipy`
- `matplotlib`, `seaborn`
- `xgboost`
- `joblib`
- `google-generativeai`, `transformers`, `torch`, `datasets`, `accelerate` (for Gemini / LLM‑based utilities and potential future extensions)
- `python-dotenv`, `requests`

---

## How to Integrate in Another Project

- Use `mail_classifier_model` as a **pure Python package**:
  - Install this repository (editable or as a dependency).
  - Train and export a model in this repo.
  - In your application, simply import and call:

```python
from mail_classifier_model import tahmin_yap

label, probs = tahmin_yap(subject, body)
```

- You can wrap `tahmin_yap` in:
  - A REST API (FastAPI, Flask, Django, etc.)
  - A background worker consuming emails from an inbox or queue
  - A microservice that classifies and routes incoming support tickets.

---

## License

This project is licensed under the **MIT License**.  
See the `LICENSE` file for full text.

#   m a i l m i n d - m o d e l  
 