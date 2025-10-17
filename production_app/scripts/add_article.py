#!/usr/bin/env python3
"""
Script pour ajouter un nouvel article à articles_metadata.csv

Usage:
    python add_article.py --category 281 --words 250 --publisher 0

ou en mode interactif:
    python add_article.py --interactive
"""

import argparse
import pandas as pd
from datetime import datetime
import os
import sys


def get_next_article_id(df: pd.DataFrame) -> int:
    """
    Retourne le prochain article_id disponible

    Args:
        df: DataFrame des articles

    Returns:
        Nouvel article_id
    """
    if df.empty:
        return 0

    max_id = df['article_id'].max()
    return int(max_id) + 1


def validate_inputs(category_id: int, words_count: int, publisher_id: int) -> bool:
    """
    Valide les entrées utilisateur

    Args:
        category_id: ID de la catégorie
        words_count: Nombre de mots
        publisher_id: ID de l'éditeur

    Returns:
        True si valide, False sinon
    """
    errors = []

    if category_id < 0:
        errors.append("category_id doit être >= 0")

    if words_count < 10 or words_count > 10000:
        errors.append("words_count doit être entre 10 et 10000")

    if publisher_id < 0:
        errors.append("publisher_id doit être >= 0")

    if errors:
        print("❌ Erreurs de validation:")
        for error in errors:
            print(f"   - {error}")
        return False

    return True


def add_article_to_csv(
    csv_path: str,
    category_id: int,
    words_count: int,
    publisher_id: int = 0,
    created_at_ts: int = None
) -> dict:
    """
    Ajoute un nouvel article au CSV

    Args:
        csv_path: Chemin vers le CSV
        category_id: ID de la catégorie
        words_count: Nombre de mots
        publisher_id: ID de l'éditeur (défaut: 0)
        created_at_ts: Timestamp de création en ms (défaut: maintenant)

    Returns:
        Dictionnaire avec les informations de l'article ajouté
    """
    # Charger le CSV existant
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"📂 CSV chargé: {len(df)} articles existants")
    else:
        # Créer un nouveau DataFrame
        df = pd.DataFrame(columns=['article_id', 'category_id', 'created_at_ts', 'publisher_id', 'words_count'])
        print("📂 Nouveau CSV créé")

    # Générer le nouvel article_id
    article_id = get_next_article_id(df)

    # Générer le timestamp si non fourni
    if created_at_ts is None:
        created_at_ts = int(datetime.utcnow().timestamp() * 1000)

    # Créer la nouvelle ligne
    new_article = {
        'article_id': article_id,
        'category_id': category_id,
        'created_at_ts': created_at_ts,
        'publisher_id': publisher_id,
        'words_count': words_count
    }

    # Ajouter au DataFrame
    df = pd.concat([df, pd.DataFrame([new_article])], ignore_index=True)

    # Convertir les types pour s'assurer qu'ils sont corrects
    df['article_id'] = df['article_id'].astype(int)
    df['category_id'] = df['category_id'].astype(int)
    df['created_at_ts'] = df['created_at_ts'].astype(int)
    df['publisher_id'] = df['publisher_id'].astype(int)
    df['words_count'] = df['words_count'].astype(int)

    # Sauvegarder
    df.to_csv(csv_path, index=False)
    print(f"✅ Article ajouté et CSV sauvegardé: {len(df)} articles total")

    return new_article


def interactive_mode(csv_path: str):
    """
    Mode interactif pour ajouter des articles

    Args:
        csv_path: Chemin vers le CSV
    """
    print("\n" + "=" * 60)
    print("📝 MODE INTERACTIF - AJOUT D'ARTICLE")
    print("=" * 60)

    # Charger le CSV pour avoir des stats
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        print(f"\n📊 Statistiques actuelles:")
        print(f"   - Articles existants: {len(df)}")
        print(f"   - Catégories uniques: {df['category_id'].nunique()}")
        print(f"   - Catégories populaires: {df['category_id'].value_counts().head(5).to_dict()}")
        print(f"   - Mots moyens: {df['words_count'].mean():.0f}")
    else:
        print("\n📊 CSV vide, création du premier article")

    print("\n" + "-" * 60)

    # Demander les informations
    try:
        category_id = int(input("🏷️  Catégorie ID (ex: 281): ").strip())
        words_count = int(input("📝 Nombre de mots (ex: 250): ").strip())
        publisher_id = int(input("📰 Publisher ID (défaut 0): ").strip() or "0")

        # Demander confirmation
        print("\n" + "-" * 60)
        print("📋 Récapitulatif:")
        print(f"   - Catégorie: {category_id}")
        print(f"   - Mots: {words_count}")
        print(f"   - Publisher: {publisher_id}")
        print(f"   - Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        confirm = input("\n✅ Confirmer l'ajout? (o/n): ").strip().lower()

        if confirm == 'o' or confirm == 'oui':
            # Valider
            if not validate_inputs(category_id, words_count, publisher_id):
                return

            # Ajouter
            new_article = add_article_to_csv(csv_path, category_id, words_count, publisher_id)

            print("\n" + "=" * 60)
            print("✅ ARTICLE AJOUTÉ AVEC SUCCÈS")
            print("=" * 60)
            print(f"   - Article ID: {new_article['article_id']}")
            print(f"   - Catégorie: {new_article['category_id']}")
            print(f"   - Mots: {new_article['words_count']}")
            print(f"   - Timestamp: {new_article['created_at_ts']}")
            print("\n⚠️  N'oubliez pas de:")
            print("   1. Uploader le CSV mis à jour vers Azure Storage")
            print("   2. Générer les embeddings pour cet article (optionnel)")
            print("   3. Réentraîner le modèle ALS si des interactions sont ajoutées")

        else:
            print("❌ Ajout annulé")

    except ValueError as e:
        print(f"❌ Erreur: Valeur invalide - {e}")
    except KeyboardInterrupt:
        print("\n❌ Opération annulée par l'utilisateur")


def main():
    parser = argparse.ArgumentParser(
        description="Ajoute un nouvel article à articles_metadata.csv"
    )

    parser.add_argument(
        '--csv',
        type=str,
        default='data/articles_metadata.csv',
        help="Chemin vers le CSV (défaut: data/articles_metadata.csv)"
    )

    parser.add_argument(
        '--category',
        type=int,
        help="ID de la catégorie"
    )

    parser.add_argument(
        '--words',
        type=int,
        help="Nombre de mots de l'article"
    )

    parser.add_argument(
        '--publisher',
        type=int,
        default=0,
        help="ID de l'éditeur (défaut: 0)"
    )

    parser.add_argument(
        '--timestamp',
        type=int,
        help="Timestamp de création en ms (défaut: maintenant)"
    )

    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help="Mode interactif"
    )

    args = parser.parse_args()

    # Vérifier que le répertoire existe
    csv_dir = os.path.dirname(args.csv)
    if csv_dir and not os.path.exists(csv_dir):
        print(f"❌ Erreur: Le répertoire {csv_dir} n'existe pas")
        sys.exit(1)

    # Mode interactif
    if args.interactive:
        interactive_mode(args.csv)
        return

    # Mode ligne de commande
    if args.category is None or args.words is None:
        parser.print_help()
        print("\n❌ Erreur: --category et --words sont requis (ou utilisez --interactive)")
        sys.exit(1)

    # Valider
    if not validate_inputs(args.category, args.words, args.publisher):
        sys.exit(1)

    # Ajouter
    print(f"\n📝 Ajout d'un nouvel article au CSV: {args.csv}")
    print(f"   - Catégorie: {args.category}")
    print(f"   - Mots: {args.words}")
    print(f"   - Publisher: {args.publisher}")

    new_article = add_article_to_csv(
        args.csv,
        args.category,
        args.words,
        args.publisher,
        args.timestamp
    )

    print("\n" + "=" * 60)
    print("✅ ARTICLE AJOUTÉ AVEC SUCCÈS")
    print("=" * 60)
    print(f"   - Article ID: {new_article['article_id']}")
    print(f"   - Catégorie: {new_article['category_id']}")
    print(f"   - Mots: {new_article['words_count']}")
    print(f"   - Timestamp: {new_article['created_at_ts']}")
    print("\n⚠️  N'oubliez pas de:")
    print("   1. Uploader le CSV mis à jour vers Azure Storage")
    print("   2. Générer les embeddings pour cet article (optionnel)")
    print("   3. Réentraîner le modèle ALS si des interactions sont ajoutées")


if __name__ == "__main__":
    main()
