# 🤖 Pipeline de Veille IA

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Dockerfile](https://img.shields.io/badge/Dockerfile-available-blue?logo=docker)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Dernier commit](https://img.shields.io/github/last-commit/arnaudstdr/resume_news)
![Dépendances](https://img.shields.io/librariesio/release/pypi/requests)
![Stars](https://img.shields.io/github/stars/arnaudstdr/resume_news?style=social)

Pipeline complet pour la **veille stratégique sur l'actualité de l'IA** : scraping RSS, normalisation (résumés courts avec le modèle local `sshleifer/distilbart-cnn-12-6` via Transformers), stockage, génération automatique d'un résumé hebdomadaire structuré et pertinent (avec l'API Mistral Large).


## 💻 Utilisation (Linux, Windows, Mac)

Le projet fonctionne aussi sur n'importe quel ordinateur avec Docker :
- Compatible Linux, Windows, Mac (x86_64 ou ARM)
- Installez [Docker Desktop](https://www.docker.com/products/docker-desktop/) et [VS Code](https://code.visualstudio.com/) avec l'extension "Dev Containers"
- Ouvrez le dossier dans VS Code et cliquez sur "Reopen in Container" pour un environnement prêt à l'emploi
- Toutes les instructions du README s'appliquent également à ces plateformes

## ✨ Fonctionnalités
- 🔎 Scraping de flux RSS IA
- 🧹 Normalisation et stockage en base SQLite (résumés courts générés localement avec `sshleifer/distilbart-cnn-12-6`)
- 🗃️ Génération automatique d'un résumé stratégique hebdomadaire (Markdown, via l'API Mistral Large)
- 🚀 Expérience utilisateur fluide (un seul script à lancer)
- 🐳 Dockerisation complète
- 📜 Documentation claire et logs détaillés

## 📦 Installation & Lancement rapide

### 1. Cloner le repo
```bash
git clone https://github.com/arnaudstdr/resume_news.git
cd resume_news
```

### 2. Configuration de l'API Mistral

Créez un fichier `.env` à la racine du projet à partir du modèle fourni :

```bash
cp .env.example .env
```

Puis éditez le fichier `.env` et remplacez `votre_clé_api_mistral` par votre vraie clé API Mistral :

```env
MISTRAL_API_KEY="votre_clé_api_mistral"
```

La clé est nécessaire pour générer le résumé hebdomadaire avec Mistral Large.

### 3. Lancement du pipeline avec Docker

#### Option A : Avec le script automatique (recommandé)

```bash
./docker-run.sh
```

Le script va automatiquement :
- Vérifier que le fichier `.env` existe
- Construire l'image Docker si nécessaire
- Lancer le pipeline avec les volumes appropriés
- Sauvegarder les résultats dans `outputs/` et la base de données dans `data/`

#### Option B : Manuellement

Construction de l'image Docker :
```bash
docker build -t resume_news .
```

Lancement du pipeline avec montage des volumes :
```bash
docker run --rm -it \
    -v "$(pwd)/.env:/app/.env:ro" \
    -v "$(pwd)/outputs:/app/outputs" \
    -v "$(pwd)/data:/app/data" \
    resume_news
```

Les volumes montés permettent de :
- Passer votre fichier de configuration `.env`
- Récupérer les résultats générés dans `outputs/`
- Persister la base de données SQLite dans `data/`


## 🐳 Utilisation avec Dev Container

Ce projet est prêt pour [Dev Containers](https://containers.dev/) de VS Code.
- Ouvrez le dossier dans VS Code
- Cliquez sur `Reopen in Container` ou utilisez la palette de commandes (`F1`)


Vous pouvez lancer le pipeline, éditer le code, exécuter les tests, etc. dans un environnement isolé.

## 🌐 Interface web (Flask)

Une interface web simple est disponible pour lancer le pipeline et ouvrir le rapport HTML.

### Lancement avec Docker

```bash
./docker-run-web.sh
```

Puis ouvrir `http://localhost:8000` (ou l'IP du Raspberry Pi) pour accéder au bouton de lancement et au rapport.

### Lancement sans Docker

```bash
pip install -r requirements.txt
./start_web.sh
```


## 🔌 Structure des dossiers
| Dossier/Fichier         | Rôle principal                                 |
|------------------------|------------------------------------------------|
| `scripts/`             | Scripts Python principaux du pipeline          |
| `scripts/scraper/`     | Scraping RSS et gestion des flux              |
| `scripts/normalizer/`  | Normalisation des articles                    |
| `scripts/database/`    | Gestion de la base SQLite                     |
| `scripts/summarizer/`  | Génération du résumé hebdomadaire             |
| `outputs/`             | Résumés générés et articles normalisés        |
| `data/`                | Base de données SQLite                        |
| `start_pipeline.sh`    | Script principal de lancement                 |
| `docker-run.sh`        | Script de lancement avec Docker               |
| `Dockerfile`           | Image Docker du projet                        |
| `.env.example`         | Modèle de configuration pour l'API Mistral    |

## 🔌 Résultats
- Résumé hebdomadaire généré dans `outputs/digest_hebdo_<date>.md` (via l'API Mistral Large)
- Articles normalisés dans `outputs/normalized/normalized_articles.json` (résumés courts avec `sshleifer/distilbart-cnn-12-6`)

## 🧪 Tests

### Lancer les tests manuellement
```bash
pytest scripts/normalizer/test_data_normalizer.py
```

## 🛠️ Personnalisation
- Modifiez les flux RSS dans `scripts/scraper/flux_rss.json`
- Adaptez les scripts Python selon vos besoins (scraping, résumé, etc.)

## 🧠 Auteur
👤 Arnaud STADLER - Développeur Python | Intégration IA

## 📄 Licence
Ce projet est open-source sous licence [MIT](LICENSE). Vous pouvez l'utiliser, le modifier et le redistribuer librement dans le respect de cette licence.
