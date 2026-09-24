FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<4" gunicorn
RUN mkdir -p /var/lib/review-defense/evidence
EXPOSE 8080
ENV REVIEW_DEFENSE_ENV=production HOST=0.0.0.0
CMD ["sh", "-c", "export REVIEW_DEFENSE_ENV=\"${REVIEW_DEFENSE_ENV:-production}\"; exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 60 wsgi:app"]
