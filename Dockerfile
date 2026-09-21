FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<4" gunicorn
EXPOSE 8080
ENV REVIEW_DEFENSE_ENV=production HOST=0.0.0.0 PORT=8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "60", "wsgi:app"]
