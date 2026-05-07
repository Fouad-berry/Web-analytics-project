# 📊 Guide Looker Studio

## 🔗 Lien du dashboard

> **[👉 Ouvrir le dashboard](https://lookerstudio.google.com/)** *(à remplacer par ton lien)*

---

## 🚀 Connexion des données

### Option A — Upload CSV (rapide)

1. [lookerstudio.google.com](https://lookerstudio.google.com/) → **Créer** → **Source de données** → **File Upload**
2. Uploader depuis `data/exports/` :
   - `main_sessions.csv` (49 915 sessions, source principale)
   - `main_transactions.csv`
   - `daily_traffic.csv`
   - `by_channel.csv`
   - `by_device.csv`
   - `funnel.csv`
   - `campaigns.csv`
   - `products.csv`
   - `cohort_long.csv`
   - `global_kpis.csv`
3. Pour chaque source : **Créer un rapport**

### Option B — BigQuery (mode entrepôt, recommandé en production)

1. Charger les 3 tables raw dans BigQuery (`sql/create_tables.sql`)
2. Looker Studio → **Source BigQuery** → choisir les tables
3. Bonus : utiliser les vues `v_sessions_with_revenue` et `v_funnel` pour simplifier

---

## 🎨 Structure recommandée — 5 pages

### 📄 Page 1 — Executive Overview

Source : `global_kpis.csv` + `daily_traffic.csv`

- **6 scorecards** : Sessions, Users, Revenue, Conversion Rate, AOV, Bounce Rate
- **Line chart** : sessions quotidiennes (avec moyenne mobile 7 jours)
- **Bar chart** : revenu par jour de la semaine
- **Donut** : répartition new vs returning

### 📄 Page 2 — Acquisition

Source : `by_channel.csv` + `campaigns.csv`

- **Pie chart** : sessions par canal (couleurs Google)
- **Bar chart horizontal** : conversion rate par canal
- **Scatter plot** : Cost (X) vs Revenue (Y), bulles = sessions, couleurs = canal
- **Table ROAS** : top campagnes triées par ROAS
- **Filtre** : période

### 📄 Page 3 — Behavior

Source : `main_sessions.csv` + `funnel.csv` + `top_pages.csv`

- **Funnel chart** : 5 étapes de conversion
- **Heatmap** : engagement (heure × jour de semaine)
- **Bar chart** : top 10 pages
- **Comparison cards** : mobile vs desktop vs tablet
- **Geo map** : sessions par pays

### 📄 Page 4 — Conversions

Source : `products.csv` + `main_transactions.csv`

- **Bar chart horizontal** : top 10 produits par revenu
- **Line chart** : revenu cumulé sur 6 mois
- **Pivot table** : revenu par catégorie × canal
- **Bar chart** : AOV par canal
- **Scorecards** : revenue per session, CAC, AOV

### 📄 Page 5 — Retention

Source : `cohort_long.csv` + `main_sessions.csv`

- **Heatmap pivot** : cohort × activity_week (utiliser le widget pivot table de Looker)
- **Line chart** : courbe de rétention moyenne par cohort
- **Bar chart** : avg sessions per user par segment
- **Comparaison** : new vs returning (sessions, conversion, revenue)

---

## 🎛️ Filtres globaux (haut de page, applicables à toutes les pages)

- **Date range picker** sur `session_date`
- **Channel** : multi-select dropdown
- **Device** : boutons (mobile / desktop / tablet)
- **Country** : multi-select dropdown
- **User type** : new / returning / all

---

## 🎨 Palette de couleurs (cohérente avec les figures Python)

**Canaux** :
- Organic Search : `#4285F4` (bleu Google)
- Direct : `#34A853` (vert Google)
- Paid Search : `#EA4335` (rouge Google)
- Social : `#9C27B0` (violet)
- Email : `#FF9800` (orange)
- Referral : `#00BCD4` (cyan)
- Display : `#795548` (brun)

**Devices** :
- Mobile : `#3498db`
- Desktop : `#9b59b6`
- Tablet : `#e67e22`

---

## 💡 Champs calculés utiles

À ajouter dans Looker pour enrichir l'analyse :

```sql
-- Marge contributive
margin = revenue_usd - cost_usd

-- ROI
ROI_pct = 100 * (revenue_usd - cost_usd) / cost_usd

-- Break-even flag
is_profitable = IF(roas > 1, "Profitable", "Loss")

-- Bucket de durée de session
duration_bucket = CASE
    WHEN duration_seconds < 30 THEN "<30s"
    WHEN duration_seconds < 120 THEN "30s-2min"
    WHEN duration_seconds < 600 THEN "2-10min"
    ELSE ">10min"
END
```

---

## 📸 Captures d'écran

Place tes captures dans `images/` et référence-les ici :

```markdown
![Page 1 — Overview](../images/dashboard_01_overview.png)
![Page 2 — Acquisition](../images/dashboard_02_acquisition.png)
![Page 3 — Behavior](../images/dashboard_03_behavior.png)
![Page 4 — Conversions](../images/dashboard_04_conversions.png)
![Page 5 — Retention](../images/dashboard_05_retention.png)
```

---

## 🎯 KPIs clés à mettre en valeur

Pour un dashboard convaincant pour un recruteur web analyst, met en avant :

1. **Conversion rate global** (en % grand sur la home)
2. **Funnel chart** (visuellement le plus impactant)
3. **ROAS table** par campagne (la métrique sacrée des marketeux)
4. **Cohort heatmap** (montre la maturité technique)
5. **Saisonnalité hebdo** (pour les insights actionnables)