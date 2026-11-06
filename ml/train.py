"""Train and compare multi-label toxicity classifiers on the Jigsaw dataset."""

import json
import os
import time
from datetime import datetime, timezone

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from ml.config import (
    COMPARISON_PATH,
    EVAL_DIR,
    LABELS,
    MAX_DF,
    MAX_FEATURES,
    METRICS_PATH,
    MIN_DF,
    MODEL_DIR,
    MODEL_PATH,
    NGRAM_RANGE,
    PROCESSED_DIR,
    RANDOM_STATE,
    RAW_TEST,
    RAW_TEST_LABELS,
    RAW_TRAIN,
    TOXICITY_THRESHOLD,
    VAL_SIZE,
    VECTORIZER_PATH,
)
from ml.preprocess import clean_text


def load_frames():
    train_df = pd.read_csv(RAW_TRAIN)
    test_df = pd.read_csv(RAW_TEST)
    test_labels = pd.read_csv(RAW_TEST_LABELS)
    test_full = test_df.merge(test_labels, on="id")
    labeled_test = test_full[(test_full[LABELS] != -1).all(axis=1)].copy()
    train_df = train_df.drop_duplicates(subset=["comment_text"]).dropna(subset=["comment_text"])
    labeled_test = labeled_test.drop_duplicates(subset=["comment_text"]).dropna(subset=["comment_text"])
    return train_df, labeled_test


def add_clean_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["clean_text"] = df["comment_text"].astype(str).map(clean_text)
    df = df[df["clean_text"].str.len() > 0]
    return df


def build_models():
    return {
        "logistic_regression": OneVsRestClassifier(
            LogisticRegression(
                solver="liblinear",
                class_weight="balanced",
                max_iter=400,
                C=1.0,
            ),
            n_jobs=1,
        ),
        "naive_bayes": OneVsRestClassifier(MultinomialNB(alpha=0.3), n_jobs=1),
        "linear_svm": OneVsRestClassifier(
            LinearSVC(class_weight="balanced", C=0.5, max_iter=4000, dual="auto"),
            n_jobs=1,
        ),
    }


def decision_scores(estimator, X):
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(X)
    scores = estimator.decision_function(X)
    return 1.0 / (1.0 + np.exp(-scores))


def subset_metrics(y_true, y_pred, y_score):
    per_label = {}
    for idx, label in enumerate(LABELS):
        yt = y_true[:, idx]
        yp = y_pred[:, idx]
        ys = y_score[:, idx]
        item = {
            "accuracy": float(accuracy_score(yt, yp)),
            "precision": float(precision_score(yt, yp, zero_division=0)),
            "recall": float(recall_score(yt, yp, zero_division=0)),
            "f1": float(f1_score(yt, yp, zero_division=0)),
            "support": int(yt.sum()),
        }
        if len(np.unique(yt)) > 1:
            item["roc_auc"] = float(roc_auc_score(yt, ys))
            item["pr_auc"] = float(average_precision_score(yt, ys))
        else:
            item["roc_auc"] = None
            item["pr_auc"] = None
        per_label[label] = item

    any_true = (y_true.sum(axis=1) > 0).astype(int)
    any_pred = (y_pred.sum(axis=1) > 0).astype(int)
    any_score = y_score.max(axis=1)
    overall = {
        "subset_accuracy": float(accuracy_score(y_true, y_pred)),
        "hamming_accuracy": float(1.0 - np.mean(y_true != y_pred)),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "micro_f1": float(f1_score(y_true, y_pred, average="micro", zero_division=0)),
        "any_toxic_accuracy": float(accuracy_score(any_true, any_pred)),
        "any_toxic_precision": float(precision_score(any_true, any_pred, zero_division=0)),
        "any_toxic_recall": float(recall_score(any_true, any_pred, zero_division=0)),
        "any_toxic_f1": float(f1_score(any_true, any_pred, zero_division=0)),
        "any_toxic_roc_auc": float(roc_auc_score(any_true, any_score)),
        "macro_roc_auc": float(roc_auc_score(y_true, y_score, average="macro")),
    }
    return overall, per_label


def save_confusion_matrices(y_true, y_pred, model_name, split_name):
    os.makedirs(EVAL_DIR, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()
    for idx, label in enumerate(LABELS):
        cm = confusion_matrix(y_true[:, idx], y_pred[:, idx])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[idx], cbar=False)
        axes[idx].set_title(label.replace("_", " ").title())
        axes[idx].set_xlabel("Predicted")
        axes[idx].set_ylabel("Actual")
    fig.suptitle(f"{model_name} confusion matrices ({split_name})")
    fig.tight_layout()
    path = os.path.join(EVAL_DIR, f"confusion_{model_name}_{split_name}.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def evaluate(estimator, X, y, model_name, split_name):
    y_score = decision_scores(estimator, X)
    y_pred = (y_score >= TOXICITY_THRESHOLD).astype(int)
    overall, per_label = subset_metrics(y, y_pred, y_score)
    cm_path = save_confusion_matrices(y, y_pred, model_name, split_name)
    report = classification_report(
        y,
        y_pred,
        target_names=LABELS,
        zero_division=0,
        output_dict=True,
    )
    return {
        "overall": overall,
        "per_label": per_label,
        "classification_report": report,
        "confusion_matrix_path": cm_path,
    }


def persist_split_preview(train_df, val_df, test_df):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    summary = {
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "holdout_test_rows": int(len(test_df)),
        "train_positive_rate": {k: float(train_df[k].mean()) for k in LABELS},
        "val_positive_rate": {k: float(val_df[k].mean()) for k in LABELS},
        "test_positive_rate": {k: float(test_df[k].mean()) for k in LABELS},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(PROCESSED_DIR, "split_summary.json"), "w") as handle:
        json.dump(summary, handle, indent=2)
    return summary


def main():
    started = time.time()
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(EVAL_DIR, exist_ok=True)

    print("Loading dataset...")
    train_raw, test_raw = load_frames()
    print(f"  train={len(train_raw)}  labeled_test={len(test_raw)}")

    print("Cleaning text...")
    train_raw = add_clean_column(train_raw)
    test_raw = add_clean_column(test_raw)

    any_toxic = (train_raw[LABELS].sum(axis=1) > 0).astype(int)
    train_df, val_df = train_test_split(
        train_raw,
        test_size=VAL_SIZE,
        random_state=RANDOM_STATE,
        stratify=any_toxic,
    )
    split_summary = persist_split_preview(train_df, val_df, test_raw)
    print("Split summary:", json.dumps(split_summary, indent=2))

    print("Fitting TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        ngram_range=NGRAM_RANGE,
        min_df=MIN_DF,
        max_df=MAX_DF,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    X_train = vectorizer.fit_transform(train_df["clean_text"])
    X_val = vectorizer.transform(val_df["clean_text"])
    X_test = vectorizer.transform(test_raw["clean_text"])
    y_train = train_df[LABELS].to_numpy(dtype=int)
    y_val = val_df[LABELS].to_numpy(dtype=int)
    y_test = test_raw[LABELS].to_numpy(dtype=int)
    print(f"  vocabulary={len(vectorizer.vocabulary_)}  train_shape={X_train.shape}")

    comparison = {}
    best_name = None
    best_score = -1.0
    best_estimator = None

    for name, model in build_models().items():
        print(f"\nTraining {name}...")
        t0 = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - t0
        val_metrics = evaluate(model, X_val, y_val, name, "validation")
        score = val_metrics["overall"]["macro_f1"]
        comparison[name] = {
            "train_seconds": round(elapsed, 2),
            "validation": val_metrics["overall"],
            "validation_per_label": val_metrics["per_label"],
        }
        print(
            f"  val macro-F1={score:.4f}  any-toxic-F1="
            f"{val_metrics['overall']['any_toxic_f1']:.4f}  ({elapsed:.1f}s)"
        )
        if score > best_score:
            best_score = score
            best_name = name
            best_estimator = model

    print(f"\nBest validation model: {best_name} (macro-F1={best_score:.4f})")
    print("Evaluating best model on official labeled holdout test set...")
    test_metrics = evaluate(best_estimator, X_test, y_test, best_name, "test")
    print("Test overall:", json.dumps(test_metrics["overall"], indent=2))

    pipeline = Pipeline(
        [
            ("tfidf", vectorizer),
            ("clf", best_estimator),
        ]
    )

    payload = {
        "best_model": best_name,
        "threshold": TOXICITY_THRESHOLD,
        "labels": LABELS,
        "vectorizer": {
            "max_features": MAX_FEATURES,
            "ngram_range": list(NGRAM_RANGE),
            "min_df": MIN_DF,
            "max_df": MAX_DF,
            "vocabulary_size": int(len(vectorizer.vocabulary_)),
        },
        "split": split_summary,
        "comparison": comparison,
        "test": {
            "overall": test_metrics["overall"],
            "per_label": test_metrics["per_label"],
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "train_seconds_total": round(time.time() - started, 2),
        "notes": (
            "Metrics are measured on a held-out labeled Jigsaw test split that was "
            "never used during training or model selection. Accuracy is high because "
            "the dataset is imbalanced; F1/ROC-AUC are the primary selection metrics."
        ),
    }

    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(best_estimator, MODEL_PATH)
    joblib.dump(pipeline, os.path.join(MODEL_DIR, "pipeline.joblib"))
    with open(METRICS_PATH, "w") as handle:
        json.dump(payload, handle, indent=2)
    with open(COMPARISON_PATH, "w") as handle:
        json.dump(comparison, handle, indent=2)

    print(f"\nSaved model to {MODEL_PATH}")
    print(f"Saved metrics to {METRICS_PATH}")
    print(f"Done in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
