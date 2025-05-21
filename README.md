# Pipeline de veille IA

Ce projet propose un pipeline complet de veille sur l’actualité de l’IA : scraping RSS, normalisation, insertion en base, génération d’un résumé hebdomadaire pertinent et structuré.

## Fonctionnalités
- Scraping de flux RSS IA
- Normalisation et stockage en base SQLite
- Génération automatique d’un résumé stratégique hebdomadaire
- Expérience utilisateur fluide (un seul script à lancer)

## Prérequis
- [Docker](https://www.docker.com/) installé sur votre machine
- [Ollama](https://ollama.com/) installé et lancé en local
- Le modèle `mistral` téléchargé dans Ollama (`ollama run mistral`)

## Utilisation rapide

### 1. Construction de l’image Docker
```bash
docker build -t veille-ia .
```

### 2. Lancement du pipeline
```bash
docker run --rm -it veille-ia
```

#### 💡 Astuce : récupérer les résultats sur votre machine
Pour accéder aux fichiers générés (`outputs/`) sur votre machine hôte, montez le dossier en volume :
```bash
docker run --rm -it -v $(pwd)/outputs:/app/outputs veille-ia
```
Ainsi, le dossier `outputs` du conteneur sera synchronisé avec celui de votre projet local.

Le pipeline s’exécute automatiquement et le résumé généré s’ouvre dans VS Code (si disponible dans le conteneur) ou s’affiche dans le terminal.

### 3. Résultats
- Le résumé hebdomadaire est généré dans `outputs/digest_hebdo_<date>.md`
- Les articles normalisés sont dans `outputs/normalized/normalized_articles.json`

## Personnalisation
- Modifiez les flux RSS dans `scripts/scraper/flux_rss.json`.
- Adaptez les scripts Python selon vos besoins (scraping, résumé, etc).

## Développement local (hors Docker)
- Installez Python 3.10+
- Installez les dépendances : `pip install -r requirements.txt`
- Lancez le pipeline : `bash start.sh`

## Bonnes pratiques MLOps
- Conteneurisation complète (Docker)
- Automatisation du pipeline
- Documentation claire
- Logs générés dans le dossier du projet

---

**Auteur :** Votre Nom — 2025
