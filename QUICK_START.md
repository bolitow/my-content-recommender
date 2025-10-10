# 🚀 Quick Start - My Content Recommender

Guide rapide pour déployer et tester le système de recommandation.

---

## 📦 Fichiers créés

Voici les nouveaux fichiers et leurs rôles :

| Fichier | Description |
|---------|-------------|
| `app_v2.py` | **Interface Streamlit modernisée** avec design épuré |
| `reduce_embeddings.py` | Script de réduction PCA des embeddings (250→80 dim) |
| `upload_to_azure.py` | Script d'upload du modèle vers Azure Storage |
| `AZURE_SETUP_GUIDE.md` | **📖 Guide complet pas à pas pour Azure** |
| `.github/workflows/azure-deploy.yml` | Déploiement automatique via GitHub Actions |
| `azure_function/recommend_function/__init__.py` | Azure Function V2 avec chargement depuis Storage |

---

## 🎯 Démarrage rapide en 5 étapes

### 1️⃣ Tester l'interface locale (mode test)

```bash
# Lancer Streamlit
streamlit run app_v2.py

# Dans l'interface:
# - Sélectionner un user ID
# - Cocher "Mode test"
# - Cliquer sur "Recommander"
```

✅ Vous devriez voir 5 recommandations simulées avec un beau design !

---

### 2️⃣ Configurer Azure (une seule fois)

**Suivez le guide complet** : `AZURE_SETUP_GUIDE.md`

Résumé des étapes principales :
1. Créer Resource Group
2. Créer Storage Account → Container "models"
3. Créer Function App (Python, Consumption plan)
4. Configurer variables d'environnement
5. Connecter GitHub

⏱️ Temps estimé : **15-20 minutes**

---

### 3️⃣ Uploader le modèle vers Azure

```bash
# Installer dépendance
pip install azure-storage-blob python-dotenv

# Configurer la connection string
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=..."

# Uploader
python upload_to_azure.py
```

✅ Le modèle ALS (130 KB) est maintenant dans Azure !

---

### 4️⃣ Déployer l'Azure Function

```bash
# Initialiser Git (si pas déjà fait)
git init
git add .
git commit -m "Deploy recommendation system"

# Créer repo GitHub et pusher
git remote add origin https://github.com/VOTRE_USERNAME/my-content-recommender.git
git push -u origin main
```

✅ GitHub Actions déploie automatiquement (5-10 minutes) !

---

### 5️⃣ Tester en production

```bash
# Configurer l'URL Azure Function
export AZURE_FUNCTION_URL="https://my-content-recommender.azurewebsites.net/api/recommend"

# Lancer Streamlit
streamlit run app_v2.py

# Dans l'interface:
# - Sélectionner un user ID
# - DÉCOCHER "Mode test"
# - Cliquer sur "Recommander"
```

✅ Recommandations en temps réel depuis Azure ! 🎉

---

## 🔧 Commandes utiles

### Voir les logs Azure Function

```bash
# Via Azure Portal
# Function App → Log stream
```

### Lister les fichiers dans Azure Storage

```bash
python upload_to_azure.py --list
```

### Re-uploader le modèle

```bash
python upload_to_azure.py
```

### Tester l'API directement

```bash
curl -X POST "https://my-content-recommender.azurewebsites.net/api/recommend" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n_recommendations": 5}'
```

---

## 📊 Architecture déployée

```
┌──────────────┐         HTTPS          ┌─────────────────┐
│   Streamlit  │ ──────────────────────▶│ Azure Functions │
│  (app_v2.py) │ ◀──────────────────────│    (Python)     │
└──────────────┘      JSON (5 articles) └────────┬────────┘
                                                  │
                                                  │ Load at startup
                                                  ▼
                                        ┌─────────────────┐
                                        │  Azure Storage  │
                                        │ als_model.pkl   │
                                        │    (130 KB)     │
                                        └─────────────────┘
```

---

## 💡 Prochaines étapes (optionnel)

### V2 - Système hybride avec embeddings

1. Utiliser `data/articles_embeddings_reduced.pickle` (111 MB)
2. Implémenter re-ranking :
   - ALS génère 20 candidats
   - Re-ranking avec similarité embeddings
   - Retourner top 5 diversifiés

### Performance

- Ajouter cache Redis pour recommandations fréquentes
- Monitoring avec Application Insights
- Optimiser cold start

---

## 🆘 Problèmes courants

**Streamlit ne démarre pas ?**
```bash
pip install streamlit requests pandas
```

**Azure Function ne répond pas ?**
- Vérifier que le déploiement GitHub Actions est terminé (onglet Actions)
- Attendre 5-10 min après le 1er déploiement
- Vérifier les logs dans Azure Portal

**Modèle non trouvé ?**
- Vérifier que `STORAGE_CONNECTION_STRING` est configurée
- Vérifier que le fichier est bien uploadé : `python upload_to_azure.py --list`

---

## 📚 Documentation complète

- **Configuration Azure** : `AZURE_SETUP_GUIDE.md` (guide détaillé avec captures)
- **API Documentation** : `README_application.md`
- **Collaborative Filtering** : `README_collaborative_filtering.md`

---

**🎉 Bon déploiement !**
