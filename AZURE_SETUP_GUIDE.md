# 🚀 Guide Complet de Configuration Azure

Guide étape par étape pour déployer le système de recommandation sur Azure avec GitHub Actions.

---

## 📋 Prérequis

- Compte Azure (inscription gratuite : https://azure.microsoft.com/fr-fr/free/)
- Compte GitHub
- Projet Git initialisé localement

**💰 Coût estimé : GRATUIT** avec le tier gratuit Azure (assez pour ce projet)

---

## 🏗️ Architecture Cible

```
┌──────────────┐         HTTPS          ┌─────────────────┐
│   Streamlit  │ ──────────────────────▶│ Azure Functions │
│   (Local)    │ ◀──────────────────────│  (Recommender)  │
└──────────────┘      JSON Response     └────────┬────────┘
                                                  │
                                                  │ Load model
                                                  ▼
                                        ┌─────────────────┐
                                        │  Azure Storage  │
                                        │  (Modèle ALS)   │
                                        └─────────────────┘
```

---

## 📝 ÉTAPE 1 : Créer un Resource Group

Le Resource Group est un conteneur logique pour toutes vos ressources Azure.

### Via le portail Azure (interface web)

1. **Connectez-vous** à https://portal.azure.com
2. Dans la barre de recherche en haut, tapez **"Resource groups"**
3. Cliquez sur **"+ Create"** (Créer)
4. Remplissez les informations :
   - **Subscription** : Sélectionnez votre abonnement (généralement "Free Trial" ou "Pay-As-You-Go")
   - **Resource group name** : `my-content-reco-rg`
   - **Region** : `West Europe` (ou France Central si disponible)
5. Cliquez sur **"Review + create"**, puis **"Create"**

✅ **Résultat** : Votre Resource Group est créé en ~10 secondes

---

## 📦 ÉTAPE 2 : Créer un Storage Account

Le Storage Account va stocker votre modèle ALS et les données nécessaires.

### Via le portail Azure

1. Dans la barre de recherche, tapez **"Storage accounts"**
2. Cliquez sur **"+ Create"**
3. Remplissez :
   - **Resource group** : Sélectionnez `my-content-reco-rg` (créé à l'étape 1)
   - **Storage account name** : `mycontentstorage` (doit être unique globalement, essayez `mycontentstorage` + vos initiales si déjà pris)
   - **Region** : `West Europe` (même que le Resource Group)
   - **Performance** : `Standard`
   - **Redundancy** : `LRS` (Locally Redundant Storage - le moins cher)
4. Cliquez sur **"Review"**, puis **"Create"**
5. ⏳ Attendez ~1-2 minutes que le Storage Account soit créé

### Créer un Container pour le modèle

1. Une fois créé, cliquez sur **"Go to resource"**
2. Dans le menu de gauche, cliquez sur **"Containers"** (sous "Data storage")
3. Cliquez sur **"+ Container"**
4. Nommez-le : `models`
5. **Public access level** : `Private`
6. Cliquez sur **"Create"**

✅ **Résultat** : Votre Storage est prêt à recevoir le modèle

---

## 🔑 ÉTAPE 3 : Récupérer la Connection String du Storage

Vous aurez besoin de cette clé pour que l'Azure Function puisse accéder au Storage.

1. Dans votre Storage Account, allez dans **"Access keys"** (menu de gauche, sous "Security + networking")
2. Cliquez sur **"Show keys"**
3. Copiez la **"Connection string"** de **key1**
4. **⚠️ IMPORTANT** : Gardez cette clé en sécurité, vous en aurez besoin plus tard !

💡 Format : `DefaultEndpointsProtocol=https;AccountName=mycontentstorage;AccountKey=...;EndpointSuffix=core.windows.net`

---

## ⚡ ÉTAPE 4 : Créer une Function App

C'est le serveur serverless qui exécutera vos recommandations.

### Via le portail Azure

1. Dans la barre de recherche, tapez **"Function App"**
2. Cliquez sur **"+ Create"**
3. **Onglet "Basics"** :
   - **Resource Group** : `my-content-reco-rg`
   - **Function App name** : `my-content-recommender` (doit être unique)
   - **Publish** : `Code`
   - **Runtime stack** : `Python`
   - **Version** : `3.9` ou `3.10` ou `3.11`
   - **Region** : `West Europe`
   - **Operating System** : `Linux`
   - **Plan type** : `Consumption (Serverless)` ✅ GRATUIT

4. **Onglet "Storage"** :
   - Sélectionnez le Storage Account créé précédemment (`mycontentstorage`)

5. **Onglet "Networking"** :
   - Laissez par défaut (Enable public access)

6. Cliquez sur **"Review + create"**, puis **"Create"**
7. ⏳ Attendez ~2-3 minutes que la Function App soit créée

✅ **Résultat** : Votre serveur serverless est prêt !

---

## 🔌 ÉTAPE 5 : Configurer les variables d'environnement de la Function

La Function a besoin de savoir où trouver le modèle dans le Storage.

1. Une fois la Function App créée, cliquez sur **"Go to resource"**
2. Dans le menu de gauche, cliquez sur **"Configuration"** (sous "Settings")
3. Cliquez sur **"+ New application setting"**
4. Ajoutez ces variables une par une :

| Name | Value | Description |
|------|-------|-------------|
| `STORAGE_CONNECTION_STRING` | La connection string copiée à l'étape 3 | Accès au Storage |
| `MODEL_CONTAINER_NAME` | `models` | Nom du container |
| `MODEL_BLOB_NAME` | `als_model.pkl` | Nom du fichier modèle |

5. Cliquez sur **"Save"** en haut
6. Cliquez sur **"Continue"** pour confirmer le redémarrage

✅ **Résultat** : La Function sait maintenant où chercher le modèle

---

## 🐙 ÉTAPE 6 : Configurer GitHub pour le déploiement automatique

On va connecter GitHub à Azure pour que chaque push déploie automatiquement.

### 6.1 - Créer un GitHub Repository

1. Allez sur https://github.com
2. Cliquez sur **"New repository"**
3. Nommez-le : `my-content-recommender`
4. Choisissez **Private** ou **Public**
5. Ne cochez PAS "Initialize with README" (vous avez déjà du code local)
6. Cliquez sur **"Create repository"**

### 6.2 - Lier votre projet local à GitHub

Ouvrez un terminal dans votre dossier projet et exécutez :

```bash
# Initialiser Git (si pas déjà fait)
git init

# Ajouter le remote GitHub
git remote add origin https://github.com/VOTRE_USERNAME/my-content-recommender.git

# Premier commit (si pas déjà fait)
git add .
git commit -m "Initial commit - My Content Recommender"

# Pusher sur GitHub
git branch -M main
git push -u origin main
```

### 6.3 - Obtenir les credentials Azure pour GitHub

Retournez dans le portail Azure :

1. Dans votre **Function App**, allez dans **"Deployment Center"** (menu de gauche)
2. Cliquez sur **"GitHub"** comme source
3. Cliquez sur **"Authorize"** pour connecter votre compte GitHub
4. Sélectionnez :
   - **Organization** : Votre compte GitHub
   - **Repository** : `my-content-recommender`
   - **Branch** : `main`
5. Azure va automatiquement créer un workflow GitHub Actions
6. Cliquez sur **"Save"**

✅ **Résultat** : GitHub Actions est configuré ! Chaque push déclenchera un déploiement automatique.

---

## 📤 ÉTAPE 7 : Uploader le modèle ALS vers Azure Storage

On va maintenant uploader le modèle entraîné vers le Storage.

### Option A : Via le portail Azure (simple)

1. Retournez dans votre **Storage Account** (`mycontentstorage`)
2. Cliquez sur **"Containers"**
3. Cliquez sur le container **"models"**
4. Cliquez sur **"Upload"** (en haut)
5. Sélectionnez le fichier `models/als_model.pkl` depuis votre ordinateur
6. Cliquez sur **"Upload"**

✅ Le modèle est maintenant dans le cloud !

### Option B : Via script Python (automatisé)

Utilisez le script `upload_to_azure.py` (que je vais créer à l'étape suivante).

---

## 🔗 ÉTAPE 8 : Récupérer l'URL de votre Azure Function

Une fois le déploiement terminé (ça peut prendre 5-10 minutes après le premier push) :

1. Dans votre **Function App**, cliquez sur **"Functions"** (menu de gauche)
2. Vous devriez voir votre function `recommend_function`
3. Cliquez dessus
4. Cliquez sur **"Get Function Url"**
5. Copiez l'URL (format : `https://my-content-recommender.azurewebsites.net/api/recommend?code=...`)

**💡 Astuce** : L'URL contient une clé d'API (`code=...`) qui sécurise l'accès.

---

## 🎨 ÉTAPE 9 : Configurer Streamlit pour utiliser Azure

Sur votre machine locale :

1. Créez un fichier `.env` à la racine du projet :

```env
AZURE_FUNCTION_URL=https://my-content-recommender.azurewebsites.net/api/recommend
AZURE_FUNCTION_KEY=votre_code_de_fonction
```

2. Ou définissez les variables d'environnement dans votre shell :

```bash
export AZURE_FUNCTION_URL="https://my-content-recommender.azurewebsites.net/api/recommend"
export AZURE_FUNCTION_KEY="votre_code"
```

3. Lancez Streamlit :

```bash
streamlit run app_v2.py
```

4. Décochez "Mode test" et testez une vraie recommandation !

---

## ✅ ÉTAPE 10 : Tester votre déploiement

### Test 1 : Vérifier que la Function répond

Dans un terminal :

```bash
curl -X POST "https://my-content-recommender.azurewebsites.net/api/recommend?code=VOTRE_CODE" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n_recommendations": 5}'
```

Vous devriez recevoir un JSON avec 5 recommandations.

### Test 2 : Via Streamlit

1. Lancez `streamlit run app_v2.py`
2. Sélectionnez un utilisateur
3. Décochez "Mode test"
4. Cliquez sur "Recommander"
5. ✨ Magie ! Vous recevez des recommandations depuis Azure !

---

## 🔍 ÉTAPE 11 : Monitoring et Logs

### Voir les logs de votre Function

1. Dans le portail Azure, allez dans votre **Function App**
2. Cliquez sur **"Log stream"** (menu de gauche, sous "Monitoring")
3. Vous verrez les logs en temps réel quand vous faites des requêtes

### Application Insights (monitoring avancé)

1. Dans votre Function App, cliquez sur **"Application Insights"**
2. Cliquez sur **"Turn on Application Insights"**
3. Cliquez sur **"Create new resource"** → `my-content-insights`
4. Attendez quelques minutes
5. Vous aurez accès à des dashboards de performance, erreurs, etc.

---

## 💰 Estimation des coûts (Tier Gratuit)

Avec le tier gratuit Azure, vous avez :

| Service | Limite gratuite | Suffisant pour |
|---------|----------------|----------------|
| Azure Functions | 1 million d'exécutions/mois | ✅ ~33K requêtes/jour |
| Storage Account | 5 GB | ✅ Largement suffisant (modèle = 130 KB) |
| Bandwidth sortant | 15 GB/mois | ✅ ~500K recommandations/mois |

**Total : 0€/mois** pour usage modéré (dev/démo)

---

## 🆘 Troubleshooting

### Problème : "Function not found"
- ✅ Vérifiez que le déploiement GitHub Actions est terminé (onglet "Actions" sur GitHub)
- ✅ Attendez 5-10 minutes après le premier déploiement

### Problème : "Model not found" ou "Storage error"
- ✅ Vérifiez que `STORAGE_CONNECTION_STRING` est bien configurée
- ✅ Vérifiez que le fichier `als_model.pkl` est bien uploadé dans le container `models`
- ✅ Vérifiez les logs dans "Log stream"

### Problème : "Timeout"
- ✅ Premier appel peut être lent (cold start ~5-10s)
- ✅ Augmentez le timeout de la Function à 60s (Configuration → Function timeout)

### Problème : GitHub Actions échoue
- ✅ Vérifiez que Python est bien 3.9/3.10/3.11 dans le workflow
- ✅ Vérifiez que toutes les dépendances sont dans `azure_function/requirements.txt`

---

## 🎓 Ressources Utiles

- **Documentation Azure Functions** : https://learn.microsoft.com/fr-fr/azure/azure-functions/
- **GitHub Actions pour Azure** : https://github.com/Azure/actions
- **Azure Free Tier** : https://azure.microsoft.com/fr-fr/pricing/free-services/

---

## 🚀 Prochaines étapes

Une fois que tout fonctionne :

1. **✅ Sécuriser** : Restreindre les CORS, ajouter authentication
2. **✅ Optimiser** : Mettre en cache les recommandations fréquentes (Redis)
3. **✅ Monitorer** : Configurer des alertes sur Application Insights
4. **✅ Scale** : Si beaucoup de trafic, passer à un plan Premium (payant)

---

**🎉 Félicitations ! Votre système de recommandation est en production sur Azure !**
