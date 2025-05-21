import feedparser
import json
from datetime import datetime, timedelta
import os
import re
import logging
import time
from typing import List, Dict, Optional
import requests
from requests.exceptions import RequestException
from urllib.parse import urlparse
import concurrent.futures

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rss_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
RSS_LIST_PATH = os.path.join(os.path.dirname(__file__), "flux_rss.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs")
DAYS_LIMIT = 7
MAX_RETRIES = 3
RETRY_DELAY = 5  # secondes
REQUEST_TIMEOUT = 30  # secondes
MAX_WORKERS = 5  # nombre de workers pour le scraping parallèle

class RSSScraperError(Exception):
    """Classe personnalisée pour les erreurs du scraper"""
    pass

def slugify(text: str) -> str:
    """Convertit un texte en slug URL-friendly"""
    return re.sub(r'\W+', '-', text.lower()).strip('-')

def load_rss_sources(filepath: str) -> List[Dict]:
    """Charge les sources RSS depuis le fichier de configuration"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Fichier de configuration non trouvé: {filepath}")
        raise RSSScraperError(f"Fichier de configuration non trouvé: {filepath}")
    except json.JSONDecodeError:
        logger.error(f"Erreur de décodage JSON dans le fichier: {filepath}")
        raise RSSScraperError(f"Format JSON invalide dans le fichier: {filepath}")

def validate_url(url: str) -> bool:
    """Valide le format d'une URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def fetch_feed_with_retry(url: str, retries: int = MAX_RETRIES) -> Optional[feedparser.FeedParserDict]:
    """Récupère le flux RSS avec gestion des retries et timeouts"""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return feedparser.parse(response.content)
        except RequestException as e:
            logger.warning(f"Tentative {attempt + 1}/{retries} échouée pour {url}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Échec de la récupération du flux après {retries} tentatives: {url}")
                return None

def scrape_rss_source(name: str, url: str, days_limit: int = DAYS_LIMIT) -> List[Dict]:
    """Scrape un flux RSS avec gestion des erreurs améliorée"""
    logger.info(f"Début du scraping pour: {name} ({url})")
    
    if not validate_url(url):
        logger.error(f"URL invalide pour {name}: {url}")
        return []

    feed = fetch_feed_with_retry(url)
    if not feed or not feed.entries:
        logger.warning(f"Aucun article trouvé pour {name}")
        return []
    
    results = []
    date_limit = datetime.now() - timedelta(days=days_limit)
    errors_count = 0

    for entry in feed.entries:
        try:
            article_data = {
                "title": entry.get('title', ''),
                "url": entry.get('link', ''),
                "date": None,
                "scraped_at": datetime.now().isoformat(),
                "source": name
            }

            # Ajout des champs de contenu si présents
            if 'summary' in entry:
                article_data['summary'] = entry['summary']
            if 'description' in entry:
                article_data['description'] = entry['description']
            if 'content' in entry:
                # Peut être une liste de dicts ou un seul dict
                content = entry['content']
                if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                    article_data['content'] = content[0].get('value', '')
                elif isinstance(content, dict):
                    article_data['content'] = content.get('value', '')
                else:
                    article_data['content'] = str(content)
            if 'content:encoded' in entry:
                article_data['content_encoded'] = entry['content:encoded']

            # Gestion de la date
            published_parsed = entry.get('published_parsed')
            if published_parsed and isinstance(published_parsed, tuple):
                try:
                    published = datetime(*published_parsed[:6])
                    if published >= date_limit:
                        article_data["date"] = published.isoformat()
                        results.append(article_data)
                    else:
                        logger.debug(f"Article trop ancien ignoré: {article_data['title']}")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Erreur de parsing de date pour {name}: {str(e)}")
                    results.append(article_data)
            else:
                logger.debug(f"Pas de date de publication pour: {article_data['title']}")
                results.append(article_data)

        except Exception as e:
            errors_count += 1
            logger.error(f"Erreur lors du traitement d'un article de {name}: {str(e)}")
            continue

    logger.info(f"Scraping terminé pour {name}: {len(results)} articles récupérés, {errors_count} erreurs")
    return results

def save_results(source_name: str, articles: List[Dict]) -> None:
    """Sauvegarde les résultats avec gestion des erreurs"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = f"{slugify(source_name)}.json"
        path = os.path.join(OUTPUT_DIR, filename)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        logger.info(f"{len(articles)} articles enregistrés dans {path}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des résultats pour {source_name}: {str(e)}")
        raise RSSScraperError(f"Erreur de sauvegarde: {str(e)}")

def process_source(source: Dict) -> None:
    """Traite une source RSS individuelle"""
    try:
        name = source["name"]
        url = source["url"]
        articles = scrape_rss_source(name, url)
        save_results(name, articles)
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la source {source.get('name', 'unknown')}: {str(e)}")

def run_all() -> None:
    """Exécute le scraping de toutes les sources en parallèle"""
    try:
        sources = load_rss_sources(RSS_LIST_PATH)
        logger.info(f"Démarrage du scraping pour {len(sources)} sources")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(process_source, sources)
            
        logger.info("Scraping terminé avec succès")
    except Exception as e:
        logger.error(f"Erreur critique lors de l'exécution: {str(e)}")
        raise RSSScraperError(f"Erreur critique: {str(e)}")

if __name__ == "__main__":
    try:
        run_all()
    except RSSScraperError as e:
        logger.error(f"Le scraping a échoué: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        exit(1)
