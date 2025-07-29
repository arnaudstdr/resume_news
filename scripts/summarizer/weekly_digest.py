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

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialise le générateur de résumé hebdomadaire.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                  "data", "rss_articles.db")
            
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.connect()  # Connexion à la base de données dès l'initialisation
        logger.info(f"Initialisation du digest hebdomadaire")
        
    def get_weekly_articles(self, days: int = 7, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère les articles publiés au cours des derniers jours.
        
        Args:
            days: Nombre de jours à considérer
            limit: Nombre maximum d'articles à récupérer (None = pas de limite raisonnable)
            
        Returns:
            Liste des articles récents
        """
        try:
            # Suppression de l'ouverture/fermeture de connexion ici
            articles = self.db_manager.get_recent_articles(limit=1000 if limit is None else limit, days=days)
            logger.info(f"Récupération de {len(articles)} articles des {days} derniers jours")
            return articles
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des articles: {str(e)}")
            return []
    
    def prepare_content_for_digest(self, articles: List[Dict[str, Any]]) -> str:
        """
        Prépare le contenu des articles pour la génération du résumé.
        Utilise en priorité le résumé, puis la description, puis le contenu.
        
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
                summary = article.get('summary', '')
                description = article.get('description', '')
                content = article.get('content', '')
                url = article.get('url', '')
                date = article.get('date', '')
                
                # Formatage de la date si disponible
                if date:
                    try:
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        date_str = date_obj.strftime("%d/%m/%Y")
                        content_list.append(f"\n### [{title}]({url}) - {date_str}")
                    except:
                        content_list.append(f"\n### [{title}]({url})")
                else:
                    content_list.append(f"\n### [{title}]({url})")
                
                # Utiliser le meilleur contenu disponible
                if summary and len(summary) > 50:
                    content_list.append(f"Résumé : {summary}")
                elif description and len(description) > 50:
                    content_list.append(f"Description : {description}")
                elif content and len(content) > 50:
                    # Limiter la taille du contenu pour ne pas dépasser le contexte du modèle
                    content = content[:2000] + "..." if len(content) > 2000 else content
                    content_list.append(f"Contenu : {content}")
                
        return "\n".join(content_list)
    
    
    def ollama_generate(self, prompt: str, model: str = "mistral", max_tokens: int = 3500) -> str:
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
                timeout=180
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Erreur lors de la génération avec Ollama : {str(e)}")
            return f"Erreur lors de la génération avec Ollama : {str(e)}"
    
    def mistral_generate(self, prompt: str, max_tokens: int = 3500) -> str:
        """
        Utilise l'API HTTP de Mistral Large pour générer du texte avec la clé API stockée dans .env.
        """
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            logger.error("Clé API Mistral manquante dans .env (MISTRAL_API_KEY)")
            return "Erreur : clé API Mistral manquante."
        try:
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "mistral-large-latest",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            response = requests.post(url, headers=headers, json=data, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erreur lors de la génération avec Mistral Large : {str(e)}")
            return f"Erreur lors de la génération avec Mistral Large : {str(e)}"

    def generate_digest(self, days: int = 7, max_tokens: int = 3500, limit: Optional[int] = None, use_mistral: bool = True) -> str:
        """
        Génère un résumé hebdomadaire des articles récents.
        
        Args:
            days: Nombre de jours à considérer
            max_tokens: Nombre maximum de tokens pour la génération (défaut: 3000)
            limit: Nombre maximum d'articles à résumer (None = pas de limite raisonnable)
            use_mistral: Utiliser l'API Mistral (True) ou Ollama (False)
            
        Returns:
            Résumé hebdomadaire au format texte
        """
        try:
            # Récupérer les articles
            # Note: La connexion est déjà établie dans l'initialiseur
            articles = self.db_manager.get_recent_articles(limit=1000 if limit is None else limit, days=days)
            
            if not articles:
                logger.warning("Aucun article trouvé pour la période spécifiée.")
                self.db_manager.disconnect()  # Assurons-nous de fermer la connexion
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
            prompt = f"""Tu es un expert en intelligence artificielle chargé de rédiger un résumé hebdomadaire clair et exhaustif sur les actualités récentes en IA.

Voici les articles publiés du {date_range} sur l’intelligence artificielle :

{content}

Rédige un résumé approfondi et stratégique en français, en suivant cette structure simple :

🗞️ Synthèse hebdomadaire
	•	Un résumé détaillé de 400-500 mots des principales actualités et tendances importantes de la semaine.
	•	Mentionne clairement ce qui est particulièrement impactant, innovant ou stratégique dans le domaine de l’IA.

📌 Lectures complémentaires
	•	Une liste simple avec les liens directs vers les articles les plus pertinents pour approfondir.

Directives :
	•	Priorise la clarté, la pertinence et l’exhaustivité.
	•	Style : professionnel, synthétique, facile à lire rapidement.
	•	Format : Markdown structuré avec titres et listes à puces.
	•	Langue : Français clair et accessible.
"""
            
            logger.info(f"Génération du résumé hebdomadaire avec Mistral Large...")
            if use_mistral:
                response = self.mistral_generate(prompt, max_tokens=max_tokens)
            else:
                response = self.ollama_generate(prompt, model="mistral", max_tokens=max_tokens)
            
            # Déconnexion de la base de données
            self.db_manager.disconnect()
            
            if not response or len(response) < 50:
                logger.error(f"Réponse trop courte ou vide: '{response}'")
                return f"# Erreur de génération du résumé\n\nAucune réponse de qualité générée. Réponse reçue: {response}"
                
            header = f"# Veille IA: Résumé hebdomadaire du {date_range}\n\n"
            return header + response
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {str(e)}", exc_info=True)
            # S'assurer que la connexion est fermée même en cas d'erreur
            try:
                self.db_manager.disconnect()
            except:
                pass
            return f"Erreur lors de la génération du résumé: {str(e)}"
    
    def save_digest(self, digest: str, output_dir: Optional[str] = None) -> str:
        """
        Sauvegarde le résumé dans un fichier markdown.
        
        Args:
            digest: Contenu du résumé
            output_dir: Répertoire de sortie (par défaut: outputs/normalized/digest_hebdo)
            
        Returns:
            Chemin du fichier de sortie
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outputs", "normalized", "digest_hebdo")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"digest_hebdo_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(digest)
        logger.info(f"Résumé hebdomadaire sauvegardé dans {output_path}")
        return output_path

    def save_full_articles_markdown(self, days: int = 7, output_dir: Optional[str] = None, limit: Optional[int] = None) -> str:
        """
        Génère un fichier markdown listant tous les articles scrappés de la semaine avec toutes les infos (titre, contenu, lien, etc.).
        Args:
            days: Nombre de jours à considérer
            output_dir: Répertoire de sortie (défaut: outputs/normalized/articles_complets)
            limit: Nombre max d'articles (None = pas de limite raisonnable)
        Returns:
            Chemin du fichier markdown généré
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outputs", "normalized", "articles_complets")
        os.makedirs(output_dir, exist_ok=True)
        articles = self.db_manager.get_recent_articles(limit=1000 if limit is None else limit, days=days)
        if not articles:
            logger.warning("Aucun article trouvé pour la génération du markdown complet.")
            return ""
        filename = f"articles_complets_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Articles scrappés de la semaine ({len(articles)})\n\n")
            for idx, article in enumerate(articles, 1):
                title = article.get('title', 'Sans titre')
                url = article.get('url', '')
                date = article.get('date', '')
                content = article.get('content', '')
                summary = article.get('summary', '')
                description = article.get('description', '')
                source = article.get('source_name', article.get('source', 'Inconnu'))
                f.write(f"## {idx}. [{title}]({url})\n")
                if date:
                    f.write(f"**Date :** {date}\n\n")
                f.write(f"**Source :** {source}\n\n")
                if summary:
                    f.write(f"**Résumé :** {summary}\n\n")
                if description:
                    f.write(f"**Description :** {description}\n\n")
                f.write(f"**Contenu :**\n\n{content}\n\n")
                f.write("---\n\n")
        logger.info(f"Markdown complet des articles sauvegardé dans {output_path}")
        return output_path

def main():
    """
    Fonction principale pour générer le résumé hebdomadaire.
    """
    try:
        dotenv.load_dotenv()
        # Initialiser le digest hebdomadaire
        digest = WeeklyDigest()

        # Générer le résumé avec tous les articles de la semaine (limit élevé)
        summary = digest.generate_digest(limit=1000)

        # Sauvegarder le résumé
        output_path = digest.save_digest(summary)
        logger.info(f"Génération du résumé hebdomadaire terminée. Fichier: {output_path}")
        print(f"Résumé hebdomadaire généré avec succès: {output_path}")

        # Générer le markdown complet des articles de la semaine
        digest.db_manager.connect()  # Ré-ouvrir la connexion pour la génération du markdown complet
        full_md_path = digest.save_full_articles_markdown(days=7, limit=1000)
        digest.db_manager.disconnect()  # Fermer la connexion après
        if full_md_path:
            print(f"Markdown complet des articles généré: {full_md_path}")
        else:
            print("Aucun article à inclure dans le markdown complet.")
    except Exception as e:
        logger.error(f"Erreur dans le programme principal: {str(e)}")
        print(f"Erreur: {str(e)}")

if __name__ == "__main__":
    main()
