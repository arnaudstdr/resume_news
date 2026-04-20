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

EXPOSE 8000

# Le fichier .env doit être monté ou copié lors de l'exécution.
# La vérification de sa présence est faite dans start_pipeline.sh.
CMD ["bash", "start_pipeline.sh"]
