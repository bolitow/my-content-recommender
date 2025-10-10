"""
API FastAPI pour exposer le système de recommandation ALS
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
import os
from datetime import datetime
from recommender_als import ALSRecommender

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation de l'API FastAPI
app = FastAPI(
    title="API Système de Recommandation",
    description="API pour le système de recommandation d'articles basé sur ALS",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable globale pour le modèle
recommender = None

# Chemin du modèle
MODEL_PATH = os.getenv("MODEL_PATH", "models/als_model.pkl")


# Modèles Pydantic pour les requêtes et réponses
class RecommendationRequest(BaseModel):
    """Requête pour obtenir des recommandations"""
    user_id: int = Field(..., description="ID de l'utilisateur", ge=1)
    n_recommendations: int = Field(5, description="Nombre de recommandations", ge=1, le=50)
    exclude_seen: bool = Field(True, description="Exclure les articles déjà vus")


class RecommendationResponse(BaseModel):
    """Réponse avec les recommandations"""
    user_id: int
    recommendations: List[int]
    model: str = "ALS"
    timestamp: str
    status: str


class UserInfoResponse(BaseModel):
    """Informations sur un utilisateur"""
    user_id: int
    is_known: bool
    items_seen: int
    total_users: int
    total_items: int


class HealthResponse(BaseModel):
    """État de santé de l'API"""
    status: str
    model_loaded: bool
    timestamp: str


class ModelInfoResponse(BaseModel):
    """Informations sur le modèle"""
    model_type: str
    is_trained: bool
    n_users: int
    n_items: int
    parameters: Dict


@app.on_event("startup")
async def load_model():
    """Charge le modèle au démarrage de l'API"""
    global recommender

    try:
        logger.info(f"Chargement du modèle depuis {MODEL_PATH}")
        recommender = ALSRecommender()

        if os.path.exists(MODEL_PATH):
            recommender.load_model(MODEL_PATH)
            logger.info("Modèle chargé avec succès")
        else:
            logger.warning(f"Modèle non trouvé à {MODEL_PATH}")
            # En développement, créer un modèle de test
            if os.getenv("ENVIRONMENT", "development") == "development":
                logger.info("Mode développement: création d'un modèle de test")
                _create_test_model()

    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle: {e}")
        recommender = None


def _create_test_model():
    """Crée un modèle de test pour le développement"""
    global recommender

    try:
        import pandas as pd
        import glob

        # Charger quelques données
        click_files = sorted(glob.glob('data/clicks/clicks_hour_*.csv'))[:5]

        if click_files:
            clicks_df = pd.concat([pd.read_csv(f) for f in click_files], ignore_index=True)

            # Préparer les données
            from recommender_als import prepare_training_data
            train_data = prepare_training_data(clicks_df)

            # Entraîner un modèle simple
            recommender = ALSRecommender(factors=50, iterations=5)
            recommender.fit(train_data)

            # Créer le dossier models si nécessaire
            os.makedirs("models", exist_ok=True)

            # Sauvegarder
            recommender.save_model(MODEL_PATH)
            logger.info("Modèle de test créé et sauvegardé")
        else:
            logger.error("Aucune donnée de clics trouvée")

    except Exception as e:
        logger.error(f"Impossible de créer le modèle de test: {e}")


@app.get("/", tags=["General"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API Système de Recommandation",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Vérification de l'état de l'API"""
    return HealthResponse(
        status="healthy" if recommender and recommender.is_trained else "degraded",
        model_loaded=recommender is not None and recommender.is_trained,
        timestamp=datetime.now().isoformat()
    )


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
async def get_model_info():
    """Retourne les informations sur le modèle"""
    if not recommender:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle non chargé"
        )

    return ModelInfoResponse(
        model_type="ALS (Alternating Least Squares)",
        is_trained=recommender.is_trained,
        n_users=len(recommender.user_to_idx) if recommender.is_trained else 0,
        n_items=len(recommender.item_to_idx) if recommender.is_trained else 0,
        parameters={
            "factors": recommender.model.factors if recommender.model else 0,
            "iterations": recommender.model.iterations if recommender.model else 0,
            "regularization": recommender.model.regularization if recommender.model else 0,
            "alpha": recommender.model.alpha if recommender.model else 0
        }
    )


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendationRequest):
    """
    Génère des recommandations pour un utilisateur

    - **user_id**: ID de l'utilisateur
    - **n_recommendations**: Nombre d'articles à recommander (défaut: 5)
    - **exclude_seen**: Exclure les articles déjà vus (défaut: true)
    """
    if not recommender or not recommender.is_trained:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle non disponible"
        )

    try:
        # Générer les recommandations
        recommendations = recommender.recommend(
            user_id=request.user_id,
            n=request.n_recommendations,
            exclude_seen=request.exclude_seen
        )

        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            model="ALS",
            timestamp=datetime.now().isoformat(),
            status="success"
        )

    except Exception as e:
        logger.error(f"Erreur lors de la recommandation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des recommandations: {str(e)}"
        )


@app.get("/user/{user_id}", response_model=UserInfoResponse, tags=["Users"])
async def get_user_info(user_id: int):
    """Retourne les informations sur un utilisateur"""
    if not recommender or not recommender.is_trained:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle non disponible"
        )

    try:
        user_info = recommender.get_user_info(user_id)
        return UserInfoResponse(**user_info)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos utilisateur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )


@app.get("/users", tags=["Users"])
async def list_users(limit: int = 100, offset: int = 0):
    """Liste les utilisateurs connus du système"""
    if not recommender or not recommender.is_trained:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle non disponible"
        )

    try:
        all_users = sorted(recommender.user_to_idx.keys())
        total = len(all_users)
        users = all_users[offset:offset + limit]

        return {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste des utilisateurs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )


@app.get("/articles/popular", tags=["Articles"])
async def get_popular_articles(limit: int = 10):
    """Retourne les articles les plus populaires"""
    if not recommender or not recommender.is_trained:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modèle non disponible"
        )

    try:
        popular = sorted(
            recommender.item_popularity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return {
            "articles": [{"article_id": item[0], "popularity": item[1]} for item in popular],
            "total": len(popular)
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des articles populaires: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Lancer l'API en mode développement
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )