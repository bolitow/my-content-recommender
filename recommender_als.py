"""
Module de recommandation ALS
Gestion du modèle de filtrage collaboratif ALS
"""

import numpy as np
import pandas as pd
import pickle
from scipy.sparse import lil_matrix, csr_matrix
from implicit.als import AlternatingLeastSquares
from typing import List, Dict, Optional, Set
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ALSRecommender:
    """
    Système de recommandation basé sur l'algorithme ALS
    (Alternating Least Squares) pour le filtrage collaboratif
    """

    def __init__(
        self,
        factors: int = 100,
        regularization: float = 0.01,
        iterations: int = 20,
        alpha: float = 40
    ):
        """
        Initialise le modèle ALS

        Args:
            factors: Nombre de facteurs latents
            regularization: Paramètre de régularisation
            iterations: Nombre d'itérations
            alpha: Paramètre de confiance pour les données implicites
        """
        self.model = AlternatingLeastSquares(
            factors=factors,
            regularization=regularization,
            iterations=iterations,
            alpha=alpha,
            random_state=42,
            use_gpu=False
        )
        self.is_trained = False
        self.user_item_matrix = None
        self.item_user_matrix = None
        self.user_to_idx = {}
        self.idx_to_user = {}
        self.item_to_idx = {}
        self.idx_to_item = {}
        self.user_items = {}
        self.item_popularity = {}
        self.all_items = set()

        logger.info(
            f"Modèle ALS initialisé: "
            f"factors={factors}, reg={regularization}, "
            f"iterations={iterations}, alpha={alpha}"
        )

    def fit(self, train_df: pd.DataFrame):
        """
        Entraîne le modèle ALS sur les données d'entraînement

        Args:
            train_df: DataFrame avec colonnes [user_id, article_id, click_count]
        """
        logger.info("Début de l'entraînement du modèle ALS")

        # Créer les mappings utilisateur/article vers indices
        unique_users = sorted(train_df['user_id'].unique())
        unique_items = sorted(train_df['article_id'].unique())

        self.user_to_idx = {user: idx for idx, user in enumerate(unique_users)}
        self.idx_to_user = {idx: user for user, idx in self.user_to_idx.items()}
        self.item_to_idx = {item: idx for idx, item in enumerate(unique_items)}
        self.idx_to_item = {idx: item for item, idx in self.item_to_idx.items()}

        # Ajouter les indices au DataFrame
        train_df = train_df.copy()
        train_df['user_idx'] = train_df['user_id'].map(self.user_to_idx).astype(int)
        train_df['item_idx'] = train_df['article_id'].map(self.item_to_idx).astype(int)

        # Créer la matrice sparse user-item
        n_users = len(unique_users)
        n_items = len(unique_items)

        logger.info(f"Création de la matrice {n_users}x{n_items}")

        self.user_item_matrix = lil_matrix((n_users, n_items))

        for _, row in train_df.iterrows():
            user_idx = int(row['user_idx'])
            item_idx = int(row['item_idx'])
            self.user_item_matrix[user_idx, item_idx] = row['click_count']

        # Convertir en CSR pour efficacité
        self.user_item_matrix = self.user_item_matrix.tocsr()
        self.item_user_matrix = self.user_item_matrix.T.tocsr()

        # Entraîner le modèle
        logger.info("Entraînement du modèle en cours...")
        self.model.fit(self.item_user_matrix)
        self.is_trained = True

        # Stocker les informations supplémentaires
        self.user_items = train_df.groupby('user_id')['article_id'].apply(set).to_dict()
        self.item_popularity = train_df['article_id'].value_counts().to_dict()
        self.all_items = set(unique_items)

        logger.info(f"Modèle entraîné avec succès sur {n_users} utilisateurs et {n_items} articles")

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude_seen: bool = True
    ) -> List[int]:
        """
        Génère des recommandations pour un utilisateur

        Args:
            user_id: ID de l'utilisateur
            n: Nombre de recommandations
            exclude_seen: Exclure les articles déjà vus

        Returns:
            Liste des IDs d'articles recommandés
        """
        if not self.is_trained:
            logger.warning("Modèle non entraîné")
            return []

        # Vérifier si l'utilisateur est connu
        if user_id not in self.user_to_idx:
            logger.info(f"Utilisateur {user_id} inconnu - recommandations par popularité")
            return self._recommend_popular(user_id, n, exclude_seen)

        user_idx = self.user_to_idx[user_id]

        try:
            # Obtenir les recommandations du modèle ALS
            recommendations, scores = self.model.recommend(
                user_idx,
                self.user_item_matrix[user_idx],
                N=n + len(self.user_items.get(user_id, [])),
                filter_already_liked_items=exclude_seen
            )

            # Convertir les indices en IDs d'articles
            recommended_items = [
                self.idx_to_item[idx] for idx in recommendations
                if idx in self.idx_to_item
            ]

            return recommended_items[:n]

        except Exception as e:
            logger.error(f"Erreur lors de la recommandation pour user {user_id}: {e}")
            return self._recommend_popular(user_id, n, exclude_seen)

    def _recommend_popular(
        self,
        user_id: int,
        n: int,
        exclude_seen: bool
    ) -> List[int]:
        """
        Recommande les articles les plus populaires (fallback)

        Args:
            user_id: ID de l'utilisateur
            n: Nombre de recommandations
            exclude_seen: Exclure les articles déjà vus

        Returns:
            Liste des IDs d'articles populaires
        """
        popular_items = sorted(
            self.all_items,
            key=lambda x: self.item_popularity.get(x, 0),
            reverse=True
        )

        if exclude_seen:
            seen_items = self.user_items.get(user_id, set())
            popular_items = [item for item in popular_items if item not in seen_items]

        return popular_items[:n]

    def get_user_info(self, user_id: int) -> Dict:
        """
        Retourne les informations sur un utilisateur

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dictionnaire avec les informations utilisateur
        """
        return {
            "user_id": user_id,
            "is_known": user_id in self.user_to_idx,
            "items_seen": len(self.user_items.get(user_id, [])),
            "total_users": len(self.user_to_idx),
            "total_items": len(self.item_to_idx)
        }

    def save_model(self, filepath: str):
        """
        Sauvegarde le modèle entraîné

        Args:
            filepath: Chemin du fichier de sauvegarde
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant sauvegarde")

        model_data = {
            'model_state': self.model,
            'user_item_matrix': self.user_item_matrix,
            'item_user_matrix': self.item_user_matrix,
            'user_to_idx': self.user_to_idx,
            'idx_to_user': self.idx_to_user,
            'item_to_idx': self.item_to_idx,
            'idx_to_item': self.idx_to_item,
            'user_items': self.user_items,
            'item_popularity': self.item_popularity,
            'all_items': self.all_items
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        logger.info(f"Modèle sauvegardé dans {filepath}")

    def load_model(self, filepath: str):
        """
        Charge un modèle pré-entraîné

        Args:
            filepath: Chemin du fichier de modèle
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model_state']
        self.user_item_matrix = model_data['user_item_matrix']
        self.item_user_matrix = model_data['item_user_matrix']
        self.user_to_idx = model_data['user_to_idx']
        self.idx_to_user = model_data['idx_to_user']
        self.item_to_idx = model_data['item_to_idx']
        self.idx_to_item = model_data['idx_to_item']
        self.user_items = model_data['user_items']
        self.item_popularity = model_data['item_popularity']
        self.all_items = model_data['all_items']
        self.is_trained = True

        logger.info(f"Modèle chargé depuis {filepath}")


def prepare_training_data(clicks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prépare les données de clics pour l'entraînement

    Args:
        clicks_df: DataFrame brut des clics

    Returns:
        DataFrame préparé avec [user_id, article_id, click_count]
    """
    # Agrégation des clics par utilisateur-article
    interactions = clicks_df.groupby(['user_id', 'click_article_id']).agg({
        'click_timestamp': 'count'
    }).reset_index()

    interactions.columns = ['user_id', 'article_id', 'click_count']

    # Filtrer les utilisateurs actifs (au moins 5 interactions)
    user_counts = interactions['user_id'].value_counts()
    active_users = user_counts[user_counts >= 5].index

    filtered_interactions = interactions[interactions['user_id'].isin(active_users)]

    logger.info(
        f"Données préparées: {len(filtered_interactions)} interactions, "
        f"{filtered_interactions['user_id'].nunique()} utilisateurs, "
        f"{filtered_interactions['article_id'].nunique()} articles"
    )

    return filtered_interactions


if __name__ == "__main__":
    # Code de test
    import glob

    logger.info("Test du module ALS Recommender")

    # Charger des données de test
    click_files = sorted(glob.glob('data/clicks/clicks_hour_*.csv'))[:10]
    clicks_df = pd.concat([pd.read_csv(f) for f in click_files], ignore_index=True)

    # Préparer les données
    train_data = prepare_training_data(clicks_df)

    # Créer et entraîner le modèle
    recommender = ALSRecommender(factors=50, iterations=10)
    recommender.fit(train_data)

    # Test de recommandation
    test_user = train_data['user_id'].iloc[0]
    recommendations = recommender.recommend(test_user, n=5)

    logger.info(f"Recommandations pour l'utilisateur {test_user}: {recommendations}")

    # Sauvegarder le modèle
    recommender.save_model("models/als_model.pkl")

    # Test de chargement
    new_recommender = ALSRecommender()
    new_recommender.load_model("models/als_model.pkl")

    logger.info("Test terminé avec succès")