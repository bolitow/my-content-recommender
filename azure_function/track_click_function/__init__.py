"""
Azure Function pour le tracking des interactions utilisateur
Capture les clics et les stocke dans Azure Blob Storage pour analyse future
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any
import azure.functions as func
from azure.storage.blob import BlobServiceClient

# Configuration
STORAGE_CONNECTION_STRING = os.environ.get("STORAGE_CONNECTION_STRING", "")
CLICKS_CONTAINER_NAME = os.environ.get("CLICKS_CONTAINER_NAME", "clicks")

# Configuration du logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def validate_click_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Valide les données de clic

    Args:
        data: Dictionnaire des données de clic

    Returns:
        Tuple (is_valid, error_message)
    """
    required_fields = ["user_id", "article_id"]

    for field in required_fields:
        if field not in data:
            return False, f"Champ obligatoire manquant: {field}"

        # Vérifier que ce sont des entiers
        try:
            int(data[field])
        except (ValueError, TypeError):
            return False, f"Le champ {field} doit être un entier"

    return True, ""


def store_click(click_data: Dict[str, Any]) -> bool:
    """
    Stocke un clic dans Azure Blob Storage

    Args:
        click_data: Données du clic à stocker

    Returns:
        True si succès, False sinon
    """
    try:
        if not STORAGE_CONNECTION_STRING:
            logger.error("STORAGE_CONNECTION_STRING non configurée")
            return False

        # Créer le client Blob Service
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING
        )

        # Nom du fichier basé sur la date du jour
        today = datetime.utcnow().strftime("%Y-%m-%d")
        blob_name = f"clicks_new_{today}.jsonl"

        # Obtenir le blob client
        blob_client = blob_service_client.get_blob_client(
            container=CLICKS_CONTAINER_NAME,
            blob=blob_name
        )

        # Préparer la ligne JSON (JSON Lines format)
        click_line = json.dumps(click_data) + "\n"

        # Si le blob existe, on append, sinon on crée
        try:
            # Télécharger le contenu existant
            existing_data = blob_client.download_blob().readall()
            new_data = existing_data + click_line.encode('utf-8')
        except Exception:
            # Le blob n'existe pas encore
            new_data = click_line.encode('utf-8')

        # Upload le contenu mis à jour
        blob_client.upload_blob(new_data, overwrite=True)

        logger.info(f"Clic stocké avec succès: user={click_data['user_id']}, article={click_data['article_id']}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors du stockage du clic: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Point d'entrée de l'Azure Function

    Endpoint: POST /api/track_click
    Body: {
        "user_id": 123,
        "article_id": 456,
        "interaction_type": "click",  # optionnel
        "timestamp": 1234567890,      # optionnel (généré si absent)
        "metadata": {...}              # optionnel
    }
    """
    logger.info("Requête de tracking reçue")

    try:
        # Vérifier la méthode HTTP
        if req.method != "POST":
            return func.HttpResponse(
                json.dumps({
                    "error": "Method not allowed",
                    "message": "Utilisez POST pour envoyer des clics"
                }),
                status_code=405,
                mimetype="application/json"
            )

        # Parser le body JSON
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({
                    "error": "Invalid JSON",
                    "message": "Le body doit être un JSON valide"
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Valider les données
        is_valid, error_message = validate_click_data(req_body)
        if not is_valid:
            return func.HttpResponse(
                json.dumps({
                    "error": "Validation error",
                    "message": error_message
                }),
                status_code=400,
                mimetype="application/json"
            )

        # Enrichir les données avec timestamp si absent
        click_data = {
            "user_id": int(req_body["user_id"]),
            "article_id": int(req_body["article_id"]),
            "interaction_type": req_body.get("interaction_type", "click"),
            "timestamp": req_body.get("timestamp", int(datetime.utcnow().timestamp() * 1000)),
            "metadata": req_body.get("metadata", {}),
            "tracked_at": datetime.utcnow().isoformat()
        }

        # Stocker le clic
        success = store_click(click_data)

        if success:
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "Clic enregistré avec succès",
                    "data": {
                        "user_id": click_data["user_id"],
                        "article_id": click_data["article_id"],
                        "tracked_at": click_data["tracked_at"]
                    }
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "error": "Storage error",
                    "message": "Impossible de stocker le clic"
                }),
                status_code=500,
                mimetype="application/json"
            )

    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        import traceback
        logger.error(traceback.format_exc())

        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
