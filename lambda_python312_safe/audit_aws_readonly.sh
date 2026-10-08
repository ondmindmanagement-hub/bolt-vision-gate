#!/usr/bin/env bash
# READ ONLY. Does not create, update, delete, invoke or deploy any AWS resource.
set -euo pipefail
REGION="${AWS_REGION:-eu-north-1}"
if [[ "$REGION" != "eu-north-1" ]]; then
  echo "Refusing to audit unexpected region $REGION; expected eu-north-1" >&2
  exit 2
fi

echo "Inspecting account identity with existing AWS CLI credentials..."
ARN="$(aws sts get-caller-identity --query Arn --output text)"
if [[ "$ARN" == *":root" ]]; then
  echo "ERROR: AWS account root session is not approved for CLI work. Use scoped IAM credentials." >&2
  exit 3
fi
echo "Authenticated as an IAM principal (not root)."
echo "Reading function names, runtimes, package types and last-modified timestamps."

aws lambda list-functions --region "$REGION" --output json |
  /usr/bin/python3 -c '
import sys,json
j=json.load(sys.stdin)
items=j.get("Functions",[])
print("Functions: %s" % len(items))
print("Name | Runtime | Package | Last modified | Architecture")
for f in items:
  rt=f.get("Runtime","container_image")
  if rt=="python3.9" or "vision" in f.get("FunctionName","").lower():
    print(" | ".join([
      f.get("FunctionName",""),rt,f.get("PackageType",""),
      f.get("LastModified",""),
      ",".join(f.get("Architectures",[])),
    ]))
print("Only python3.9 and vision-name functions shown. Do not infer identity from names alone.")
'
echo "Read-only discovery finished. Next: inspect target details and affected ARN with IAM."
