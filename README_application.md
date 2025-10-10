# Système de Recommandation d'Articles - Application

## Architecture

L'application suit l'architecture 1 proposée avec Azure Functions comme middleware :

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Streamlit  │────▶│ Azure Functions │────▶│   API FastAPI │
│   (Frontend) │◀────│   (Middleware)  │◀────│   (Backend)   │
└──────────────┘     └─────────────────┘     └──────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Azure Storage  │
                    │  (Modèle ALS)   │
                    └─────────────────┘
```

## Composants

### 1. Interface Streamlit (`app.py`)

Interface utilisateur en français permettant de :
- Sélectionner un utilisateur (liste ou saisie manuelle)
- Choisir le nombre de recommandations (1-10)
- Afficher les articles recommandés avec leurs métadonnées
- Mode test local pour développement

### 2. Module ALS (`recommender_als.py`)

Implémentation du modèle de filtrage collaboratif :
- Algorithme ALS (Alternating Least Squares)
- Gestion des utilisateurs connus/inconnus
- Fallback sur popularité si nécessaire
- Sauvegarde/chargement du modèle

### 3. API FastAPI (`api.py`)

API REST exposant le système de recommandation :
- Endpoint `/recommend` pour obtenir des recommandations
- Endpoint `/health` pour vérifier l'état
- Endpoint `/users` pour lister les utilisateurs
- Documentation automatique sur `/docs`

### 4. Azure Functions (`azure_function/`)

Fonction serverless faisant le pont entre l'app et l'API :
- Validation des requêtes
- Appel à l'API de recommandation
- Gestion des erreurs
- Timeout configurable

## Installation et Configuration

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration Azure

#### Variables d'environnement à configurer :

**Pour l'application Streamlit :**
```bash
AZURE_FUNCTION_URL=https://[VOTRE_FUNCTION].azurewebsites.net/api/recommend
AZURE_FUNCTION_KEY=[VOTRE_CLE_FONCTION]
```

**Pour Azure Functions :**
```bash
API_BASE_URL=https://[VOTRE_API].azurewebsites.net
API_TIMEOUT=10
```

### 3. Déploiement Azure Functions

```bash
# Se placer dans le dossier azure_function
cd azure_function

# Créer une Function App dans Azure
az functionapp create \
  --resource-group [VOTRE_RG] \
  --consumption-plan-location westeurope \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name [NOM_FUNCTION] \
  --storage-account [VOTRE_STORAGE]

# Déployer la fonction
func azure functionapp publish [NOM_FUNCTION]
```

### 4. Déploiement de l'API

L'API peut être déployée sur :
- Azure App Service
- Azure Container Instances
- Azure Kubernetes Service

Exemple avec App Service :

```bash
# Créer un App Service
az webapp create \
  --resource-group [VOTRE_RG] \
  --plan [VOTRE_PLAN] \
  --name [NOM_API] \
  --runtime "PYTHON:3.9"

# Déployer l'API
az webapp up --name [NOM_API]
```

## Utilisation

### Mode Développement Local

1. **Lancer l'API :**
```bash
python api.py
# API disponible sur http://localhost:8000
```

2. **Lancer Streamlit :**
```bash
streamlit run app.py
# Application sur http://localhost:8501
```

3. **Mode test local :**
- Cocher "Mode test local" dans l'interface
- Utilise des données simulées sans appel Azure

### Mode Production

1. Configurer toutes les variables d'environnement
2. Déployer les composants sur Azure
3. Accéder à l'application Streamlit

## Structure des Données

### Requête de recommandation
```json
{
  "user_id": 123,
  "n_recommendations": 5
}
```

### Réponse de l'API
```json
{
  "user_id": 123,
  "recommendations": [1234, 5678, 9012, 3456, 7890],
  "model": "ALS",
  "timestamp": "2024-01-15T10:30:00",
  "status": "success"
}
```

## Modèle ALS

### Paramètres optimisés
- **factors**: 100 (dimensions latentes)
- **regularization**: 0.01 (régularisation L2)
- **iterations**: 20 (nombre d'itérations)
- **alpha**: 40 (confiance pour données implicites)

### Performance
- Hit Rate@20: ~26%
- Precision@10: ~0.02
- Temps de réponse: < 100ms pour une recommandation

## Monitoring et Logs

### Application Insights (Azure)
- Configurer dans Azure Functions
- Métriques de performance
- Logs d'erreurs

### Logs locaux
- API: Logs niveau INFO
- Azure Function: Azure Monitor
- Streamlit: Console

## Sécurité

### Authentification
- Azure Function Key pour l'accès
- CORS configuré dans l'API
- HTTPS obligatoire en production

### Limites
- Max 50 recommandations par requête
- Timeout de 30 secondes
- Rate limiting recommandé

## Troubleshooting

### Erreurs communes

1. **"Modèle non disponible"**
   - Vérifier que le modèle est bien chargé
   - Vérifier le chemin MODEL_PATH

2. **"Timeout de la requête"**
   - Augmenter API_TIMEOUT
   - Vérifier la connectivité réseau

3. **"Utilisateur inconnu"**
   - Normal pour nouveaux utilisateurs
   - Utilise les recommandations par popularité

## Évolutions futures

1. **Cache Redis** pour les recommandations fréquentes
2. **Batch processing** pour plusieurs utilisateurs
3. **A/B testing** avec plusieurs modèles
4. **Mise à jour incrémentale** du modèle
5. **Métriques temps réel** dans l'interface