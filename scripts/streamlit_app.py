import streamlit as st
import os
import sys
from summarizer.weekly_digest import WeeklyDigest

# Pour pouvoir importer run_all du pipeline principal
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
sys.path.append(SCRIPTS_DIR)
from run_all import main as run_pipeline

st.set_page_config(page_title="Veille IA - Interface", layout="wide")
st.title("📰 Veille IA : Lecture & Résumé LLM")

# Bouton pour lancer le scrapping complet
def lancer_scrapping():
    with st.spinner("Scrapping, normalisation et insertion en base en cours..."):
        run_pipeline()
    st.success("Scrapping terminé ! Les articles sont à jour.")
    st.info("Veuillez rafraîchir la page manuellement pour voir les nouveaux articles.")

if st.button("🔄 Lancer un nouveau scrapping complet", type="primary"):
    lancer_scrapping()

# Correction du chemin vers la base de données (racine du projet)
DB_PATH = os.path.join(PROJECT_ROOT, "data", "rss_articles.db")
digest = WeeklyDigest(db_path=DB_PATH)

# Affichage des articles récents
days = st.sidebar.slider("Nombre de jours à afficher", 1, 30, 7)
limit = st.sidebar.slider("Nombre d'articles max", 5, 100, 20)
articles = digest.get_weekly_articles(days=days, limit=limit)

st.subheader(f"Articles des {days} derniers jours ({len(articles)})")
for idx, article in enumerate(articles, 1):
    with st.expander(f"{idx}. {article.get('title', 'Sans titre')}"):
        st.markdown(f"**Source :** {article.get('source', 'Inconnu')}")
        st.markdown(f"**Date :** {article.get('date', '')}")
        st.markdown(f"**Résumé :** {article.get('summary', '')}")
        st.markdown(f"**Contenu :**\n\n{article.get('content', '')}")
        st.markdown(f"[Lien vers l'article]({article.get('url', '')})")

# Génération du résumé LLM
st.markdown("---")
st.header("Résumé stratégique généré par LLM")
if st.button("Générer le résumé LLM (Mistral)"):
    with st.spinner("Génération du résumé, cela peut prendre 1-2 minutes..."):
        summary = digest.generate_digest(days=days, limit=limit, use_mistral=True)
        st.markdown(summary)
