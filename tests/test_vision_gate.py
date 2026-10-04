import sys
import unittest
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vision_gate import analyze_frame


class VisionGateTests(unittest.TestCase):
    def test_blank_frame_requires_review(self):
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        report = analyze_frame(img)
        self.assertEqual(report["decision"], "human_review")
        self.assertIn("scene_too_dark", report["reasons"])

    def test_structured_frame_uses_opencv5(self):
        img = np.full((240, 320, 3), 128, dtype=np.uint8)
        cv2.rectangle(img, (30, 30), (290, 210), (255, 255, 255), 4)
        cv2.line(img, (30, 210), (290, 30), (0, 0, 0), 5)
        report = analyze_frame(img)
        self.assertTrue(report["opencv_version"].startswith("5."))
        self.assertEqual(report["width"], 320)
        self.assertEqual(report["height"], 240)
        self.assertGreater(report["edge_density"], 0)


if __name__ == "__main__":
    unittest.main()
