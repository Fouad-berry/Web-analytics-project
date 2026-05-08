# 📖 Data Dictionary

## Modèle de données : 3 tables au format GA4

### 1. `sessions.csv` — 49 915 lignes

Une ligne = une session utilisateur.

| Colonne | Type | Description |
|---------|------|-------------|
| `session_id` | string | ID unique (S0000001…) |
| `user_id` | string | ID utilisateur (peut avoir plusieurs sessions) |
| `session_start` | datetime | Timestamp de début de session |
| `session_date` | date | Date de la session |
| `channel` | string | 7 modalités : Organic Search, Direct, Paid Search, Social, Email, Referral, Display |
| `campaign` | string | Nom de la campagne (vide pour les canaux non-paid) |
| `device` | string | mobile / desktop / tablet |
| `country` | string | 8 pays (France, USA, UK, Germany, Spain, Italy, Belgium, Canada) |
| `browser` | string | Chrome / Safari / Firefox / Edge / Samsung Internet |
| `is_new_user` | bool | True si première visite |
| `page_views` | int | Nombre de pages vues dans la session |
| `duration_seconds` | int | Durée en secondes |
| `bounced` | bool | True si une seule page vue |
| `converted` | bool | True si la session a abouti à un achat |
| `session_cost_usd` | float | Coût d'acquisition (uniquement Paid Search, Social, Display) |

### 2. `events.csv` — 154 990 lignes

Une ligne = un événement utilisateur (modèle GA4 strict).

| Colonne | Type | Description |
|---------|------|-------------|
| `event_id` | string | ID unique de l'événement |
| `session_id` | string | FK vers sessions |
| `user_id` | string | ID utilisateur |
| `event_timestamp` | datetime | Horodatage |
| `event_name` | string | `page_view`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase` |
| `page_path` | string | URL de la page |
| `value` | float | Valeur monétaire (uniquement pour `add_to_cart` et `purchase`) |

### 3. `transactions.csv` — 1 073 lignes

Une ligne = un produit acheté (une transaction peut avoir plusieurs lignes).

| Colonne | Type | Description |
|---------|------|-------------|
| `transaction_id` | string | ID unique |
| `session_id` | string | FK vers sessions |
| `user_id` | string | ID utilisateur |
| `transaction_date` | date | Date de la transaction |
| `product_sku` | string | SKU produit (SKU001…SKU010) |
| `product_name` | string | Nom du produit |
| `category` | string | Sneakers / Running / Casual / Sports / Boots |
| `quantity` | int | Quantité achetée |
| `unit_price_usd` | float | Prix unitaire |
| `discount_usd` | float | Remise éventuelle |
| `revenue_usd` | float | Revenu net (= unit_price × quantity − discount) |

---

## Variables dérivées (créées par `src/preprocessing.py`)

| Variable | Source | Description |
|----------|--------|-------------|
| `session_revenue_usd` | join transactions → sessions | Revenu généré par la session |
| `session_day_of_week` | session_date | Monday, Tuesday… |
| `session_hour` | session_start | 0-23 |
| `year_month` | session_date | 2025-01, 2025-02… |
| `year_week` | session_date | 2025-W01… |
| `is_weekend` | session_date | True si samedi/dimanche |
| `engagement_level` | page_views | bounced / low / medium / high |
| `cohort_week` | min(session_date) par user | Semaine d'acquisition de l'utilisateur |
| `activity_week` | session_date | Semaine d'activité courante |

---

## Notes méthodologiques

- **Dataset synthétique** généré par `generate_dataset.py` avec patterns réalistes (saisonnalité hebdo, funnel d'attrition, tendance, biais channel × device)
- **Période** : 1er janvier 2025 → 30 juin 2025 (181 jours)
- **Conversion rate** : 1.32 % (cohérent avec les benchmarks e-commerce 1-3 %)
- **Pas de valeurs manquantes**

## Connexion à de vraies données

Pour brancher le projet sur du **vrai GA4** :

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
# Voir : https://developers.google.com/analytics/devguides/reporting/data/v1
```

Ou via **BigQuery export GA4** (gratuit pour GA4, voir Property Settings) :

```sql
SELECT * FROM `your-project.analytics_NNNNN.events_*`
```

Le pipeline `build_project.py` est conçu pour fonctionner avec n'importe quelle source qui produit ces 3 tables.