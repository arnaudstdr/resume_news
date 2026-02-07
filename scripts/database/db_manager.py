import sqlite3
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configuration du logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gestionnaire de base de données SQLite pour stocker les articles RSS normalisés.
    """

    def __init__(self, db_path: str = "rss_articles.db"):
        """
        Initialise le gestionnaire de base de données.

        Args:
            db_path: Chemin vers le fichier de base de données SQLite
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Établit une connexion à la base de données."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
            self.cursor = self.conn.cursor()
            logger.info(f"Connexion à la base de données établie: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la connexion à la base de données: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion à la base de données fermée")

    def create_tables(self) -> None:
        """Crée les tables nécessaires si elles n'existent pas."""
        try:
            # Table des sources
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    url TEXT NOT NULL,
                    last_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Table des articles
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    source_id INTEGER NOT NULL,
                    date TIMESTAMP,
                    author TEXT,
                    summary TEXT,
                    content TEXT,
                    image_url TEXT,
                    scraped_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
            ''')

            # Table des catégories
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')

            # Table de liaison articles-catégories
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_categories (
                    article_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    PRIMARY KEY (article_id, category_id),
                    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
                )
            ''')

            # Index pour améliorer les performances
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_date ON articles (date)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source ON articles (source_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles (url)')

            self.conn.commit()
            logger.info("Tables créées avec succès")
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la création des tables: {str(e)}")
            raise

    def add_source(self, name: str, url: str) -> int:
        """
        Ajoute une source RSS à la base de données.

        Args:
            name: Nom de la source
            url: URL du flux RSS

        Returns:
            int: ID de la source ajoutée
        """
        try:
            # Vérifier si la source existe déjà
            self.cursor.execute("SELECT id FROM sources WHERE name = ?", (name,))
            result = self.cursor.fetchone()

            if result:
                # Mettre à jour la source existante
                self.cursor.execute(
                    "UPDATE sources SET url = ?, last_updated = ? WHERE id = ?",
                    (url, datetime.now().isoformat(), result['id'])
                )
                source_id = result['id']
                logger.info(f"Source mise à jour: {name}")
            else:
                # Ajouter une nouvelle source
                self.cursor.execute(
                    "INSERT INTO sources (name, url, last_updated) VALUES (?, ?, ?)",
                    (name, url, datetime.now().isoformat())
                )
                source_id = self.cursor.lastrowid
                logger.info(f"Nouvelle source ajoutée: {name}")

            self.conn.commit()
            return source_id
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'ajout de la source {name}: {str(e)}")
            raise

    def add_article(self, article: Dict[str, Any], source_id: int) -> int:
        """
        Ajoute un article à la base de données.

        Args:
            article: Dictionnaire contenant les données de l'article
            source_id: ID de la source de l'article

        Returns:
            int: ID de l'article ajouté ou None si l'article existe déjà
        """
        try:
            # Vérifier si l'article existe déjà
            self.cursor.execute("SELECT id FROM articles WHERE url = ?", (article.get('url'),))
            result = self.cursor.fetchone()

            if result:
                logger.info(f"Article déjà existant: {article.get('title')}")
                return result['id']

            # Ajouter l'article
            self.cursor.execute('''
                INSERT INTO articles (
                    title, url, source_id, date, author, summary, content,
                    image_url, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.get('title'),
                article.get('url'),
                source_id,
                article.get('date'),
                article.get('author'),
                article.get('summary'),
                article.get('content'),
                article.get('image_url'),
                article.get('scraped_at', datetime.now().isoformat())
            ))

            article_id = self.cursor.lastrowid

            # Ajouter les catégories
            categories = article.get('categories', [])
            if categories:
                self._add_categories(article_id, categories)

            self.conn.commit()
            logger.info(f"Nouvel article ajouté: {article.get('title')}")
            return article_id
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'ajout de l'article {article.get('title')}: {str(e)}")
            raise

    def _add_categories(self, article_id: int, categories: List[str]) -> None:
        """
        Ajoute des catégories à un article.

        Args:
            article_id: ID de l'article
            categories: Liste des catégories
        """
        for category_name in categories:
            # Vérifier si la catégorie existe déjà
            self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            result = self.cursor.fetchone()

            if result:
                category_id = result['id']
            else:
                # Ajouter une nouvelle catégorie
                self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                category_id = self.cursor.lastrowid

            # Lier la catégorie à l'article
            self.cursor.execute(
                "INSERT OR IGNORE INTO article_categories (article_id, category_id) VALUES (?, ?)",
                (article_id, category_id)
            )

    def add_articles_batch(self, articles: List[Dict[str, Any]], source_name: str, source_url: str) -> int:
        """
        Ajoute un lot d'articles à la base de données.

        Args:
            articles: Liste d'articles à ajouter
            source_name: Nom de la source
            source_url: URL du flux RSS

        Returns:
            int: Nombre d'articles ajoutés
        """
        try:
            # Ajouter ou mettre à jour la source
            source_id = self.add_source(source_name, source_url)

            # Ajouter les articles
            added_count = 0
            for article in articles:
                try:
                    self.add_article(article, source_id)
                    added_count += 1
                except sqlite3.Error as e:
                    logger.error(f"Erreur lors de l'ajout d'un article: {str(e)}")
                    continue

            logger.info(f"{added_count} articles ajoutés pour la source {source_name}")
            return added_count
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'ajout du lot d'articles: {str(e)}")
            raise

    def get_recent_articles(self, limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """
        Récupère les articles récents.

        Args:
            limit: Nombre maximum d'articles à récupérer
            days: Nombre de jours à considérer

        Returns:
            List[Dict]: Liste des articles récents
        """
        try:
            query = '''
                SELECT
                    a.*,
                    s.name as source_name,
                    s.url as source_url,
                    GROUP_CONCAT(c.name) as categories,
                    a.summary as summary,
                    a.content as content
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                LEFT JOIN article_categories ac ON a.id = ac.article_id
                LEFT JOIN categories c ON ac.category_id = c.id
                WHERE a.date >= datetime('now', ?)
                GROUP BY a.id
                ORDER BY a.date DESC
                LIMIT ?
            '''

            self.cursor.execute(query, (f'-{days} days', limit))
            rows = self.cursor.fetchall()

            # Convertir les lignes en dictionnaires
            articles = []
            for row in rows:
                article = dict(row)
                # Convertir la chaîne de catégories en liste
                if article.get('categories'):
                    article['categories'] = article['categories'].split(',')
                else:
                    article['categories'] = []

                # S'assurer que les champs de contenu ne sont pas None
                for field in ['summary', 'content']:
                    if article.get(field) is None:
                        article[field] = ''

                articles.append(article)

            return articles
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des articles récents: {str(e)}")
            raise

    def get_articles_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les articles par catégorie.

        Args:
            category: Nom de la catégorie
            limit: Nombre maximum d'articles à récupérer

        Returns:
            List[Dict]: Liste des articles de la catégorie
        """
        try:
            query = '''
                SELECT a.*, s.name as source_name, GROUP_CONCAT(c.name) as categories
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                JOIN article_categories ac ON a.id = ac.article_id
                JOIN categories c ON ac.category_id = c.id
                WHERE c.name = ?
                GROUP BY a.id
                ORDER BY a.date DESC
                LIMIT ?
            '''

            self.cursor.execute(query, (category, limit))
            rows = self.cursor.fetchall()

            # Convertir les lignes en dictionnaires
            articles = []
            for row in rows:
                article = dict(row)
                # Convertir la chaîne de catégories en liste
                if article.get('categories'):
                    article['categories'] = article['categories'].split(',')
                else:
                    article['categories'] = []
                articles.append(article)

            return articles
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des articles par catégorie {category}: {str(e)}")
            raise

    def get_all_categories(self) -> List[str]:
        """
        Récupère toutes les catégories.

        Returns:
            List[str]: Liste des catégories
        """
        try:
            self.cursor.execute("SELECT name FROM categories ORDER BY name")
            rows = self.cursor.fetchall()
            return [row['name'] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des catégories: {str(e)}")
            raise

    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un article par son URL.

        Args:
            url: URL de l'article

        Returns:
            Dict: Article ou None si non trouvé
        """
        try:
            query = '''
                SELECT a.*, s.name as source_name, GROUP_CONCAT(c.name) as categories
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                LEFT JOIN article_categories ac ON a.id = ac.article_id
                LEFT JOIN categories c ON ac.category_id = c.id
                WHERE a.url = ?
                GROUP BY a.id
            '''

            self.cursor.execute(query, (url,))
            row = self.cursor.fetchone()

            if row:
                article = dict(row)
                # Convertir la chaîne de catégories en liste
                if article.get('categories'):
                    article['categories'] = article['categories'].split(',')
                else:
                    article['categories'] = []
                return article
            else:
                return None
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération de l'article par URL {url}: {str(e)}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Récupère des statistiques sur la base de données.

        Returns:
            Dict: Statistiques
        """
        try:
            stats = {}

            # Nombre total d'articles
            self.cursor.execute("SELECT COUNT(*) as count FROM articles")
            stats['total_articles'] = self.cursor.fetchone()['count']

            # Nombre total de sources
            self.cursor.execute("SELECT COUNT(*) as count FROM sources")
            stats['total_sources'] = self.cursor.fetchone()['count']

            # Nombre total de catégories
            self.cursor.execute("SELECT COUNT(*) as count FROM categories")
            stats['total_categories'] = self.cursor.fetchone()['count']

            # Articles par source
            self.cursor.execute('''
                SELECT s.name, COUNT(a.id) as count
                FROM sources s
                LEFT JOIN articles a ON s.id = a.source_id
                GROUP BY s.id
                ORDER BY count DESC
            ''')
            stats['articles_by_source'] = {row['name']: row['count'] for row in self.cursor.fetchall()}

            # Articles par catégorie
            self.cursor.execute('''
                SELECT c.name, COUNT(ac.article_id) as count
                FROM categories c
                LEFT JOIN article_categories ac ON c.id = ac.category_id
                GROUP BY c.id
                ORDER BY count DESC
            ''')
            stats['articles_by_category'] = {row['name']: row['count'] for row in self.cursor.fetchall()}

            # Articles par jour (derniers 7 jours)
            self.cursor.execute('''
                SELECT date(a.date) as day, COUNT(*) as count
                FROM articles a
                WHERE a.date >= datetime('now', '-7 days')
                GROUP BY day
                ORDER BY day DESC
            ''')
            stats['articles_by_day'] = {row['day']: row['count'] for row in self.cursor.fetchall()}

            return stats
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            raise