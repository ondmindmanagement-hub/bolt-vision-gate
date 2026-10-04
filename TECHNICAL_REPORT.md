# BOLT Vision Gate — Technical Report

## Problem and intended users

Automated workflows increasingly consume images from cameras, uploads, and tools. A downstream agent can make a confident-looking decision even when the frame is dark, blurred, overexposed, or visually empty. BOLT Vision Gate is a bounded proof of concept for developers who want a transparent quality gate before an automated workflow acts on visual input.

## Architecture

The system accepts an image, computes a small set of OpenCV 5 quality signals, converts them into explicit reasons, and returns either `allow` or `human_review`.

```
client
  |
  v
Flask /analyze
  |
  v
OpenCV 5
  |- brightness
  |- contrast
  |- Laplacian blur variance
  |- Canny edge density
  |
  v
policy gate
  |---- allow
  |
  '---- human_review + reasons
```

## OpenCV 5 implementation

The implementation pins `opencv-python==5.0.0.93`. It uses:

- `cv2.cvtColor` to create grayscale input.
- `cv2.Laplacian(...).var()` as a blur/detail signal.
- `cv2.Canny` for edge density.
- NumPy mean and standard deviation over the OpenCV image matrix for brightness and contrast.

The project intentionally avoids identity recognition or demographic inference.

## Evaluation

Two deterministic sample images are included.

| Case | Expected | Result |
| --- | --- | --- |
| Structured, mid-exposure scene | allow | allow |
| Fully dark scene | human_review | human_review |

Automated tests also verify that OpenCV 5 is actually being used and that the dark case produces an explicit `scene_too_dark` reason.

## Failure cases and limitations

- Fixed thresholds will not generalize to every camera, domain, or lighting environment.
- A technically sharp image can still be semantically wrong.
- The current gate evaluates visual quality, not task correctness.
- Production use would require domain-specific calibration, monitoring, and a broader evaluation set.

## Responsible operation

The system refuses to proceed automatically on clearly weak visual evidence. It emits machine-readable reasons so operators can understand why a frame was escalated. No face identification or biometric classification is performed.

## Web API

Run locally:

```bash
python src/web.py
curl http://localhost:8080/health
curl -F image=@samples/good_scene.png http://localhost:8080/analyze
```

## AWS deployment package

The repository includes a production-shaped Dockerfile exposing port 8080. The same image can be pushed to Amazon ECR and deployed to App Runner or ECS/Fargate.

The AWS deployment itself must be performed from an authenticated AWS account. No cloud endpoint is claimed until that step has actually completed.

## Reproducibility

Dependencies are pinned in `requirements.txt`, deterministic sample generation is provided by `make_sample.py`, and automated tests are in `tests/`.

## Live AWS validation

The proof of concept is deployed as an AWS Lambda function in the Stockholm (eu-north-1) region. The public function URL exposes /health and /analyze routes. Live validation returned opencv_version 5.0.0 and a structured human_review decision for a low-detail test image, demonstrating that the OpenCV 5 quality gate is executing in AWS rather than only locally.
