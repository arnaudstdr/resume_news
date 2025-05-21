import os
import json
import logging
from scraper.rss_scraper import run_all as run_scraper
from normalizer.data_normalizer import DataNormalizer
from database.db_manager import DatabaseManager
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rss_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_scraped_articles():
    """Charge tous les articles scrapés depuis les fichiers JSON."""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    all_articles = []

    try:
        for filename in os.listdir(output_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    all_articles.extend(articles)

        logger.info(f"Chargement de {len(all_articles)} articles depuis {len(os.listdir(output_dir))} fichiers")
        return all_articles

    except Exception as e:
        logger.error(f"Erreur lors du chargement des articles: {str(e)}")
        return []

def save_normalized_articles(articles, output_dir):
    """Sauvegarde les articles normalisés dans un fichier JSON."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "normalized_articles.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(articles)} articles normalisés sauvegardés dans {output_file}")

    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des articles normalisés: {str(e)}")

def main():
    """Fonction principale qui exécute le pipeline complet."""
    try:
        # Initialisation de la base de données
        db_manager = DatabaseManager()
        db_manager.connect()
        db_manager.create_tables()

        # Étape 1: Scraping des flux RSS
        logger.info("Démarrage du scraping des flux RSS")
        run_scraper()

        # Étape 2: Chargement des articles scrapés
        logger.info("Chargement des articles scrapés")
        articles = load_scraped_articles()

        if not articles:
            logger.error("Aucun article trouvé à normaliser")
            return

        # Étape 3: Normalisation des articles
        logger.info("Normalisation des articles")
        normalizer = DataNormalizer()
        normalized_articles = normalizer.normalize_batch(articles)
        # Étape 4: Sauvegarde des articles normalisés dans la base de données
        source_name = "RSS Feed"  # Vous pouvez ajuster ceci en fonction de vos besoins
        source_url = "https://example.com/rss"  # URL de la source RSS
        db_manager.add_articles_batch(normalized_articles, source_name, source_url)

        # Sauvegarde des articles normalisés dans un fichier JSON (optionnel)
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "normalized")
        save_normalized_articles(normalized_articles, output_dir)

        logger.info("Pipeline terminé avec succès")

    except Exception as e:
        logger.error(f"Erreur critique dans le pipeline: {str(e)}")

    finally:
        # Déconnexion de la base de données
        db_manager.disconnect()

if __name__ == "__main__":
    main()
