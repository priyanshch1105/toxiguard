import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request, send_from_directory

from backend.config import Config
from backend.models import Analysis, init_db
from backend.predictor import ModelNotReadyError, classify_text, load_artifacts
from ml.config import LABELS, LABEL_DISPLAY, METRICS_PATH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "frontend", "templates")
STATIC_DIR = os.path.join(ROOT, "frontend", "static")


def create_app():
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
        static_url_path="/static",
    )
    app.config.from_object(Config)
    _, SessionLocal = init_db(app.config["DATABASE_URL"])
    app.session_factory = SessionLocal

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        ready = True
        detail = "ok"
        try:
            load_artifacts()
        except ModelNotReadyError as exc:
            ready = False
            detail = str(exc)
        return jsonify({"status": "ok" if ready else "training", "detail": detail})

    @app.post("/api/analyze")
    def analyze():
        payload = request.get_json(silent=True) or {}
        text = payload.get("text", "")
        source = str(payload.get("source", "web"))[:64]
        try:
            result = classify_text(text, max_length=app.config["MAX_TEXT_LENGTH"])
        except ModelNotReadyError as exc:
            return jsonify({"error": str(exc)}), 503
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        session = app.session_factory()
        try:
            row = Analysis(
                comment_text=result["text"],
                clean_text=result["clean_text"],
                is_toxic=result["is_toxic"],
                moderation_result=result["moderation_result"],
                toxic=result["labels"]["toxic"]["score"],
                severe_toxic=result["labels"]["severe_toxic"]["score"],
                obscene=result["labels"]["obscene"]["score"],
                threat=result["labels"]["threat"]["score"],
                insult=result["labels"]["insult"]["score"],
                identity_hate=result["labels"]["identity_hate"]["score"],
                max_confidence=result["max_confidence"],
                triggered_labels=json.dumps(result["triggered_labels"]),
                source=source,
            )
            session.add(row)
            session.commit()
            result["id"] = row.id
            result["created_at"] = row.created_at.isoformat() + "Z"
        finally:
            session.close()
        return jsonify(result)

    @app.get("/api/history")
    def history():
        limit = min(int(request.args.get("limit", 50)), 200)
        session = app.session_factory()
        try:
            rows = (
                session.query(Analysis)
                .order_by(Analysis.created_at.desc())
                .limit(limit)
                .all()
            )
            return jsonify([_serialize_row(row) for row in rows])
        finally:
            session.close()

    @app.get("/api/analytics")
    def analytics():
        session = app.session_factory()
        try:
            rows = session.query(Analysis).all()
            total = len(rows)
            toxic_count = sum(1 for row in rows if row.is_toxic)
            safe_count = total - toxic_count
            moderation = defaultdict(int)
            label_hits = {label: 0 for label in LABELS}
            daily = defaultdict(lambda: {"total": 0, "toxic": 0})
            recent_cutoff = datetime.utcnow() - timedelta(days=13)

            for row in rows:
                moderation[row.moderation_result] += 1
                for label in LABELS:
                    if getattr(row, label, 0) >= 0.5:
                        label_hits[label] += 1
                if row.created_at and row.created_at >= recent_cutoff:
                    key = row.created_at.date().isoformat()
                    daily[key]["total"] += 1
                    if row.is_toxic:
                        daily[key]["toxic"] += 1

            timeline = []
            for offset in range(13, -1, -1):
                day = (datetime.utcnow() - timedelta(days=offset)).date().isoformat()
                timeline.append(
                    {
                        "date": day,
                        "total": daily[day]["total"],
                        "toxic": daily[day]["toxic"],
                    }
                )

            return jsonify(
                {
                    "totals": {
                        "analyzed": total,
                        "toxic": toxic_count,
                        "safe": safe_count,
                        "toxic_rate": round((toxic_count / total) if total else 0.0, 4),
                    },
                    "moderation": dict(moderation),
                    "label_distribution": {
                        LABEL_DISPLAY[k]: v for k, v in label_hits.items()
                    },
                    "timeline": timeline,
                }
            )
        finally:
            session.close()

    @app.get("/api/metrics")
    def metrics():
        if not os.path.exists(METRICS_PATH):
            return jsonify({"error": "Model metrics are not available yet."}), 503
        with open(METRICS_PATH, "r") as handle:
            payload = json.load(handle)
        return jsonify(payload)

    @app.get("/evaluation/<path:filename>")
    def evaluation_files(filename):
        return send_from_directory(os.path.join(ROOT, "evaluation"), filename)

    return app


def _serialize_row(row: Analysis) -> dict:
    try:
        triggered = json.loads(row.triggered_labels or "[]")
    except json.JSONDecodeError:
        triggered = []
    return {
        "id": row.id,
        "text": row.comment_text,
        "is_toxic": bool(row.is_toxic),
        "moderation_result": row.moderation_result,
        "max_confidence": row.max_confidence,
        "triggered_labels": triggered,
        "scores": {label: getattr(row, label) for label in LABELS},
        "created_at": row.created_at.isoformat() + "Z" if row.created_at else None,
        "source": row.source,
    }


app = create_app()
