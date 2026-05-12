# 🌐 Web Analytics Project

> Analyse complète des **49 915 sessions** d'un site e-commerce sur 6 mois (jan–juin 2025) : trafic, conversions, funnel, cohort retention. Pipeline orienté **GA4** avec dashboard Looker Studio.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458.svg)
![Looker Studio](https://img.shields.io/badge/Looker_Studio-Dashboard-4285F4.svg)
![GA4 inspired](https://img.shields.io/badge/Modèle-GA4_inspired-FF6F00.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🎯 Objectif du projet

Construire un pipeline data analytics complet sur des données web (modèle Google Analytics 4) couvrant les **trois axes du web analytics** :

1. **🚦 Trafic** — d'où viennent les visiteurs ? (canaux, devices, géo, saisonnalité)
2. **💰 Conversions** — comment se passe le funnel d'achat ? (taux, AOV, ROAS)
3. **🔁 Cohorts & engagement** — les utilisateurs reviennent-ils ? (rétention par semaine)

**Questions métier auxquelles ce projet répond :**
- Quels canaux d'acquisition génèrent le plus de revenus (et lesquels coûtent trop cher) ?
- Où se trouvent les fuites du funnel de conversion ?
- Le mobile convertit-il aussi bien que le desktop ?
- Quelle est la rétention semaine par semaine ?
- Quelles campagnes payantes sont rentables (ROAS > 1) ?

---

## 📊 Aperçu des résultats

### Évolution quotidienne des sessions

![Daily traffic](images/figures/01_daily_traffic.png)

> Saisonnalité hebdomadaire claire (creux week-end) et **tendance haussière** sur 6 mois (+20 % entre janvier et juin).

### Funnel de conversion

![Funnel](images/figures/03_conversion_funnel.png)

> **49 915 sessions** → 7 469 vues produit (15 %) → 7 060 ajouts panier (14.1 %) → **659 achats (1.32 %)**. Le drop-off majeur est entre `add_to_cart` et `begin_checkout` — c'est le pain point n°1.

### Cohort retention (semaine d'acquisition × activité)

![Cohort retention](images/figures/07_cohort_retention.png)

> Triangle classique : ~12 % des nouveaux utilisateurs reviennent la semaine suivante. La rétention se stabilise rapidement.

### Heatmap d'engagement

![Engagement heatmap](images/figures/08_engagement_heatmap.png)

> Pic d'engagement les **mardi-jeudi entre 10h et 12h** (pause café au bureau).

📁 **12 figures générées** dans [`images/figures/`](images/figures/).

---

## 📁 Structure du projet

```
web-analytics-project/
│
├── data/
│   ├── raw/
│   │   ├── sessions.csv                    # 49 915 sessions
│   │   ├── events.csv                      # 154 990 événements
│   │   └── transactions.csv                # 1 073 lignes de transaction
│   ├── processed/
│   │   └── sessions_enriched.csv           # + features (revenu, engagement, cohort)
│   ├── datamarts/                          # 🧱 12 datamarts
│   │   ├── dm_global_kpis.csv
│   │   ├── dm_traffic_by_channel.csv
│   │   ├── dm_traffic_by_device.csv
│   │   ├── dm_traffic_by_country.csv
│   │   ├── dm_daily_traffic.csv
│   │   ├── dm_conversion_funnel.csv
│   │   ├── dm_campaign_performance.csv
│   │   ├── dm_top_pages.csv
│   │   ├── dm_top_products.csv
│   │   ├── dm_cohort_retention.csv
│   │   ├── dm_cohort_long.csv
│   │   ├── dm_new_vs_returning.csv
│   │   └── dm_hourly_heatmap.csv
│   └── exports/                            # Exports Looker Studio
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_traffic_analysis.ipynb           # Trafic & sources
│   ├── 03_conversion_funnel.ipynb          # Funnel & ROAS
│   └── 04_cohort_retention.ipynb           # Cohorts & engagement
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── datamarts.py
│   └── utils.py
│
├── sql/
│   ├── create_tables.sql                   # Schéma BigQuery (GA4-like)
│   └── queries.sql                         # 10 requêtes types web analytics
│
├── dashboards/
│   └── looker_studio_guide.md              # Guide dashboard 5 pages
│
├── docs/
│   ├── data_dictionary.md
│   ├── datamarts_spec.md
│   └── methodology.md
│
├── images/figures/                         # 12 PNG pré-générées
│
├── generate_dataset.py                     # ⭐ Génère le dataset synthétique
├── build_project.py                        # ⭐ Pipeline complet (DM + figures)
├── .gitignore, LICENSE, requirements.txt
└── README.md
```

---

## 📊 Description des données

Le projet utilise **3 tables au modèle GA4** :

### `sessions.csv` (49 915 lignes)

| Colonne | Description |
|---------|-------------|
| `session_id` | ID unique de la session |
| `user_id` | ID de l'utilisateur |
| `session_start`, `session_date` | Timestamp et date |
| `channel` | Source d'acquisition (Organic, Paid Search, Social, Email…) |
| `campaign` | Nom de la campagne (pour les canaux paid) |
| `device`, `country`, `browser` | Contexte technique |
| `page_views`, `duration_seconds` | Métriques d'engagement |
| `bounced`, `converted` | Flags |
| `is_new_user` | Premier passage ou non |
| `session_cost_usd` | Coût d'acquisition pour les canaux paid |

### `events.csv` (154 990 lignes)

Modèle GA4 strict : un event par ligne (`page_view`, `view_item`, `add_to_cart`, `begin_checkout`, `purchase`).

### `transactions.csv` (1 073 lignes)

Une ligne par produit acheté. Permet de calculer revenu, AOV, panier moyen.

📄 Détails : [`docs/data_dictionary.md`](docs/data_dictionary.md).

---

## 🧱 Les 12 datamarts

| # | Datamart | Question business |
|---|----------|-------------------|
| 1 | `dm_global_kpis` | KPIs globaux pour scorecards |
| 2 | `dm_traffic_by_channel` | Quels canaux apportent le plus de trafic et de revenus ? |
| 3 | `dm_traffic_by_device` | Mobile, desktop, tablet : qui convertit le mieux ? |
| 4 | `dm_traffic_by_country` | Top pays par sessions et revenus |
| 5 | `dm_daily_traffic` | Saisonnalité et tendance |
| 6 | `dm_conversion_funnel` | Où se situent les drop-offs ? |
| 7 | `dm_campaign_performance` | ROAS par campagne payante |
| 8 | `dm_top_pages` | Pages les plus vues |
| 9 | `dm_top_products` | Produits qui rapportent le plus |
| 10 | `dm_cohort_retention` | Pivot cohort retention (heatmap-ready) |
| 11 | `dm_cohort_long` | Cohort retention en format long (Looker-ready) |
| 12 | `dm_new_vs_returning` | Nouveaux vs récurrents |

📄 Spécification complète : [`docs/datamarts_spec.md`](docs/datamarts_spec.md).

---

## 🚀 Installation & utilisation

### 1. Cloner le repo

```bash
git clone https://github.com/<ton-username>/web-analytics-project.git
cd web-analytics-project
```

### 2. Environnement virtuel + dépendances

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Générer le dataset synthétique

```bash
python generate_dataset.py
```

> Pour un vrai projet : remplacer par un export GA4 BigQuery, Mixpanel, Amplitude, ou Segment.

### 4. Lancer le pipeline complet

```bash
python build_project.py
```

Ce script :
1. Charge sessions + events + transactions
2. Enrichit les sessions (revenu, cohort, engagement bucket)
3. Construit les **12 datamarts**
4. Régénère les **12 figures PNG**
5. Exporte les CSV pour Looker Studio

---

## 🔎 Workflow

```
Raw data (3 tables GA4-like)
     │
     ▼
[1] Enrichissement
     │  • Joindre revenu de transactions sur sessions
     │  • Features temporelles (cohort_week, year_month, hour…)
     │  • Engagement bucket (bounced/low/medium/high)
     ▼
[2] 12 datamarts thématiques
     │  • Trafic (4) : channel, device, country, daily
     │  • Conversion (4) : funnel, campaign, pages, products
     │  • Engagement (3) : cohort, new vs returning, hourly
     │  • KPI global (1)
     ▼
[3] 12 figures PNG + exports Looker
     │
     ▼
[4] Dashboard Looker Studio interactif
```

---

## 📈 Dashboard Looker Studio

Structure recommandée en **5 pages** :

1. **Executive Overview** — KPIs principaux + évolution quotidienne
2. **Acquisition** — Performance par canal, ROAS, campagnes
3. **Behavior** — Funnel, top pages, devices, géographie
4. **Conversions** — Top produits, AOV, revenu cumulé
5. **Retention** — Cohort heatmap, new vs returning

📄 Guide complet : [`dashboards/looker_studio_guide.md`](dashboards/looker_studio_guide.md).

---

## 📌 Principaux insights (data-driven)

- **Conversion rate global** : 1.32 % → cohérent avec les benchmarks e-commerce (1-3 %)
- **Top canal en volume** : Organic Search (32 % du trafic)
- **Top canal en conversion** : Email (7.5 % de CR) → un canal sous-utilisé à pousser
- **Drop-off funnel principal** : entre `add_to_cart` (14.1 %) et `begin_checkout` (1.3 %) — opportunité d'optimisation UX énorme
- **Mobile** = 62 % du trafic mais bounce rate plus élevé que desktop → optimiser le mobile = gros impact
- **Pic d'audience** : mardi-jeudi 10h-12h → meilleur moment pour les pushs marketing
- **Tendance** : trafic en croissance de **+20 %** sur 6 mois

---

## 🛠️ Stack technique

- **Python 3.10+** · Pandas · NumPy
- **Matplotlib** · Seaborn (avec axes datetime)
- **Jupyter** pour l'exploration
- **Looker Studio** pour le dashboard final
- **BigQuery** (optionnel) pour le mode entrepôt

---

## 🎓 Compétences démontrées

Ce projet montre la maîtrise de :

- **Modélisation GA4** : sessions, events, transactions, attribution
- **Cohort analysis** : pivot table de rétention (compétence rare et recherchée)
- **Funnel analysis** : drop-off entre étapes
- **ROAS & CAC** : KPIs marketing payants
- **Time-series** : saisonnalité hebdo, tendance, heures de pointe
- **Pipeline reproductible** : un seul `python build_project.py` regénère tout

---

## 📝 Licence

MIT — voir [`LICENSE`](LICENSE).

---

## 👤 Auteur

**[Fouad MOUTAIROU]**
- [LinkedIn](https://www.linkedin.com/in/fouad-moutairou-044460273/)
- [Portfolio](https://portfolio-fouad.netlify.app/)

---

## 🚀 Pistes d'amélioration

- [ ] **Attribution multi-touch** : passer de last-click à un modèle data-driven (Markov chains)
- [ ] **Forecasting** : Prophet sur le trafic quotidien pour prédire les 30 prochains jours
- [ ] **Customer LTV** : modèle prédictif sur la valeur vie client
- [ ] **A/B testing framework** : ajouter une analyse statistique de tests A/B
- [ ] **Connexion réelle GA4** : remplacer le dataset synthétique par un vrai export BigQuery GA4