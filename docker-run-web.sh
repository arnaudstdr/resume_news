#!/bin/bash

set -e

echo "Lancement de l'interface web Resume News avec Docker..."

if [ ! -f .env ]; then
    echo "Erreur: Le fichier .env est introuvable a la racine du projet."
    echo ""
    echo "Pour creer votre fichier .env, executez:"
    echo "   cp .env.example .env"
    echo ""
    echo "Puis editez le fichier .env et remplacez 'votre_cle_api_mistral' par votre vraie cle API Mistral."
    exit 1
fi

if ! docker image inspect resume_news:latest >/dev/null 2>&1; then
    echo "Construction de l'image Docker..."
    docker build -t resume_news:latest .
fi

echo "Interface accessible sur http://localhost:8000"
docker run --rm -it \
    -p 8000:8000 \
    -v "$(pwd)/.env:/app/.env:ro" \
    -v "$(pwd)/outputs:/app/outputs" \
    -v "$(pwd)/data:/app/data" \
    resume_news:latest \
    bash start_web.sh
