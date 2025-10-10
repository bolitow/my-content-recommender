# 🇫🇷 Guide Azure en Français - Création Function App

## 📌 C'est quoi une "Function App" ?

**Function App** = **Application de Fonction** en français dans Azure

C'est un **serveur serverless** qui exécute ton code Python sans que tu aies à gérer l'infrastructure. Tu paies seulement quand ton code s'exécute (et c'est gratuit jusqu'à 1 million d'exécutions/mois).

**Analogie :** C'est comme AWS Lambda, Google Cloud Functions, mais version Microsoft.

---

## 🔍 Où trouver "Function App" dans Azure Portal français ?

Dans le portail Azure en français, ça peut s'appeler :
- **"Application de fonction"** (traduction officielle)
- **"Function App"** (parfois non traduit)
- **"Applications de fonction"** (au pluriel)

---

## 📝 ÉTAPE PAR ÉTAPE : Créer une Function App (Interface Française)

### Étape 1 : Ouvrir le portail Azure

1. Va sur **https://portal.azure.com**
2. Connecte-toi avec ton compte Microsoft

### Étape 2 : Chercher "Function App"

#### Option A : Via la barre de recherche (RECOMMANDÉ)

1. En haut de la page, tu vois une **barre de recherche** avec une icône de loupe 🔍
2. Tape dedans : **"function"** ou **"fonction"**
3. Tu devrais voir apparaître dans les suggestions :
   - **"Applications de fonction"** ✅ ← C'EST ÇA !
   - ou **"Function App"** (si pas traduit)
4. Clique dessus

#### Option B : Via le menu

1. Clique sur le menu hamburger **☰** (3 barres) en haut à gauche
2. Clique sur **"Créer une ressource"** (ou **"Create a resource"**)
3. Dans la catégorie, cherche **"Calcul"** ou **"Compute"**
4. Tu verras **"Application de fonction"** ou **"Function App"**

#### Option C : Via "Tous les services"

1. Dans le menu de gauche, clique sur **"Tous les services"** (ou **"All services"**)
2. Cherche la catégorie **"Calcul"** ou **"Compute"**
3. Trouve **"Applications de fonction"**

---

### Étape 3 : Créer une nouvelle Function App

1. Une fois sur la page **"Applications de fonction"**, tu verras :
   - Un bouton **"+ Créer"** en haut à gauche
   - ou **"+ Ajouter"**
   - ou **"+ Create"**
2. **Clique sur ce bouton**

---

### Étape 4 : Remplir le formulaire (Onglet "Informations de base")

Tu vas voir un formulaire avec plusieurs champs. Voici ce qu'il faut mettre :

#### 🔹 **Détails du projet**

| Champ (Français) | Valeur à mettre | Explication |
|------------------|-----------------|-------------|
| **Abonnement** | Sélectionne ton abonnement | Probablement "Essai gratuit" ou "Pay-As-You-Go" |
| **Groupe de ressources** | `my-content-reco-rg` | Celui créé à l'étape précédente |

💡 Si tu vois un lien **"Créer nouveau"** à côté du groupe de ressources, tu peux aussi créer le groupe maintenant.

#### 🔹 **Détails de l'instance**

| Champ (Français) | Valeur à mettre | Explication |
|------------------|-----------------|-------------|
| **Nom de l'application de fonction** | `my-content-recommender` | Nom unique (si déjà pris, essaie `my-content-reco-2024`) |
| **Publier** | **Code** ✅ | PAS "Conteneur Docker" |
| **Pile d'exécution** | **Python** | Le langage qu'on utilise |
| **Version** | **3.9** ou **3.10** ou **3.11** | N'importe laquelle de ces 3 versions fonctionne |
| **Région** | **Europe Ouest** (West Europe) ou **France Centre** | Choisis la plus proche |

#### 🔹 **Système d'exploitation**

| Champ | Valeur |
|-------|--------|
| **Système d'exploitation** | **Linux** ✅ |

💡 Linux est moins cher et recommandé pour Python

#### 🔹 **Type de plan** (TRÈS IMPORTANT !)

| Champ (Français) | Valeur à mettre | Explication |
|------------------|-----------------|-------------|
| **Type de plan** ou **Plan d'hébergement** | **Consommation (serverless)** ✅ | C'est le mode GRATUIT ! |

**⚠️ ATTENTION :**
- Ne choisis PAS "Premium"
- Ne choisis PAS "Plan App Service"
- Choisis bien **"Consommation"** ou **"Consumption"** en anglais

---

### Étape 5 : Onglet "Stockage"

1. Clique sur **"Suivant : Stockage >"** en bas
2. Tu verras :

| Champ | Valeur |
|-------|--------|
| **Compte de stockage** | Sélectionne `mycontentstorage` (celui créé avant) |

💡 Si tu n'as pas encore créé le Storage Account, tu peux cliquer sur **"Créer nouveau"**

---

### Étape 6 : Onglet "Mise en réseau"

1. Clique sur **"Suivant : Mise en réseau >"**
2. Laisse les paramètres par défaut :
   - **Activer l'accès public** : ✅ OUI

---

### Étape 7 : Onglet "Surveillance" (Monitoring)

1. Clique sur **"Suivant : Surveillance >"**
2. Tu peux :
   - Laisser **Application Insights** activé (recommandé pour voir les logs)
   - Ou le désactiver pour économiser (optionnel, mais utile)

---

### Étape 8 : Vérifier et créer

1. Clique sur **"Vérifier + créer"** (ou **"Review + create"**) en bas
2. Azure va valider ta configuration
3. Tu verras un résumé avec :
   - Coût estimé : **0,00 €/mois** (si bien en mode Consommation)
4. Clique sur **"Créer"** (ou **"Create"**)

---

### Étape 9 : Attendre la création

- ⏳ Ça prend environ **2-3 minutes**
- Tu verras une notification "Le déploiement est en cours..."
- Une fois terminé, clique sur **"Accéder à la ressource"**

---

## ✅ Vérification : Tu as bien créé ta Function App

Tu devrais maintenant voir une page avec :

- **Nom** : `my-content-recommender`
- **Type** : Application de fonction
- **État** : En cours d'exécution (Running)
- **URL** : `https://my-content-recommender.azurewebsites.net`

---

## 🔧 Étape suivante : Configurer les variables d'environnement

Maintenant que ta Function App est créée, il faut lui dire où trouver le modèle.

### Dans le menu de gauche de ta Function App

1. Cherche **"Configuration"** (sous "Paramètres" ou "Settings")
2. Clique dessus
3. Tu verras des onglets : **"Paramètres d'application"**, **"Paramètres généraux"**, etc.
4. Reste sur **"Paramètres d'application"** (premier onglet)

### Ajouter les variables

1. Clique sur **"+ Nouveau paramètre d'application"** (ou **"+ New application setting"**)
2. Ajoute ces 3 variables **une par une** :

#### Variable 1

| Champ | Valeur |
|-------|--------|
| **Nom** | `STORAGE_CONNECTION_STRING` |
| **Valeur** | Colle ici ta connection string du Storage Account |

💡 Pour récupérer la connection string :
- Va dans ton **Storage Account** (`mycontentstorage`)
- Menu de gauche → **"Clés d'accès"** (ou **"Access keys"**)
- Clique sur **"Afficher les clés"**
- Copie la **"Chaîne de connexion"** de **key1**

#### Variable 2

| Champ | Valeur |
|-------|--------|
| **Nom** | `MODEL_CONTAINER_NAME` |
| **Valeur** | `models` |

#### Variable 3

| Champ | Valeur |
|-------|--------|
| **Nom** | `MODEL_BLOB_NAME` |
| **Valeur** | `als_model.pkl` |

### Sauvegarder

1. Après avoir ajouté les 3 variables, clique sur **"Enregistrer"** en haut
2. Un message te demandera de confirmer le redémarrage → Clique **"Continuer"**

---

## 🎯 Récapitulatif : Ce que tu as créé

```
┌─────────────────────────────┐
│  Application de fonction    │
│  (Function App)             │
├─────────────────────────────┤
│  Nom: my-content-recommender│
│  Type: Consommation         │ ← Gratuit !
│  Runtime: Python 3.10       │
│  OS: Linux                  │
│  Région: Europe Ouest       │
└─────────────────────────────┘
        │
        │ Utilise
        ▼
┌─────────────────────────────┐
│  Compte de stockage         │
│  (Storage Account)          │
├─────────────────────────────┤
│  Nom: mycontentstorage      │
│  Container: models          │
│  Fichier: als_model.pkl     │
└─────────────────────────────┘
```

---

## ❓ FAQ - Questions fréquentes

### Q1 : Je ne trouve vraiment pas "Function App" / "Application de fonction"

**Astuce :** Utilise la barre de recherche en haut et tape exactement :

```
function
```

Même si l'interface est en français, le mot "function" fonctionne toujours.

### Q2 : Le nom `my-content-recommender` est déjà pris

**Solution :** Ajoute tes initiales ou l'année :

```
my-content-recommender-jd
my-content-recommender-2024
mycontent-reco-prod
```

### Q3 : Je ne vois pas "Consommation" dans les plans

**Noms possibles :**
- "Consommation (serverless)"
- "Consumption"
- "Plan de consommation"
- "Serverless"

C'est celui qui dit **"Paiement à l'utilisation"** et **"0,00 €"**.

### Q4 : Ça me demande une carte bancaire

- C'est normal pour l'essai gratuit Azure
- Tu ne seras PAS débité si tu restes dans les limites gratuites
- Le plan Consommation offre 1 million d'exécutions gratuites/mois

### Q5 : C'est quoi la différence avec un "App Service" ?

| Type | Description | Coût |
|------|-------------|------|
| **Function App (Consommation)** | Serverless, paiement à l'utilisation | Gratuit jusqu'à 1M exécutions |
| **App Service** | Serveur toujours actif | ~13€/mois minimum |

Pour notre projet, **Function App** suffit largement !

---

## 🎉 C'est fait ?

Si tu as réussi à créer ta Function App, tu peux passer à l'étape suivante :

1. ✅ Function App créée
2. ✅ Variables d'environnement configurées
3. ➡️ **Prochaine étape :** Connecter GitHub pour le déploiement automatique

Voir section **"ÉTAPE 6 : Configurer GitHub"** dans `AZURE_SETUP_GUIDE.md`

---

## 🆘 Besoin d'aide ?

Si tu bloques encore, dis-moi exactement :
1. Ce que tu vois dans ton interface Azure
2. À quelle étape tu bloques
3. Envoie une capture d'écran si possible

Je t'aiderai étape par étape ! 👍
