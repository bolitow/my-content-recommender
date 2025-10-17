#!/usr/bin/env python3
"""
Script pour uploader les données vers Azure Blob Storage

Usage:
    # Uploader toutes les données
    python upload_data_to_azure.py --all

    # Uploader seulement le modèle
    python upload_data_to_azure.py --model

    # Uploader seulement les métadonnées
    python upload_data_to_azure.py --metadata

    # Uploader seulement les embeddings
    python upload_data_to_azure.py --embeddings

    # Lister les fichiers existants
    python upload_data_to_azure.py --list
"""

import argparse
import os
import sys
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
from pathlib import Path


def get_connection_string() -> str:
    """
    Récupère la connection string depuis les variables d'environnement

    Returns:
        Connection string ou None si non trouvée
    """
    # Charger .env si présent
    load_dotenv()

    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING") or \
               os.environ.get("STORAGE_CONNECTION_STRING")

    if not conn_str:
        print("❌ Erreur: AZURE_STORAGE_CONNECTION_STRING non trouvée")
        print("\nConfigurer avec:")
        print('  export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."')
        print("\nOu créer un fichier .env avec:")
        print('  AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."')
        return None

    return conn_str


def create_container_if_not_exists(blob_service_client: BlobServiceClient, container_name: str):
    """
    Crée un container s'il n'existe pas

    Args:
        blob_service_client: Client Azure Blob Service
        container_name: Nom du container
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
            print(f"   ✅ Container '{container_name}' créé")
        else:
            print(f"   ℹ️  Container '{container_name}' existe déjà")
    except Exception as e:
        print(f"   ❌ Erreur lors de la création du container '{container_name}': {e}")


def upload_file(
    blob_service_client: BlobServiceClient,
    container_name: str,
    local_file_path: str,
    blob_name: str = None,
    overwrite: bool = True
) -> bool:
    """
    Upload un fichier vers Azure Blob Storage

    Args:
        blob_service_client: Client Azure Blob Service
        container_name: Nom du container
        local_file_path: Chemin local du fichier
        blob_name: Nom du blob (défaut: nom du fichier)
        overwrite: Écraser si existe (défaut: True)

    Returns:
        True si succès, False sinon
    """
    if not os.path.exists(local_file_path):
        print(f"   ❌ Fichier non trouvé: {local_file_path}")
        return False

    # Utiliser le nom du fichier si blob_name non fourni
    if blob_name is None:
        blob_name = os.path.basename(local_file_path)

    # Obtenir la taille du fichier
    file_size = os.path.getsize(local_file_path)
    file_size_mb = file_size / (1024 * 1024)

    print(f"\n📤 Upload: {local_file_path}")
    print(f"   - Container: {container_name}")
    print(f"   - Blob name: {blob_name}")
    print(f"   - Taille: {file_size_mb:.2f} MB")

    try:
        # Obtenir le blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        # Upload avec barre de progression (pour les gros fichiers)
        with open(local_file_path, "rb") as data:
            blob_client.upload_blob(
                data,
                overwrite=overwrite,
                content_settings=ContentSettings(
                    content_type=get_content_type(local_file_path)
                )
            )

        print(f"   ✅ Upload réussi!")
        return True

    except Exception as e:
        print(f"   ❌ Erreur lors de l'upload: {e}")
        return False


def get_content_type(file_path: str) -> str:
    """
    Détermine le content type d'un fichier

    Args:
        file_path: Chemin du fichier

    Returns:
        Content type MIME
    """
    extension = Path(file_path).suffix.lower()

    content_types = {
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.pkl': 'application/octet-stream',
        '.pickle': 'application/octet-stream',
        '.txt': 'text/plain',
    }

    return content_types.get(extension, 'application/octet-stream')


def list_blobs(blob_service_client: BlobServiceClient, container_name: str):
    """
    Liste les blobs dans un container

    Args:
        blob_service_client: Client Azure Blob Service
        container_name: Nom du container
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)

        if not container_client.exists():
            print(f"   ⚠️  Container '{container_name}' n'existe pas")
            return

        print(f"\n📦 Fichiers dans '{container_name}':")
        blobs = list(container_client.list_blobs())

        if not blobs:
            print("   (vide)")
            return

        for blob in blobs:
            size_mb = blob.size / (1024 * 1024)
            print(f"   - {blob.name} ({size_mb:.2f} MB) - Modifié: {blob.last_modified}")

    except Exception as e:
        print(f"   ❌ Erreur lors du listage: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload des données vers Azure Blob Storage"
    )

    # Options d'upload
    parser.add_argument('--all', action='store_true', help="Uploader toutes les données")
    parser.add_argument('--model', action='store_true', help="Uploader le modèle ALS")
    parser.add_argument('--metadata', action='store_true', help="Uploader les métadonnées articles")
    parser.add_argument('--embeddings', action='store_true', help="Uploader les embeddings réduits")

    # Option de listage
    parser.add_argument('--list', action='store_true', help="Lister les fichiers existants")

    # Chemins des fichiers
    parser.add_argument('--model-path', default='models/als_model.pkl', help="Chemin du modèle")
    parser.add_argument('--metadata-path', default='data/articles_metadata.csv', help="Chemin des métadonnées")
    parser.add_argument('--embeddings-path', default='data/articles_embeddings_reduced.pickle', help="Chemin des embeddings")

    # Options générales
    parser.add_argument('--no-overwrite', action='store_true', help="Ne pas écraser les fichiers existants")

    args = parser.parse_args()

    # Récupérer la connection string
    conn_str = get_connection_string()
    if not conn_str:
        sys.exit(1)

    # Créer le client Blob Service
    try:
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        print("✅ Connecté à Azure Storage")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)

    # Mode listage
    if args.list:
        print("\n" + "=" * 60)
        print("📋 LISTAGE DES FICHIERS AZURE STORAGE")
        print("=" * 60)

        list_blobs(blob_service_client, "models")
        list_blobs(blob_service_client, "data")
        list_blobs(blob_service_client, "clicks")
        return

    # Vérifier qu'au moins une option d'upload est spécifiée
    if not (args.all or args.model or args.metadata or args.embeddings):
        parser.print_help()
        print("\n❌ Erreur: Spécifiez au moins une option (--all, --model, --metadata, --embeddings, ou --list)")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("📤 UPLOAD DES DONNÉES VERS AZURE STORAGE")
    print("=" * 60)

    overwrite = not args.no_overwrite
    success_count = 0
    total_count = 0

    # Créer les containers nécessaires
    print("\n📦 Vérification des containers...")
    if args.all or args.model:
        create_container_if_not_exists(blob_service_client, "models")

    if args.all or args.metadata or args.embeddings:
        create_container_if_not_exists(blob_service_client, "data")

    # Toujours créer le container clicks pour les futurs clics
    create_container_if_not_exists(blob_service_client, "clicks")

    # Upload du modèle
    if args.all or args.model:
        total_count += 1
        if upload_file(
            blob_service_client,
            "models",
            args.model_path,
            "als_model.pkl",
            overwrite
        ):
            success_count += 1

    # Upload des métadonnées
    if args.all or args.metadata:
        total_count += 1
        if upload_file(
            blob_service_client,
            "data",
            args.metadata_path,
            "articles_metadata.csv",
            overwrite
        ):
            success_count += 1

    # Upload des embeddings
    if args.all or args.embeddings:
        total_count += 1
        if upload_file(
            blob_service_client,
            "data",
            args.embeddings_path,
            "articles_embeddings_reduced.pickle",
            overwrite
        ):
            success_count += 1

    # Résumé
    print("\n" + "=" * 60)
    print(f"✅ UPLOAD TERMINÉ: {success_count}/{total_count} fichiers uploadés avec succès")
    print("=" * 60)

    if success_count < total_count:
        print("\n⚠️  Certains fichiers n'ont pas pu être uploadés")
        sys.exit(1)

    print("\n📋 Prochaines étapes:")
    print("   1. Vérifier les fichiers avec: python upload_data_to_azure.py --list")
    print("   2. Configurer les variables d'environnement dans Azure Function App:")
    print("      - DATA_CONTAINER_NAME=data")
    print("      - ARTICLES_METADATA_BLOB=articles_metadata.csv")
    print("      - EMBEDDINGS_BLOB=articles_embeddings_reduced.pickle")
    print("      - CLICKS_CONTAINER_NAME=clicks")
    print("   3. Déployer le code via GitHub Actions")
    print("   4. Tester l'endpoint /api/recommend")


if __name__ == "__main__":
    main()
