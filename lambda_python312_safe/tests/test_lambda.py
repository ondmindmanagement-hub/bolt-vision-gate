"""Contract-level unit tests for candidate AWS migration; no production AWS calls."""
import base64
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault("cv2", types.SimpleNamespace(__version__="5.test", IMREAD_COLOR=1))
sys.modules.setdefault("numpy", types.SimpleNamespace(uint8="uint8"))

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "lambda_function.py"
spec = importlib.util.spec_from_file_location("vision_migration_candidate", SOURCE)
handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler)


def event(body, method="POST", path="/analyze"):
    return {
        "rawPath": path,
        "requestContext": {"http": {"method": method}},
        "body": json.dumps(body),
    }


def parsed(res):
    return res["statusCode"], json.loads(res["body"])


class CandidateTests(unittest.TestCase):
    def test_health(self):
        status, body = parsed(handler.lambda_handler(event({}, method="GET", path="/health"), None))
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "BOLT Vision Gate")

    def test_no_server_side_external_url(self):
        for u in ("http://169.254.169.254/latest/meta-data/", "http://127.0.0.1/", "https://example.com/"):
            with self.subTest(url=u):
                status, body = parsed(handler.lambda_handler(event({"image_url": u}), None))
                self.assertEqual(status, 400)
                self.assertIn("image_url is not accepted", body["error"])

    def test_missing_base64(self):
        self.assertEqual(parsed(handler.lambda_handler(event({}), None))[0], 400)

    def test_unknown_path(self):
        self.assertEqual(parsed(handler.lambda_handler(event({}, path="/favicon.ico"), None))[0], 404)

    def test_invalid_json(self):
        res = handler.lambda_handler({
            "rawPath": "/analyze",
            "requestContext": {"http": {"method": "POST"}},
            "body": "{no_json}",
        }, None)
        self.assertEqual(res["statusCode"], 400)

    def test_bad_base64(self):
        self.assertEqual(parsed(handler.lambda_handler(event({"image_base64": "%%%"}), None))[0], 400)

    def test_oversized_data(self):
        fake = "A" * (handler.MAX_ENCODED_CHARS + 1)
        self.assertEqual(parsed(handler.lambda_handler(event({"image_base64": fake}), None))[0], 413)

    def test_rejects_wrong_mime_bytes(self):
        text = base64.b64encode(b"not an image").decode()
        self.assertEqual(parsed(handler.lambda_handler(event({"image_base64": text}), None))[0], 400)

    def test_jpeg_passes_to_decoder(self):
        contents = b"\\xff\\xd8\\xff" + b"TEST"
        contents = bytes([255,216,255]) + b"TEST"
        b64 = base64.b64encode(contents).decode()
        with patch.object(handler.np, "frombuffer", return_value="encoded-array", create=True) as frombuffer, \
             patch.object(handler.cv2, "imdecode", return_value="image", create=True) as imdecode, \
             patch.object(handler, "analyze_frame", return_value={"decision":"human_review"}) as analyze:
            status, body = parsed(handler.lambda_handler(event({"image_base64": b64}), None))
        self.assertEqual(status, 200)
        self.assertEqual(body["source"], "inline_image")
        imdecode.assert_called_once()
        frombuffer.assert_called_once()
        analyze.assert_called_once_with("image")

    def test_error_does_not_leak_exception(self):
        b64 = base64.b64encode(bytes([255,216,255,1,2,3])).decode()
        with patch.object(handler.np, "frombuffer", side_effect=RuntimeError("internal secret"), create=True):
            status, body = parsed(handler.lambda_handler(event({"image_base64":b64}), None))
        self.assertEqual(status, 500)
        self.assertNotIn("internal secret", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
