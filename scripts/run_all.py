#!/usr/bin/env python3
"""
Script principal pour exécuter l'ensemble du pipeline de veille IA :
- Scraping RSS
- Normalisation
- Insertion en base
- Génération du résumé hebdomadaire
"""
import os
import sys
import logging
from datetime import datetime

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import rss_scraper
from normalizer.data_normalizer import DataNormalizer
from database.db_manager import DatabaseManager
from summarizer.weekly_digest import WeeklyDigest

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_all.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
NORMALIZED_DIR = os.path.join(OUTPUTS_DIR, "normalized")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rss_articles.db")

# S'assurer que le dossier data existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def main():
    # 1. Scraping RSS
    logger.info("[1/4] Scraping des flux RSS...")
    try:
        rss_scraper.run_all()
    except Exception as e:
        logger.error(f"Erreur lors du scraping RSS : {e}")
        return

    # 2. Normalisation
    logger.info("[2/4] Normalisation des articles...")
    try:
        # Charger tous les articles bruts
        articles = []
        for fname in os.listdir(OUTPUTS_DIR):
            if fname.endswith('.json') and fname != 'normalized_articles.json':
                with open(os.path.join(OUTPUTS_DIR, fname), 'r', encoding='utf-8') as f:
                    articles.extend(__import__('json').load(f))
        normalizer = DataNormalizer()
        normalized = normalizer.normalize_batch(articles)
        os.makedirs(NORMALIZED_DIR, exist_ok=True)
        with open(os.path.join(NORMALIZED_DIR, "normalized_articles.json"), 'w', encoding='utf-8') as f:
            __import__('json').dump(normalized, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erreur lors de la normalisation : {e}")
        return

    # 3. Insertion en base
    logger.info("[3/4] Insertion en base de données...")
    try:
        db = DatabaseManager(DB_PATH)
        db.connect()
        db.create_tables()
        # On suppose que chaque article a un champ 'source' et 'url'
        for fname in os.listdir(OUTPUTS_DIR):
            if fname.endswith('.json') and fname != 'normalized_articles.json':
                with open(os.path.join(OUTPUTS_DIR, fname), 'r', encoding='utf-8') as f:
                    articles = __import__('json').load(f)
                    if articles:
                        source_name = articles[0].get('source', fname.replace('.json',''))
                        source_url = articles[0].get('url', '')
                        db.add_articles_batch(articles, source_name, source_url)
        db.disconnect()
    except Exception as e:
        logger.error(f"Erreur lors de l'insertion en base : {e}")
        return

    # 4. Génération du résumé hebdomadaire
    logger.info("[4/4] Génération du résumé hebdomadaire...")
    try:
        digest = WeeklyDigest(db_path=DB_PATH)
        articles = digest.get_weekly_articles(limit=1000)
        if not articles:
            logger.warning("Aucun article trouvé pour générer le résumé. Résumé non généré.")
            return
        summary = digest.generate_digest(limit=1000)
        output_path = digest.save_digest(summary)
        logger.info(f"Résumé hebdomadaire généré : {output_path}")
        print(f"Résumé hebdomadaire généré : {output_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé : {e}")
        return

if __name__ == "__main__":
    main()
