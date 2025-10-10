"""
Script d'upload du modèle ALS vers Azure Blob Storage
Simplifie le déploiement du modèle en production
"""

import os
import sys
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import argparse
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration par défaut
DEFAULT_FILES = {
    'models/als_model.pkl': 'als_model.pkl',  # local_path: blob_name
}

CONTAINER_NAME = 'models'


def get_connection_string() -> str:
    """
    Récupère la connection string depuis les variables d'environnement

    Returns:
        Connection string Azure Storage
    """
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

    if not conn_str:
        print("❌ Erreur: Variable d'environnement AZURE_STORAGE_CONNECTION_STRING non définie")
        print("\n💡 Pour la définir:")
        print("   1. Via terminal:")
        print("      export AZURE_STORAGE_CONNECTION_STRING='votre_connection_string'")
        print("\n   2. Via fichier .env:")
        print("      Créez un fichier .env avec:")
        print("      AZURE_STORAGE_CONNECTION_STRING=votre_connection_string")
        print("\n   3. Récupérez la connection string depuis Azure Portal:")
        print("      Storage Account → Access keys → Connection string")
        sys.exit(1)

    return conn_str


def create_container_if_not_exists(blob_service_client: BlobServiceClient,
                                   container_name: str):
    """
    Crée le container s'il n'existe pas

    Args:
        blob_service_client: Client Azure Blob Service
        container_name: Nom du container
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)

        # Vérifier si le container existe
        if not container_client.exists():
            print(f"📦 Création du container '{container_name}'...")
            container_client.create_container()
            print(f"✅ Container '{container_name}' créé")
        else:
            print(f"✅ Container '{container_name}' existe déjà")

    except Exception as e:
        print(f"❌ Erreur lors de la création du container: {e}")
        sys.exit(1)


def upload_file(blob_service_client: BlobServiceClient,
                container_name: str,
                local_file_path: str,
                blob_name: str) -> bool:
    """
    Upload un fichier vers Azure Blob Storage

    Args:
        blob_service_client: Client Azure Blob Service
        container_name: Nom du container
        local_file_path: Chemin local du fichier
        blob_name: Nom du blob dans Azure

    Returns:
        True si succès, False sinon
    """
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(local_file_path):
            print(f"❌ Fichier non trouvé: {local_file_path}")
            return False

        # Obtenir la taille du fichier
        file_size_mb = os.path.getsize(local_file_path) / 1024 / 1024

        print(f"\n📤 Upload de '{local_file_path}' ({file_size_mb:.2f} MB)...")
        print(f"   → Destination: {container_name}/{blob_name}")

        # Créer le blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        # Upload le fichier
        with open(local_file_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)

        print(f"✅ Upload réussi: {blob_name}")

        # Obtenir l'URL du blob
        blob_url = blob_client.url
        print(f"   URL: {blob_url}")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'upload: {e}")
        return False


def list_blobs(blob_service_client: BlobServiceClient, container_name: str):
    """
    Liste tous les blobs dans le container

    Args:
        blob_service_client: Client Azure Blob Service
        container_name: Nom du container
    """
    try:
        print(f"\n📋 Contenu du container '{container_name}':")

        container_client = blob_service_client.get_container_client(container_name)
        blobs = list(container_client.list_blobs())

        if not blobs:
            print("   (vide)")
        else:
            for blob in blobs:
                size_mb = blob.size / 1024 / 1024
                print(f"   - {blob.name} ({size_mb:.2f} MB)")

    except Exception as e:
        print(f"❌ Erreur lors de la liste des blobs: {e}")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Upload du modèle ALS vers Azure Blob Storage"
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Chemin du fichier à uploader (défaut: models/als_model.pkl)'
    )
    parser.add_argument(
        '--blob-name',
        type=str,
        help='Nom du blob dans Azure (défaut: als_model.pkl)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='Lister les fichiers dans le container'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("📤 UPLOAD VERS AZURE BLOB STORAGE")
    print("=" * 70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Récupérer la connection string
    connection_string = get_connection_string()

    try:
        # Créer le client Blob Service
        print("🔌 Connexion à Azure Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        print("✅ Connexion établie\n")

        # Créer le container si nécessaire
        create_container_if_not_exists(blob_service_client, CONTAINER_NAME)

        # Mode liste seulement
        if args.list:
            list_blobs(blob_service_client, CONTAINER_NAME)
            return

        # Upload le(s) fichier(s)
        if args.file:
            # Upload un fichier spécifique
            blob_name = args.blob_name or os.path.basename(args.file)
            success = upload_file(
                blob_service_client,
                CONTAINER_NAME,
                args.file,
                blob_name
            )
        else:
            # Upload les fichiers par défaut
            all_success = True
            for local_path, blob_name in DEFAULT_FILES.items():
                success = upload_file(
                    blob_service_client,
                    CONTAINER_NAME,
                    local_path,
                    blob_name
                )
                all_success = all_success and success

            success = all_success

        # Lister les blobs après upload
        list_blobs(blob_service_client, CONTAINER_NAME)

        # Résumé
        print("\n" + "=" * 70)
        if success:
            print("✅ UPLOAD TERMINÉ AVEC SUCCÈS!")
            print("\n💡 Prochaines étapes:")
            print("   1. Vérifiez dans Azure Portal (Storage Account → Containers → models)")
            print("   2. Déployez l'Azure Function avec GitHub Actions")
            print("   3. Testez avec Streamlit (décochez 'Mode test')")
        else:
            print("❌ UPLOAD ÉCHOUÉ")
            print("\n💡 Vérifiez:")
            print("   1. La connection string est correcte")
            print("   2. Vous avez les permissions sur le Storage Account")
            print("   3. Le fichier local existe")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
