#!/usr/bin/env python
# filepath: /workspaces/veille_ai/scripts/summarizer/weekly_digest.py
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import dotenv
import requests

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from huggingface_hub import login, InferenceClient

# Charger automatiquement les variables d'environnement depuis .env
dotenv.load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekly_digest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeeklyDigest:
    """
    Classe pour générer un résumé hebdomadaire des articles scrapés
    en utilisant un LLM open source compatible text-generation.
    """

    def __init__(self, db_path: str = None, model_name: str = "mistralai/Mistral-7B-Instruct-v0.3"):
        """
        Initialise le générateur de résumé hebdomadaire.
        
        Args:
            db_path: Chemin vers la base de données SQLite
            model_name: Nom du modèle à utiliser (par défaut: mistral/Mistral-7B-Instruct-v0.3)
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                  "data", "rss_articles.db")
            
        self.db_manager = DatabaseManager(db_path)
        self.model_name = model_name
        self.client = InferenceClient(model=model_name)
        logger.info(f"Initialisation du digest hebdomadaire avec le modèle {model_name}")
        
    def get_weekly_articles(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Récupère les articles publiés au cours des derniers jours.
        
        Args:
            days: Nombre de jours à considérer
            
        Returns:
            Liste des articles récents
        """
        try:
            self.db_manager.connect()
            articles = self.db_manager.get_recent_articles(days=days)
            self.db_manager.disconnect()
            
            logger.info(f"Récupération de {len(articles)} articles des {days} derniers jours")
            return articles
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des articles: {str(e)}")
            return []
    
    def prepare_content_for_digest(self, articles: List[Dict[str, Any]]) -> str:
        """
        Prépare le contenu des articles pour la génération du résumé.
        Utilise le contenu s'il est disponible, sinon utilise le titre.
        
        Args:
            articles: Liste des articles à résumer
            
        Returns:
            Texte formaté pour être envoyé au modèle
        """
        content_list = []
        
        # Regrouper les articles par source
        articles_by_source = {}
        for article in articles:
            source = article.get('source', 'Unknown')
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)
        
        # Formater les articles par source
        for source, source_articles in articles_by_source.items():
            content_list.append(f"\n## Articles de {source} ({len(source_articles)} articles)")
            
            for article in source_articles:
                title = article.get('title', 'Sans titre')
                content = article.get('content', '')
                summary = article.get('summary', '')
                url = article.get('url', '')
                
                content_list.append(f"\n### {title}")
                content_list.append(f"URL: {url}")
                
                if summary and len(summary) > 10:
                    content_list.append(f"Résumé: {summary}")
                elif content and len(content) > 10:
                    # Limiter la taille du contenu pour ne pas dépasser le contexte du modèle
                    content = content[:1000] + "..." if len(content) > 1000 else content
                    content_list.append(f"Contenu: {content}")
                
        return "\n".join(content_list)
    
    def ollama_generate(self, prompt: str, model: str = "mistral", max_tokens: int = 1000) -> str:
        """
        Utilise l'API locale d'Ollama pour générer du texte avec le modèle spécifié.
        """
        try:
            response = requests.post(
                "http://host.docker.internal:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens}
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Erreur lors de la génération avec Ollama : {str(e)}")
            return f"Erreur lors de la génération avec Ollama : {str(e)}"

    def generate_digest(self, days: int = 7, max_tokens: int = 1000) -> str:
        """
        Génère un résumé hebdomadaire des articles récents.
        
        Args:
            days: Nombre de jours à considérer
            max_tokens: Nombre maximum de tokens pour la génération
            
        Returns:
            Résumé hebdomadaire au format texte
        """
        try:
            # Récupérer les articles
            articles = self.get_weekly_articles(days)
            
            if not articles:
                logger.warning("Aucun article trouvé pour la période spécifiée.")
                return "Aucun article disponible pour cette semaine."
            
            # Vérifier si au moins quelques articles ont du contenu ou un résumé
            articles_with_content = [a for a in articles if a.get('content') or a.get('summary')]
            if not articles_with_content and len(articles) > 0:
                logger.warning("Aucun article n'a de contenu ou de résumé. Utilisation des titres uniquement.")
                # Adapter pour utiliser uniquement les titres
                for a in articles:
                    a['content'] = f"{a.get('title', 'Sans titre')}"
            
            # Préparer le contenu
            content = self.prepare_content_for_digest(articles)
            
            # Date de début et de fin pour le titre
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_range = f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
            
            # Créer le prompt pour Mistral (en français)
            prompt = f"""Voici une liste d'articles sur l'intelligence artificielle publiés du {date_range}.

{content}

Rédige un résumé hebdomadaire synthétique en français sur les actualités importantes en IA durant cette période.
Le résumé doit être structuré avec :
1. Une introduction résumant les tendances principales de la semaine
2. 3 à 5 points clés ou thématiques qui ressortent de ces articles
3. Une courte conclusion

Format souhaité : Markdown
Langue : Français
Ton : Professionnel et informatif
Longueur : Environ 500 mots
"""
            logger.info(f"Génération du résumé hebdomadaire avec Ollama (modèle : mistral)...")
            response = self.ollama_generate(prompt, model="mistral", max_tokens=max_tokens)
            if not response or len(response) < 50:
                logger.error(f"Réponse trop courte ou vide d'Ollama: '{response}'")
                return f"# Erreur de génération du résumé\n\nOllama n'a pas réussi à générer un résumé de qualité. Réponse reçue: {response}"
            header = f"# Veille IA: Résumé hebdomadaire du {date_range}\n\n"
            return header + response
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {str(e)}", exc_info=True)
            return f"Erreur lors de la génération du résumé: {str(e)}"
    
    def save_digest(self, digest: str, output_dir: Optional[str] = None) -> str:
        """
        Sauvegarde le résumé dans un fichier markdown.
        
        Args:
            digest: Contenu du résumé
            output_dir: Répertoire de sortie (par défaut: dossier outputs)
            
        Returns:
            Chemin du fichier de sortie
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outputs")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer un nom de fichier basé sur la date
        filename = f"digest_hebdo_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(digest)
            
        logger.info(f"Résumé hebdomadaire sauvegardé dans {output_path}")
        return output_path

def main():
    """
    Fonction principale pour générer le résumé hebdomadaire.
    """
    try:
        # Vérifier si un token d'API Hugging Face est fourni
        api_token = os.environ.get("HF_API_TOKEN")
        if api_token:
            login(token=api_token)
            logger.info("Authentification à Hugging Face réussie")
        else:
            logger.warning("Aucun token Hugging Face trouvé dans HF_API_TOKEN. Utilisation en mode invité.")
        
        # Initialiser le digest hebdomadaire
        digest = WeeklyDigest()
        
        # Générer le résumé
        summary = digest.generate_digest()
        
        # Sauvegarder le résumé
        output_path = digest.save_digest(summary)
        
        logger.info(f"Génération du résumé hebdomadaire terminée. Fichier: {output_path}")
        print(f"Résumé hebdomadaire généré avec succès: {output_path}")
        
    except Exception as e:
        logger.error(f"Erreur dans le programme principal: {str(e)}")
        print(f"Erreur: {str(e)}")

if __name__ == "__main__":
    main()
