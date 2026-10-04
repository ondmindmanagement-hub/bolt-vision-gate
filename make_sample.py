from pathlib import Path
import cv2
import numpy as np

out = Path("samples")
out.mkdir(exist_ok=True)

good = np.full((480, 720, 3), 135, dtype=np.uint8)
cv2.rectangle(good, (80, 80), (640, 400), (245, 245, 245), 8)
cv2.circle(good, (360, 240), 100, (40, 40, 40), 8)
cv2.putText(good, "BOLT VISION GATE", (140, 455), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
cv2.imwrite(str(out / "good_scene.png"), good)

dark = np.zeros((480, 720, 3), dtype=np.uint8)
cv2.imwrite(str(out / "dark_scene.png"), dark)
print("generated samples")
