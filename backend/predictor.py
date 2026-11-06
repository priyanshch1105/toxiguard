import json
import os
from functools import lru_cache

import joblib
import numpy as np

from ml.config import LABELS, LABEL_DISPLAY, METRICS_PATH, MODEL_PATH, TOXICITY_THRESHOLD, VECTORIZER_PATH
from ml.preprocess import clean_text, validate_input


class ModelNotReadyError(RuntimeError):
    pass


def _sigmoid(values):
    values = np.clip(values, -30, 30)
    return 1.0 / (1.0 + np.exp(-values))


@lru_cache(maxsize=1)
def load_artifacts():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        raise ModelNotReadyError(
            "Trained model artifacts were not found. Run `python -m ml.train` first."
        )
    vectorizer = joblib.load(VECTORIZER_PATH)
    classifier = joblib.load(MODEL_PATH)
    metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as handle:
            metrics = json.load(handle)
    return vectorizer, classifier, metrics


def scores_from_estimator(estimator, features):
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(features)
    return _sigmoid(estimator.decision_function(features))


def classify_text(raw_text: str, max_length: int = 5000) -> dict:
    text = validate_input(raw_text, max_length=max_length)
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Comment text has no usable words after preprocessing.")

    vectorizer, classifier, metrics = load_artifacts()
    features = vectorizer.transform([cleaned])
    probabilities = scores_from_estimator(classifier, features)[0]

    labels = {}
    triggered = []
    for name, score in zip(LABELS, probabilities):
        confidence = float(np.clip(score, 0.0, 1.0))
        flagged = confidence >= TOXICITY_THRESHOLD
        labels[name] = {
            "label": LABEL_DISPLAY[name],
            "score": round(confidence, 4),
            "flagged": flagged,
        }
        if flagged:
            triggered.append(LABEL_DISPLAY[name])

    max_confidence = float(max(item["score"] for item in labels.values()))
    is_toxic = len(triggered) > 0
    if not is_toxic:
        moderation = "SAFE"
    elif "Severe Toxic" in triggered or "Threat" in triggered:
        moderation = "BLOCK"
    elif max_confidence >= 0.80:
        moderation = "BLOCK"
    else:
        moderation = "REVIEW"

    return {
        "text": text,
        "clean_text": cleaned,
        "labels": labels,
        "triggered_labels": triggered,
        "is_toxic": is_toxic,
        "moderation_result": moderation,
        "max_confidence": round(max_confidence, 4),
        "threshold": TOXICITY_THRESHOLD,
        "model_name": metrics.get("best_model", "unknown"),
    }
