# Système de Recommandation Collaborative Filtering

## Vue d'ensemble

Ce projet implémente trois algorithmes de filtrage collaboratif (Collaborative Filtering) pour recommander des articles d'actualité. Le système exploite les interactions utilisateur-article pour identifier des patterns de préférences et générer des recommandations personnalisées basées sur les comportements collectifs.

## Architecture des Approches

### 🎯 Approche 1: SVD (Singular Value Decomposition)

**Principe:** Décomposition matricielle par factorisation en valeurs singulières pour capturer les facteurs latents des préférences utilisateurs et caractéristiques des articles.

**Fonctionnement:**
1. **Factorisation matricielle:** Décompose la matrice R (utilisateur-article) en trois matrices
2. **Optimisation:** Minimisation de l'erreur de reconstruction avec régularisation
3. **Prédiction:** Calcul du produit des facteurs latents pour estimer les ratings manquants

**Formulation mathématique:**

Variables :
- `R` : Matrice de ratings utilisateur-article
- `U` : Matrice des facteurs latents utilisateurs (n_users × n_factors)
- `Σ` : Matrice diagonale des valeurs singulières
- `V^T` : Matrice des facteurs latents articles (n_factors × n_items)
- `p_u` : Vecteur de facteurs latents pour l'utilisateur u
- `q_i` : Vecteur de facteurs latents pour l'article i
- `μ` : Moyenne globale des ratings
- `b_u` : Biais de l'utilisateur u
- `b_i` : Biais de l'article i
- `λ` : Paramètre de régularisation (reg_all = 0.02)
- `α` : Taux d'apprentissage (lr_all = 0.005)

Équations :
```
# Décomposition SVD
R ≈ U × Σ × V^T

# Prédiction de rating
r̂_ui = μ + b_u + b_i + p_u · q_i

# Fonction objectif à minimiser
L = Σ(r_ui - r̂_ui)² + λ(||p_u||² + ||q_i||² + b_u² + b_i²)

# Mise à jour par descente de gradient
p_u ← p_u + α(e_ui × q_i - λ × p_u)
q_i ← q_i + α(e_ui × p_u - λ × q_i)
b_u ← b_u + α(e_ui - λ × b_u)
b_i ← b_i + α(e_ui - λ × b_i)

où e_ui = r_ui - r̂_ui (erreur de prédiction)
```

**Paramètres du modèle:**
- `n_factors`: 100 (dimensions des facteurs latents)
- `n_epochs`: 20 (nombre d'itérations)
- `lr_all`: 0.005 (taux d'apprentissage)
- `reg_all`: 0.02 (régularisation L2)

**Avantages:**
- Capture efficacement les patterns complexes dans les données
- Gestion robuste des données manquantes
- Bonne généralisation grâce à la régularisation

**Limitations:**
- Problème de démarrage à froid pour nouveaux utilisateurs/articles
- Sensible aux hyperparamètres
- Coût computationnel élevé pour grandes matrices

---

### 🧠 Approche 2: NMF (Non-Negative Matrix Factorization)

**Principe:** Factorisation matricielle non-négative garantissant l'interprétabilité des facteurs latents en imposant des contraintes de positivité.

**Fonctionnement:**
1. **Décomposition non-négative:** Factorise R en deux matrices non-négatives
2. **Optimisation itérative:** Règles de mise à jour multiplicatives
3. **Interprétation:** Les facteurs représentent des thèmes/catégories positifs

**Formulation mathématique:**

Variables :
- `W` : Matrice des profils utilisateurs (n_users × n_factors), W ≥ 0
- `H` : Matrice des profils articles (n_factors × n_items), H ≥ 0
- `w_u` : Vecteur profil de l'utilisateur u
- `h_i` : Vecteur profil de l'article i
- `n_factors` : Nombre de facteurs latents (50)
- `ε` : Petite constante pour éviter la division par zéro

Équations :
```
# Approximation NMF
R ≈ W × H
avec contrainte : W ≥ 0, H ≥ 0

# Prédiction
r̂_ui = w_u · h_i = Σ_k(w_uk × h_ki)

# Fonction objectif (divergence de Kullback-Leibler)
D_KL = Σ_ui[r_ui × log(r_ui/r̂_ui) - r_ui + r̂_ui]

# Règles de mise à jour multiplicatives
W_uk ← W_uk × [Σ_i(R_ui × H_ki / r̂_ui)] / [Σ_i H_ki]
H_ki ← H_ki × [Σ_u(R_ui × W_uk / r̂_ui)] / [Σ_u W_uk]

# Gestion des utilisateurs/articles inconnus
Si utilisateur inconnu : utiliser moyenne des ratings de l'article
Si article inconnu : score basé sur popularité
```

**Paramètres du modèle:**
- `n_factors`: 50 (dimensions réduites pour meilleure interprétabilité)
- `n_epochs`: 50 (plus d'itérations pour convergence)

**Avantages:**
- Facteurs interprétables (toujours positifs)
- Adapté aux données de comptage (clics)
- Résultats explicables

**Limitations:**
- Contrainte de non-négativité peut limiter l'expressivité
- Convergence plus lente que SVD
- Performance généralement inférieure à SVD

---

### ⚡ Approche 3: ALS (Alternating Least Squares)

**Principe:** Optimisation alternée des facteurs utilisateurs et articles pour les données implicites (clics), particulièrement efficace pour les matrices creuses.

**Fonctionnement:**
1. **Feedback implicite:** Conversion des clics en niveaux de confiance
2. **Optimisation alternée:** Fixe U pour optimiser V, puis fixe V pour optimiser U
3. **Pondération:** Les clics multiples indiquent une préférence plus forte

**Formulation mathématique:**

Variables :
- `C_ui` : Matrice de confiance (basée sur le nombre de clics)
- `P_ui` : Matrice de préférence binaire (1 si cliqué, 0 sinon)
- `X_u` : Facteurs latents utilisateur
- `Y_i` : Facteurs latents article
- `α` : Paramètre de confiance (40)
- `λ` : Régularisation (0.01)
- `r_ui` : Nombre de clics utilisateur u sur article i

Équations :
```
# Matrice de confiance
C_ui = 1 + α × r_ui

# Matrice de préférence
P_ui = 1 si r_ui > 0, 0 sinon

# Fonction objectif
L = Σ_ui C_ui(P_ui - X_u^T × Y_i)² + λ(||X_u||² + ||Y_i||²)

# Optimisation alternée (fermée analytiquement)
Fixe Y, résout pour X:
X_u = (Y^T × C^u × Y + λI)^(-1) × Y^T × C^u × P^u

Fixe X, résout pour Y:
Y_i = (X^T × C^i × X + λI)^(-1) × X^T × C^i × P^i

où C^u est la matrice diagonale des confiances pour l'utilisateur u

# Score de recommandation
score(u,i) = X_u^T × Y_i
```

**Paramètres du modèle:**
- `factors`: 100 (dimensions des facteurs latents)
- `regularization`: 0.01 (régularisation L2)
- `iterations`: 20 (nombre d'alternances)
- `alpha`: 40 (paramètre de confiance)

**Implémentation avec matrices creuses:**
```python
# Utilisation de lil_matrix pour construction efficace
user_item_matrix = lil_matrix((n_users, n_items))
# Conversion en csr_matrix pour calculs rapides
user_item_matrix = user_item_matrix.tocsr()
item_user_matrix = user_item_matrix.T.tocsr()
```

**Avantages:**
- Très efficace pour données implicites
- Excellent pour matrices très creuses (~99.8% de sparsité)
- Solution analytique à chaque étape
- Meilleure performance empirique du notebook

**Limitations:**
- Suppose linéarité des interactions
- Nécessite tuning du paramètre α
- Cold start problem persistant

---

## Préparation des Données

### Traitement des Interactions

**Calcul du score d'engagement:**
```python
# Score composite basé sur clics et temps
max_time = interactions['avg_time_to_click'].max()
engagement_score = click_count × (1 - avg_time_to_click / max_time)

# Normalisation en rating 1-5
rating = 1 + 4 × (engagement_score - min) / (max - min)
```

**Statistiques du dataset:**
- Articles totaux: 363,946
- Articles cliqués: 20,793
- Utilisateurs uniques: 210,991
- Interactions totales: 1,176,699
- Rating moyen: 1.23
- Sparsité de la matrice: ~99.8%

### Split Temporel Amélioré

**Stratégie de split:**
```python
def improved_temporal_split(interactions, test_ratio=0.2):
    # Pour chaque utilisateur:
    # - 80% premières interactions → train
    # - 20% dernières interactions → test
    # - Garantit min 2 interactions dans train
    # - Filtre test pour articles présents dans train
```

**Résultats du split:**
- Train: 618,118 interactions
- Test: 208,472 interactions
- Utilisateurs dans test: 78,500
- Articles testables: 3,493

---

## Métriques d'Évaluation

### Métriques Utilisées

**Hit@K:** Utilisateur a au moins une bonne recommandation dans le TOP K
```
Hit@K = 1 si |reco[:K] ∩ actual| > 0, 0 sinon
```

**Precision@K:** Proportion de recommandations correctes
```
Precision@K = |reco[:K] ∩ actual| / K
```

**Recall@K:** Proportion d'articles pertinents retrouvés
```
Recall@K = |reco[:K] ∩ actual| / |actual|
```

**F1@K:** Moyenne harmonique precision-recall
```
F1@K = 2 × (Precision@K × Recall@K) / (Precision@K + Recall@K)
```

### Résultats Expérimentaux

| Modèle | Hit@5 | Hit@10 | Hit@20 | Precision@10 | Recall@10 | F1@10 |
|--------|-------|--------|--------|--------------|-----------|-------|
| **SVD** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0000 |
| **NMF** | 0.004 | 0.018 | 0.046 | 0.002 | 0.008 | 0.0032 |
| **ALS** | 0.064 | 0.190 | 0.256 | 0.020 | 0.091 | 0.0328 |

**Meilleur modèle:** ALS (F1@10 = 0.0328)

### Analyse des Résultats

**Performance par modèle:**
- **ALS:** 25.6% des utilisateurs ont au moins un hit @20
- **NMF:** 4.6% des utilisateurs ont au moins un hit @20
- **SVD:** 0% de hits (problème potentiel de configuration)

**Insights:**
- Les métriques faibles reflètent la nature éphémère des articles d'actualité
- ALS surperforme grâce à sa gestion native du feedback implicite
- SVD nécessite probablement un ajustement d'hyperparamètres
- La sparsité extrême (99.8%) impacte tous les modèles

---

## Framework d'Évaluation Robuste

### Gestion des Cas Limites

```python
class ImprovedRecommender:
    def recommend(self, user_id, n=10):
        # Cas 1: Utilisateur et article connus
        if user_known and item_known:
            return model.predict(user_id, item_id)

        # Cas 2: Utilisateur inconnu, article connu
        elif item_known:
            return global_mean + item_bias

        # Cas 3: Article inconnu
        else:
            return popularity_based_score
```

### Stratégies de Fallback

1. **Échantillonnage intelligent des candidats:**
   - Top 250 articles populaires
   - 250 articles aléatoires
   - Limite à 500 candidats pour performance

2. **Scoring hybride pour articles inconnus:**
   ```python
   popularity_score = item_clicks / max_clicks
   fallback_score = global_mean × (0.5 + 0.5 × popularity_score)
   ```

3. **Recommandations de secours:**
   - Utilisateurs sans historique → articles populaires
   - Erreurs de prédiction → fallback vers popularité

---

## Optimisations Implémentées

### Performance

- **Matrices creuses:** Utilisation de scipy.sparse (lil_matrix, csr_matrix)
- **Batch processing:** Évaluation par lots de 500 utilisateurs
- **Caching:** Pré-calcul des statistiques de popularité
- **Limitation candidats:** Maximum 500 articles à scorer par utilisateur

### Qualité

- **Filtrage intelligent:** Exclusion des articles déjà vus
- **Pondération temporelle:** Articles récents privilégiés
- **Diversification:** Mix articles populaires + aléatoires

### Scalabilité

- **Indexation efficace:** Mappings user_id ↔ user_idx optimisés
- **Calcul parallélisable:** ALS permet parallélisation native
- **Mémoire optimisée:** Stockage sparse pour matrices creuses

---

## Guide d'Utilisation

### Installation des dépendances
```bash
pip install pandas numpy scikit-learn scipy
pip install surprise implicit
pip install matplotlib seaborn
```

### Structure des données requises
```
data/
├── articles_metadata.csv       # Métadonnées des articles
├── clicks/                      # Interactions utilisateur-article
│   └── clicks_hour_*.csv
```

### Utilisation basique

```python
# Préparation des données
train_df, test_df = improved_temporal_split(interactions)

# SVD
svd_rec = ImprovedSVDRecommender(n_factors=100)
svd_rec.fit(train_df)
recommendations = svd_rec.recommend(user_id, n=10)

# NMF
nmf_rec = ImprovedNMFRecommender(n_factors=50)
nmf_rec.fit(train_df)
recommendations = nmf_rec.recommend(user_id, n=10)

# ALS
als_rec = ImprovedALSRecommender(factors=100)
als_rec.fit(train_df)
recommendations = als_rec.recommend(user_id, n=10)
```

### Paramètres ajustables

**SVD:**
- `n_factors`: [50, 100, 200] - Nombre de facteurs latents
- `n_epochs`: [10, 20, 50] - Itérations d'entraînement
- `lr_all`: [0.001, 0.005, 0.01] - Taux d'apprentissage
- `reg_all`: [0.01, 0.02, 0.05] - Régularisation

**NMF:**
- `n_factors`: [15, 30, 50] - Facteurs (moins pour interprétabilité)
- `n_epochs`: [30, 50, 100] - Plus d'itérations nécessaires

**ALS:**
- `factors`: [50, 100, 200] - Dimensions latentes
- `regularization`: [0.001, 0.01, 0.1] - Régularisation L2
- `iterations`: [10, 15, 20] - Alternances
- `alpha`: [1, 20, 40, 100] - Paramètre de confiance critique

---

## Considérations pour la Production

### Architecture Recommandée
```
                    ┌──────────────┐
                    │ Load Balancer │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
   │   SVD    │      │   NMF    │      │   ALS    │
   │ Service  │      │ Service  │      │ Service  │
   └────┬─────┘      └────┬─────┘      └────┬─────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼───────┐
                    │ Redis Cache  │
                    │   (15 min)   │
                    └──────────────┘
```

### Monitoring

**Métriques clés:**
- Latence P95 < 200ms (calcul matriciel)
- Hit rate du cache > 80%
- Coverage hebdomadaire > 10%
- Diversité des recommandations > 0.3

**Alertes:**
- Dégradation hit rate > 20%
- Latence spike > 500ms
- Erreurs de prédiction > 5%

### A/B Testing

Configuration suggérée:
- 40% ALS (champion actuel)
- 30% ALS avec hyperparamètres optimisés
- 20% Hybride ALS + popularité
- 10% Contrôle (popularité pure)

Métriques de décision:
- CTR (Click-Through Rate)
- Temps de session
- Articles uniques cliqués
- Rétention J+1

### Améliorations Futures

1. **Deep Learning:**
   - Neural Collaborative Filtering (NCF)
   - AutoEncoders pour réduction dimensionnalité
   - Transformers pour séquences de clics

2. **Features additionnelles:**
   - Métadonnées articles (catégorie, publisher)
   - Contexte temporel (heure, jour)
   - Signaux sociaux (partages, likes)

3. **Optimisations:**
   - Apprentissage en ligne (online learning)
   - Mise à jour incrémentale des modèles
   - Quantification pour réduction mémoire

4. **Hybridation:**
   - Ensemble learning des 3 modèles
   - Pondération dynamique selon contexte
   - Fusion avec content-based filtering

---

## Diagnostic des Problèmes

### SVD avec 0% de hits

**Causes possibles:**
1. Hyperparamètres inadaptés (learning rate trop élevé)
2. Overfitting sur le train
3. Problème de normalisation des ratings

**Solutions:**
- Grid search sur hyperparamètres
- Cross-validation pour régularisation optimale
- Vérifier la distribution des ratings

### Performance ALS supérieure

**Raisons:**
1. Conçu spécifiquement pour feedback implicite
2. Gestion native de la sparsité
3. Paramètre α bien ajusté pour les clics

### Métriques globalement faibles

**Explications:**
1. Nature éphémère du contenu news
2. Sparsité extrême (99.8%)
3. Peu de re-clics sur même article
4. Split temporel strict

---

## Conclusion

Le système de collaborative filtering implémenté offre trois approches complémentaires pour la recommandation d'articles. **ALS émerge comme le modèle le plus performant** avec un Hit@20 de 25.6%, particulièrement adapté aux données implicites de clics. Bien que les métriques absolues restent modestes, elles sont cohérentes avec les défis inhérents aux recommandations d'actualités (contenu éphémère, pas de re-consultation).

Pour la production, une approche hybride combinant ALS pour la personnalisation et un fallback sur la popularité temporelle est recommandée. L'optimisation continue des hyperparamètres et l'enrichissement avec des features contextuelles constituent les axes prioritaires d'amélioration.