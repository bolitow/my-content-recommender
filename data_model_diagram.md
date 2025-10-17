# Modèle de Données - My Content Recommendation System

## Vue d'ensemble du système

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SYSTÈME DE RECOMMANDATION MY CONTENT                     │
│                                                                               │
│  📊 364,047 Articles  →  🔗 448,380 Interactions  →  👥 117,185 Utilisateurs │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Entité ARTICLES

**Table: `articles_metadata`**

| Attribut         | Type      | Description                                    | Exemple           |
|------------------|-----------|------------------------------------------------|-------------------|
| article_id (key) | int64     | Identifiant unique de l'article                | 160974            |
| category_id      | int64     | Catégorie de l'article (461 catégories)        | 281               |
| created_at_ts    | int64     | Timestamp de création (millisecondes)          | 1513144419000     |
| publisher_id     | int64     | Identifiant de l'éditeur (1 seul éditeur)     | 0                 |
| words_count      | int64     | Nombre de mots de l'article                    | 168               |

**Attributs dérivés (enrichissement):**
- `created_at`: datetime (conversion du timestamp)
- `year`: int (2010-2018)
- `month`: int (1-12)
- `day_of_week`: string (Monday-Sunday)
- `hour`: int (0-23)
- `word_count_category`: category (very_short, short, medium, long, very_long)
- `category_label`: string (ex: "Cat_281_Medium_Popular_Recent")

**Fichier associé:**
- `articles_embeddings.pickle`: Array numpy (364,047 × 250 dimensions)

**Statistiques clés:**
- 📈 Articles totaux: 364,047
- 📁 Catégories uniques: 461
- 📝 Longueur moyenne: 191 mots (médiane: 186 mots)
- 📅 Période: 2010-2018
- ⚠️ Articles avec 0 mots: 35 (0.01%)

---

## 2. Entité CLICS (Interactions)

**Table: `clicks_hour_*.csv` (385 fichiers)**

| Attribut              | Type          | Description                                  | Exemple           |
|-----------------------|---------------|----------------------------------------------|-------------------|
| 🔑 session_id         | int64         | Identifiant unique de session                | 162020            |
| 👤 user_id            | int64         | Identifiant de l'utilisateur                 | 5890              |
| 📄 click_article_id   | int64         | Article cliqué (FK → articles)               | 160974            |
| session_start         | int64         | Début de session (timestamp ms)              | 1513144419000     |
| click_timestamp       | int64         | Moment du clic (timestamp ms)                | 1513144419000     |
| session_size          | int64         | Nombre d'articles dans la session            | 5                 |
| click_environment     | int64         | Environnement de lecture (3 valeurs)         | 1                 |
| click_deviceGroup     | int64         | Type d'appareil (4 valeurs)                  | 2                 |
| click_os              | int64         | Système d'exploitation (8 valeurs)           | 3                 |
| click_country         | int64         | Pays de l'utilisateur (11 valeurs)           | 5                 |
| click_region          | int64         | Région géographique (28 valeurs)             | 12                |
| click_referrer_type   | int64         | Type de référent (7 valeurs)                 | 2                 |

**Attributs dérivés (enrichissement):**
- `session_start_dt`: datetime
- `click_timestamp_dt`: datetime
- `hour_of_day`: int (0-23)
- `day_of_week`: string
- `time_to_click`: float (secondes entre début session et clic)

**Statistiques clés:**
- 🔗 Interactions totales: 448,380 (après nettoyage: 412,634)
- 📊 Taux de rétention après nettoyage: 92.0%
- 👥 Utilisateurs uniques: 117,185
- 📄 Articles cliqués uniques: 9,386 (2.58% du catalogue)
- ⏱️ Temps médian avant clic: variable
- 📱 Sessions > 100 articles: 35,746

---

## 3. Entité UTILISATEURS (Profils dérivés)

**Table dérivée: `user_profiles`**

| Attribut              | Type          | Description                                  | Exemple           |
|-----------------------|---------------|----------------------------------------------|-------------------|
| 🔑 user_id            | int64         | Identifiant unique                           | 5890              |
| total_clicks          | int64         | Nombre total de clics                        | 182               |
| unique_articles       | int64         | Articles uniques consultés                   | 153               |
| sessions              | int64         | Nombre de sessions                           | 45                |
| avg_session_size      | float64       | Taille moyenne des sessions                  | 4.04              |
| first_click           | datetime      | Premier clic enregistré                      | 2017-01-15        |
| last_click            | datetime      | Dernier clic enregistré                      | 2018-02-28        |
| main_environment      | int64         | Environnement principal                      | 1                 |
| main_device           | int64         | Appareil principal                           | 2                 |
| country               | int64         | Pays                                         | 5                 |
| days_active           | int64         | Jours entre premier et dernier clic          | 409               |
| clicks_per_day        | float64       | Clics moyens par jour                        | 0.44              |
| article_diversity     | float64       | Ratio articles uniques / clics totaux        | 0.84              |
| sessions_per_day      | float64       | Sessions moyennes par jour                   | 0.11              |
| segment               | string        | Segment comportemental                       | Explorer_Actif    |

**Segments utilisateurs:**
- 🎯 **Explorer_Actif** (36.2%): Forte activité + grande diversité d'articles (≥70%)
- 🎯 **Explorer_Modéré** (63.6%): Activité moyenne + grande diversité
- 🎯 **Lecteur_Fidèle** (0.2%): Forte activité + faible diversité (articles récurrents)

**Statistiques clés:**
- 👥 Utilisateurs uniques: 117,185
- 📊 Clics moyens/utilisateur: 3.83
- 📚 Articles uniques moyens/utilisateur: 3.77
- 🎲 Diversité moyenne: 0.993 (très élevée)

---

## 4. Entité CATÉGORIES (Métadonnées)

**Table dérivée: `category_stats`**

| Attribut          | Type      | Description                                    | Exemple           |
|-------------------|-----------|------------------------------------------------|-------------------|
| 🔑 category_id    | int64     | Identifiant unique de catégorie                | 281               |
| nb_articles       | int64     | Nombre d'articles dans la catégorie            | 12,817            |
| mots_moy          | float64   | Longueur moyenne des articles (mots)           | 225.17            |
| mots_std          | float64   | Écart-type de la longueur                      | 65.31             |
| mots_min          | int64     | Article le plus court                          | 14                |
| mots_max          | int64     | Article le plus long                           | 1757              |
| date_debut        | datetime  | Premier article publié                         | 2011-12-01        |
| date_fin          | datetime  | Dernier article publié                         | 2018-02-28        |
| duree_jours       | int64     | Durée de vie de la catégorie (jours)           | 2281              |

**Labels de catégories:**
Format: `Cat_{id}_{content_type}_{popularity}_{age}`
- Content type: Short, Medium, Long
- Popularity: Niche, Standard, Popular
- Age: Archive, Active, Recent

**Top 5 catégories:**
1. **Cat 281**: 12,817 articles (Medium, Popular)
2. **Cat 375**: 10,005 articles (Medium, Popular)
3. **Cat 399**: 9,049 articles (Medium, Popular)
4. **Cat 412**: 8,648 articles (Medium, Popular)
5. **Cat 431**: 7,759 articles (Medium, Popular)

---

## 5. Relations entre entités

```
┌──────────────────┐
│    ARTICLES      │
│  (364,047)       │
│                  │
│ • article_id (PK)│─────┐
│ • category_id    │     │
│ • embeddings     │     │ 1:N
│ • metadata       │     │
└──────────────────┘     │
         │               │
         │ 1:N           │
         │               ▼
         │     ┌──────────────────┐
         │     │      CLICS       │
         └────▶│   (448,380)      │◀────┐
               │                  │     │
               │ • session_id (PK)│     │ N:1
               │ • click_article  │     │
               │ • user_id (FK)   │─────┤
               │ • timestamp      │     │
               │ • context        │     │
               └──────────────────┘     │
                                        │
                              ┌─────────────────┐
                              │  UTILISATEURS   │
                              │  (117,185)      │
                              │                 │
                              │ • user_id (PK)  │
                              │ • profil        │
                              │ • segment       │
                              │ • preferences   │
                              └─────────────────┘
```

---

## 6. Métriques système critiques

### Problème de Cold Start
```
┌─────────────────────────────────────────────────────────────┐
│  Articles avec clics:     9,386 (2.58%)    ████░░░░░░░░░░░ │
│  Articles sans clics: 354,661 (97.42%)     ░░░░░░░░░░░░░░░ │
└─────────────────────────────────────────────────────────────┘
```

### Concentration des interactions
- **Top 10% des articles** génèrent **95.9% des clics**
- **Sparsité de la matrice**: 99.8%
- **Coverage du catalogue**: 2.58%

### Patterns temporels
- 🕐 **Heure de pointe**: 22h
- 📅 **Jour le plus actif**: Lundi
- 📊 **Distribution**: Articles concentrés sur 2016-2018

---

## 7. Architecture des embeddings

**Format: `articles_embeddings.pickle`**

```
┌─────────────────────────────────────────────────────────────┐
│  Matrice d'embeddings: (364,047 articles × 250 dimensions)  │
│                                                              │
│  • Type: numpy array (float64)                              │
│  • Taille en mémoire: ~700 MB                               │
│  • Variance expliquée (PCA 50): 94.61%                      │
│  • Utilisé pour: similarité cosinus                         │
│                                                              │
│  Clustering (k-means):                                       │
│  • 10 clusters identifiés                                   │
│  • Distribution équilibrée (5.7% - 17.0% par cluster)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Qualité des données

### Problèmes identifiés et corrigés

| Problème                      | Avant     | Après     | Action                    |
|-------------------------------|-----------|-----------|---------------------------|
| Articles avec 0 mots          | 35        | 0         | Imputation médiane        |
| Articles < 10 mots            | 87        | 0         | Filtrage                  |
| Articles > 2000 mots          | 14        | 0         | Filtrage                  |
| Sessions > 100 articles       | 35,746    | 0         | Filtrage                  |
| Temps de clic négatif         | Variable  | 0         | Filtrage                  |
| Doublons                      | Variable  | 0         | Suppression               |
| **Taux de rétention articles**| -         | 100.0%    | -                         |
| **Taux de rétention clics**   | -         | 92.0%     | -                         |

---

## 9. Flux de données

```
DONNÉES BRUTES                  TRAITEMENT                    DONNÉES ENRICHIES
═══════════════                ══════════════                ══════════════════

articles_metadata.csv    →    Nettoyage                 →    articles_df
  (364,047 lignes)           • Filtrage outliers              + category_label
                             • Imputation                     + temporal features
                             • Validation                     + word_count_category

clicks_hour_*.csv        →    Agrégation                →    clicks_df
  (385 fichiers)             • Concaténation                  + session_start_dt
                             • Déduplication                  + time_to_click
                             • Validation FK                  + day/hour features

                         →    Dérivation                →    user_profiles
                             • Agrégation/user                + segment
                             • Calcul métriques               + behavioral metrics
                             • Segmentation                   + preferences

articles_embeddings      →    Réduction dimension       →    embeddings_2d
  (250D vectors)             • PCA (50D)                      + clusters
                             • t-SNE (2D)                     + similarities
                             • k-means clustering
```

---

## 10. Cas d'usage du modèle

### Pour le système de recommandation:
1. **User Profile Building**: Agrégation des embeddings des articles cliqués
2. **Similarity Computation**: Cosinus similarity entre user profile et articles
3. **Ranking**: Top-N articles les plus similaires au profil utilisateur
4. **Filtering**: Exclusion des articles déjà consultés

### Pour l'analyse:
1. **Segmentation utilisateurs**: Identification de personas
2. **Analyse de contenu**: Clustering d'articles similaires
3. **Patterns temporels**: Optimisation des moments de publication
4. **Cold start detection**: Identification d'articles sous-exposés

---

## Résumé des cardinalités

```
1 Article     ──────→  N Clics        (1:N)
1 Utilisateur ──────→  N Clics        (1:N)
1 Catégorie   ──────→  N Articles     (1:N)
1 Session     ──────→  N Clics        (1:N)
```

**Volumétrie totale:**
- 364,047 articles
- 448,380 interactions
- 117,185 utilisateurs
- 162,020 sessions
- 461 catégories