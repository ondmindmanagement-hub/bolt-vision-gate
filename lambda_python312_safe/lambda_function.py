"""BOLT Vision Gate — candidate AWS Lambda Python 3.12 migration.

SECURITY CHANGE: This version accepts inline base64-encoded images only. The
previous image_url fetch capability allowed user-controlled outbound HTTP
requests and is intentionally disabled to prevent server-side request
forgery (SSRF) and access to private VPC/metadata endpoints.

DO NOT DEPLOY to an existing Lambda before identifying its callers; the
request contract is different. See README.md.
"""
from __future__ import annotations

import base64
import binascii
import json

import cv2
import numpy as np

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_ENCODED_CHARS = (MAX_IMAGE_BYTES * 4 // 3) + 8


def response(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
            "access-control-allow-origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def analyze_frame(image) -> dict:
    if image is None or getattr(image, "ndim", 0) < 2:
        raise ValueError("Could not decode image")
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError("Only color JPEG/PNG images are supported")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    brightness = float(np.mean(gray))
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(np.count_nonzero(edges) / max(1, edges.size))
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
    return {
        "opencv_version": cv2.__version__,
        "width": int(w), "height": int(h),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "blur_variance": round(blur_variance, 2),
        "edge_density": round(edge_density, 5),
        "decision": "human_review" if reasons else "allow",
        "reasons": reasons,
    }


def lambda_handler(event: dict, context) -> dict:
    if not isinstance(event, dict):
        return response(400, {"error": "invalid_request"})
    path = event.get("rawPath", "/")
    method = str((event.get("requestContext") or {}).get("http", {}).get("method") or "GET").upper()
    if method == "GET" and path in ("/", "/health"):
        return response(200, {"ok": True, "service": "BOLT Vision Gate", "version": "python312-safe",
                              "opencv_version": cv2.__version__})
    if method != "POST" or path != "/analyze":
        return response(404, {"error": "Use GET /health or POST /analyze"})

    try:
        raw_body = event.get("body") or "{}"
        if not isinstance(raw_body, str) or len(raw_body) > MAX_ENCODED_CHARS + 1000:
            return response(413, {"error": "payload_too_large"})
        if event.get("isBase64Encoded"):
            raw_body = base64.b64decode(raw_body, validate=True).decode("utf-8")
        payload = json.loads(raw_body)
        if not isinstance(payload, dict):
            return response(400, {"error": "JSON object required"})

        # Explicitly fail closed: do not fetch attacker-controlled remote URLs.
        if "image_url" in payload:
            return response(400, {"error": "image_url is not accepted; send image_base64 instead"})
        encoded = payload.get("image_base64")
        if not isinstance(encoded, str) or not encoded:
            return response(400, {"error": "image_base64 is required"})
        if len(encoded) > MAX_ENCODED_CHARS:
            return response(413, {"error": "image_too_large"})
        data = base64.b64decode(encoded, validate=True)
        if len(data) > MAX_IMAGE_BYTES:
            return response(413, {"error": "image_too_large"})
        if not (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff")):
            return response(400, {"error": "Only PNG or JPEG images are accepted"})

        arr = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            return response(400, {"error": "image_decode_failed"})
        report = analyze_frame(image)
        report["source"] = "inline_image"
        return response(200, report)
    except (ValueError, UnicodeError, json.JSONDecodeError, binascii.Error):
        return response(400, {"error": "invalid_image_payload"})
    except Exception:
        # Avoid publishing implementation details to unauthenticated callers.
        return response(500, {"error": "internal_error"})
