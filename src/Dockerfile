FROM public.ecr.aws/lambda/python:3.9

# Upgrade pip first
RUN pip install --upgrade pip

# Install Python dependencies with verbose output for debugging
RUN pip install --no-cache-dir --target /var/task \
    mlflow==2.13.2 \
    sagemaker-mlflow==0.1.0 \
    xgboost==2.1.4 \
    numpy \
    pandas

# Copy the function code
# COPY app/lambda_function.py ${LAMBDA_TASK_ROOT}/
# COPY lambda_function.py /var/task/lambda_function.py
COPY entrypoint.py /var/task/entrypoint.py

# RUN cd /var/task && python -c "import mlflow; print(f'✅ MLflow version: {mlflow.__version__}')"

# Command to run the Lambda function
CMD ["entrypoint.lambda_handler"]