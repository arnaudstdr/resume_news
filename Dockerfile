# Dockerfile pour pipeline de veille IA
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le code source et les scripts
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Donner les droits d'exécution au script de démarrage
RUN chmod +x /app/start.sh

# Définir le point d'entrée
ENTRYPOINT ["/app/start.sh"]
