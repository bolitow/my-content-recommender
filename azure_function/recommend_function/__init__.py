"""
Azure Function V3 pour le système de recommandation
Charge le modèle ALS, les métadonnées articles et les embeddings depuis Azure Blob Storage
"""

import logging
import json
import os
import sys
import pickle
import tempfile
from typing import Dict, Any, Optional, List
from io import BytesIO
from datetime import datetime

import azure.functions as func
from azure.storage.blob import BlobServiceClient
import pandas as pd
import numpy as np

# Ajouter le chemin parent au PYTHONPATH pour trouver recommender_als
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configuration
STORAGE_CONNECTION_STRING = os.environ.get("STORAGE_CONNECTION_STRING", "")
MODEL_CONTAINER_NAME = os.environ.get("MODEL_CONTAINER_NAME", "models")
MODEL_BLOB_NAME = os.environ.get("MODEL_BLOB_NAME", "als_model.pkl")
DATA_CONTAINER_NAME = os.environ.get("DATA_CONTAINER_NAME", "data")
ARTICLES_METADATA_BLOB = os.environ.get("ARTICLES_METADATA_BLOB", "articles_metadata.csv")
EMBEDDINGS_BLOB = os.environ.get("EMBEDDINGS_BLOB", "articles_embeddings_reduced.pickle")

# Configuration du logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Variables globales (chargées une seule fois au démarrage)
_recommender_model = None
_articles_metadata = None
_articles_embeddings = None
_data_loaded = False


def load_data_from_storage() -> bool:
    """
    Charge toutes les données nécessaires depuis Azure Blob Storage :
    - Modèle ALS
    - Métadonnées articles
    - Embeddings réduits (optionnel)

    Returns:
        True si succès, False sinon
    """
    global _recommender_model, _articles_metadata, _articles_embeddings, _data_loaded

    if _data_loaded:
        logger.info("Données déjà chargées en mémoire")
        return True

    logger.info("=" * 60)
    logger.info("🚀 CHARGEMENT DES DONNÉES AU DÉMARRAGE")
    logger.info("=" * 60)

    try:
        # Vérifier la connection string
        if not STORAGE_CONNECTION_STRING:
            logger.error("❌ STORAGE_CONNECTION_STRING non configurée")
            return False

        # Créer le client Blob Service
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING
        )

        # ===== 1. CHARGER LE MODÈLE ALS =====
        logger.info(f"\n📦 [1/3] Chargement du modèle ALS depuis {MODEL_CONTAINER_NAME}/{MODEL_BLOB_NAME}...")

        model_blob_client = blob_service_client.get_blob_client(
            container=MODEL_CONTAINER_NAME,
            blob=MODEL_BLOB_NAME
        )

        # Télécharger dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
            blob_data = model_blob_client.download_blob()
            blob_data.readinto(temp_file)
            temp_file_path = temp_file.name

        # Charger le modèle
        with open(temp_file_path, 'rb') as f:
            model_data = pickle.load(f)

        os.unlink(temp_file_path)

        # Reconstruire l'objet ALSRecommender
        from recommender_als import ALSRecommender

        recommender = ALSRecommender()
        recommender.model = model_data['model_state']
        recommender.user_item_matrix = model_data['user_item_matrix']
        recommender.item_user_matrix = model_data['item_user_matrix']
        recommender.user_to_idx = model_data['user_to_idx']
        recommender.idx_to_user = model_data['idx_to_user']
        recommender.item_to_idx = model_data['item_to_idx']
        recommender.idx_to_item = model_data['idx_to_item']
        recommender.user_items = model_data['user_items']
        recommender.item_popularity = model_data['item_popularity']
        recommender.all_items = model_data['all_items']
        recommender.is_trained = True

        _recommender_model = recommender
        logger.info(f"   ✅ Modèle ALS chargé : {len(recommender.user_to_idx)} utilisateurs, {len(recommender.item_to_idx)} articles")

        # ===== 2. CHARGER LES MÉTADONNÉES ARTICLES =====
        logger.info(f"\n📊 [2/3] Chargement des métadonnées depuis {DATA_CONTAINER_NAME}/{ARTICLES_METADATA_BLOB}...")

        metadata_blob_client = blob_service_client.get_blob_client(
            container=DATA_CONTAINER_NAME,
            blob=ARTICLES_METADATA_BLOB
        )

        # Télécharger le CSV en mémoire
        metadata_stream = BytesIO()
        metadata_blob_client.download_blob().readinto(metadata_stream)
        metadata_stream.seek(0)

        # Charger dans un DataFrame pandas
        articles_df = pd.read_csv(metadata_stream)
        _articles_metadata = articles_df

        logger.info(f"   ✅ Métadonnées chargées : {len(articles_df)} articles avec {len(articles_df.columns)} attributs")

        # ===== 3. CHARGER LES EMBEDDINGS (OPTIONNEL) =====
        try:
            logger.info(f"\n🧠 [3/3] Chargement des embeddings depuis {DATA_CONTAINER_NAME}/{EMBEDDINGS_BLOB}...")

            embeddings_blob_client = blob_service_client.get_blob_client(
                container=DATA_CONTAINER_NAME,
                blob=EMBEDDINGS_BLOB
            )

            # Télécharger dans un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
                embeddings_data = embeddings_blob_client.download_blob()
                embeddings_data.readinto(temp_file)
                temp_embeddings_path = temp_file.name

            # Charger les embeddings
            with open(temp_embeddings_path, 'rb') as f:
                embeddings_dict = pickle.load(f)

            os.unlink(temp_embeddings_path)

            _articles_embeddings = embeddings_dict
            logger.info(f"   ✅ Embeddings chargés : {len(embeddings_dict)} articles")

        except Exception as e:
            logger.warning(f"   ⚠️  Embeddings non disponibles (optionnel): {e}")
            _articles_embeddings = None

        # Tout est chargé
        _data_loaded = True

        logger.info("\n" + "=" * 60)
        logger.info("✅ TOUTES LES DONNÉES CHARGÉES AVEC SUCCÈS")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ ERREUR LORS DU CHARGEMENT DES DONNÉES: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def enrich_recommendations(recommendations: List[int]) -> List[Dict[str, Any]]:
    """
    Enrichit les recommandations avec les métadonnées des articles

    Args:
        recommendations: Liste des IDs d'articles recommandés

    Returns:
        Liste de dictionnaires avec détails enrichis
    """
    if _articles_metadata is None:
        # Pas de métadonnées disponibles, retourner juste les IDs
        return [{"article_id": int(article_id)} for article_id in recommendations]

    enriched = []

    for article_id in recommendations:
        # Chercher l'article dans les métadonnées
        article_row = _articles_metadata[_articles_metadata['article_id'] == article_id]

        if article_row.empty:
            # Article non trouvé dans les métadonnées
            enriched.append({
                "article_id": int(article_id),
                "metadata_available": False
            })
        else:
            # Extraire les informations
            article = article_row.iloc[0]

            # Convertir le timestamp en date lisible
            try:
                created_at = datetime.fromtimestamp(article['created_at_ts'] / 1000)
                created_at_str = created_at.strftime('%Y-%m-%d')
            except:
                created_at_str = None

            enriched.append({
                "article_id": int(article_id),
                "category_id": int(article['category_id']),
                "words_count": int(article['words_count']),
                "created_at": created_at_str,
                "publisher_id": int(article['publisher_id']),
                "metadata_available": True
            })

    return enriched


def calculate_diversity(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcule des métriques de diversité sur les recommandations

    Args:
        recommendations: Liste des recommandations enrichies

    Returns:
        Dictionnaire avec métriques de diversité
    """
    if not recommendations or not any(r.get('metadata_available') for r in recommendations):
        return {
            "category_diversity": 0,
            "unique_categories": 0,
            "total_recommendations": len(recommendations)
        }

    # Extraire les catégories
    categories = [r['category_id'] for r in recommendations if r.get('metadata_available')]

    if not categories:
        return {
            "category_diversity": 0,
            "unique_categories": 0,
            "total_recommendations": len(recommendations)
        }

    unique_categories = len(set(categories))
    total_recommendations = len(categories)

    # Diversité = ratio de catégories uniques
    diversity_score = unique_categories / total_recommendations if total_recommendations > 0 else 0

    return {
        "category_diversity": round(diversity_score, 3),
        "unique_categories": unique_categories,
        "total_recommendations": total_recommendations,
        "categories_distribution": dict(pd.Series(categories).value_counts())
    }


def generate_recommendations(user_id: int, n_recommendations: int) -> Dict[str, Any]:
    """
    Génère des recommandations enrichies pour un utilisateur

    Args:
        user_id: ID de l'utilisateur
        n_recommendations: Nombre de recommandations

    Returns:
        Dictionnaire avec les recommandations enrichies
    """
    # Charger les données si nécessaire
    if not _data_loaded:
        success = load_data_from_storage()
        if not success:
            return {
                "error": "Data unavailable",
                "message": "Les données de recommandation n'ont pas pu être chargées"
            }

    if _recommender_model is None:
        return {
            "error": "Model unavailable",
            "message": "Le modèle de recommandation n'est pas disponible"
        }

    try:
        # Générer les recommandations via le modèle ALS
        recommendations_ids = _recommender_model.recommend(
            user_id=user_id,
            n=n_recommendations,
            exclude_seen=True
        )

        # Enrichir avec les métadonnées
        enriched_recommendations = enrich_recommendations(recommendations_ids)

        # Calculer la diversité
        diversity_metrics = calculate_diversity(enriched_recommendations)

        # Construire la réponse
        response = {
            "user_id": user_id,
            "recommendations": enriched_recommendations,
            "count": len(enriched_recommendations),
            "model": "ALS",
            "diversity": diversity_metrics,
            "metadata_loaded": _articles_metadata is not None,
            "embeddings_loaded": _articles_embeddings is not None,
            "status": "success"
        }

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "error": "Recommendation error",
            "message": str(e)
        }


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Point d'entrée de l'Azure Function

    Args:
        req: Requête HTTP entrante

    Returns:
        Réponse HTTP avec les recommandations enrichies ou erreur
    """
    logger.info("=" * 60)
    logger.info("📥 NOUVELLE REQUÊTE DE RECOMMANDATION")
    logger.info("=" * 60)

    try:
        # Parser le body
        req_body = req.get_json()
    except ValueError:
        logger.error("❌ Corps de requête invalide (JSON attendu)")
        return func.HttpResponse(
            json.dumps({
                "error": "Invalid request body",
                "message": "Le corps de la requête doit être un JSON valide"
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Extraire les paramètres
    user_id = req_body.get("user_id")
    n_recommendations = req_body.get("n_recommendations", 5)

    # Validation
    if not user_id:
        logger.error("❌ Paramètre user_id manquant")
        return func.HttpResponse(
            json.dumps({
                "error": "Missing parameter",
                "message": "Le paramètre 'user_id' est requis"
            }),
            status_code=400,
            mimetype="application/json"
        )

    try:
        user_id = int(user_id)
        n_recommendations = int(n_recommendations)

        if user_id <= 0:
            raise ValueError("user_id doit être positif")

        if n_recommendations <= 0 or n_recommendations > 50:
            raise ValueError("n_recommendations doit être entre 1 et 50")

    except (TypeError, ValueError) as e:
        logger.error(f"❌ Paramètres invalides: {e}")
        return func.HttpResponse(
            json.dumps({
                "error": "Invalid parameters",
                "message": str(e)
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Générer les recommandations
    logger.info(f"👤 Utilisateur: {user_id}")
    logger.info(f"🔢 Nombre demandé: {n_recommendations}")

    result = generate_recommendations(user_id, n_recommendations)

    # Gérer les erreurs
    if "error" in result:
        logger.error(f"❌ Erreur: {result['error']}")
        status_code = 503 if "unavailable" in result['error'].lower() else 500

        return func.HttpResponse(
            json.dumps(result),
            status_code=status_code,
            mimetype="application/json"
        )

    # Succès
    logger.info(f"✅ {len(result['recommendations'])} recommandations générées")
    logger.info(f"📊 Diversité: {result['diversity']['category_diversity']}")
    logger.info("=" * 60)

    return func.HttpResponse(
        json.dumps(result),
        status_code=200,
        mimetype="application/json"
    )


# Pré-chargement au démarrage (warm-up)
# Ceci réduit le cold start time pour les requêtes suivantes
try:
    logger.info("🚀 PRÉ-CHARGEMENT DES DONNÉES AU DÉMARRAGE DE LA FUNCTION...")
    load_data_from_storage()
except Exception as e:
    logger.warning(f"⚠️  Pré-chargement échoué (les données seront chargées à la première requête): {e}")
