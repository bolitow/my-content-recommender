# 🚀 My Content - Application de Production

Structure organisée et clean pour le système de recommandation d'articles.

## 📁 Structure du Projet

```
production_app/
├── README.md                          # Ce fichier
│
├── frontend/                          # Application utilisateur
│   ├── app.py                         # Interface Streamlit V3 (enrichie)
│   ├── requirements.txt               # Dépendances Python frontend
│   └── .env.example                   # Template de configuration
│
├── backend/                           # Services backend
│   ├── azure_function/                # Azure Functions
│   │   ├── recommend_function/        # API de recommandation (V3 enrichie)
│   │   │   ├── __init__.py
│   │   │   └── function.json
│   │   ├── track_click_function/      # API de tracking des clics
│   │   │   ├── __init__.py
│   │   │   └── function.json
│   │   ├── recommender_als.py         # Module ALS Recommender
│   │   ├── requirements.txt           # Dépendances Azure Functions
│   │   └── host.json                  # Configuration Azure Functions
│   │
│   └── models/                        # Modèles ML
│       ├── als_model.pkl              # Modèle ALS entraîné (130 KB)
│       └── README.md                  # Documentation des modèles
│
├── scripts/                           # Scripts utilitaires
│   ├── add_article.py                 # Ajout manuel d'articles au CSV
│   ├── upload_data_to_azure.py        # Upload vers Azure Storage
│   ├── train_model.py                 # Réentraînement du modèle (TODO)
│   └── README.md                      # Documentation des scripts
│
├── docs/                              # Documentation
│   ├── DEPLOYMENT.md                  # Guide de déploiement complet
│   ├── ARCHITECTURE.md                # Architecture technique
│   ├── API.md                         # Documentation des endpoints
│   └── PREMIUM_MIGRATION.md           # Migration vers Azure Premium
│
└── config/                            # Configuration
    ├── .env.example                   # Template des variables d'environnement
    └── azure-deploy.yml               # Workflow GitHub Actions
```

## 🎯 Composants Principaux

### 1. Frontend (Streamlit)
- **Fichier** : `frontend/app.py`
- **Description** : Interface web moderne pour interagir avec le système
- **Fonctionnalités** :
  - Sélection utilisateur (liste, manuel, aléatoire)
  - Affichage des recommandations enrichies
  - Tracking des clics utilisateur
  - Affichage des métriques de diversité
  - Mode test (sans Azure)

### 2. Backend (Azure Functions)

#### 2.1 API de Recommandation (`recommend_function`)
- **Endpoint** : `POST /api/recommend`
- **Fonctionnalités** :
  - Charge le modèle ALS au démarrage
  - Charge les métadonnées articles (11 MB)
  - Charge les embeddings réduits (111 MB) - optionnel
  - Génère N recommandations personnalisées
  - Enrichit les réponses avec métadonnées complètes
  - Calcule la diversité des catégories

**Request** :
```json
{
  "user_id": 12345,
  "n_recommendations": 5
}
```

**Response** :
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
    "unique_categories": 4,
    "total_recommendations": 5
  },
  "metadata_loaded": true,
  "embeddings_loaded": true,
  "status": "success"
}
```

#### 2.2 API de Tracking (`track_click_function`)
- **Endpoint** : `POST /api/track_click`
- **Fonctionnalités** :
  - Capture les interactions utilisateur
  - Stocke dans Azure Blob Storage (format JSON Lines)
  - Fichiers quotidiens pour faciliter l'analyse

**Request** :
```json
{
  "user_id": 12345,
  "article_id": 160974,
  "interaction_type": "click",
  "timestamp": 1234567890000,
  "metadata": {
    "source": "recommendation",
    "rank": 1
  }
}
```

**Response** :
```json
{
  "status": "success",
  "message": "Clic enregistré avec succès",
  "data": {
    "user_id": 12345,
    "article_id": 160974,
    "tracked_at": "2025-10-17T14:30:00Z"
  }
}
```

### 3. Scripts Utilitaires

#### 3.1 `add_article.py`
Ajoute un nouvel article au CSV des métadonnées.

```bash
# Mode interactif
python scripts/add_article.py --interactive

# Mode ligne de commande
python scripts/add_article.py --category 281 --words 250
```

#### 3.2 `upload_data_to_azure.py`
Upload les données vers Azure Blob Storage.

```bash
# Uploader toutes les données
python scripts/upload_data_to_azure.py --all

# Uploader seulement le modèle
python scripts/upload_data_to_azure.py --model

# Lister les fichiers existants
python scripts/upload_data_to_azure.py --list
```

## 🚀 Quick Start

### Prérequis

1. **Python 3.9+** installé
2. **Azure Account** avec une subscription active
3. **Azure CLI** installé et configuré (`az login`)
4. **Git** pour le versioning et le déploiement

### Installation Locale

```bash
# 1. Installer les dépendances frontend
cd production_app/frontend
pip install -r requirements.txt

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs Azure

# 3. Lancer l'application
streamlit run app.py
```

### Déploiement Azure

Voir `docs/DEPLOYMENT.md` pour le guide complet.

**Résumé rapide** :

1. **Créer les ressources Azure** :
   - Resource Group
   - Storage Account (avec containers `models`, `data`, `clicks`)
   - Function App (Premium EP1 recommandé pour charger les embeddings)

2. **Uploader les données** :
   ```bash
   export AZURE_STORAGE_CONNECTION_STRING="..."
   python scripts/upload_data_to_azure.py --all
   ```

3. **Configurer les variables d'environnement** dans Azure Function App :
   - `STORAGE_CONNECTION_STRING`
   - `MODEL_CONTAINER_NAME=models`
   - `MODEL_BLOB_NAME=als_model.pkl`
   - `DATA_CONTAINER_NAME=data`
   - `ARTICLES_METADATA_BLOB=articles_metadata.csv`
   - `EMBEDDINGS_BLOB=articles_embeddings_reduced.pickle`
   - `CLICKS_CONTAINER_NAME=clicks`

4. **Déployer via GitHub Actions** :
   - Connecter le repo à Azure (Deployment Center)
   - Push vers `main` → déploiement automatique

5. **Tester** :
   ```bash
   curl -X POST https://YOUR_FUNCTION.azurewebsites.net/api/recommend \
     -H "Content-Type: application/json" \
     -d '{"user_id": 12345, "n_recommendations": 5}'
   ```

## 📊 Architecture Technique

```
┌─────────────────┐
│   Streamlit     │  ← Interface utilisateur web
│   (Frontend)    │
└────────┬────────┘
         │ HTTPS
         │
         ▼
┌─────────────────────────────────────┐
│     Azure Function App (Premium)     │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  recommend_function            │ │
│  │  - Modèle ALS (130 KB)         │ │
│  │  - Métadonnées (11 MB)         │ │
│  │  - Embeddings (111 MB)         │ │
│  │  → Recommandations enrichies   │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  track_click_function          │ │
│  │  → Capture interactions        │ │
│  └────────────────────────────────┘ │
└─────────┬────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│     Azure Blob Storage              │
│                                      │
│  📦 Container: models                │
│     - als_model.pkl                 │
│                                      │
│  📦 Container: data                  │
│     - articles_metadata.csv         │
│     - articles_embeddings_reduced.pickle │
│                                      │
│  📦 Container: clicks                │
│     - clicks_new_2025-10-17.jsonl   │
│     - clicks_new_2025-10-18.jsonl   │
└─────────────────────────────────────┘
```

## 💰 Coûts Estimés

### Configuration Actuelle (Premium EP1)

| Service | Plan | Coût Mensuel Estimé |
|---------|------|---------------------|
| Azure Functions | Premium EP1 (3.5 GB RAM, 1 vCPU) | ~60€ |
| Azure Storage | Standard LRS | ~1€ |
| Bandwidth | 15 GB sortant/mois | Gratuit |
| **TOTAL** | | **~61€/mois** |

### Configuration Alternative (Consumption)

Si vous n'avez pas besoin des embeddings (111 MB), vous pouvez rester en plan **Consumption** (gratuit).

**Limitations** :
- Pas assez de RAM pour charger les embeddings
- Cold start plus long (~5-10s)
- Timeout potentiel sur première requête

**Coût** : **0€/mois** (tier gratuit)

## 📝 To-Do & Améliorations Futures

### Court Terme
- [ ] Configurer MCP Azure pour déploiement automatisé
- [ ] Tester end-to-end avec données de production
- [ ] Ajouter Application Insights pour monitoring

### Moyen Terme
- [ ] Script de réentraînement automatique (`train_model.py`)
- [ ] Génération d'embeddings pour nouveaux articles
- [ ] Dashboard de métriques de performance
- [ ] A/B testing framework

### Long Terme
- [ ] Base de données relationnelle (Azure SQL/CosmosDB)
- [ ] API CRUD complète pour articles/users
- [ ] Système hybride (ALS + Content-Based)
- [ ] Réentraînement incrémental (online learning)
- [ ] Intégration deep learning models

## 🔗 Liens Utiles

- [Documentation Azure Functions](https://learn.microsoft.com/azure/azure-functions/)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Implicit Library (ALS)](https://implicit.readthedocs.io/)
- [Azure Blob Storage SDK](https://learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python)

## 📧 Support

Pour toute question ou problème :
1. Consulter `docs/DEPLOYMENT.md`
2. Vérifier les logs Azure (Function App → Log stream)
3. Tester en local avec mode test activé

---

**Version** : 3.0
**Dernière mise à jour** : Octobre 2025
**Status** : Production Ready ✅
