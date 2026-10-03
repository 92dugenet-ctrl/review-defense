# ÉTAPE 1 — Construction du frontend React/Vite.
# Node n'est utilisé que pour compiler les ressources web ; il n'est pas
# nécessaire dans l'image Python finale.
FROM node:22-alpine AS frontend-build

WORKDIR /frontend

# Copier les manifests séparément permet de mettre en cache l'installation
# des dépendances tant que package.json ne change pas.
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund

# Le code frontend est ensuite copié et compilé dans /frontend/dist.
COPY frontend/ ./
RUN npm run build


# ÉTAPE 2 — Image d'exécution Python.
# L'image finale ne conserve pas Node : elle contient le backend WSGI,
# les scripts opérationnels et les fichiers frontend déjà compilés.
FROM python:3.12-slim

# Évite les fichiers .pyc dans le conteneur et force les logs Python
# à sortir immédiatement vers stdout/stderr (visibles par Docker).
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Dépendances backend installées dans l'image d'exécution.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sources applicatives et ressources compilées du frontend.
COPY . .
COPY --from=frontend-build /frontend/dist ./frontend/dist

# Répertoire persistant prévu pour les pièces justificatives.
# Les permissions restrictives évitent l'accès aux autres utilisateurs du conteneur.
RUN mkdir -p /var/lib/review-defense/evidence \
    && chmod 700 /var/lib/review-defense/evidence \
    && chmod +x scripts/start_production.sh scripts/worker.py

# Port interne exposé par Gunicorn ; le port public est géré par Compose/proxy.
EXPOSE 8080

# Le script prépare la configuration, applique les migrations, puis lance WSGI.
CMD ["./scripts/start_production.sh"]
