# 🚀 Migration vers Azure Functions Premium

## Étape 1 : Créer un Plan Premium

### Dans Azure Portal :

1. **Barre de recherche** → Tape **"Plans App Service"** ou **"App Service Plans"**
2. Clique sur **"+ Créer"** ou **"+ Create"**

### Configuration du Plan :

| Champ | Valeur |
|-------|--------|
| **Abonnement** | Ton abonnement Azure |
| **Groupe de ressources** | `my-content-reco-rg` (le même) |
| **Nom** | `my-content-premium-plan` |
| **Système d'exploitation** | **Linux** ✅ |
| **Région** | **France Central** (même que ta Function) |
| **Plan de tarification** | **Elastic Premium EP1** |

#### 💡 Détails du plan EP1 :
- **210 ACU** (Azure Compute Units)
- **3.5 GB RAM**
- **1 vCPU**
- **250 GB stockage**
- **Coût** : ~60€/mois

3. Clique sur **"Vérifier + créer"** → **"Créer"**
4. ⏳ Attends 1-2 minutes

---

## Étape 2 : Migrer la Function App vers le Plan Premium

### ⚠️ IMPORTANT : Sauvegarde les variables d'environnement

Avant de migrer, **note tes 3 variables** (on va les remettre après) :
- `STORAGE_CONNECTION_STRING`
- `MODEL_CONTAINER_NAME`
- `MODEL_BLOB_NAME`

### Migration :

1. **Retourne dans ta Function App** : `my-content-recommender`
2. **Menu de gauche** → **"Scale up (App Service Plan)"** ou **"Monter en puissance"**
3. Tu verras les différents plans disponibles
4. **Sélectionne** : **"Elastic Premium"** → **EP1**
5. Clique sur **"Appliquer"** ou **"Apply"**
6. ⏳ **Attends 5-10 minutes** que la migration se fasse

💡 **Alternative si "Scale up" ne fonctionne pas** :

1. Va dans **"Configuration"** de ta Function App
2. **Onglet "Paramètres généraux"**
3. **Plan App Service** : Change pour `my-content-premium-plan`
4. Clique sur **"Enregistrer"**

---

## Étape 3 : Vérifier les variables d'environnement

Après la migration, vérifie que tes variables sont toujours là :

1. **Function App** → **"Configuration"**
2. **Paramètres d'application**
3. Vérifie que tu as bien :
   - ✅ `STORAGE_CONNECTION_STRING`
   - ✅ `MODEL_CONTAINER_NAME`
   - ✅ `MODEL_BLOB_NAME`

Si elles ont disparu (rare), **réajoute-les**.

---

## Étape 4 : Restaurer la version complète de la fonction

Maintenant que tu es en Premium, on peut remettre la version avec le modèle ML complet.

### Sur ton ordinateur :

```bash
cd /Users/bolito/Documents/Projet10/azure_function/recommend_function

# Restaurer la version complète
cp __init___full.py __init__.py

# Commit et push
cd ../..
git add azure_function/recommend_function/__init__.py
git commit -m "Restore full function with ML model loading (Premium plan)"
git push
```

---

## Étape 5 : Attendre le déploiement et tester

1. ⏳ **Attends 3-5 minutes** que GitHub Actions redéploie
2. **Va sur GitHub** → Onglet **"Actions"** → Vérifie que le workflow est ✅

3. **Teste avec Python** :

```bash
python test_azure_function.py
```

4. **Tu devrais voir** :
   - Le modèle se charger (peut prendre 10-20s la première fois)
   - De vraies recommandations ALS

---

## Étape 6 : Vérifier les logs Azure

1. **Function App** → **"Flux de journaux"** (Log stream)
2. **Lance un test** : `python test_azure_function.py`
3. **Tu devrais voir dans les logs** :
   ```
   🚀 Pré-chargement du modèle au démarrage...
   Chargement du modèle depuis Azure Blob Storage...
   Téléchargement de models/als_model.pkl...
   ✅ Modèle chargé avec succès!
      - 7982 utilisateurs
      - 364047 articles
   ```

---

## 🎉 C'est fait !

Tu as maintenant :
- ✅ Function App sur **Elastic Premium EP1**
- ✅ Support complet des bibliothèques ML
- ✅ Modèle ALS chargé depuis Azure Storage
- ✅ Recommandations en temps réel

---

## 💰 Estimation des coûts

| Service | Plan | Coût estimé |
|---------|------|-------------|
| Function App | Elastic Premium EP1 | ~60€/mois |
| Storage Account | Standard (LRS) | ~1€/mois |
| Bandwidth | 15 GB sortant/mois | Gratuit |
| **TOTAL** | | **~61€/mois** |

💡 **Astuce d'économie** : Tu peux arrêter/démarrer le plan quand tu ne l'utilises pas :
- **Arrêter** : Function App → Clic sur "Arrêter" (tu ne paies pas)
- **Démarrer** : Function App → Clic sur "Démarrer"

---

## 🆘 Problèmes possibles

### "Je ne peux pas migrer / Scale up est grisé"

**Solution** : Supprime l'ancienne Function App et recrée-en une nouvelle directement en Premium :

1. Supprime `my-content-recommender` (sauvegarde les variables avant!)
2. Crée une nouvelle Function App :
   - Nom : `my-content-recommender` (ou nouveau nom)
   - **Plan** : Choisis le `my-content-premium-plan` créé
   - Runtime : Python 3.11, Linux
3. Reconfigure les variables d'environnement
4. Reconnecte GitHub (Deployment Center)

### "GitHub Actions échoue encore"

Vérifie dans les logs que les dépendances s'installent bien :
```
Installing numpy...
Installing scipy...
Installing implicit...
```

Si ça échoue, c'est peut-être qu'il faut plus de temps. Augmente le timeout dans le workflow.

---

Bonne migration ! 🚀
