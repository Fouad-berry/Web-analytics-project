# 🔬 Méthodologie

## 1. Génération du dataset (synthétique)

Le projet utilise un dataset synthétique pour garantir la **reproductibilité**. Le script `generate_dataset.py` simule des patterns réalistes :

- **Saisonnalité hebdomadaire** : pic mardi-mercredi (×1.20), creux samedi-dimanche (×0.78)
- **Tendance** : +20 % de croissance entre janvier et juin
- **Distribution channel** : Organic Search domine (32 %), suivi de Direct (22 %), Social (14 %), Paid Search (12 %)
- **Conversion rates différenciés** : Email (7.5 %) > Paid Search (5.5 %) > Direct (4.5 %) > Organic (2.5 %) > Social (1.8 %) > Display (1.2 %)
- **Mobile-first** : 62 % du trafic, mais convertit moins bien que le desktop (× 0.7)
- **Heures de pointe** : pic 10h-12h, creux 2h-5h
- **Funnel d'attrition** : ~15 % vue → produit, 14 % → panier, ~1.3 % → achat (cohérent avec benchmarks)

Ces patterns rendent le dataset crédible pour démontrer toutes les techniques d'analyse web.

## 2. Modèle GA4

Le projet adopte le **modèle Google Analytics 4** :
- 1 ligne par **session** dans `sessions.csv`
- 1 ligne par **événement** dans `events.csv` (page_view, view_item, add_to_cart, begin_checkout, purchase)
- 1 ligne par **produit acheté** dans `transactions.csv`

Cette structure permet de répliquer fidèlement ce qu'on aurait avec un export GA4 BigQuery.

## 3. Enrichissement (`src/preprocessing.py`)

1. **Jointure revenu** : `transactions.csv` → `sessions.csv` pour avoir `session_revenue_usd` au grain session
2. **Features temporelles** : `session_day_of_week`, `session_hour`, `year_month`, `year_week`, `is_weekend`
3. **Engagement bucket** : `bounced` / `low` / `medium` / `high` selon `page_views`
4. **Cohort weeks** : `cohort_week` = semaine de la première session du user, `activity_week` = semaine courante

## 4. Construction des 12 datamarts

Chaque datamart répond à **une question business précise** et est directement utilisable dans Looker Studio sans jointure.

**Cas particulier de la cohort retention** : on produit deux formats car Looker Studio préfère le format long, mais le pivot est plus pratique pour les heatmaps Python :
- `dm_cohort_retention.csv` : pivot (cohort × activity_week)
- `dm_cohort_long.csv` : long (1 ligne par cohort × activity_week, avec retention_pct)

## 5. Calcul des KPIs

| KPI | Formule |
|-----|---------|
| **Conversion rate** | `transactions / sessions × 100` |
| **Bounce rate** | `bounced_sessions / total_sessions × 100` |
| **AOV** (Average Order Value) | `total_revenue / total_transactions` |
| **Revenue per session** | `total_revenue / total_sessions` |
| **CAC** (Customer Acquisition Cost) | `total_paid_cost / paid_conversions` |
| **ROAS** (Return on Ad Spend) | `revenue / cost` |
| **CPA** (Cost per Acquisition) | `cost / transactions` |
| **Retention rate** | `users actifs en semaine N / cohort size × 100` |

## 6. Visualisations

**Choix design** :
- **Couleurs Google** pour les canaux (Organic = bleu Google, Paid Search = rouge Google…)
- **Annotations directes** sur chaque graphique pour éviter la lecture d'axe
- **Format dates** : `Jan`, `Feb`… au lieu de `2025-01-01` (lisibilité)
- **DPI=140** pour rendu net sur GitHub

## 7. Limitations

- **Pas d'attribution multi-touch** : on travaille en last-click. Pour une vraie attribution, il faudrait reconstruire le parcours complet d'un user (multi-sessions) et appliquer un modèle (linear, time-decay, position-based, ou data-driven Markov).
- **Pas de LTV** : impossible sans données plus longues (12+ mois) et un identifiant client stable.
- **Pas de coûts SEO/Email** : seuls les canaux strictement paid (Paid Search, Social, Display) ont un coût attribué. Les coûts SEO et email sont des coûts fixes non répartis.
- **Dataset synthétique** : les valeurs absolues n'ont pas de sens business, seuls les patterns relatifs sont pertinents.

## 8. Pour brancher de vraies données

Le pipeline est conçu pour être **agnostique de la source**. Pour brancher GA4 réel :

```python
# 1. Export GA4 → BigQuery (gratuit, à activer dans Property Settings)
# 2. Requêter BigQuery pour produire les 3 tables CSV
# 3. Les déposer dans data/raw/
# 4. python build_project.py → tout est régénéré
```

Tutoriel complet : [GA4 BigQuery Export](https://support.google.com/analytics/answer/9358801).

## 9. Pistes d'amélioration

- **Attribution multi-touch** avec chaînes de Markov (`pip install ChannelAttribution`)
- **Forecasting** quotidien avec Prophet (saisonnalité hebdo + tendance déjà en place)
- **A/B testing framework** : tests statistiques (t-test, chi²) sur métriques de conversion
- **Customer LTV** : modélisation prédictive (BG/NBD + Gamma-Gamma) avec `lifetimes`
- **Funnel par segment** : recalculer le funnel pour chaque combinaison (canal × device) pour identifier les segments où optimiser