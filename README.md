# SentinelGuard

Toxic / abusive content detection system for a college major project. The app trains real multi-label classifiers on the Jigsaw Toxic Comment Classification dataset, then serves predictions through a Flask dashboard with history and analytics.

## What it does

- Classifies a comment into six labels: Toxic, Severe Toxic, Obscene, Threat, Insult, Identity Hate
- Shows confidence scores and a moderation decision (`SAFE`, `REVIEW`, or `BLOCK`)
- Stores every analysis in SQLite by default (MySQL is supported)
- Compares Logistic Regression, Naive Bayes, and Linear SVM on a held-out validation split
- Reports official labeled Jigsaw test metrics without dummy numbers

## Project structure

```text
dataset/raw            Jigsaw train/test CSVs
dataset/processed      Split summary after preprocessing
ml                     Preprocessing and training pipeline
models                 Saved TF-IDF vectorizer, classifier, metrics
backend                Flask APIs and predictor
frontend               Dashboard HTML/CSS/JS
database               MySQL schema
evaluation             Confusion-matrix plots
tests                  Sample API and preprocessing tests
```

## Dataset

Source: [Jigsaw Toxic Comment Classification Challenge](https://huggingface.co/datasets/thesofakillers/jigsaw-toxic-comment-classification-challenge)

- Training comments: 159,571
- Six multi-label toxicity targets
- Official test comments with labels (`-1` rows are discarded)

Download:

```bash
python -m ml.download_dataset
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

SQLite is the default database so the demo can run without MySQL:

```text
DATABASE_URL=sqlite:///database/sentinel.db
```

MySQL option:

```bash
mysql -u root -p < database/schema.sql
```

Then set:

```text
DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/sentinel_guard
```

## Train the model

```bash
python -m ml.train
```

The script:

1. Cleans text and removes empty rows
2. Splits training data into train / validation (85 / 15), stratified by any-toxic
3. Fits TF-IDF word/char n-grams
4. Trains Logistic Regression, Naive Bayes, and Linear SVM
5. Selects the best model by validation macro-F1
6. Evaluates once on the official labeled test set
7. Writes `models/best_model.joblib`, `models/tfidf_vectorizer.joblib`, and `models/metrics.json`

Do not use the test split during training. The saved metrics are measured after model selection.

## Run the web app

```bash
python run.py
```

Open `http://127.0.0.1:5000`.

API endpoints:

- `POST /api/analyze` body: `{ "text": "..." }`
- `GET /api/history`
- `GET /api/analytics`
- `GET /api/metrics`
- `GET /health`

## Tests

```bash
python -m pytest tests -q
```

Sample comments live in `tests/sample_cases.json`.

## Notes on accuracy

Toxic comments are rare (about 10% of training rows). A model can look accurate while missing abuse. This project reports accuracy, precision, recall, F1, ROC-AUC, and confusion matrices. Selection uses macro-F1, not raw accuracy.

BERT is optional and not included in the default pipeline because it needs a GPU and a much longer training cycle. The classical TF-IDF + Linear SVM / Logistic Regression stack is the recommended baseline for this demo.
