import os
import sys
import logging
from typing import List, Dict, Any

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_statistics(stats: Dict[str, Any]) -> None:
    """Affiche les statistiques de la base de données."""
    print("\n=== STATISTIQUES DE LA BASE DE DONNÉES ===")
    print(f"Nombre total d'articles: {stats['total_articles']}")
    print(f"Nombre total de sources: {stats['total_sources']}")
    print(f"Nombre total de catégories: {stats['total_categories']}")
    
    print("\n=== ARTICLES PAR SOURCE ===")
    for source, count in sorted(stats['articles_by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"{source}: {count} articles")
    
    print("\n=== ARTICLES PAR CATÉGORIE ===")
    for category, count in sorted(stats['articles_by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"{category}: {count} articles")
    
    print("\n=== ARTICLES PAR JOUR (DERNIERS 7 JOURS) ===")
    for day, count in sorted(stats['articles_by_day'].items(), reverse=True):
        print(f"{day}: {count} articles")

def print_recent_articles(articles: List[Dict[str, Any]], limit: int = 5) -> None:
    """Affiche les articles récents."""
    print(f"\n=== {limit} ARTICLES RÉCENTS ===")
    for i, article in enumerate(articles[:limit], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source_name']}")
        print(f"   Date: {article['date']}")
        if article.get('categories'):
            print(f"   Catégories: {', '.join(article['categories'])}")
        print(f"   URL: {article['url']}")

def print_articles_by_category(articles: List[Dict[str, Any]], category: str, limit: int = 5) -> None:
    """Affiche les articles par catégorie."""
    print(f"\n=== {limit} ARTICLES DE LA CATÉGORIE '{category}' ===")
    for i, article in enumerate(articles[:limit], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source_name']}")
        print(f"   Date: {article['date']}")
        print(f"   URL: {article['url']}")

def main():
    """Fonction principale pour tester la base de données."""
    try:
        # Chemin vers la base de données
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "rss_articles.db")
        
        # Vérifier si la base de données existe
        if not os.path.exists(db_path):
            logger.error(f"Base de données non trouvée: {db_path}")
            print(f"Base de données non trouvée: {db_path}")
            print("Veuillez exécuter le script db_pipeline.py pour créer la base de données.")
            return
        
        # Initialisation du gestionnaire de base de données
        db_manager = DatabaseManager(db_path)
        db_manager.connect()
        
        # Récupération des statistiques
        stats = db_manager.get_statistics()
        print_statistics(stats)
        
        # Récupération des articles récents
        recent_articles = db_manager.get_recent_articles(limit=5)
        print_recent_articles(recent_articles)
        
        # Récupération des catégories
        categories = db_manager.get_all_categories()
        if categories:
            print("\n=== CATÉGORIES DISPONIBLES ===")
            for i, category in enumerate(categories, 1):
                print(f"{i}. {category}")
            
            # Afficher les articles de la première catégorie
            if categories:
                articles_by_category = db_manager.get_articles_by_category(categories[0], limit=5)
                print_articles_by_category(articles_by_category, categories[0])
        
        # Fermeture de la connexion à la base de données
        db_manager.disconnect()
        
    except Exception as e:
        logger.error(f"Erreur lors du test de la base de données: {str(e)}")
        print(f"Erreur: {str(e)}")

if __name__ == "__main__":
    main() 