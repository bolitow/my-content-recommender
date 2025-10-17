"""
Application Streamlit V3 - Système de Recommandation d'Articles
Version Production avec métadonnées enrichies et tracking des clics
"""

import streamlit as st
import requests
import pandas as pd
import json
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="My Content - Recommandations",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS
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
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
    }
    hr {
        margin: 2rem 0;
        border-color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration Azure Functions
AZURE_FUNCTION_URL = os.getenv(
    "AZURE_FUNCTION_URL",
    "https://YOUR_FUNCTION_NAME.azurewebsites.net/api/recommend"
)
AZURE_TRACK_CLICK_URL = os.getenv(
    "AZURE_TRACK_CLICK_URL",
    "https://YOUR_FUNCTION_NAME.azurewebsites.net/api/track_click"
)
AZURE_FUNCTION_KEY = os.getenv("AZURE_FUNCTION_KEY", "")


def get_recommendations(user_id: int, n_recommendations: int = 5) -> Dict:
    """Appelle l'Azure Function pour obtenir les recommandations enrichies"""
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
            timeout=30  # Timeout plus long pour le premier chargement
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Erreur serveur: {response.status_code}",
                "message": response.text
            }

    except requests.exceptions.Timeout:
        return {"error": "Timeout de la requête (cold start?)"}
    except requests.exceptions.ConnectionError:
        return {"error": "Impossible de se connecter au serveur"}
    except Exception as e:
        return {"error": f"Erreur inattendue: {str(e)}"}


def track_click(user_id: int, article_id: int, rank: int):
    """Envoie un événement de clic à l'API de tracking"""
    try:
        headers = {"Content-Type": "application/json"}
        if AZURE_FUNCTION_KEY:
            headers["x-functions-key"] = AZURE_FUNCTION_KEY

        payload = {
            "user_id": user_id,
            "article_id": article_id,
            "interaction_type": "click",
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "metadata": {
                "source": "streamlit_app",
                "rank": rank
            }
        }

        response = requests.post(
            AZURE_TRACK_CLICK_URL,
            json=payload,
            headers=headers,
            timeout=5
        )

        return response.status_code == 200

    except:
        return False


def display_recommendation_card(rank: int, article: Dict, user_id: int):
    """Affiche une carte de recommandation enrichie avec tracking"""

    article_id = article.get('article_id')
    has_metadata = article.get('metadata_available', False)

    # Container avec bordure
    with st.container():
        col_rank, col_content, col_action = st.columns([1, 8, 1])

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
            # Titre
            st.markdown(f"### 📰 Article **{article_id}**")

            if has_metadata:
                # Afficher les métadonnées enrichies
                meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)

                with meta_col1:
                    category = article.get('category_id', 'N/A')
                    st.metric("📁 Catégorie", category)

                with meta_col2:
                    publisher = article.get('publisher_id', 'N/A')
                    st.metric("✍️ Éditeur", publisher)

                with meta_col3:
                    words = article.get('words_count', 0)
                    st.metric("📝 Longueur", f"{words} mots")

                with meta_col4:
                    created_at = article.get('created_at')
                    if created_at:
                        st.metric("📅 Publié", created_at)
                    else:
                        st.metric("📅 Publié", "N/A")
            else:
                st.caption("_Métadonnées non disponibles côté serveur_")

        with col_action:
            # Bouton de tracking
            if st.button("👆 Clic", key=f"track_{article_id}", use_container_width=True):
                if track_click(user_id, article_id, rank):
                    st.success("✅", icon="✅")
                else:
                    st.error("❌")

        # Séparateur
        st.divider()


def main():
    """Interface principale"""

    # Sidebar - Options
    with st.sidebar:
        st.title("⚙️ Options")

        st.markdown("### 🧪 Mode de saisie")
        input_mode = st.radio(
            "Choisir le mode",
            ["✍️ Saisie manuelle", "🎲 Utilisateur aléatoire"],
            help="Sélectionne comment choisir l'utilisateur"
        )

        st.markdown("---")

        st.markdown("### 🔧 Configuration")
        use_mock = st.checkbox(
            "Mode test (sans Azure)",
            value=False,
            help="Utilise des données simulées au lieu de l'API Azure"
        )

        n_recommendations = st.slider(
            "Nombre de recommandations",
            min_value=1,
            max_value=10,
            value=5,
            help="Nombre d'articles à recommander"
        )

        st.markdown("---")

        st.markdown("### ℹ️ Info")
        st.caption(f"**API:** {'🔴 Mode test' if use_mock else '🟢 Azure Functions'}")
        st.caption(f"**Endpoint:** `{AZURE_FUNCTION_URL.split('/api')[0]}/api/...`")

    # En-tête
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">📰 My Content</h1>
        <p class="header-subtitle">Système de recommandation d'articles personnalisés</p>
    </div>
    """, unsafe_allow_html=True)

    # Section de sélection utilisateur
    col1, col2 = st.columns([3, 1])

    with col1:
        if input_mode == "✍️ Saisie manuelle":
            selected_user = st.number_input(
                "👤 Entrer un ID utilisateur",
                min_value=1,
                max_value=999999,
                value=12345,
                step=1,
                help="Saisissez n'importe quel ID utilisateur"
            )
        else:  # Mode aléatoire
            import random
            if 'random_user' not in st.session_state:
                st.session_state.random_user = random.randint(1, 100000)

            col_rand1, col_rand2 = st.columns([3, 1])
            with col_rand1:
                selected_user = st.number_input(
                    "👤 Utilisateur aléatoire",
                    value=st.session_state.random_user,
                    disabled=True
                )
            with col_rand2:
                if st.button("🔄 Nouveau", use_container_width=True):
                    st.session_state.random_user = random.randint(1, 100000)
                    st.rerun()

    with col2:
        generate_btn = st.button(
            "✨ Recommander",
            type="primary",
            use_container_width=True
        )

    st.markdown("---")

    # Affichage des recommandations
    if generate_btn:
        st.markdown(f"## 🎯 Recommandations pour l'utilisateur **{selected_user}**")
        st.markdown("")

        with st.spinner("Génération des recommandations... (peut prendre 10-15s au premier chargement)"):

            if use_mock:
                # Mode test
                import random
                st.info("Mode test activé - Données simulées")

                recommendations_data = {
                    "user_id": selected_user,
                    "recommendations": [
                        {
                            "article_id": random.randint(1000, 10000),
                            "category_id": random.randint(1, 461),
                            "words_count": random.randint(100, 500),
                            "created_at": "2025-10-17",
                            "publisher_id": 0,
                            "metadata_available": True
                        }
                        for _ in range(n_recommendations)
                    ],
                    "count": n_recommendations,
                    "model": "ALS",
                    "diversity": {
                        "category_diversity": 0.800,
                        "unique_categories": 4
                    },
                    "metadata_loaded": True,
                    "embeddings_loaded": False,
                    "status": "success"
                }
            else:
                # Appel réel à Azure
                recommendations_data = get_recommendations(selected_user, n_recommendations)

            # Gestion des erreurs
            if "error" in recommendations_data:
                error_msg = f"❌ **Erreur:** {recommendations_data['error']}"
                if "message" in recommendations_data:
                    error_msg += f"\n\n_{recommendations_data['message']}_"
                st.error(error_msg)

            elif "recommendations" in recommendations_data:
                # Afficher les infos de chargement
                if not use_mock:
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        model = recommendations_data.get('model', 'ALS')
                        st.success(f"✅ Modèle: **{model}**")
                    with col_info2:
                        metadata_loaded = recommendations_data.get('metadata_loaded', False)
                        icon = "✅" if metadata_loaded else "⚠️"
                        st.info(f"{icon} Métadonnées: **{'Chargées' if metadata_loaded else 'Non chargées'}**")
                    with col_info3:
                        embeddings_loaded = recommendations_data.get('embeddings_loaded', False)
                        icon = "✅" if embeddings_loaded else "⚠️"
                        st.info(f"{icon} Embeddings: **{'Chargés' if embeddings_loaded else 'Non chargés'}**")

                    st.markdown("")

                # Afficher les recommandations
                recommendations = recommendations_data["recommendations"]

                for idx, article in enumerate(recommendations, 1):
                    display_recommendation_card(idx, article, selected_user)

                # Résumé
                st.markdown("---")

                col_summary1, col_summary2, col_summary3 = st.columns(3)

                with col_summary1:
                    st.metric("👤 Utilisateur", selected_user)

                with col_summary2:
                    diversity_info = recommendations_data.get('diversity', {})
                    diversity_score = diversity_info.get('category_diversity', 0)
                    st.metric("🎨 Diversité", f"{diversity_score:.2f}")

                with col_summary3:
                    unique_cats = diversity_info.get('unique_categories', 0)
                    st.metric("📁 Catégories uniques", unique_cats)

            else:
                st.warning("⚠️ Format de réponse inattendu")

    else:
        st.info("👆 Sélectionnez un utilisateur et cliquez sur 'Recommander'")

    # Footer
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.95rem; padding: 1.5rem; margin-top: 3rem; border-top: 1px solid #e0e0e0;">
        🚀 Powered by <strong>Azure Functions Premium</strong> & <strong>ALS Collaborative Filtering</strong>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
