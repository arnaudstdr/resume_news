#!/bin/bash

# Déterminer le dossier de base du projet
if [ -d "/app" ]; then
  # En environnement Docker
  BASE_DIR="/app"
else
  # En environnement local
  BASE_DIR="$(dirname "$0")"
fi

# Aller dans le dossier des scripts
cd "$BASE_DIR/scripts"

# Lancer le pipeline Python
echo "[INFO] Exécution du pipeline de veille IA..."
python3 run_all.py

# Générer le rapport HTML statique
cd "$BASE_DIR/web_viewer"
echo "[INFO] Génération du rapport HTML statique..."
python3 generate_static.py
cd "$BASE_DIR/scripts"

# Trouver dynamiquement le dernier fichier digest_hebdo_*.md généré
DIGEST_FILE=$(ls -t "$BASE_DIR/outputs/digest_hebdo_"*.md 2>/dev/null | head -n 1)

# Chemin du rapport HTML généré
HTML_REPORT="$BASE_DIR/outputs/veille_ia_rapport.html"

if [ -n "$DIGEST_FILE" ] && [ -f "$DIGEST_FILE" ]; then
    echo "[INFO] Résumé généré : $DIGEST_FILE"
    # Vérifier si la commande 'code' (VS Code CLI) est disponible
    if command -v code >/dev/null 2>&1; then
        echo "[INFO] Ouverture dans VS Code..."
        code "$DIGEST_FILE"
    else
        echo "[INFO] VS Code non disponible. Affichage dans le terminal :"
        echo "-----------------------------"
        cat "$DIGEST_FILE"
        echo "-----------------------------"
    fi
else
    echo "[ERREUR] Aucun fichier de résumé trouvé dans $BASE_DIR/outputs/ (digest_hebdo_*.md)"
    exit 1
fi

# Ouvrir automatiquement le rapport HTML dans le navigateur
if [ -f "$HTML_REPORT" ]; then
    echo "[INFO] Ouverture du rapport HTML dans le navigateur..."
    if [ -n "$BROWSER" ]; then
        "$BROWSER" "$HTML_REPORT"
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$HTML_REPORT"
    elif command -v open >/dev/null 2>&1; then # Pour macOS
        open "$HTML_REPORT"
    else
        echo "[WARN] Impossible d'ouvrir automatiquement le navigateur. Ouvrez manuellement : $HTML_REPORT"
    fi
else
    echo "[ERREUR] Le rapport HTML n'a pas été trouvé : $HTML_REPORT"
fi
