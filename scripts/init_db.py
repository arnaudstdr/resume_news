import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

def create_database():
    """Crée la base de données et les tables nécessaires."""
    db_path = Path("db/articles.db")
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Création de la table articles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL,
        publication_date TEXT,
        content TEXT,
        summary TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_article(article_data):
    """Insère un article dans la base de données."""
    conn = sqlite3.connect("db/articles.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO articles (title, url, source, publication_date, content, summary)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            article_data['title'],
            article_data['url'],
            article_data['source'],
            article_data.get('publication_date'),
            article_data.get('content'),
            article_data.get('summary')
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # L'article existe déjà (URL unique)
        return False
    finally:
        conn.close()

def migrate_json_files():
    """Migre les données des fichiers JSON vers la base de données."""
    outputs_dir = Path("outputs")
    
    for json_file in outputs_dir.glob("*.json"):
        source_name = json_file.stem
        
        with open(json_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            
        for article in articles:
            article['source'] = source_name
            insert_article(article)

def main():
    """Fonction principale pour initialiser la base de données."""
    print("Création de la base de données...")
    create_database()
    
    print("Migration des données JSON existantes...")
    migrate_json_files()
    
    print("Initialisation terminée avec succès!")

if __name__ == "__main__":
    main() 