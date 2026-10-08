# Build dependencies in the real AWS Lambda Python 3.12 (Amazon Linux 2023)
# environment, not on a macOS host. Separate from the original managed .zip.
FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
CMD ["lambda_function.lambda_handler"]
