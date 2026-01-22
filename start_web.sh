#!/bin/bash
set -e

echo "Lancement de l'interface Flask..."
python3 -m flask --app web_viewer.app run --host 0.0.0.0 --port 8000 --no-reload
