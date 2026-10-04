#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:=eu-west-1}"
: "${APP_NAME:=bolt-vision-gate}"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REPO_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"

aws ecr describe-repositories --repository-names "$APP_NAME" --region "$AWS_REGION" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name "$APP_NAME" --region "$AWS_REGION" >/dev/null

aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build --platform linux/amd64 -t "$APP_NAME" .
docker tag "$APP_NAME:latest" "$REPO_URI:latest"
docker push "$REPO_URI:latest"

echo "Image pushed to: $REPO_URI:latest"
echo "Next: create an AWS App Runner service using this ECR image, container port 8080."
