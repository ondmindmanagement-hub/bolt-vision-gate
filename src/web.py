from __future__ import annotations
import tempfile
from pathlib import Path
from flask import Flask, jsonify, request

from vision_gate import analyze_file

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/analyze")
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "multipart field 'image' is required"}), 400

    uploaded = request.files["image"]
    suffix = Path(uploaded.filename or "image.png").suffix or ".png"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        uploaded.save(tmp.name)
        report = analyze_file(tmp.name)

    report["source"] = "uploaded_image"
    return jsonify(report)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
