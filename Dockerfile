FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-build /frontend/dist ./frontend/dist

RUN mkdir -p /var/lib/review-defense/evidence \
    && chmod 700 /var/lib/review-defense/evidence \
    && chmod +x scripts/start_production.sh scripts/worker.py

EXPOSE 8080
CMD ["./scripts/start_production.sh"]
