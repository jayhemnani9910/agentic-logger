FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including Tesseract, xdotool, xclip)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    xdotool \
    xclip \
    wl-clipboard \
    x11-utils \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run gunicorn
CMD ["gunicorn", "--workers", "1", "--worker-class", "sync", "--bind", "0.0.0.0:8000", "--timeout", "120", "--chdir", "/app", "app:create_app()"]
