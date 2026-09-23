FROM python:3.10-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies for PyMuPDF & build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all application code
COPY . /app

# Create persistent storage directories
RUN mkdir -p /app/backend/data/uploads /app/backend/data/vectorstore /app/backend/data/evaluation && \
    chmod -R 777 /app/backend/data

# Hugging Face Spaces expects port 7860
EXPOSE 7860

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
