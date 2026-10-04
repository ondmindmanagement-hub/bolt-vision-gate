from __future__ import annotations
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def analyze_frame(image: np.ndarray) -> dict:
    if image is None or image.size == 0:
        raise ValueError("empty image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]

    brightness = float(np.mean(gray))
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(np.count_nonzero(edges) / edges.size)

    contrast = float(np.std(gray))

    reasons = []
    if brightness < 40:
        reasons.append("scene_too_dark")
    if brightness > 230:
        reasons.append("scene_overexposed")
    if blur_variance < 35:
        reasons.append("image_too_blurry")
    if edge_density < 0.005:
        reasons.append("insufficient_visual_structure")
    if contrast < 12:
        reasons.append("low_contrast")

    decision = "human_review" if reasons else "allow"

    return {
        "opencv_version": cv2.__version__,
        "width": int(width),
        "height": int(height),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "blur_variance": round(blur_variance, 2),
        "edge_density": round(edge_density, 5),
        "decision": decision,
        "reasons": reasons,
    }


def analyze_file(path: str | Path) -> dict:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(path)
    result = analyze_frame(image)
    result["source"] = str(path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BOLT Vision Gate: OpenCV 5 visual quality and human-review gate."
    )
    parser.add_argument("image", help="Path to an image")
    parser.add_argument("--json-out", help="Optional path for JSON report")
    args = parser.parse_args()

    report = analyze_file(args.image)
    payload = json.dumps(report, indent=2)
    print(payload)

    if args.json_out:
        Path(args.json_out).write_text(payload + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
