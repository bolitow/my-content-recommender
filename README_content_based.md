# Système de Recommandation Content-Based

## Vue d'ensemble

Ce projet implémente trois approches de filtrage basé sur le contenu (Content-Based Filtering) pour recommander des articles d'actualité. Chaque approche utilise des stratégies différentes pour résoudre le défi de la recommandation d'articles dans un contexte d'actualités.

## Architecture des Approches

### 🎯 Approche 1: Popularité Temporelle Avancée

**Principe:** Combine la popularité des articles avec une décroissance temporelle pour favoriser le contenu récent tout en maintenant la diversité.

**Fonctionnement:**
1. **Pondération temporelle:** Chaque clic reçoit un poids qui décroît exponentiellement avec l'âge (factor = 0.95^jours)
2. **Score composite:** Agrégation de 4 métriques:
   - Clics pondérés temporellement (40%)
   - Score d'engagement basé sur le temps avant clic (30%)
   - Score de diversité (ratio utilisateurs uniques/clics totaux) (20%)
   - Sessions uniques (10%)
3. **Diversification:** Limite le nombre d'articles par catégorie pour éviter la sur-concentration

**Formulation mathématique:**

Variables :
- `t_i` : Timestamp du clic i
- `t_max` : Timestamp le plus récent dans les données
- `d_i` : Nombre de jours écoulés depuis le clic i = `(t_max - t_i) / 86400`
- `α` : Facteur de décroissance temporelle (temporal_decay = 0.95)
- `β` : Boost de fraîcheur (freshness_boost = 0.3)
- `w_i` : Poids temporel du clic i
- `τ_a` : Temps moyen avant clic pour l'article a
- `τ_max` : Temps maximum avant clic dans le dataset
- `U_a` : Ensemble des utilisateurs uniques ayant cliqué sur l'article a
- `C_a` : Nombre total de clics sur l'article a
- `S_a` : Nombre de sessions uniques contenant l'article a
- `age_a` : Âge de l'article a en jours

Équations :
```
w_i = α^(d_i)                                    # Poids temporel du clic i
W_a = Σ w_i pour tout clic i sur article a      # Clics pondérés totaux

E_a = 1 - (τ_a / τ_max)                         # Score d'engagement
D_a = |U_a| / C_a                               # Score de diversité
F_a = 1 / (1 + age_a / 7)                       # Facteur de fraîcheur

Score_base(a) = 0.4 × (W_a / max(W)) +          # Popularité pondérée normalisée
                0.3 × E_a +                      # Engagement
                0.2 × (D_a / max(D)) +          # Diversité normalisée
                0.1 × (S_a / max(S))            # Sessions normalisées

Score_final(a) = Score_base(a) × (1 + β × F_a)  # Score avec boost de fraîcheur
```

**Avantages:**
- Adapté aux nouveaux utilisateurs (cold start)
- Favorise naturellement le contenu frais et pertinent
- Calcul rapide et scalable

**Limitations:**
- Pas de personnalisation individuelle
- Peut sur-représenter les articles viraux

---

### 🧠 Approche 2: Similarité Multi-Facettes

**Principe:** Construit un profil utilisateur riche combinant embeddings sémantiques, comportement et préférences catégorielles.

**Fonctionnement:**

1. **Construction du profil utilisateur:**
   - **Embedding Profile:** Moyenne pondérée des embeddings des articles cliqués
     - Pondération temporelle: articles récents ont plus de poids
     - Fenêtre glissante: derniers 30 jours par défaut
   
   - **Behavioral Profile:** Statistiques comportementales
     - Temps moyen avant clic
     - Nombre de sessions
     - Diversité des catégories consultées
   
   - **Category Profile:** Distribution des clics par catégorie (vecteur normalisé)

2. **Matrice de co-occurrence:**
   - Capture les articles souvent consultés ensemble dans une session
   - Fenêtre de co-occurrence: 5 articles consécutifs
   - Utilisé comme signal additionnel de pertinence

3. **Scoring multi-dimensionnel:**

Variables :
- `u` : Vecteur profil utilisateur (embedding)
- `a` : Vecteur article (embedding)  
- `P_u` : Profil utilisateur multi-facettes
- `A_clicked` : Ensemble des articles cliqués par l'utilisateur
- `w_j` : Poids temporel de l'article j dans l'historique
- `e_j` : Embedding de l'article j
- `cat_u` : Vecteur de distribution des catégories pour l'utilisateur
- `cat_a` : Catégorie de l'article a
- `τ_u` : Temps moyen avant clic de l'utilisateur
- `τ_a` : Temps moyen avant clic de l'article a
- `M_cooc` : Matrice de co-occurrence des articles
- `R_u` : Ensemble des articles récents de l'utilisateur (10 derniers)

Équations :
```
# Profil utilisateur (moyenne pondérée temporellement)
u = Σ(w_j × e_j) / Σ(w_j) pour j ∈ A_clicked
où w_j = 1 / (1 + days_since_click_j)

# Similarité cosinus
sim_embedding(u, a) = (u · a) / (||u|| × ||a||)

# Similarité catégorielle  
sim_category(u, a) = cat_u[cat_a] si cat_a existe, 0 sinon

# Similarité comportementale
sim_behavior(u, a) = max(0, 1 - |τ_u - τ_a| / max(τ_u, τ_a))

# Bonus de co-occurrence
bonus_cooc(u, a) = min(0.1, Σ(M_cooc[a][r] pour r ∈ R_u) / max(M_cooc))

# Score final
Score(a|u) = 0.5 × sim_embedding(u, a) +
             0.2 × sim_category(u, a) +
             0.2 × sim_behavior(u, a) +
             0.1 × bonus_cooc(u, a)
```

4. **Exploration/Exploitation:**
   - 80% des recommandations: articles avec les meilleurs scores
   - 20% des recommandations: articles divers pour découverte

**Algorithme de similarité cosinus:**
```
cosine_sim(u, a) = (u · a) / (||u|| * ||a||)
```
Où u est le vecteur profil utilisateur et a le vecteur article.

**Avantages:**
- Personnalisation fine basée sur le comportement réel
- Capture les relations complexes entre articles
- Équilibre entre pertinence et découverte

**Limitations:**
- Nécessite un historique utilisateur substantiel
- Coût computationnel plus élevé
- Cold start problem pour nouveaux utilisateurs

---

### ⚡ Approche 3: Système Hybride

**Principe:** Combine popularité et similarité pour optimiser le compromis entre qualité garantie et personnalisation.

**Fonctionnement:**

1. **Sélection des candidats:**
   - Prend les TOP 50 articles les plus populaires non vus
   - Assure une base de qualité minimum

2. **Scoring hybride:**

Variables :
- `α` : Poids de la popularité (popularity_weight = 0.3)
- `P_a` : Score de popularité de l'article a
- `S(a|u)` : Score de similarité de l'article a pour l'utilisateur u
- `C_a` : Nombre de clics sur l'article a
- `C_max` : Nombre maximum de clics sur un article
- `u_profile` : Profil d'embedding de l'utilisateur
- `a_emb` : Embedding de l'article a
- `TOP_k` : Les k articles les plus populaires non vus

Équations :
```
# Popularité normalisée
P_a = C_a / C_max

# Similarité cosinus
S(a|u) = (u_profile · a_emb) / (||u_profile|| × ||a_emb||)

# Profil utilisateur (moyenne pondérée par fréquence)
u_profile = Σ(count_j × e_j) / Σ(count_j) pour j ∈ articles_cliqués
où count_j = nombre de clics sur l'article j par l'utilisateur

# Score hybride
H(a|u) = (1 - α) × S(a|u) + α × P_a
       = 0.7 × S(a|u) + 0.3 × P_a

# Sélection finale
Recommandations = argmax_a∈TOP_50 H(a|u) pour les n premiers
```

3. **Fallback intelligent:**
   - Si nouvel utilisateur → recommandations par popularité pure
   - Si utilisateur actif → scoring hybride complet

**Processus de décision:**
```
if user_profile exists:
    candidates = top_popular_unseen_articles(50)
    scores = hybrid_scoring(candidates, user_profile)
    return top_n(scores)
else:
    return top_n_popular_articles()
```

**Avantages:**
- Robuste pour tous types d'utilisateurs
- Balance automatique entre exploration et exploitation
- Performance constante même avec peu de données

**Limitations:**
- Moins de personnalisation que l'approche 2 pure
- Peut favoriser les articles mainstream

---

## Métriques d'Évaluation

### Split des Données
- **Split par utilisateur:** 80% des interactions de chaque utilisateur en train, 20% en test
- **Filtre:** Utilisateurs avec minimum 10 interactions
- **Avantage:** Plus réaliste que split temporel pour articles d'actualité

### Métriques Utilisées

**Hit@K:** Proportion d'utilisateurs avec au moins 1 article correct dans le TOP K
```
Hit@K = 1 si |recommendations[:K] ∩ actual| > 0, sinon 0
```

**Precision@K:** Proportion d'articles corrects dans le TOP K
```
Precision@K = |recommendations[:K] ∩ actual| / K
```

**Recall@K:** Proportion d'articles pertinents retrouvés
```
Recall@K = |recommendations[:K] ∩ actual| / |actual|
```

### Résultats Typiques

| Approche | Hit@5 | Hit@10 | Hit@20 | Precision@10 |
|----------|-------|--------|--------|--------------|
| Popularité Temporelle | 15-20% | 25-30% | 35-40% | 0.02-0.04 |
| Similarité Multi-Facettes | 10-15% | 20-25% | 30-35% | 0.01-0.03 |
| Hybride | 20-25% | 30-35% | 40-45% | 0.03-0.05 |

*Note: Les métriques sont naturellement basses pour les articles d'actualité car les utilisateurs ne re-cliquent presque jamais sur le même article.*

---

## Optimisations Implémentées

### Performance
- **Échantillonnage:** Limite à 1000 candidats pour le scoring
- **Caching:** Pré-calcul des scores de popularité
- **Vectorisation:** Utilisation de NumPy pour les calculs matriciels

### Qualité
- **Diversification forcée:** Maximum 3 articles par catégorie
- **Fenêtre temporelle:** Focus sur l'activité récente (30 jours)
- **Exploration contrôlée:** 20% de contenu nouveau

### Scalabilité
- **Batch processing:** Traitement par lots des utilisateurs
- **Sparse matrices:** Pour les grandes matrices utilisateur-article
- **Incremental updates:** Mise à jour des scores sans recalcul complet

---

## Guide d'Utilisation

### Installation des dépendances
```bash
pip install pandas numpy scikit-learn
```

### Structure des données requises
```
data/
├── articles_metadata.csv     # Métadonnées des articles
├── articles_embeddings.pickle # Embeddings pré-calculés
└── clicks/                    # Dossier des interactions
    └── clicks_hour_*.csv
```

### Utilisation basique
```python
# Chargement des données
train_df, test_df = user_based_split(clicks_df)

# Initialisation
recommender = HybridRecommender(embeddings, articles_df, train_df)

# Génération de recommandations
recommendations = recommender.recommend(user_id=123, n=10)
```

### Paramètres ajustables

**TemporalPopularityRecommender:**
- `temporal_decay`: Facteur de décroissance (défaut: 0.95)
- `max_per_category`: Articles max par catégorie (défaut: 3)

**MultiFacetSimilarityRecommender:**
- `time_window`: Fenêtre d'historique en jours (défaut: 30)
- `exploration_rate`: Taux d'exploration (défaut: 0.2)

**HybridRecommender:**
- `popularity_weight`: Poids de la popularité (défaut: 0.3)

---

## Considérations pour la Production

### Architecture Recommandée
```
API Gateway → Load Balancer → 
├── Service Popularité (Cache Redis 5min)
├── Service Similarité (Cache 15min)
└── Service Hybride (Cache 10min)
```

### Monitoring
- Latence P95 < 100ms
- CTR par approche et segment
- Couverture du catalogue hebdomadaire
- Distribution des catégories recommandées

### A/B Testing
- 40% Hybride (contrôle)
- 30% Popularité Temporelle
- 30% Similarité Multi-Facettes
- Métriques: CTR, temps de session, articles par session

### Améliorations Futures
1. **Features contextuelles:** Heure, device, localisation
2. **Apprentissage en ligne:** Mise à jour temps réel des profils
3. **Deep learning:** Transformer pour séquences de clics
4. **Multi-objectif:** Optimiser CTR + diversité + fraîcheur

---

## Conclusion

Ce système Content-Based offre trois approches complémentaires adaptées à différents scénarios. L'approche hybride est recommandée pour la production car elle offre le meilleur équilibre entre performance, personnalisation et robustesse. Les métriques doivent être interprétées dans le contexte spécifique des articles d'actualité où la répétition de consultation est rare.