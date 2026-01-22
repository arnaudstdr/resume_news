# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Variables d'environnement
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Installation des dépendances système nécessaires pour weasyprint et les autres libs
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances et installation
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie de l'ensemble du projet
COPY . .

# Création des répertoires nécessaires
RUN mkdir -p outputs data

# Le fichier .env doit être monté ou copié lors de l'exécution
# Vérification que le fichier .env existe avant de lancer le pipeline
CMD if [ ! -f .env ]; then \
        echo "❌ Erreur: Le fichier .env est requis."; \
        echo "📝 Créez un fichier .env avec: MISTRAL_API_KEY=\"votre_clé_api_mistral\""; \
        exit 1; \
    fi && \
    bash start_pipeline.sh
