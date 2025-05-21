import os
import json
import logging
from typing import List, Dict, Any
import sys

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.rss_scraper import run_all as run_scraper
from normalizer.data_normalizer import DataNormalizer
from database.db_manager import DatabaseManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_scraped_articles() -> List[Dict[str, Any]]:
    """Charge tous les articles scrapés depuis les fichiers JSON."""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs")
    all_articles = []
    
    try:
        for filename in os.listdir(output_dir):
            if filename.endswith('.json') and filename != 'normalized_articles.json':
                file_path = os.path.join(output_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    # Ajouter le nom de la source à chaque article
                    source_name = os.path.splitext(filename)[0]
                    for article in articles:
                        article['source'] = source_name
                    all_articles.extend(articles)
        
        logger.info(f"Chargement de {len(all_articles)} articles depuis {len(os.listdir(output_dir))} fichiers")
        return all_articles
    
    except Exception as e:
        logger.error(f"Erreur lors du chargement des articles: {str(e)}")
        return []

def load_rss_sources() -> List[Dict[str, str]]:
    """Charge les sources RSS depuis le fichier de configuration."""
    rss_list_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scraper", "flux_rss.json")
    
    try:
        with open(rss_list_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lors du chargement des sources RSS: {str(e)}")
        return []

def main():
    """Fonction principale qui exécute le pipeline complet."""
    try:
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
        
        # Étape 4: Chargement des sources RSS
        logger.info("Chargement des sources RSS")
        sources = load_rss_sources()
        
        if not sources:
            logger.error("Aucune source RSS trouvée")
            return
        
        # Étape 5: Initialisation de la base de données
        logger.info("Initialisation de la base de données")
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "rss_articles.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        db_manager = DatabaseManager(db_path)
        db_manager.connect()
        db_manager.create_tables()
        
        # Étape 6: Ajout des articles à la base de données
        logger.info("Ajout des articles à la base de données")
        
        # Grouper les articles par source
        articles_by_source = {}
        for article in normalized_articles:
            # Normalisation du nom de la source pour le matching
            source = article.get('source', '').strip().lower().replace('-', ' ').replace('_', ' ')
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)

        # Ajouter les articles à la base de données
        total_added = 0
        for source_name, source_articles in articles_by_source.items():
            # Trouver l'URL de la source (normalisation du nom pour le matching)
            source_url = ""
            for source in sources:
                source_match = source['name'].strip().lower().replace('-', ' ').replace('_', ' ')
                if source_match == source_name:
                    source_url = source['url']
                    break
            if source_url:
                added = db_manager.add_articles_batch(source_articles, source_name, source_url)
                total_added += added
                logger.info(f"{added} articles ajoutés pour la source {source_name}")
            else:
                logger.warning(f"URL non trouvée pour la source {source_name}")
        
        # Étape 7: Récupération des statistiques
        logger.info("Récupération des statistiques")
        stats = db_manager.get_statistics()
        logger.info(f"Statistiques de la base de données: {stats}")
        
        # Étape 8: Fermeture de la connexion à la base de données
        db_manager.disconnect()
        
        logger.info(f"Pipeline terminé avec succès. {total_added} articles ajoutés à la base de données.")
    
    except Exception as e:
        logger.error(f"Erreur critique dans le pipeline: {str(e)}")

if __name__ == "__main__":
    main()