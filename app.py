"""
Application Streamlit - Système de Recommandation d'Articles
Interface utilisateur pour le système de recommandation basé sur ALS
"""

import streamlit as st
import requests
import pandas as pd
import json
from typing import List, Dict
import os

# Configuration de la page
st.set_page_config(
    page_title="Système de Recommandation d'Articles",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration Azure Functions
AZURE_FUNCTION_URL = os.getenv(
    "AZURE_FUNCTION_URL",
    "https://YOUR_FUNCTION_NAME.azurewebsites.net/api/recommend"
)
AZURE_FUNCTION_KEY = os.getenv("AZURE_FUNCTION_KEY", "")  # À configurer

# Cache pour les métadonnées des articles
@st.cache_data
def load_articles_metadata():
    """Charge les métadonnées des articles"""
    try:
        articles_df = pd.read_csv('data/articles_metadata.csv')
        return articles_df
    except FileNotFoundError:
        st.error("Fichier de métadonnées introuvable")
        return pd.DataFrame()

# Cache pour la liste des utilisateurs
@st.cache_data
def load_users_list():
    """Charge la liste des utilisateurs disponibles"""
    try:
        # Charger depuis les données de clics pour obtenir les user_ids
        click_files = pd.read_csv('data/clicks/clicks_hour_000.csv')
        users = click_files['user_id'].unique()[:1000]  # Limiter pour la démo
        return sorted(users.tolist())
    except:
        # Fallback avec des IDs de démo
        return list(range(1, 101))

def get_recommendations(user_id: int, n_recommendations: int = 5) -> Dict:
    """
    Appelle l'Azure Function pour obtenir les recommandations

    Args:
        user_id: ID de l'utilisateur
        n_recommendations: Nombre de recommandations souhaitées

    Returns:
        Dictionnaire avec les recommandations ou erreur
    """
    try:
        # Préparer la requête
        headers = {
            "Content-Type": "application/json"
        }

        # Ajouter la clé d'API si configurée
        if AZURE_FUNCTION_KEY:
            headers["x-functions-key"] = AZURE_FUNCTION_KEY

        payload = {
            "user_id": user_id,
            "n_recommendations": n_recommendations
        }

        # Appel à l'Azure Function
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

def display_recommendations(recommendations: List[int], articles_df: pd.DataFrame):
    """
    Affiche les recommandations sous forme de cartes professionnelles

    Args:
        recommendations: Liste des IDs d'articles recommandés
        articles_df: DataFrame avec les métadonnées des articles
    """
    if not recommendations:
        st.warning("Aucune recommandation disponible")
        return

    # CSS personnalisé pour les cartes
    st.markdown("""
    <style>
    .article-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        color: white;
        transition: transform 0.2s;
    }
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .article-rank {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .article-meta {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.8rem;
        border-radius: 5px;
        margin-top: 0.8rem;
    }
    .meta-item {
        display: flex;
        justify-content: space-between;
        margin: 0.3rem 0;
        padding: 0.2rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .meta-label {
        font-weight: 600;
        opacity: 0.9;
    }
    .meta-value {
        font-weight: 300;
    }
    .category-badge {
        background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Affichage en grille responsive
    num_cols = min(3, len(recommendations))
    rows_needed = (len(recommendations) + num_cols - 1) // num_cols

    for row in range(rows_needed):
        cols = st.columns(num_cols)

        for col_idx in range(num_cols):
            article_idx = row * num_cols + col_idx

            if article_idx < len(recommendations):
                article_id = recommendations[article_idx]
                article_info = articles_df[articles_df['article_id'] == article_id]

                with cols[col_idx]:
                    if not article_info.empty:
                        article = article_info.iloc[0]

                        # Calcul du score de pertinence (position dans la liste)
                        relevance_score = 100 - (article_idx * 10)

                        # Déterminer la couleur du gradient selon la position
                        if article_idx < 3:
                            gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                        elif article_idx < 6:
                            gradient = "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
                        else:
                            gradient = "linear-gradient(135deg, #30cfd0 0%, #330867 100%)"

                        # Carte HTML personnalisée
                        card_html = f"""
                        <div class="article-card" style="background: {gradient};">
                            <div class="article-rank">TOP {article_idx + 1}</div>
                            <h3 style="margin: 0.5rem 0; font-size: 1.3rem;">Article #{article_id}</h3>

                            <div class="article-meta">
                                <div class="meta-item">
                                    <span class="meta-label">Catégorie</span>
                                    <span class="meta-value">{article.get('category_id', 'N/A')}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Éditeur</span>
                                    <span class="meta-value">{article.get('publisher_id', 'N/A')}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">Longueur</span>
                                    <span class="meta-value">{article.get('words_count', 0)} mots</span>
                                </div>
                        """

                        # Ajouter la date si disponible
                        if 'created_at_ts' in article:
                            try:
                                date_pub = pd.to_datetime(article['created_at_ts'], unit='ms')
                                card_html += f"""
                                <div class="meta-item">
                                    <span class="meta-label">Date</span>
                                    <span class="meta-value">{date_pub.strftime('%d/%m/%Y')}</span>
                                </div>
                                """
                            except:
                                pass

                        card_html += f"""
                                <div class="meta-item">
                                    <span class="meta-label">Score</span>
                                    <span class="meta-value">{relevance_score}%</span>
                                </div>
                            </div>
                        </div>
                        """

                        st.markdown(card_html, unsafe_allow_html=True)

                        # Métriques supplémentaires sous la carte
                        metric_cols = st.columns(2)
                        with metric_cols[0]:
                            st.metric(
                                "Pertinence",
                                f"{relevance_score}%",
                                delta=None if article_idx == 0 else f"-{article_idx * 10}%"
                            )
                        with metric_cols[1]:
                            # Calculer un indicateur de fraîcheur
                            if 'created_at_ts' in article:
                                try:
                                    date_pub = pd.to_datetime(article['created_at_ts'], unit='ms')
                                    days_old = (pd.Timestamp.now() - date_pub).days
                                    if days_old < 7:
                                        freshness = "Récent"
                                        delta_fresh = "7j"
                                    elif days_old < 30:
                                        freshness = "Actuel"
                                        delta_fresh = "30j"
                                    else:
                                        freshness = "Archive"
                                        delta_fresh = f"{days_old}j"
                                    st.metric("Fraîcheur", freshness, delta_fresh)
                                except:
                                    st.metric("Fraîcheur", "N/A", None)
                            else:
                                st.metric("Fraîcheur", "N/A", None)
                    else:
                        # Carte simplifiée si pas de métadonnées
                        st.error(f"Article {article_id} - Métadonnées indisponibles")

    # Résumé des recommandations
    st.markdown("---")
    st.subheader("Résumé des recommandations")

    summary_cols = st.columns(3)

    with summary_cols[0]:
        st.info(f"**Articles recommandés:** {len(recommendations)}")

    with summary_cols[1]:
        # Compter les catégories uniques
        categories = []
        for article_id in recommendations:
            article_info = articles_df[articles_df['article_id'] == article_id]
            if not article_info.empty:
                categories.append(article_info.iloc[0].get('category_id', 'N/A'))
        unique_categories = len(set(categories))
        st.info(f"**Catégories uniques:** {unique_categories}")

    with summary_cols[2]:
        # Calculer la longueur moyenne
        total_words = 0
        count = 0
        for article_id in recommendations:
            article_info = articles_df[articles_df['article_id'] == article_id]
            if not article_info.empty:
                words = article_info.iloc[0].get('words_count', 0)
                if words > 0:
                    total_words += words
                    count += 1
        avg_words = total_words // count if count > 0 else 0
        st.info(f"**Longueur moyenne:** {avg_words} mots")

# Interface principale
def main():
    # Titre principal
    st.title("Système de Recommandation d'Articles")
    st.markdown("### Recommandations personnalisées basées sur le filtrage collaboratif (ALS)")

    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("Paramètres")

        # Charger la liste des utilisateurs
        users_list = load_users_list()

        # Sélection de l'utilisateur
        user_selection_mode = st.radio(
            "Mode de sélection utilisateur",
            ["Liste déroulante", "Saisie manuelle"]
        )

        if user_selection_mode == "Liste déroulante":
            selected_user = st.selectbox(
                "Sélectionner un utilisateur",
                options=users_list,
                help="Choisissez un ID utilisateur dans la liste"
            )
        else:
            selected_user = st.number_input(
                "Entrer l'ID utilisateur",
                min_value=1,
                value=1,
                step=1,
                help="Saisissez manuellement un ID utilisateur"
            )

        # Nombre de recommandations
        n_recommendations = st.slider(
            "Nombre de recommandations",
            min_value=1,
            max_value=10,
            value=5,
            help="Nombre d'articles à recommander"
        )

        st.markdown("---")

        # Informations sur la configuration
        st.subheader("Configuration")

        # Vérifier la connexion Azure
        if AZURE_FUNCTION_URL == "https://YOUR_FUNCTION_NAME.azurewebsites.net/api/recommend":
            st.warning("Azure Function non configurée")
            st.info(
                "Configurez la variable d'environnement AZURE_FUNCTION_URL "
                "avec l'URL de votre Azure Function"
            )
        else:
            st.success("Azure Function configurée")

        # Mode de test local
        use_mock = st.checkbox(
            "Mode test local",
            value=True,
            help="Utilise des données simulées sans appel Azure"
        )

    # Zone principale
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header(f"Recommandations pour l'utilisateur {selected_user}")

    with col2:
        # Bouton pour obtenir les recommandations
        if st.button("Obtenir les recommandations", type="primary", use_container_width=True):

            with st.spinner("Génération des recommandations en cours..."):

                if use_mock:
                    # Mode test avec données simulées
                    import random
                    st.info("Mode test local activé - Données simulées")

                    # Simuler des recommandations
                    all_articles = list(range(1000, 2000))
                    recommendations_data = {
                        "user_id": selected_user,
                        "recommendations": random.sample(all_articles, n_recommendations),
                        "model": "ALS",
                        "status": "success"
                    }
                else:
                    # Appel réel à Azure Function
                    recommendations_data = get_recommendations(
                        selected_user,
                        n_recommendations
                    )

                # Vérifier les résultats
                if "error" in recommendations_data:
                    st.error(f"Erreur: {recommendations_data['error']}")
                    if "message" in recommendations_data:
                        st.error(f"Détails: {recommendations_data['message']}")

                elif "recommendations" in recommendations_data:
                    # Charger les métadonnées
                    articles_df = load_articles_metadata()

                    # Afficher les statistiques
                    with st.expander("Détails de la requête", expanded=False):
                        st.json({
                            "user_id": recommendations_data.get("user_id"),
                            "nombre_recommandations": len(recommendations_data["recommendations"]),
                            "modèle": recommendations_data.get("model", "ALS"),
                            "statut": recommendations_data.get("status", "success")
                        })

                    # Afficher les recommandations
                    st.subheader("Articles recommandés")
                    display_recommendations(
                        recommendations_data["recommendations"],
                        articles_df
                    )

                    # Métriques en bas
                    st.markdown("---")
                    col_metrics = st.columns(3)
                    with col_metrics[0]:
                        st.metric("Modèle utilisé", "ALS")
                    with col_metrics[1]:
                        st.metric("Articles recommandés", n_recommendations)
                    with col_metrics[2]:
                        st.metric("Utilisateur", selected_user)

                else:
                    st.warning("Format de réponse inattendu")
                    st.json(recommendations_data)

if __name__ == "__main__":
    main()