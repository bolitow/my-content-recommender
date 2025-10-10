"""
Azure Function SIMPLE - Pour tester que Python fonctionne
Version de test sans chargement de modèle
"""

import logging
import json
import azure.functions as func

logger = logging.getLogger(__name__)

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test simple sans modèle"""

    logger.info("✅ La fonction Python démarre correctement!")

    try:
        req_body = req.get_json()
        user_id = req_body.get("user_id", 0)
        n_recommendations = req_body.get("n_recommendations", 5)

        logger.info(f"Requête pour user {user_id}, {n_recommendations} recommandations")

        # Générer des recommandations factices
        fake_recommendations = [1000 + i for i in range(n_recommendations)]

        response = {
            "user_id": user_id,
            "recommendations": fake_recommendations,
            "model": "FAKE_TEST",
            "status": "success",
            "message": "Ceci est un test - pas de vrai modèle chargé"
        }

        logger.info("✅ Recommandations factices générées avec succès")

        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        logger.error(traceback.format_exc())

        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc()
            }),
            status_code=500,
            mimetype="application/json"
        )
