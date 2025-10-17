# 🚀 Guide de Déploiement Complet

Guide détaillé pour déployer le système de recommandation My Content sur Azure.

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Configuration Azure](#configuration-azure)
3. [Upload des Données](#upload-des-données)
4. [Déploiement des Azure Functions](#déploiement-des-azure-functions)
5. [Configuration de l'Application](#configuration-de-lapplication)
6. [Tests et Validation](#tests-et-validation)
7. [Migration vers Premium](#migration-vers-premium)
8. [Troubleshooting](#troubleshooting)

---

## Prérequis

### Outils Nécessaires

- **Python 3.9+** : `python --version`
- **Azure CLI** : `az --version`
- **Git** : `git --version`
- **Compte Azure** avec subscription active

### Installation Azure CLI

**macOS** :
```bash
brew install azure-cli
```

**Windows** :
```powershell
winget install Microsoft.AzureCLI
```

**Linux** :
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Connexion Azure

```bash
# Se connecter
az login

# Vérifier la subscription
az account show

# Lister les subscriptions disponibles
az account list --output table

# Changer de subscription si nécessaire
az account set --subscription "SUBSCRIPTION_ID"
```

---

## Configuration Azure

### Étape 1 : Créer le Resource Group

```bash
# Variables
RESOURCE_GROUP="my-content-reco-rg"
LOCATION="francecentral"

# Créer le groupe
az group create \\
  --name $RESOURCE_GROUP \\
  --location $LOCATION
```

### Étape 2 : Créer le Storage Account

```bash
# Variables
STORAGE_ACCOUNT="mycontentstorageXXXX"  # Remplacer XXXX par un identifiant unique

# Créer le storage account
az storage account create \\
  --name $STORAGE_ACCOUNT \\
  --resource-group $RESOURCE_GROUP \\
  --location $LOCATION \\
  --sku Standard_LRS \\
  --kind StorageV2

# Récupérer la connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \\
  --name $STORAGE_ACCOUNT \\
  --resource-group $RESOURCE_GROUP \\
  --output tsv)

echo "Connection String: $STORAGE_CONNECTION_STRING"

# Sauvegarder dans un fichier
echo "STORAGE_CONNECTION_STRING=\"$STORAGE_CONNECTION_STRING\"" > .env
```

### Étape 3 : Créer les Containers

```bash
# Créer les containers pour les données
az storage container create \\
  --name models \\
  --connection-string "$STORAGE_CONNECTION_STRING"

az storage container create \\
  --name data \\
  --connection-string "$STORAGE_CONNECTION_STRING"

az storage container create \\
  --name clicks \\
  --connection-string "$STORAGE_CONNECTION_STRING"

# Vérifier
az storage container list \\
  --connection-string "$STORAGE_CONNECTION_STRING" \\
  --output table
```

### Étape 4 : Créer la Function App

#### Option A : Plan Consumption (Gratuit)

**⚠️ Limitations** :
- Pas assez de RAM pour les embeddings (111 MB)
- Cold start plus long
- Convient si vous n'utilisez QUE le modèle ALS + métadonnées

```bash
FUNCTION_APP="my-content-recommender"

# Créer le plan Consumption
az functionapp create \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --storage-account $STORAGE_ACCOUNT \\
  --consumption-plan-location $LOCATION \\
  --runtime python \\
  --runtime-version 3.11 \\
  --functions-version 4 \\
  --os-type Linux
```

#### Option B : Plan Premium EP1 (Recommandé)

**✅ Avantages** :
- 3.5 GB RAM (suffisant pour embeddings)
- Cold start très rapide
- Toujours actif (warm instances)

**💰 Coût** : ~60€/mois

```bash
FUNCTION_APP="my-content-recommender"
PREMIUM_PLAN="my-content-premium-plan"

# Créer le plan Premium
az functionapp plan create \\
  --name $PREMIUM_PLAN \\
  --resource-group $RESOURCE_GROUP \\
  --location $LOCATION \\
  --sku EP1 \\
  --is-linux

# Créer la Function App sur le plan Premium
az functionapp create \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --storage-account $STORAGE_ACCOUNT \\
  --plan $PREMIUM_PLAN \\
  --runtime python \\
  --runtime-version 3.11 \\
  --functions-version 4 \\
  --os-type Linux
```

### Étape 5 : Configurer les Variables d'Environnement

```bash
# Configurer toutes les variables nécessaires
az functionapp config appsettings set \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --settings \\
    STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING" \\
    MODEL_CONTAINER_NAME=models \\
    MODEL_BLOB_NAME=als_model.pkl \\
    DATA_CONTAINER_NAME=data \\
    ARTICLES_METADATA_BLOB=articles_metadata.csv \\
    EMBEDDINGS_BLOB=articles_embeddings_reduced.pickle \\
    CLICKS_CONTAINER_NAME=clicks

# Vérifier
az functionapp config appsettings list \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --output table
```

---

## Upload des Données

### Étape 6 : Uploader les Fichiers

```bash
# Retourner dans le dossier du projet
cd production_app/scripts

# Configurer l'environnement
export AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING"

# Uploader toutes les données
python upload_data_to_azure.py --all

# Vérifier que les fichiers sont bien uploadés
python upload_data_to_azure.py --list
```

**Résultat attendu** :
```
📦 Fichiers dans 'models':
   - als_model.pkl (0.13 MB) - Modifié: 2025-10-17

📦 Fichiers dans 'data':
   - articles_metadata.csv (11.23 MB) - Modifié: 2025-10-17
   - articles_embeddings_reduced.pickle (111.45 MB) - Modifié: 2025-10-17

📦 Fichiers dans 'clicks':
   (vide)
```

---

## Déploiement des Azure Functions

### Étape 7 : Déploiement via GitHub Actions (Recommandé)

#### 7.1 Créer un Repository GitHub

```bash
# Initialiser Git si nécessaire
cd /path/to/production_app
git init
git add .
git commit -m "Initial production setup"

# Créer le repo sur GitHub (via interface web)
# Puis connecter le repo local
git remote add origin https://github.com/USERNAME/my-content-recommender.git
git branch -M main
git push -u origin main
```

#### 7.2 Récupérer le Publish Profile

```bash
# Télécharger le publish profile
az functionapp deployment list-publishing-profiles \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --xml > publish-profile.xml

# Afficher le contenu
cat publish-profile.xml
```

#### 7.3 Configurer GitHub Secrets

1. Aller sur GitHub : **Repo → Settings → Secrets and variables → Actions**
2. Cliquer sur **"New repository secret"**
3. Nom : `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
4. Valeur : Copier tout le contenu de `publish-profile.xml`
5. Cliquer sur **"Add secret"**

#### 7.4 Activer le Workflow

```bash
# Copier le workflow dans le repo
mkdir -p .github/workflows
cp config/azure-deploy.yml .github/workflows/

# Éditer le fichier pour mettre votre nom de Function App
nano .github/workflows/azure-deploy.yml
# Remplacer: AZURE_FUNCTIONAPP_NAME: 'your-function-app-name'
# Par:       AZURE_FUNCTIONAPP_NAME: 'my-content-recommender'

# Commit et push
git add .github/workflows/azure-deploy.yml
git commit -m "Add GitHub Actions workflow"
git push
```

#### 7.5 Vérifier le Déploiement

1. Aller sur GitHub : **Repo → Actions**
2. Vérifier que le workflow "Deploy Azure Functions" s'exécute
3. Attendre que le statut soit ✅ (3-5 minutes)

### Alternative : Déploiement Manuel

```bash
cd production_app/backend/azure_function

# Installer les dépendances localement
pip install -r requirements.txt --target ./.python_packages/lib/site-packages

# Déployer
func azure functionapp publish $FUNCTION_APP
```

---

## Configuration de l'Application

### Étape 8 : Configurer l'Application Streamlit

```bash
cd production_app/frontend

# Copier le template de configuration
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

**Contenu de `.env`** :
```bash
AZURE_FUNCTION_URL=https://my-content-recommender.azurewebsites.net/api/recommend
AZURE_TRACK_CLICK_URL=https://my-content-recommender.azurewebsites.net/api/track_click
AZURE_FUNCTION_KEY=  # Laisser vide si pas de clé configurée
```

### Récupérer l'URL de la Function

```bash
# Obtenir l'URL complète
az functionapp show \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --query defaultHostName \\
  --output tsv

# Résultat: my-content-recommender.azurewebsites.net
```

---

## Tests et Validation

### Étape 9 : Tester les Endpoints

#### Test 1 : Health Check

```bash
curl https://my-content-recommender.azurewebsites.net/api/recommend
```

**Réponse attendue** : Erreur de validation (normal, pas de body)

#### Test 2 : Recommandations

```bash
curl -X POST https://my-content-recommender.azurewebsites.net/api/recommend \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": 12345,
    "n_recommendations": 5
  }'
```

**Réponse attendue** :
```json
{
  "user_id": 12345,
  "recommendations": [
    {
      "article_id": 160974,
      "category_id": 281,
      "words_count": 250,
      "created_at": "2017-12-13",
      "publisher_id": 0,
      "metadata_available": true
    }
  ],
  "count": 5,
  "model": "ALS",
  "diversity": {
    "category_diversity": 0.800,
    "unique_categories": 4
  },
  "status": "success"
}
```

#### Test 3 : Tracking

```bash
curl -X POST https://my-content-recommender.azurewebsites.net/api/track_click \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": 12345,
    "article_id": 160974
  }'
```

**Réponse attendue** :
```json
{
  "status": "success",
  "message": "Clic enregistré avec succès"
}
```

### Étape 10 : Tester l'Application Streamlit

```bash
cd production_app/frontend

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'app
streamlit run app.py
```

1. Ouvrir http://localhost:8501
2. Décocher "Mode test"
3. Sélectionner un utilisateur
4. Cliquer sur "Recommander"
5. Vérifier que les recommandations s'affichent avec métadonnées

---

## Migration vers Premium

Si vous avez démarré avec un plan Consumption et souhaitez migrer vers Premium :

### Étape 11 : Migrer vers Premium

```bash
# Créer le plan Premium
az functionapp plan create \\
  --name my-content-premium-plan \\
  --resource-group $RESOURCE_GROUP \\
  --location $LOCATION \\
  --sku EP1 \\
  --is-linux

# Migrer la Function App
az functionapp update \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --plan my-content-premium-plan

# Redémarrer
az functionapp restart \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP
```

---

## Troubleshooting

### Problème 1 : Cold Start Lent (10-20s)

**Cause** : Chargement initial des données (modèle + métadonnées + embeddings)

**Solutions** :
1. **Plan Premium** : Garantit des instances warm
2. **Réduire les données** : Ne pas charger les embeddings si non utilisés
3. **Pinger régulièrement** : Faire un call toutes les 5 minutes pour garder warm

```bash
# Créer un cron job pour ping
* */5 * * * curl -X POST https://my-content-recommender.azurewebsites.net/api/recommend -d '{"user_id":1,"n_recommendations":1}' -H "Content-Type: application/json"
```

### Problème 2 : Erreur "Model unavailable"

**Cause** : Le modèle n'a pas pu être chargé depuis Storage

**Solutions** :
```bash
# Vérifier que le blob existe
az storage blob list \\
  --container-name models \\
  --connection-string "$STORAGE_CONNECTION_STRING" \\
  --output table

# Vérifier les variables d'environnement
az functionapp config appsettings list \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  | grep STORAGE_CONNECTION_STRING

# Réuploader le modèle
python scripts/upload_data_to_azure.py --model

# Redémarrer la Function
az functionapp restart \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP
```

### Problème 3 : Erreur "Metadata not available"

**Cause** : Les métadonnées n'ont pas été uploadées ou chargées

**Solutions** :
```bash
# Vérifier le container data
az storage blob list \\
  --container-name data \\
  --connection-string "$STORAGE_CONNECTION_STRING" \\
  --output table

# Uploader les métadonnées
python scripts/upload_data_to_azure.py --metadata

# Vérifier les logs Azure
az functionapp log tail \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP
```

### Problème 4 : Timeout sur Première Requête

**Cause** : Le chargement initial prend trop de temps (> 30s timeout par défaut)

**Solutions** :
```bash
# Augmenter le timeout (Premium uniquement)
az functionapp config set \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --function-timeout 60

# Ou désactiver le pré-chargement au démarrage
# Éditer __init__.py et commenter les lignes 428-432
```

### Problème 5 : GitHub Actions Échoue

**Causes possibles** :
1. Publish profile expiré
2. Mauvais nom de Function App
3. Dépendances incompatibles

**Solutions** :
```bash
# Régénérer le publish profile
az functionapp deployment list-publishing-profiles \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --xml

# Mettre à jour le secret GitHub

# Vérifier les logs dans GitHub Actions
```

---

## Monitoring et Logs

### Voir les Logs en Temps Réel

```bash
az functionapp log tail \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP
```

### Activer Application Insights

```bash
# Créer Application Insights
az monitor app-insights component create \\
  --app my-content-insights \\
  --location $LOCATION \\
  --resource-group $RESOURCE_GROUP

# Connecter à la Function App
APPINSIGHTS_KEY=$(az monitor app-insights component show \\
  --app my-content-insights \\
  --resource-group $RESOURCE_GROUP \\
  --query instrumentationKey \\
  --output tsv)

az functionapp config appsettings set \\
  --name $FUNCTION_APP \\
  --resource-group $RESOURCE_GROUP \\
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$APPINSIGHTS_KEY
```

---

## Checklist Finale

- [ ] Resource Group créé
- [ ] Storage Account créé avec containers
- [ ] Function App créée (Consumption ou Premium)
- [ ] Variables d'environnement configurées
- [ ] Modèle ALS uploadé vers Storage
- [ ] Métadonnées uploadées vers Storage
- [ ] Embeddings uploadés vers Storage (optionnel)
- [ ] GitHub Actions configuré et déployé
- [ ] Endpoint `/api/recommend` testé et fonctionnel
- [ ] Endpoint `/api/track_click` testé et fonctionnel
- [ ] Application Streamlit testée en local
- [ ] Application Streamlit connectée à Azure
- [ ] Logs Azure vérifiés (pas d'erreurs)

---

**Temps estimé** : 45-60 minutes
**Niveau de difficulté** : Intermédiaire
**Prérequis** : Compte Azure actif, connaissance CLI basique

**Support** : En cas de problème, consultez les logs Azure et vérifiez chaque étape une par une.

---

**Dernière mise à jour** : Octobre 2025
