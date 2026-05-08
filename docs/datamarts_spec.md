# 🧱 Spécification des 12 datamarts

## Organisation thématique

Les 12 datamarts sont organisés selon les **3 axes du web analytics** :

- 🚦 **Trafic** (5) : channel, device, country, daily, hourly heatmap
- 💰 **Conversions** (4) : funnel, campaigns, top pages, top products
- 🔁 **Engagement / Cohorts** (3) : cohort retention pivot, cohort long, new vs returning
- 📊 **KPI global** (1) : tableau de bord

---

## 🚦 Trafic

### 1. `dm_traffic_by_channel.csv`

**Grain** : 1 ligne par canal (7 lignes) · **Usage** : page Acquisition

Colonnes : `channel`, `sessions`, `users`, `avg_pageviews`, `avg_duration_sec`, `bounce_rate_pct`, `conversion_rate_pct`, `revenue_usd`, `cost_usd`, `traffic_share_pct`, `roas`.

### 2. `dm_traffic_by_device.csv`

**Grain** : 1 ligne par device (3 lignes : mobile / desktop / tablet)

Colonnes : `device`, `sessions`, `bounce_rate_pct`, `avg_duration_sec`, `conversion_rate_pct`, `revenue_usd`, `share_pct`.

### 3. `dm_traffic_by_country.csv`

**Grain** : 1 ligne par pays (8 lignes)

Colonnes : `country`, `sessions`, `users`, `conversion_rate_pct`, `revenue_usd`.

### 4. `dm_daily_traffic.csv`

**Grain** : 1 ligne par jour (181 lignes) · **Usage** : line charts saisonnalité

Colonnes : `session_date`, `sessions`, `users`, `new_users`, `transactions`, `revenue_usd`, `avg_duration_sec`, `bounce_rate_pct`.

### 5. `dm_hourly_heatmap.csv`

**Grain** : jour × heure (~168 lignes) · **Usage** : heatmap d'engagement

Colonnes : `session_day_of_week`, `session_hour`, `sessions`.

---

## 💰 Conversions

### 6. `dm_conversion_funnel.csv`

**Grain** : 1 ligne par étape du funnel (5 lignes)

Colonnes : `step`, `sessions`, `pct_of_total`, `dropoff_pct_from_previous`.

Étapes : `page_view` → `view_item` → `add_to_cart` → `begin_checkout` → `purchase`.

### 7. `dm_campaign_performance.csv`

**Grain** : 1 ligne par couple (channel × campaign) — uniquement les canaux paid

Colonnes : `channel`, `campaign`, `sessions`, `cost_usd`, `transactions`, `revenue_usd`, `cpa_usd`, `roas`, `conversion_rate_pct`.

### 8. `dm_top_pages.csv`

**Grain** : top 20 pages

Colonnes : `page_path`, `page_views`, `unique_sessions`, `share_pct`.

### 9. `dm_top_products.csv`

**Grain** : 1 ligne par SKU (10 lignes)

Colonnes : `product_sku`, `product_name`, `category`, `units_sold`, `transactions`, `revenue_usd`, `avg_unit_price`, `revenue_share_pct`.

---

## 🔁 Engagement & Cohorts

### 10. `dm_cohort_retention.csv` (format pivot)

**Grain** : matrice cohort_week × activity_week · **Usage** : heatmap directe

Format pivot avec les semaines en colonnes et les cohortes en lignes. Valeurs = % de rétention.

### 11. `dm_cohort_long.csv` (format long)

**Grain** : 1 ligne par (cohort, activity_week) · **Usage** : Looker Studio (préfère le long)

Colonnes : `cohort_week`, `activity_week`, `active_users`, `cohort_size`, `retention_pct`.

### 12. `dm_new_vs_returning.csv`

**Grain** : 2 lignes (new / returning)

Colonnes : `user_type`, `sessions`, `avg_pageviews`, `avg_duration_sec`, `bounce_rate_pct`, `conversion_rate_pct`, `revenue_usd`.

---

## 📊 KPI global

### 13. `dm_global_kpis.csv`

**Grain** : 1 ligne · **Usage** : scorecards en haut du dashboard

Colonnes : `total_sessions`, `total_users`, `total_pageviews`, `total_transactions`, `total_revenue_usd`, `total_cost_usd`, `avg_session_duration_sec`, `bounce_rate_pct`, `conversion_rate_pct`, `avg_order_value`, `revenue_per_session`, `pct_new_users`.

---

## Règles communes

- Tous les arrondis à **2 décimales**
- Pourcentages en base 100 (0.XX → XX.XX %)
- Source : `data/processed/sessions_enriched.csv` + `events.csv` + `transactions.csv`
- Régénérés à chaque exécution de `build_project.py`
- Format CSV pour compatibilité maximale avec Looker Studio et Excel