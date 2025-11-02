# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (main.py, model-v1.joblib, etc.)
COPY . .

# Expose FastAPI default port
EXPOSE 8100

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
