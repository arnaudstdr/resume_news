#!/bin/bash
set -e

if [ ! -f .env ]; then
    echo "❌ Erreur: Le fichier .env est requis."
    echo "📝 Créez un fichier .env avec OLLAMA_URL et OLLAMA_MODEL (voir .env.example)."
    exit 1
fi

echo "🚀 Lancement du pipeline Python (run_all.py)..."
python3 scripts/run_all.py

echo "📝 Génération du rapport HTML statique..."
python3 web_viewer/generate_static.py
