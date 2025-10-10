"""
Azure Function pour le système de recommandation
Fait le pont entre l'application Streamlit et l'API de recommandation
"""

import logging
import json
import os
import requests
from typing import Dict, Any

import azure.functions as func

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "10"))

# Configuration du logging
logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Point d'entrée principal de l'Azure Function

    Cette fonction:
    1. Reçoit la requête de l'application Streamlit
    2. Valide les paramètres
    3. Appelle l'API de recommandation
    4. Retourne les résultats

    Args:
        req: Requête HTTP entrante

    Returns:
        Réponse HTTP avec les recommandations ou erreur
    """
    logger.info("Nouvelle requête de recommandation reçue")

    try:
        # Parser le body de la requête
        req_body = req.get_json()
    except ValueError:
        logger.error("Corps de requête invalide")
        return func.HttpResponse(
            json.dumps({
                "error": "Corps de requête invalide",
                "message": "Le corps de la requête doit être un JSON valide"
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Valider les paramètres requis
    user_id = req_body.get("user_id")
    n_recommendations = req_body.get("n_recommendations", 5)

    if not user_id:
        logger.error("user_id manquant dans la requête")
        return func.HttpResponse(
            json.dumps({
                "error": "Paramètre manquant",
                "message": "Le paramètre 'user_id' est requis"
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Valider les types et valeurs
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
                "error": "Paramètres invalides",
                "message": str(e)
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Appeler l'API de recommandation
    try:
        logger.info(f"Appel API pour user_id={user_id}, n={n_recommendations}")

        response = call_recommendation_api(user_id, n_recommendations)

        # Retourner la réponse
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    except requests.exceptions.Timeout:
        logger.error("Timeout lors de l'appel API")
        return func.HttpResponse(
            json.dumps({
                "error": "Timeout",
                "message": "L'API de recommandation n'a pas répondu à temps"
            }),
            status_code=504,
            mimetype="application/json"
        )

    except requests.exceptions.ConnectionError:
        logger.error("Impossible de se connecter à l'API")
        return func.HttpResponse(
            json.dumps({
                "error": "Erreur de connexion",
                "message": "Impossible de se connecter à l'API de recommandation"
            }),
            status_code=503,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return func.HttpResponse(
            json.dumps({
                "error": "Erreur interne",
                "message": "Une erreur inattendue s'est produite"
            }),
            status_code=500,
            mimetype="application/json"
        )


def call_recommendation_api(user_id: int, n_recommendations: int) -> Dict[str, Any]:
    """
    Appelle l'API de recommandation

    Args:
        user_id: ID de l'utilisateur
        n_recommendations: Nombre de recommandations

    Returns:
        Dictionnaire avec les recommandations

    Raises:
        requests.exceptions.RequestException: En cas d'erreur HTTP
    """
    # Construire l'URL de l'endpoint
    endpoint = f"{API_BASE_URL}/recommend"

    # Préparer la requête
    payload = {
        "user_id": user_id,
        "n_recommendations": n_recommendations,
        "exclude_seen": True
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Appeler l'API
    logger.info(f"Appel API: POST {endpoint}")
    response = requests.post(
        endpoint,
        json=payload,
        headers=headers,
        timeout=API_TIMEOUT
    )

    # Vérifier le statut
    if response.status_code == 200:
        logger.info("Recommandations obtenues avec succès")
        return response.json()

    elif response.status_code == 503:
        logger.warning("API non disponible")
        raise requests.exceptions.ConnectionError("Service de recommandation non disponible")

    else:
        logger.error(f"Erreur API: {response.status_code} - {response.text}")
        response.raise_for_status()


def validate_environment():
    """
    Valide que les variables d'environnement nécessaires sont configurées

    Returns:
        Tuple (is_valid, error_message)
    """
    if not API_BASE_URL:
        return False, "API_BASE_URL non configurée"

    # Vérifier que l'URL est valide
    if not API_BASE_URL.startswith(("http://", "https://")):
        return False, "API_BASE_URL doit commencer par http:// ou https://"

    return True, None


# Point d'entrée alternatif pour tests locaux
if __name__ == "__main__":
    # Test local de la fonction
    import json

    # Simuler une requête
    class MockRequest:
        def get_json(self):
            return {
                "user_id": 123,
                "n_recommendations": 5
            }

    # Tester la validation
    is_valid, error = validate_environment()
    if not is_valid:
        print(f"Erreur de configuration: {error}")
    else:
        print("Configuration valide")

    # Tester la fonction
    mock_req = MockRequest()
    result = main(mock_req)
    print(f"Résultat: {result.get_body().decode('utf-8')}")