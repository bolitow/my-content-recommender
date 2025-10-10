"""
Azure Function V2 pour le système de recommandation
Charge le modèle ALS depuis Azure Blob Storage au démarrage
"""

import logging
import json
import os
import pickle
import tempfile
from typing import Dict, Any, Optional

import azure.functions as func
from azure.storage.blob import BlobServiceClient

# Configuration
STORAGE_CONNECTION_STRING = os.environ.get("STORAGE_CONNECTION_STRING", "")
MODEL_CONTAINER_NAME = os.environ.get("MODEL_CONTAINER_NAME", "models")
MODEL_BLOB_NAME = os.environ.get("MODEL_BLOB_NAME", "als_model.pkl")

# Configuration du logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Variable globale pour le modèle (chargé une seule fois au démarrage)
_recommender_model = None
_model_loaded = False


def load_model_from_storage() -> Optional[Any]:
    """
    Charge le modèle ALS depuis Azure Blob Storage

    Returns:
        Objet ALSRecommender ou None si échec
    """
    global _recommender_model, _model_loaded

    if _model_loaded and _recommender_model is not None:
        logger.info("Modèle déjà chargé en mémoire")
        return _recommender_model

    logger.info("Chargement du modèle depuis Azure Blob Storage...")

    try:
        # Vérifier la connection string
        if not STORAGE_CONNECTION_STRING:
            logger.error("STORAGE_CONNECTION_STRING non configurée")
            return None

        # Créer le client Blob Service
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING
        )

        # Obtenir le blob client
        blob_client = blob_service_client.get_blob_client(
            container=MODEL_CONTAINER_NAME,
            blob=MODEL_BLOB_NAME
        )

        # Télécharger le blob dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
            logger.info(f"Téléchargement de {MODEL_CONTAINER_NAME}/{MODEL_BLOB_NAME}...")

            blob_data = blob_client.download_blob()
            blob_data.readinto(temp_file)
            temp_file_path = temp_file.name

        # Charger le modèle depuis le fichier temporaire
        logger.info(f"Chargement du modèle depuis {temp_file_path}...")

        with open(temp_file_path, 'rb') as f:
            model_data = pickle.load(f)

        # Nettoyer le fichier temporaire
        os.unlink(temp_file_path)

        # Reconstruire l'objet ALSRecommender
        # Le pickle contient un dictionnaire avec toutes les données nécessaires
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

        logger.info(f"✅ Modèle chargé avec succès!")
        logger.info(f"   - {len(recommender.user_to_idx)} utilisateurs")
        logger.info(f"   - {len(recommender.item_to_idx)} articles")

        _recommender_model = recommender
        _model_loaded = True

        return recommender

    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def generate_recommendations(user_id: int, n_recommendations: int) -> Dict[str, Any]:
    """
    Génère des recommandations pour un utilisateur

    Args:
        user_id: ID de l'utilisateur
        n_recommendations: Nombre de recommandations

    Returns:
        Dictionnaire avec les recommandations
    """
    # Charger le modèle si nécessaire
    recommender = load_model_from_storage()

    if recommender is None:
        return {
            "error": "Model unavailable",
            "message": "Le modèle de recommandation n'a pas pu être chargé"
        }

    try:
        # Générer les recommandations
        recommendations = recommender.recommend(
            user_id=user_id,
            n=n_recommendations,
            exclude_seen=True
        )

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "model": "ALS",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {e}")
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
        Réponse HTTP avec les recommandations ou erreur
    """
    logger.info("=== Nouvelle requête de recommandation ===")

    try:
        # Parser le body
        req_body = req.get_json()
    except ValueError:
        logger.error("Corps de requête invalide (JSON attendu)")
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
        logger.error("Paramètre user_id manquant")
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
        logger.error(f"Paramètres invalides: {e}")
        return func.HttpResponse(
            json.dumps({
                "error": "Invalid parameters",
                "message": str(e)
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Générer les recommandations
    logger.info(f"Génération de {n_recommendations} recommandations pour l'utilisateur {user_id}")

    result = generate_recommendations(user_id, n_recommendations)

    # Gérer les erreurs
    if "error" in result:
        logger.error(f"Erreur: {result['error']}")
        status_code = 503 if "unavailable" in result['error'].lower() else 500

        return func.HttpResponse(
            json.dumps(result),
            status_code=status_code,
            mimetype="application/json"
        )

    # Succès
    logger.info(f"✅ {len(result['recommendations'])} recommandations générées")

    return func.HttpResponse(
        json.dumps(result),
        status_code=200,
        mimetype="application/json"
    )


# Optionnel : Charger le modèle au démarrage (warm-up)
# Ceci réduit le cold start time
try:
    logger.info("🚀 Pré-chargement du modèle au démarrage...")
    load_model_from_storage()
except Exception as e:
    logger.warning(f"⚠️  Pré-chargement échoué (le modèle sera chargé à la première requête): {e}")
