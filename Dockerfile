# Dockerfile pour pipeline de veille IA (compatible devcontainer)
FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Définir le répertoire de travail
WORKDIR /app

# Copier le code source et les scripts
COPY . /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Donner les droits d'exécution au script de démarrage
RUN chmod +x /app/start.sh

# Pas d'ENTRYPOINT : le devcontainer lance un shell interactif par défaut
# CMD ["/bin/bash"]
