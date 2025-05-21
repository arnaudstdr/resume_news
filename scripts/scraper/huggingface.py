import feedparser
import json
from datetime import datetime, timedelta
import os

# URL du blog Hugging Face
BLOG_URL = "https://huggingface.co/blog/feed.xml"

def scrape_huggingface_blog(days_limit=7):
    """Scrape le blog Hugging Face et retourne les articles récents."""

    feed = feedparser.parse(BLOG_URL)
    print(f"[DEBUG] Nombre d'entrées dans le flux : {len(feed.entries)}")
    
    if not feed.entries:
        print("[WARNING] Aucun article trouvé dans le flux RSS.")
        return []
    
    results = []
    date_limit = datetime.now() - timedelta(days=days_limit)
    print(f"[DEBUG] Date limite : {date_limit}")

    for entry in feed.entries:
        print(f"[DEBUG] Traitement de l'article : {entry.title}")
        # pubDate est souvent au format struct_time
        if hasattr(entry, 'published_parsed'):
            published = datetime(*entry.published_parsed[:6])
            print(f"[DEBUG] Date de publication : {published}")
            if published < date_limit:
                print(f"[DEBUG] Article trop ancien, ignoré")
                continue

        else:
            print(f"[DEBUG] Pas de date de publication trouvée")
            continue
    
        results.append({
            "title": entry.title,
            "url": entry.link,
            "date": published.isoformat(),
            "scraped_at": datetime.now().isoformat()
        })
        print(f"[DEBUG] Article ajouté aux résultats")

    print(f"[DEBUG] Nombre total d'articles retenus : {len(results)}")
    return results

def save_to_json(data, filepath="outputs/hf_articles.json"):
    """Enregistre les résultats dans un fichier JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Données enregistrées dans {filepath}")

if __name__ == "__main__":
    articles = scrape_huggingface_blog()
    save_to_json(articles)