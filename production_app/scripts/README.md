# 🛠️ Scripts Utilitaires

Scripts pour gérer les données et le déploiement du système.

## 📝 add_article.py

Ajoute un nouvel article au CSV des métadonnées.

### Usage

**Mode interactif** :
```bash
python add_article.py --interactive
```

**Mode ligne de commande** :
```bash
python add_article.py --category 281 --words 250 --publisher 0
```

### Options

| Option | Description | Requis | Défaut |
|--------|-------------|--------|--------|
| `--csv` | Chemin vers le CSV | Non | `data/articles_metadata.csv` |
| `--category` | ID de la catégorie | Oui (ou -i) | - |
| `--words` | Nombre de mots | Oui (ou -i) | - |
| `--publisher` | ID de l'éditeur | Non | 0 |
| `--timestamp` | Timestamp en ms | Non | Maintenant |
| `--interactive`, `-i` | Mode interactif | Non | False |

### Exemple Complet

```bash
# Mode interactif recommandé
python add_article.py --interactive

# Mode ligne de commande
python add_article.py \\
  --csv data/articles_metadata.csv \\
  --category 281 \\
  --words 250 \\
  --publisher 0
```

### ⚠️ Important

Après l'ajout d'articles :
1. Uploader le CSV mis à jour vers Azure Storage
2. Générer les embeddings pour le nouvel article (optionnel mais recommandé)
3. Réentraîner le modèle ALS si des interactions sont ajoutées

---

## 📤 upload_data_to_azure.py

Upload les données vers Azure Blob Storage.

### Usage

**Uploader toutes les données** :
```bash
python upload_data_to_azure.py --all
```

**Uploader des fichiers spécifiques** :
```bash
# Modèle ALS uniquement
python upload_data_to_azure.py --model

# Métadonnées uniquement
python upload_data_to_azure.py --metadata

# Embeddings uniquement
python upload_data_to_azure.py --embeddings
```

**Lister les fichiers existants** :
```bash
python upload_data_to_azure.py --list
```

### Options

| Option | Description |
|--------|-------------|
| `--all` | Uploader toutes les données |
| `--model` | Uploader le modèle ALS |
| `--metadata` | Uploader les métadonnées articles |
| `--embeddings` | Uploader les embeddings réduits |
| `--list` | Lister les fichiers existants |
| `--model-path` | Chemin custom du modèle (défaut: `models/als_model.pkl`) |
| `--metadata-path` | Chemin custom des métadonnées (défaut: `data/articles_metadata.csv`) |
| `--embeddings-path` | Chemin custom des embeddings (défaut: `data/articles_embeddings_reduced.pickle`) |
| `--no-overwrite` | Ne pas écraser les fichiers existants |

### Configuration

Le script utilise la variable d'environnement `AZURE_STORAGE_CONNECTION_STRING`.

**Option 1 - Variable d'environnement** :
```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."
```

**Option 2 - Fichier .env** :
```bash
# Créer un fichier .env
echo 'AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."' > .env
```

### Exemple Complet

```bash
# 1. Configurer la connection string
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=mystorageaccount;AccountKey=...;EndpointSuffix=core.windows.net"

# 2. Lister les fichiers existants
python upload_data_to_azure.py --list

# 3. Uploader toutes les données
python upload_data_to_azure.py --all

# 4. Vérifier que les fichiers sont bien uploadés
python upload_data_to_azure.py --list
```

### Fichiers Uploadés

| Fichier Local | Container Azure | Blob Name | Taille |
|---------------|-----------------|-----------|--------|
| `models/als_model.pkl` | `models` | `als_model.pkl` | ~130 KB |
| `data/articles_metadata.csv` | `data` | `articles_metadata.csv` | ~11 MB |
| `data/articles_embeddings_reduced.pickle` | `data` | `articles_embeddings_reduced.pickle` | ~111 MB |

---

## 🔄 train_model.py (À venir)

Script de réentraînement du modèle ALS.

**Fonctionnalités prévues** :
- Charger les nouveaux clics depuis Azure Storage
- Fusionner avec les clics historiques
- Entraîner un nouveau modèle ALS
- Comparer les performances (ancien vs nouveau)
- Upload du nouveau modèle vers Azure Storage
- Déploiement automatique

**Usage prévu** :
```bash
python train_model.py \\
  --clicks-path data/clicks/ \\
  --new-clicks-container clicks \\
  --output models/als_model_new.pkl \\
  --evaluate
```

---

## 🔧 Dépendances

Les scripts nécessitent les dépendances suivantes :

```bash
pip install azure-storage-blob python-dotenv pandas
```

Ou utiliser le fichier requirements du backend :

```bash
pip install -r ../backend/azure_function/requirements.txt
```

---

## 📋 Workflow Recommandé

### Ajout d'un nouvel article

1. **Ajouter au CSV** :
   ```bash
   python add_article.py --interactive
   ```

2. **Uploader vers Azure** :
   ```bash
   python upload_data_to_azure.py --metadata
   ```

3. **Redémarrer la Function App** (pour recharger les métadonnées) :
   ```bash
   az functionapp restart \\
     --name your-function-app \\
     --resource-group your-resource-group
   ```

### Mise à jour du modèle

1. **Réentraîner** :
   ```bash
   python train_model.py --evaluate
   ```

2. **Uploader le nouveau modèle** :
   ```bash
   python upload_data_to_azure.py --model
   ```

3. **Redémarrer la Function App** :
   ```bash
   az functionapp restart \\
     --name your-function-app \\
     --resource-group your-resource-group
   ```

---

## 🆘 Troubleshooting

### Erreur: "STORAGE_CONNECTION_STRING non trouvée"

**Solution** :
```bash
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
```

### Erreur: "Container 'xxx' n'existe pas"

**Solution** : Les containers sont créés automatiquement lors de l'upload. Si l'erreur persiste :
```bash
az storage container create --name data --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
az storage container create --name models --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
az storage container create --name clicks --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
```

### Erreur: "Fichier non trouvé"

**Solution** : Vérifiez que vous êtes dans le bon répertoire et que les chemins sont corrects :
```bash
ls -la models/als_model.pkl
ls -la data/articles_metadata.csv
ls -la data/articles_embeddings_reduced.pickle
```

---

**Dernière mise à jour** : Octobre 2025
