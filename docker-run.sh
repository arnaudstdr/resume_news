#!/bin/bash

# Script de lancement du pipeline avec Docker

set -e

echo "🐳 Lancement du pipeline Resume News avec Docker..."

# Vérification que le fichier .env existe
if [ ! -f .env ]; then
    echo "❌ Erreur: Le fichier .env est introuvable à la racine du projet."
    echo ""
    echo "📝 Pour créer votre fichier .env, exécutez:"
    echo "   cp .env.example .env"
    echo ""
    echo "Puis éditez le fichier .env et remplacez 'votre_clé_api_mistral' par votre vraie clé API Mistral."
    exit 1
fi

echo "✅ Fichier .env détecté"

# Construction de l'image Docker si elle n'existe pas
if ! docker image inspect resume_news:latest >/dev/null 2>&1; then
    echo "🔨 Construction de l'image Docker..."
    docker build -t resume_news:latest .
fi

# Lancement du container avec montage du fichier .env et du dossier outputs
echo "🚀 Lancement du pipeline..."
docker run --rm -it \
    -v "$(pwd)/.env:/app/.env:ro" \
    -v "$(pwd)/outputs:/app/outputs" \
    -v "$(pwd)/data:/app/data" \
    resume_news:latest

echo "✅ Pipeline terminé!"
echo "📁 Les résultats sont disponibles dans le dossier outputs/"
