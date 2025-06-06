# 🤖 Pipeline de Veille IA

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Dockerfile](https://img.shields.io/badge/Dockerfile-available-blue?logo=docker)
![Jetson](https://img.shields.io/badge/Jetson-supported-green?logo=nvidia)
![NVIDIA GPU](https://img.shields.io/badge/NVIDIA-GPU-green?logo=nvidia)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Dernier commit](https://img.shields.io/github/last-commit/arnaudstdr/resume_news)
![Dépendances](https://img.shields.io/librariesio/release/pypi/requests)
![Stars](https://img.shields.io/github/stars/arnaudstdr/resume_news?style=social)

Pipeline complet pour la **veille stratégique sur l’actualité de l’IA** : scraping RSS, normalisation (résumés courts avec le modèle local `sshleifer/distilbart-cnn-12-6` via Transformers), stockage, génération automatique d’un résumé hebdomadaire structuré et pertinent (avec l’API Mistral Large).


## 💻 Utilisation (Linux, Windows, Mac)

Le projet fonctionne aussi sur n’importe quel ordinateur avec Docker :
- Compatible Linux, Windows, Mac (x86_64 ou ARM)
- Installez [Docker Desktop](https://www.docker.com/products/docker-desktop/) et [VS Code](https://code.visualstudio.com/) avec l’extension “Dev Containers”
- Ouvrez le dossier dans VS Code et cliquez sur “Reopen in Container” pour un environnement prêt à l’emploi
- Toutes les instructions du README s’appliquent également à ces plateformes

## ✨ Fonctionnalités
- 🔎 Scraping de flux RSS IA
- 🧹 Normalisation et stockage en base SQLite (résumés courts générés localement avec `sshleifer/distilbart-cnn-12-6`)
- 🗃️ Génération automatique d’un résumé stratégique hebdomadaire (Markdown, via l’API Mistral Large)
- 🚀 Expérience utilisateur fluide (un seul script à lancer)
- 🐳 Dockerisation complète
- 📜 Documentation claire et logs détaillés

## 📦 Installation & Lancement rapide

### 1. Cloner le repo
```bash
git clone https://github.com/arnaudstdr/resume_news.git
cd resume_news
```

### 2. Construction de l’image Docker
```bash
docker build -t resume_news .
```

### 3. Configuration de l'API Mistral

Avant de lancer le pipeline, créez un fichier `.env` à la racine du projet et ajoutez votre clé API Mistral :

```env
MISTRAL_API_KEY="votre_clé_api_mistral"
```

La clé est nécessaire pour générer le résumé hebdomadaire avec Mistral Large.

### 4. Lancement du pipeline
```bash
docker run --rm -it resume_news
```

#### 💡 Astuce : synchroniser les résultats sur votre machine
Pour accéder aux fichiers générés (`outputs/`) sur votre machine hôte :
```bash
docker run --rm -it -v $(pwd)/outputs:/app/outputs resume_news
```

Le résumé généré s’ouvre dans VS Code (si disponible) ou s’affiche dans le terminal.


## 🐳 Utilisation avec Dev Container

Ce projet est prêt pour [Dev Containers](https://containers.dev/) de VS Code.
- Ouvrez le dossier dans VS Code
- Cliquez sur `Reopen in Container` ou utilisez la palette de commandes (`F1`)

Vous pouvez lancer le pipeline, éditer le code, exécuter les tests, etc. dans un environnement isolé.

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
| `start.sh`             | Script principal de lancement                 |
| `Dockerfile`           | Image Docker du projet                        |

## 🔌 Endpoints & Résultats
- Résumé hebdomadaire généré dans `outputs/digest_hebdo_<date>.md` (via l’API Mistral Large)
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
👤 Arnaud STADLER - MLOps en reconversion passionné de data, de vélo et d'IA 🚴‍♂️🧠

## 📄 Licence
Ce projet est open-source sous licence [MIT](LICENSE). Vous pouvez l’utiliser, le modifier et le redistribuer librement dans le respect de cette licence.
