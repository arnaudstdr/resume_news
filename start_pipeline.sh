#!/bin/bash
set -e

# Exécution du pipeline principal
echo "🚀 Lancement du pipeline Python (run_all.py)..."
python3 scripts/run_all.py

# Génération de la page HTML statique
echo "📝 Génération du rapport HTML statique..."
python3 web_viewer/generate_static.py
