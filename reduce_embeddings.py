"""
Script de réduction dimensionnelle des embeddings d'articles
Utilise PCA pour réduire de 250 dimensions à 50-80 dimensions
pour optimiser l'espace de stockage Azure
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
import os
import sys
from datetime import datetime


def load_embeddings(filepath: str) -> np.ndarray:
    """
    Charge le fichier embeddings original (matrice numpy)

    Args:
        filepath: Chemin vers le fichier pickle

    Returns:
        Matrice numpy des embeddings
    """
    print(f"📂 Chargement des embeddings depuis {filepath}...")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier non trouvé: {filepath}")

    with open(filepath, 'rb') as f:
        embeddings = pickle.load(f)

    # Vérifier que c'est bien un numpy array
    if not isinstance(embeddings, np.ndarray):
        raise TypeError(f"Format inattendu: {type(embeddings)}")

    print(f"✅ Embeddings chargés")
    print(f"📊 Structure: Matrice {embeddings.shape[0]} articles × {embeddings.shape[1]} dimensions")
    print(f"   Taille en mémoire: {embeddings.nbytes / 1024 / 1024:.2f} MB")

    return embeddings


def reduce_dimensions(matrix: np.ndarray, n_components: int = 80,
                     random_state: int = 42) -> tuple:
    """
    Applique PCA pour réduire les dimensions

    Args:
        matrix: Matrice des embeddings originaux
        n_components: Nombre de dimensions cibles
        random_state: Seed pour reproductibilité

    Returns:
        Tuple (matrice_réduite, modèle_pca)
    """
    print(f"\n🎯 Réduction PCA: {matrix.shape[1]} → {n_components} dimensions")
    print("⏳ Cette opération peut prendre quelques minutes...")

    # Initialiser PCA
    pca = PCA(n_components=n_components, random_state=random_state)

    # Appliquer la transformation
    reduced_matrix = pca.fit_transform(matrix)

    # Afficher les statistiques
    explained_variance = pca.explained_variance_ratio_.sum()

    print(f"\n✅ Réduction terminée!")
    print(f"📊 Statistiques PCA:")
    print(f"   - Variance expliquée: {explained_variance * 100:.2f}%")
    print(f"   - Dimensions: {matrix.shape[1]} → {reduced_matrix.shape[1]}")
    print(f"   - Réduction: {(1 - reduced_matrix.shape[1] / matrix.shape[1]) * 100:.1f}%")
    print(f"   - Taille avant: {matrix.nbytes / 1024 / 1024:.2f} MB")
    print(f"   - Taille après: {reduced_matrix.nbytes / 1024 / 1024:.2f} MB")
    print(f"   - Économie: {(1 - reduced_matrix.nbytes / matrix.nbytes) * 100:.1f}%")

    return reduced_matrix, pca


def save_reduced_embeddings(embeddings_matrix: np.ndarray, pca_model: PCA,
                           output_path: str, pca_path: str):
    """
    Sauvegarde les embeddings réduits et le modèle PCA

    Args:
        embeddings_matrix: Matrice numpy des embeddings réduits
        pca_model: Modèle PCA entraîné
        output_path: Chemin de sauvegarde des embeddings
        pca_path: Chemin de sauvegarde du modèle PCA
    """
    print(f"\n💾 Sauvegarde des résultats...")

    # Sauvegarder les embeddings réduits (matrice numpy)
    with open(output_path, 'wb') as f:
        pickle.dump(embeddings_matrix, f, protocol=pickle.HIGHEST_PROTOCOL)

    file_size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"✅ Embeddings réduits sauvegardés: {output_path}")
    print(f"   Taille du fichier: {file_size_mb:.2f} MB")

    # Sauvegarder le modèle PCA (pour référence)
    with open(pca_path, 'wb') as f:
        pickle.dump(pca_model, f, protocol=pickle.HIGHEST_PROTOCOL)

    pca_size_mb = os.path.getsize(pca_path) / 1024 / 1024
    print(f"✅ Modèle PCA sauvegardé: {pca_path}")
    print(f"   Taille du fichier: {pca_size_mb:.2f} MB")


def test_quality(original_matrix: np.ndarray, reduced_matrix: np.ndarray,
                n_samples: int = 100):
    """
    Teste la qualité de la réduction en comparant les similarités

    Args:
        original_matrix: Matrice des embeddings originaux
        reduced_matrix: Matrice des embeddings réduits
        n_samples: Nombre d'échantillons à tester
    """
    print(f"\n🧪 Test de qualité sur {n_samples} échantillons...")

    from sklearn.metrics.pairwise import cosine_similarity

    # Limiter le nombre d'échantillons si nécessaire
    n_samples = min(n_samples, original_matrix.shape[0])
    n_comparison = min(200, original_matrix.shape[0])

    correlations = []

    # Échantillonner aléatoirement
    np.random.seed(42)
    sample_indices = np.random.choice(original_matrix.shape[0], n_samples, replace=False)

    for idx in sample_indices:
        # Vecteurs de l'article à tester
        orig_vec = original_matrix[idx:idx+1]  # Garder dimension (1, n)
        red_vec = reduced_matrix[idx:idx+1]

        # Prendre un échantillon de comparaison
        comparison_indices = np.random.choice(original_matrix.shape[0], n_comparison, replace=False)

        # Calculer similarités cosinus
        orig_sims = cosine_similarity(orig_vec, original_matrix[comparison_indices])[0]
        red_sims = cosine_similarity(red_vec, reduced_matrix[comparison_indices])[0]

        # Corrélation entre les similarités
        correlation = np.corrcoef(orig_sims, red_sims)[0, 1]
        correlations.append(correlation)

    avg_correlation = np.mean(correlations)

    print(f"✅ Test terminé!")
    print(f"📊 Corrélation moyenne des similarités: {avg_correlation:.4f}")

    if avg_correlation > 0.95:
        print("🎉 Excellente qualité! La réduction préserve très bien les relations.")
    elif avg_correlation > 0.90:
        print("👍 Bonne qualité. La réduction est acceptable.")
    else:
        print("⚠️  Qualité moyenne. Envisager d'augmenter le nombre de composantes.")

    return avg_correlation


def main():
    """Fonction principale"""
    print("=" * 70)
    print("🔬 RÉDUCTION DIMENSIONNELLE DES EMBEDDINGS D'ARTICLES")
    print("=" * 70)
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Configuration
    INPUT_PATH = "data/articles_embeddings.pickle"
    OUTPUT_PATH = "data/articles_embeddings_reduced.pickle"
    PCA_MODEL_PATH = "models/pca_model.pkl"
    N_COMPONENTS = 80  # Réduction à 80 dimensions (ajustable)

    # Créer le dossier models si nécessaire
    os.makedirs("models", exist_ok=True)

    try:
        # Étape 1: Charger les embeddings originaux (matrice numpy)
        embeddings_original = load_embeddings(INPUT_PATH)

        # Étape 2: Appliquer PCA
        reduced_matrix, pca_model = reduce_dimensions(
            embeddings_original,
            n_components=N_COMPONENTS
        )

        # Étape 3: Sauvegarder
        save_reduced_embeddings(
            reduced_matrix,
            pca_model,
            OUTPUT_PATH,
            PCA_MODEL_PATH
        )

        # Étape 4: Tester la qualité
        correlation = test_quality(embeddings_original, reduced_matrix)

        # Résumé final
        print("\n" + "=" * 70)
        print("✅ RÉDUCTION TERMINÉE AVEC SUCCÈS!")
        print("=" * 70)

        original_size = os.path.getsize(INPUT_PATH) / 1024 / 1024
        reduced_size = os.path.getsize(OUTPUT_PATH) / 1024 / 1024

        print(f"\n📦 Résumé:")
        print(f"   Fichier original:  {original_size:.2f} MB")
        print(f"   Fichier réduit:    {reduced_size:.2f} MB")
        print(f"   Économie:          {original_size - reduced_size:.2f} MB ({(1 - reduced_size/original_size)*100:.1f}%)")
        print(f"   Qualité (corr.):   {correlation:.4f}")
        print(f"\n💡 Le fichier réduit peut maintenant être utilisé avec Azure Functions!")
        print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
