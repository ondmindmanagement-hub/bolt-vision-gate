# BOLT Vision Gate — OpenCV AI Competition 2026

BOLT Vision Gate is a small OpenCV 5 proof of concept that places a visual-quality gate in front of an automated workflow.

Before an autonomous workflow acts on an image, the gate checks whether the frame is visually reliable enough for automatic execution or should be escalated to a human.

## OpenCV 5 signals

- brightness / exposure
- contrast
- Laplacian blur variance
- Canny edge density
- structured escalation reasons

The JSON decision is either `allow` or `human_review`.

This is intentionally a bounded proof of concept. It does not claim to solve general visual safety.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python make_sample.py
python src/vision_gate.py samples/good_scene.png
python src/vision_gate.py samples/dark_scene.png
```

## Test

```bash
python -m unittest discover -s tests
```

## Architecture

image -> OpenCV 5 analysis -> visual-quality report -> policy decision -> allow / human review

## Responsible operation

The system escalates uncertain or poor-quality inputs instead of pretending that weak visual evidence is reliable. It performs no biometric identity inference.

## AWS reproducibility

A Dockerfile is included so the workload can be packaged for a container-based AWS deployment. No cloud endpoint is claimed in the current proof of concept.

## Team

Omar Baró — Founder, Unfire  
https://unfire.technology
