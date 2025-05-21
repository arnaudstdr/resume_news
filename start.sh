#!/bin/bash

# Aller dans le dossier du projet
cd /scripts/

# Lancer le pipeline Python
echo "[INFO] Exécution du pipeline de veille IA..."
python3 run_all.py

# Chemin du résumé généré (à adapter si besoin)
DIGEST_FILE="/workspaces/resume_news/outputs/digest_hebdo_20250521.md"

if [ -f "$DIGEST_FILE" ]; then
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
    echo "[ERREUR] Le fichier de résumé n'a pas été trouvé : $DIGEST_FILE"
    exit 1
fi
