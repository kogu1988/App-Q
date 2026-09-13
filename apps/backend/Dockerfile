FROM python:3.12-slim

WORKDIR /app

# Deterministik/paylaşımlı çalışma için bytecode ve tampon ayarları
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies if needed (e.g., for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Non-root kullanıcı (güvenlik hardening) — Celery'nin "superuser" uyarısını giderir
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for FastAPI
EXPOSE 3000

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "3000"]
