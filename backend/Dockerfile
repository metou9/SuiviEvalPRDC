# backend/Dockerfile
FROM python:3.12-slim-bookworm

# --- System libraries -------------------------------------------------------
# WeasyPrint (PDF export) needs Pango/HarfBuzz + fonts at runtime. psycopg[binary]
# bundles libpq, so no libpq-dev is required.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi8 \
        libfontconfig1 libcairo2 libgdk-pixbuf-2.0-0 shared-mime-info \
        fonts-dejavu fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static at build is optional; we do it at start (entrypoint) so env is available.
RUN chmod +x ./entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
