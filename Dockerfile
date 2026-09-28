FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
ENV REVIEW_DEFENSE_ENV=production HOST=0.0.0.0
CMD ["gunicorn","--bind","0.0.0.0:8080","--workers","2","--threads","4","--timeout","60","wsgi:app"]
