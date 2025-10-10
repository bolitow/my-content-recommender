"""
Azure Function V2 pour le système de recommandation
VERSION AVEC LOGS DÉTAILLÉS POUR DEBUGGING
"""

import logging
import json
import os
import sys
import pickle
import tempfile
from typing import Dict, Any, Optional

import azure.functions as func
from azure.storage.blob import BlobServiceClient

# Configuration du logging TRÈS verbeux
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Log de démarrage
logger.info("=" * 80)
logger.info("🚀 DÉMARRAGE DE LA FONCTION AZURE")
logger.info("=" * 80)

# Ajouter le chemin parent au PYTHONPATH pour trouver recommender_als
try:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger.info(f"📂 Répertoire parent: {parent_dir}")

    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        logger.info(f"✅ Ajout de {parent_dir} au sys.path")
    else:
        logger.info(f"ℹ️  {parent_dir} déjà dans sys.path")

    logger.info(f"📋 sys.path complet: {sys.path[:5]}...")  # Premiers 5 éléments
except Exception as e:
    logger.error(f"❌ ERREUR lors de la config sys.path: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Configuration
STORAGE_CONNECTION_STRING = os.environ.get("STORAGE_CONNECTION_STRING", "")
MODEL_CONTAINER_NAME = os.environ.get("MODEL_CONTAINER_NAME", "models")
MODEL_BLOB_NAME = os.environ.get("MODEL_BLOB_NAME", "als_model.pkl")

logger.info("🔧 Configuration:")
logger.info(f"   - STORAGE_CONNECTION_STRING configurée: {bool(STORAGE_CONNECTION_STRING)}")
logger.info(f"   - MODEL_CONTAINER_NAME: {MODEL_CONTAINER_NAME}")
logger.info(f"   - MODEL_BLOB_NAME: {MODEL_BLOB_NAME}")

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

    logger.info("=" * 80)
    logger.info("📥 DÉBUT load_model_from_storage()")
    logger.info("=" * 80)

    if _model_loaded and _recommender_model is not None:
        logger.info("✅ Modèle déjà chargé en mémoire - réutilisation")
        return _recommender_model

    logger.info("🔄 Chargement du modèle depuis Azure Blob Storage...")

    try:
        # Étape 1 : Vérifier la connection string
        logger.info("📍 Étape 1/6 : Vérification STORAGE_CONNECTION_STRING")
        if not STORAGE_CONNECTION_STRING:
            logger.error("❌ STORAGE_CONNECTION_STRING non configurée!")
            return None
        logger.info(f"✅ STORAGE_CONNECTION_STRING présente (longueur: {len(STORAGE_CONNECTION_STRING)} chars)")

        # Étape 2 : Créer le client Blob Service
        logger.info("📍 Étape 2/6 : Création du BlobServiceClient")
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING
        )
        logger.info("✅ BlobServiceClient créé")

        # Étape 3 : Obtenir le blob client
        logger.info(f"📍 Étape 3/6 : Obtention du blob client pour {MODEL_CONTAINER_NAME}/{MODEL_BLOB_NAME}")
        blob_client = blob_service_client.get_blob_client(
            container=MODEL_CONTAINER_NAME,
            blob=MODEL_BLOB_NAME
        )
        logger.info("✅ Blob client obtenu")

        # Étape 4 : Télécharger le blob
        logger.info("📍 Étape 4/6 : Téléchargement du blob dans fichier temporaire")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as temp_file:
            logger.info(f"📂 Fichier temporaire: {temp_file.name}")
            logger.info(f"⏬ Téléchargement de {MODEL_CONTAINER_NAME}/{MODEL_BLOB_NAME}...")

            blob_data = blob_client.download_blob()
            blob_data.readinto(temp_file)
            temp_file_path = temp_file.name

        logger.info(f"✅ Blob téléchargé vers {temp_file_path}")

        # Étape 5 : Charger le pickle
        logger.info("📍 Étape 5/6 : Chargement du modèle depuis le fichier pickle")
        with open(temp_file_path, 'rb') as f:
            logger.info("🔓 Ouverture du fichier pickle...")
            model_data = pickle.load(f)
            logger.info(f"✅ Pickle chargé - Clés: {list(model_data.keys())}")

        # Nettoyer le fichier temporaire
        os.unlink(temp_file_path)
        logger.info("🗑️  Fichier temporaire supprimé")

        # Étape 6 : Reconstruire l'objet ALSRecommender
        logger.info("📍 Étape 6/6 : Reconstruction de l'objet ALSRecommender")
        logger.info("📦 Import de recommender_als...")

        try:
            from recommender_als import ALSRecommender
            logger.info("✅ Import recommender_als réussi!")
        except ImportError as ie:
            logger.error(f"❌ ERREUR D'IMPORT recommender_als: {ie}")
            logger.error(f"📂 Contenu du répertoire parent: {os.listdir(parent_dir)}")
            logger.error(f"📋 sys.path: {sys.path}")
            raise

        logger.info("🏗️  Création de l'objet ALSRecommender...")
        recommender = ALSRecommender()

        logger.info("📋 Assignation des attributs du modèle...")
        recommender.model = model_data['model_state']
        logger.info("   ✅ model_state assigné")

        recommender.user_item_matrix = model_data['user_item_matrix']
        logger.info("   ✅ user_item_matrix assigné")

        recommender.item_user_matrix = model_data['item_user_matrix']
        logger.info("   ✅ item_user_matrix assigné")

        recommender.user_to_idx = model_data['user_to_idx']
        logger.info("   ✅ user_to_idx assigné")

        recommender.idx_to_user = model_data['idx_to_user']
        logger.info("   ✅ idx_to_user assigné")

        recommender.item_to_idx = model_data['item_to_idx']
        logger.info("   ✅ item_to_idx assigné")

        recommender.idx_to_item = model_data['idx_to_item']
        logger.info("   ✅ idx_to_item assigné")

        recommender.user_items = model_data['user_items']
        logger.info("   ✅ user_items assigné")

        recommender.item_popularity = model_data['item_popularity']
        logger.info("   ✅ item_popularity assigné")

        recommender.all_items = model_data['all_items']
        logger.info("   ✅ all_items assigné")

        recommender.is_trained = True
        logger.info("   ✅ is_trained = True")

        logger.info("")
        logger.info("🎉 MODÈLE CHARGÉ AVEC SUCCÈS!")
        logger.info(f"   👥 {len(recommender.user_to_idx)} utilisateurs")
        logger.info(f"   📰 {len(recommender.item_to_idx)} articles")

        _recommender_model = recommender
        _model_loaded = True

        return recommender

    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ ERREUR LORS DU CHARGEMENT DU MODÈLE")
        logger.error("=" * 80)
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Message: {e}")
        logger.error("")
        logger.error("📋 Stack trace complète:")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
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
    logger.info("=" * 80)
    logger.info(f"🎯 GÉNÉRATION DE RECOMMANDATIONS - User {user_id}")
    logger.info("=" * 80)

    # Charger le modèle si nécessaire
    logger.info("📥 Appel de load_model_from_storage()...")
    recommender = load_model_from_storage()

    if recommender is None:
        logger.error("❌ Le modèle n'a pas pu être chargé!")
        return {
            "error": "Model unavailable",
            "message": "Le modèle de recommandation n'a pas pu être chargé"
        }

    logger.info("✅ Modèle disponible")

    try:
        logger.info(f"🔮 Appel de recommender.recommend(user_id={user_id}, n={n_recommendations}, exclude_seen=True)")

        # Générer les recommandations
        recommendations = recommender.recommend(
            user_id=user_id,
            n=n_recommendations,
            exclude_seen=True
        )

        logger.info(f"✅ {len(recommendations)} recommandations générées: {recommendations}")

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "model": "ALS",
            "status": "success"
        }

    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ ERREUR LORS DE LA GÉNÉRATION DES RECOMMANDATIONS")
        logger.error("=" * 80)
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error("=" * 80)

        return {
            "error": "Recommendation error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Point d'entrée de l'Azure Function

    Args:
        req: Requête HTTP entrante

    Returns:
        Réponse HTTP avec les recommandations ou erreur
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🌐 NOUVELLE REQUÊTE HTTP")
    logger.info("=" * 80)

    try:
        # Parser le body
        logger.info("📨 Parsing du corps de la requête...")
        req_body = req.get_json()
        logger.info(f"✅ Corps parsé: {req_body}")

    except ValueError as ve:
        logger.error(f"❌ Corps de requête invalide: {ve}")
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

    logger.info(f"📋 Paramètres reçus:")
    logger.info(f"   - user_id: {user_id} (type: {type(user_id).__name__})")
    logger.info(f"   - n_recommendations: {n_recommendations} (type: {type(n_recommendations).__name__})")

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
        logger.info("🔢 Conversion des paramètres en entiers...")
        user_id = int(user_id)
        n_recommendations = int(n_recommendations)

        logger.info(f"✅ Paramètres convertis: user_id={user_id}, n={n_recommendations}")

        if user_id <= 0:
            raise ValueError("user_id doit être positif")

        if n_recommendations <= 0 or n_recommendations > 50:
            raise ValueError("n_recommendations doit être entre 1 et 50")

        logger.info("✅ Validation des paramètres OK")

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
    logger.info(f"🚀 Lancement de la génération pour user {user_id}...")

    result = generate_recommendations(user_id, n_recommendations)

    # Gérer les erreurs
    if "error" in result:
        logger.error(f"❌ Erreur retournée: {result['error']}")
        status_code = 503 if "unavailable" in result['error'].lower() else 500

        return func.HttpResponse(
            json.dumps(result),
            status_code=status_code,
            mimetype="application/json"
        )

    # Succès
    logger.info("=" * 80)
    logger.info(f"🎉 SUCCÈS - {len(result['recommendations'])} recommandations générées")
    logger.info("=" * 80)

    return func.HttpResponse(
        json.dumps(result),
        status_code=200,
        mimetype="application/json"
    )


# Optionnel : Charger le modèle au démarrage (warm-up)
# DÉSACTIVÉ pour éviter les erreurs au démarrage si les variables ne sont pas configurées
# try:
#     logger.info("🚀 Pré-chargement du modèle au démarrage...")
#     load_model_from_storage()
# except Exception as e:
#     logger.warning(f"⚠️  Pré-chargement échoué (le modèle sera chargé à la première requête): {e}")

logger.info("✅ Module __init__.py chargé et prêt")
