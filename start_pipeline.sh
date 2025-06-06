#!/bin/bash
set -e

# Exécution du pipeline principal
echo "🚀 Lancement du pipeline Python (run_all.py)..."
python3 scripts/run_all.py

# Génération de la page HTML statique
echo "📝 Génération du rapport HTML statique..."
python3 web_viewer/generate_static.py

# Ouverture du rapport dans le navigateur par défaut
HTML_FILE="outputs/veille_ia_rapport.html"
if [ -f "$HTML_FILE" ]; then
    echo "🌐 Ouverture du rapport dans le navigateur..."
    "$BROWSER" "$(realpath $HTML_FILE)"
else
    echo "❌ Fichier HTML non trouvé : $HTML_FILE"
    exit 1
fi