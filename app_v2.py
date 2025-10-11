"""
Application Streamlit V2 - Système de Recommandation d'Articles
Interface simplifiée et moderne pour Azure deployment
"""

import streamlit as st
import requests
import pandas as pd
import json
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandations",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Style CSS simplifié
st.markdown("""
<style>
    /* En-tête */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        text-align: center;
    }

    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        color: white;
    }

    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.95;
        margin-top: 0.8rem;
        color: white;
    }

    /* Améliorer l'apparence des metrics Streamlit */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
    }

    /* Divider style */
    hr {
        margin: 2rem 0;
        border-color: #e0e0e0;
    }

    /* Footer */
    .footer-text {
        text-align: center;
        color: #999;
        font-size: 0.95rem;
        padding: 1.5rem;
        margin-top: 3rem;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration Azure Functions
AZURE_FUNCTION_URL = os.getenv(
    "AZURE_FUNCTION_URL",
    "https://YOUR_FUNCTION_NAME.azurewebsites.net/api/recommend"
)
AZURE_FUNCTION_KEY = os.getenv("AZURE_FUNCTION_KEY", "")

# Cache pour les métadonnées
@st.cache_data
def load_articles_metadata():
    """Charge les métadonnées des articles"""
    try:
        return pd.read_csv('data/articles_metadata.csv')
    except FileNotFoundError:
        st.warning("⚠️ Fichier de métadonnées introuvable")
        return pd.DataFrame()

# Cache pour la liste des utilisateurs
@st.cache_data
def load_users_list(sample_size: int = 500):
    """Charge un échantillon d'utilisateurs"""
    try:
        clicks_df = pd.read_csv('data/clicks_sample.csv')
        users = sorted(clicks_df['user_id'].unique()[:sample_size].tolist())
        return users
    except:
        return list(range(1, 101))

def get_recommendations(user_id: int, n_recommendations: int = 5) -> Dict:
    """Appelle l'Azure Function pour obtenir les recommandations"""
    try:
        headers = {"Content-Type": "application/json"}
        if AZURE_FUNCTION_KEY:
            headers["x-functions-key"] = AZURE_FUNCTION_KEY

        payload = {
            "user_id": user_id,
            "n_recommendations": n_recommendations
        }

        response = requests.post(
            AZURE_FUNCTION_URL,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Erreur serveur: {response.status_code}",
                "message": response.text
            }

    except requests.exceptions.Timeout:
        return {"error": "Timeout de la requête"}
    except requests.exceptions.ConnectionError:
        return {"error": "Impossible de se connecter au serveur"}
    except Exception as e:
        return {"error": f"Erreur inattendue: {str(e)}"}

def display_recommendation_card(rank: int, article_id: int, article_data: Optional[pd.Series]):
    """Affiche une carte de recommandation avec Streamlit natif"""

    # Container avec bordure et style
    with st.container():
        # Badge de rang
        col_rank, col_content = st.columns([1, 9])

        with col_rank:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 0.5rem;
                    border-radius: 50%;
                    text-align: center;
                    font-weight: 700;
                    font-size: 1.2rem;
                    width: 50px;
                    height: 50px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    {rank}
                </div>
            """, unsafe_allow_html=True)

        with col_content:
            # Titre de l'article
            st.markdown(f"### 📰 Article **{article_id}**")

            if article_data is not None and not article_data.empty:
                # Afficher les métadonnées dans des colonnes
                meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)

                with meta_col1:
                    category = article_data.get('category_id', 'N/A')
                    st.metric("📁 Catégorie", category)

                with meta_col2:
                    publisher = article_data.get('publisher_id', 'N/A')
                    st.metric("✍️ Éditeur", publisher)

                with meta_col3:
                    words = int(article_data.get('words_count', 0))
                    st.metric("📝 Longueur", f"{words} mots")

                with meta_col4:
                    if 'created_at_ts' in article_data:
                        try:
                            date = pd.to_datetime(article_data['created_at_ts'], unit='ms')
                            st.metric("📅 Publié", date.strftime('%d/%m/%Y'))
                        except:
                            st.metric("📅 Publié", "N/A")
                    else:
                        st.metric("📅 Publié", "N/A")
            else:
                st.caption("_Métadonnées non disponibles_")

        # Séparateur
        st.divider()

def main():
    """Interface principale"""

    # En-tête
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">📰 My Content</h1>
        <p class="header-subtitle">Système de recommandation d'articles personnalisés</p>
    </div>
    """, unsafe_allow_html=True)

    # Section de sélection utilisateur
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        # Charger la liste des utilisateurs
        users_list = load_users_list()

        selected_user = st.selectbox(
            "👤 Sélectionner un utilisateur",
            options=users_list,
            help="Choisissez un ID utilisateur"
        )

    with col2:
        # Mode de test
        use_mock = st.checkbox(
            "🔧 Mode test (sans Azure)",
            value=False,
            help="Utilise des données simulées"
        )

    with col3:
        # Bouton de génération
        generate_btn = st.button(
            "✨ Recommander",
            type="primary",
            use_container_width=True
        )

    st.markdown("---")

    # Affichage des recommandations
    if generate_btn:

        # Titre de la section
        st.markdown(f"## 🎯 Recommandations pour l'utilisateur **{selected_user}**")
        st.markdown("")  # Espacement

        with st.spinner("Génération des recommandations en cours..."):

            if use_mock:
                # Mode test avec données simulées
                import random
                st.info("Mode test activé - Données simulées")

                recommendations_data = {
                    "user_id": selected_user,
                    "recommendations": random.sample(range(1000, 10000), 5),
                    "model": "ALS",
                    "status": "success"
                }
            else:
                # Appel réel à Azure
                recommendations_data = get_recommendations(selected_user, 5)

            # Gestion des erreurs
            if "error" in recommendations_data:
                error_msg = f"❌ **Erreur:** {recommendations_data['error']}"
                if "message" in recommendations_data and recommendations_data["message"]:
                    error_msg += f"\n\n_{recommendations_data['message']}_"
                st.error(error_msg)

            elif "recommendations" in recommendations_data:
                # Message de succès
                if not use_mock:
                    st.success(f"✅ Recommandations générées avec succès par le modèle {recommendations_data.get('model', 'ALS')}")

                # Charger les métadonnées
                articles_df = load_articles_metadata()

                # Afficher les 5 recommandations
                recommendations = recommendations_data["recommendations"][:5]

                for idx, article_id in enumerate(recommendations, 1):
                    # Récupérer les données de l'article
                    article_data = None
                    if not articles_df.empty:
                        article_row = articles_df[articles_df['article_id'] == article_id]
                        if not article_row.empty:
                            article_data = article_row.iloc[0]

                    display_recommendation_card(idx, article_id, article_data)

                # Résumé en bas
                st.markdown("---")

                col_summary1, col_summary2, col_summary3 = st.columns(3)

                with col_summary1:
                    st.metric("👤 Utilisateur", selected_user)

                with col_summary2:
                    st.metric("📊 Modèle", "ALS")

                with col_summary3:
                    n_reco = len(recommendations)
                    if not articles_df.empty:
                        categories = []
                        for aid in recommendations:
                            article_row = articles_df[articles_df['article_id'] == aid]
                            if not article_row.empty:
                                categories.append(article_row.iloc[0].get('category_id', 'N/A'))
                        diversity = len(set(categories))
                        st.metric("🎨 Diversité", f"{diversity} catégories")
                    else:
                        st.metric("📰 Articles", n_reco)

            else:
                st.warning("⚠️ Format de réponse inattendu")

    else:
        # Message d'accueil
        st.info("👆 Sélectionnez un utilisateur et cliquez sur 'Recommander' pour obtenir des suggestions personnalisées")

    # Footer
    st.markdown("")
    st.markdown("")
    st.markdown("""
    <div class="footer-text">
        🚀 Powered by <strong>Azure Functions</strong> & <strong>Collaborative Filtering (ALS)</strong>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
