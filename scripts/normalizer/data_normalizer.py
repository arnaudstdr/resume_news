import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from bs4 import BeautifulSoup
import html
from transformers import pipeline

# Configuration du logging
logger = logging.getLogger(__name__)

class DataNormalizer:
    """
    Classe pour normaliser les données RSS provenant de différentes sources.
    """

    def __init__(self):
        """Initialise le normaliseur de données."""
        self.required_fields = ["title", "url", "source", "scraped_at"]
        self.optional_fields = ["date", "author", "summary", "content", "categories", "image_url"]
        self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")

    def normalize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise un article RSS en appliquant un format standard.

        Args:
            article: Dictionnaire contenant les données d'un article

        Returns:
            Dict: Article normalisé
        """
        try:
            # Vérification des champs requis
            for field in self.required_fields:
                if field not in article:
                    logger.warning(f"Champ requis manquant: {field}")
                    article[field] = ""

            # Normalisation des champs
            normalized = {
                "title": self._normalize_text(article.get("title", "")),
                "url": self._normalize_url(article.get("url", "")),
                "source": article.get("source", ""),
                "scraped_at": article.get("scraped_at", datetime.now().isoformat()),
                "date": self._normalize_date(article.get("date")),
                "author": self._normalize_text(article.get("author", "")),
                "summary": self.generate_summary(article),  # Ajout du résumé
                "content": self._normalize_text(article.get("content", "")),
                "categories": self._normalize_categories(article.get("categories", [])),
                "image_url": self._normalize_url(article.get("image_url", ""))
            }

            # Nettoyage des champs vides
            return {k: v for k, v in normalized.items() if v is not None and v != ""}

        except Exception as e:
            logger.error(f"Erreur lors de la normalisation de l'article: {str(e)}")
            return article

    def _normalize_text(self, text: str) -> str:
        """
        Normalise un texte en supprimant les balises HTML et en nettoyant le formatage.

        Args:
            text: Texte à normaliser

        Returns:
            str: Texte normalisé
        """
        if not text:
            return ""

        # Décodage des entités HTML
        text = html.unescape(text)

        # Suppression des balises HTML
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text()

        # Nettoyage du texte
        text = re.sub(r'\s+', ' ', text)  # Remplace les espaces multiples par un seul espace
        text = text.strip()  # Supprime les espaces au début et à la fin

        return text

    def _normalize_url(self, url: str) -> str:
        """
        Normalise une URL en s'assurant qu'elle est valide.

        Args:
            url: URL à normaliser

        Returns:
            str: URL normalisée ou chaîne vide si invalide
        """
        if not url:
            return ""

        # Vérification basique du format URL
        url_pattern = re.compile(
            r'^https?://'  # http:// ou https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domaine
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # port optionnel
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if url_pattern.match(url):
            return url
        else:
            logger.warning(f"URL invalide: {url}")
            return ""

    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Normalise une date en format ISO 8601.

        Args:
            date_str: Date à normaliser

        Returns:
            str: Date normalisée au format ISO 8601 ou None si invalide
        """
        if not date_str:
            return None

        try:
            # Tentative de parsing de la date
            if isinstance(date_str, str):
                # Essai de différents formats courants
                formats = [
                    "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 avec timezone
                    "%Y-%m-%dT%H:%M:%S",    # ISO 8601 sans timezone
                    "%Y-%m-%d %H:%M:%S",    # Format standard
                    "%a, %d %b %Y %H:%M:%S %z",  # Format RSS standard
                    "%Y-%m-%d"              # Date simple
                ]

                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue

                logger.warning(f"Format de date non reconnu: {date_str}")
                return None
            else:
                return date_str.isoformat()

        except Exception as e:
            logger.error(f"Erreur lors de la normalisation de la date {date_str}: {str(e)}")
            return None

    def _normalize_categories(self, categories: List[str]) -> List[str]:
        """
        Normalise une liste de catégories.

        Args:
            categories: Liste de catégories à normaliser

        Returns:
            List[str]: Liste de catégories normalisées
        """
        if not categories:
            return []

        # Si categories est une chaîne, la convertir en liste
        if isinstance(categories, str):
            categories = [categories]

        # Normalisation des catégories
        normalized = []
        for category in categories:
            if category:
                # Nettoyage et normalisation
                clean_category = self._normalize_text(category)
                if clean_category:
                    normalized.append(clean_category)

        # Suppression des doublons
        return list(set(normalized))

    def normalize_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalise un lot d'articles.

        Args:
            articles: Liste d'articles à normaliser

        Returns:
            List[Dict]: Liste d'articles normalisés
        """
        normalized_articles = []
        for article in articles:
            try:
                normalized = self.normalize_article(article)
                normalized_articles.append(normalized)
            except Exception as e:
                logger.error(f"Erreur lors de la normalisation d'un article: {str(e)}")
                continue

        return normalized_articles

    def generate_summary(self, article: Dict[str, Any]) -> str:
        """
        Génère un résumé pour un article en utilisant le LLM.

        Args:
            article: Dictionnaire contenant les données d'un article

        Returns:
            str: Résumé de l'article
        """
        try:
            content = article.get('content', '')
            if not content or not isinstance(content, str) or not content.strip():
                logger.warning("Aucun contenu à résumer pour l'article")
                return ""
            summary = self.summarizer(content, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
            return summary
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {str(e)}")
            return ""