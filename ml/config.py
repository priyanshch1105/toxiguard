import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LABELS = [
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
]

LABEL_DISPLAY = {
    "toxic": "Toxic",
    "severe_toxic": "Severe Toxic",
    "obscene": "Obscene",
    "threat": "Threat",
    "insult": "Insult",
    "identity_hate": "Identity Hate",
}

RAW_TRAIN = os.path.join(ROOT, "dataset", "raw", "train.csv")
RAW_TEST = os.path.join(ROOT, "dataset", "raw", "test.csv")
RAW_TEST_LABELS = os.path.join(ROOT, "dataset", "raw", "test_labels.csv")
PROCESSED_DIR = os.path.join(ROOT, "dataset", "processed")
MODEL_DIR = os.path.join(ROOT, "models")
EVAL_DIR = os.path.join(ROOT, "evaluation")

VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")
COMPARISON_PATH = os.path.join(MODEL_DIR, "model_comparison.json")

TOXICITY_THRESHOLD = 0.50
MAX_TEXT_LENGTH = 5000
RANDOM_STATE = 42
VAL_SIZE = 0.15
MAX_FEATURES = 25000
NGRAM_RANGE = (1, 2)
MIN_DF = 3
MAX_DF = 0.9
