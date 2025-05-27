# Dockerfile pour pipeline de veille IA
FROM dustynv/l4t-ml:r36.2.0

# Définir le répertoire de travail
WORKDIR /app

# Copier le code source et les scripts
COPY . /app

RUN --mount=type=cache,target=/root/.cache \
    pip install --no-cache-dir -r requirements.txt

# Donner les droits d'exécution au script de démarrage
RUN chmod +x /app/start.sh

# Définir le point d'entrée
ENTRYPOINT ["/app/start.sh"]
