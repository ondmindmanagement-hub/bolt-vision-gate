# Candidate BOLT Vision Gate Lambda — Python 3.12

**Migration candidate, NOT a deployed update.** Added Oct 8, 2026 in a feature branch. The AWS CLI login was expired, so no live Lambda configuration or affected function ARN has been verified.

## Why this differs from the old package

1. Replaces the unsupported Python 3.9 **runtime** with the AWS-provided Python 3.12 / Amazon Linux 2023 container image.
2. Native OpenCV/NumPy wheels are installed **inside the target Linux image**, not from a macOS virtual environment.
3. Deliberately **removes `image_url`** from the public API. Previous Lambda code fetched arbitrary remote URLs with `urllib.request.urlopen` and could access internal/metadata URLs or follow redirects. Use inline `image_base64` instead; only PNG/JPEG bytes, <= 5 MiB.
4. The endpoint avoids returning exception details to unauthenticated callers.
5. The Lambda is **not authenticated**, nor are rate limits/WAF configured; they remain deployment prerequisites. A compressed-image decompression attack remains possible without a separate pixel-dimension/pixel-budget validator.

## Contract

HTTP API v2: `GET /health`; `POST /analyze` with a JSON object containing `{"image_base64":"<base64-encoded JPEG or PNG>"}`. Requesting `image_url` gets a 400 response by design. This is **breaking** for any clients expecting URL input.

## Validate safely on the Mac

```sh
python3.12 -m unittest discover -s lambda_python312_safe/tests -v
docker buildx build --platform linux/amd64 --provenance=false -f lambda_python312_safe/Dockerfile \
  -t bolt-vision-gate-lambda:python312 lambda_python312_safe
docker run --rm -p 9000:8080 bolt-vision-gate-lambda:python312
# In a second terminal:
curl -sS http://localhost:9000/2015-03-31/functions/function/invocations \
 -H 'Content-Type: application/json' \
 -d '{"rawPath":"/health","requestContext":{"http":{"method":"GET"}}}'
```

## Deployment gate — **DO NOT run until AWS IAM approval and dependent clients verified**

- Read AWS Health > Affected resources in `eu-north-1` and list actual function ARNs and their runtime and package types. After IAM credentials exist, run `bash lambda_python312_safe/audit_aws_readonly.sh` for a read-only inventory. The script deliberately refuses AWS root identity and never changes cloud resources.
- This local Vision Gate code is a **candidate only**, not proof that it is the function mentioned in the AWS Health email.
- Use an appropriately scoped **IAM role** (not AWS account root) to inspect code/configuration, environment variables, aliases and clients.
- Review the breaking request contract and add required authentication, WAF/rate limits, payload pixel-size safeguards and logging before any public deployment.
- Snapshot current configuration/code, deploy to separate staging Lambda, compare latency and decoded-image outputs, and review CloudWatch logs.
- Only after approvals and passing staging tests, switch traffic by versioned alias with rollback to existing pinned version.
- Do not overwrite the original function with this branch by default.

Official docs: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html

This candidate has no secrets and requires no external funds or production changes.
