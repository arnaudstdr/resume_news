#!/usr/bin/env python3
"""
Générateur de page HTML statique pour la veille IA.
Crée une page web autonome avec tous les résumés et articles.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import markdown
import sys

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.database.db_manager import DatabaseManager
except ImportError:
    print("⚠️  Module db_manager non trouvé. Utilisation des fichiers JSON.")
    DatabaseManager = None

class StaticHTMLGenerator:
    """Générateur de page HTML statique pour la veille IA."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.outputs_dir = self.base_dir / "outputs"
        self.data_dir = self.base_dir / "data"
        self.db_path = self.data_dir / "rss_articles.db"
        
    def get_articles(self):
        """Récupère tous les articles."""
        if DatabaseManager and self.db_path.exists():
            try:
                db_manager = DatabaseManager(str(self.db_path))
                db_manager.connect()
                articles = db_manager.get_recent_articles(limit=1000, days=30)
                db_manager.disconnect()
                return articles
            except Exception as e:
                print(f"Erreur base de données : {e}")
        
        # Fallback : fichiers JSON
        return self._get_articles_from_json()
    
    def _get_articles_from_json(self):
        """Récupère les articles depuis les fichiers JSON."""
        articles = []
        
        for json_file in self.outputs_dir.glob("*.json"):
            if json_file.name == "normalized_articles.json":
                continue
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_articles = json.load(f)
                    source_name = json_file.stem.replace('-', ' ').title()
                    
                    for article in file_articles:
                        article['source_name'] = source_name
                        articles.append(article)
            except Exception as e:
                print(f"Erreur lecture {json_file} : {e}")
        
        # Tri par date
        articles.sort(key=lambda x: x.get('date', ''), reverse=True)
        return articles
    
    def get_latest_digest(self):
        """Récupère le dernier résumé."""
        try:
            # Chercher dans le bon répertoire
            digest_dir = self.outputs_dir / "normalized" / "digest_hebdo"
            digest_files = list(digest_dir.glob("digest_hebdo_*.md"))
            if not digest_files:
                return None
            
            latest_digest = max(digest_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_digest, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'filename': latest_digest.name,
                'content': content,
                'html': markdown.markdown(content),
                'date': datetime.fromtimestamp(latest_digest.stat().st_mtime)
            }
        except Exception as e:
            print(f"Erreur lecture résumé : {e}")
            return None
    
    def generate_html(self):
        """Génère la page HTML complète."""
        articles = self.get_articles()
        digest = self.get_latest_digest()
        
        # Statistiques
        sources = list(set(a.get('source_name', a.get('source', 'Unknown')) for a in articles))
        total_articles = len(articles)
        
        html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📰 Veille IA - Rapport Statique</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --accent-color: #0ea5e9;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --gradient-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
        }}

        .header {{
            background: var(--gradient-bg);
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}

        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
        }}

        .stat-label {{
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }}

        .section {{
            background: var(--card-bg);
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .section-header {{
            background: #f8fafc;
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .section-header h2 {{
            font-size: 1.5rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .section-content {{
            padding: 1.5rem;
        }}

        .digest-content {{
            line-height: 1.7;
        }}

        .digest-content h1, .digest-content h2, .digest-content h3 {{
            color: var(--text-primary);
            margin: 1.5rem 0 1rem 0;
        }}

        .digest-content h1 {{
            font-size: 1.875rem;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
        }}

        .digest-content h2 {{
            font-size: 1.5rem;
            color: var(--primary-color);
        }}

        .digest-content h3 {{
            font-size: 1.25rem;
        }}

        .digest-content p {{
            margin-bottom: 1rem;
        }}

        .digest-content ul, .digest-content ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}

        .digest-content li {{
            margin-bottom: 0.5rem;
        }}

        .articles-grid {{
            display: grid;
            gap: 1rem;
        }}

        .article-item {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            transition: box-shadow 0.2s;
        }}

        .article-item:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .article-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .article-title a {{
            color: var(--text-primary);
            text-decoration: none;
        }}

        .article-title a:hover {{
            color: var(--primary-color);
        }}

        .article-meta {{
            display: flex;
            align-items: center;
            gap: 1rem;
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}

        .article-source {{
            background: var(--primary-color);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}

        .article-summary {{
            color: var(--text-secondary);
            line-height: 1.5;
        }}

        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
            margin-top: 2rem;
        }}

        .toc {{
            background: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
        }}

        .toc h3 {{
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }}

        .toc ul {{
            list-style: none;
            padding: 0;
        }}

        .toc li {{
            margin-bottom: 0.25rem;
        }}

        .toc a {{
            color: var(--primary-color);
            text-decoration: none;
        }}

        .toc a:hover {{
            text-decoration: underline;
        }}

        @media print {{
            .header {{
                background: white;
                color: black;
            }}
            
            .section {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-robot"></i> Veille Intelligence Artificielle</h1>
        <p>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
    </div>

    <div class="container">
        <div class="toc">
            <h3><i class="fas fa-list"></i> Table des matières</h3>
            <ul>
                <li><a href="#stats">📊 Statistiques</a></li>
                <li><a href="#digest">📄 Résumé hebdomadaire</a></li>
                <li><a href="#articles">📰 Articles récents</a></li>
            </ul>
        </div>

        <div id="stats" class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_articles}</div>
                <div class="stat-label">Articles collectés</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(sources)}</div>
                <div class="stat-label">Sources surveillées</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([a for a in articles if a.get('date') and (datetime.now() - datetime.fromisoformat(a['date'].replace('Z', '+00:00'))).days <= 7])}</div>
                <div class="stat-label">Articles cette semaine</div>
            </div>
        </div>

        <div id="digest" class="section">
            <div class="section-header">
                <h2><i class="fas fa-file-text"></i> Résumé hebdomadaire</h2>
            </div>
            <div class="section-content">
                <div class="digest-content">
                    {digest['html'] if digest else '<p><em>Aucun résumé disponible</em></p>'}
                </div>
            </div>
        </div>

        <div id="articles" class="section">
            <div class="section-header">
                <h2><i class="fas fa-newspaper"></i> Articles récents ({len(articles)} articles)</h2>
            </div>
            <div class="section-content">
                <div class="articles-grid">
                    {self._generate_articles_html(articles)}
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Rapport généré automatiquement par le pipeline de Veille IA</p>
        <p>Sources : {', '.join(sources)}</p>
    </div>
</body>
</html>"""

        return html_template
    
    def _generate_articles_html(self, articles):
        """Génère le HTML pour la liste des articles."""
        if not articles:
            return '<p><em>Aucun article disponible</em></p>'
        
        html_parts = []
        for article in articles[:50]:  # Limiter à 50 articles pour la page statique
            title = article.get('title', 'Sans titre')
            url = article.get('url', '#')
            source = article.get('source_name', article.get('source', 'Unknown'))
            date = article.get('date', '')
            summary = article.get('summary', article.get('description', 'Aucun résumé disponible'))
            
            date_formatted = ''
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_formatted = date_obj.strftime('%d/%m/%Y à %H:%M')
                except:
                    date_formatted = date
            
            html_parts.append(f'''
                <div class="article-item">
                    <div class="article-title">
                        <a href="{url}" target="_blank">{title}</a>
                    </div>
                    <div class="article-meta">
                        <span class="article-source">{source}</span>
                        <span><i class="fas fa-calendar"></i> {date_formatted}</span>
                    </div>
                    <div class="article-summary">{summary}</div>
                </div>
            ''')
        
        return ''.join(html_parts)
    
    def save_html(self, filename='veille_ia_rapport.html'):
        """Sauvegarde la page HTML."""
        html_content = self.generate_html()
        output_path = self.outputs_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Rapport HTML généré : {output_path}")
        return output_path

def main():
    """Fonction principale."""
    print("🔄 Génération du rapport HTML statique...")
    
    generator = StaticHTMLGenerator()
    output_path = generator.save_html()
    
    print(f"📄 Rapport accessible à : file://{output_path.absolute()}")
    print("💡 Vous pouvez ouvrir ce fichier dans votre navigateur pour consulter le rapport hors ligne.")

if __name__ == '__main__':
    main()
