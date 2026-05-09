"""
build_project.py
----------------
Pipeline complet web analytics :
  1. Charge sessions, events, transactions
  2. Construit 12 datamarts (trafic + conversions + cohorts)
  3. Génère 12 figures PNG
  4. Exporte les CSV pour Looker Studio

Usage :
    python build_project.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# ============================================================
# Configuration
# ============================================================
ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DATAMARTS = ROOT / "data" / "datamarts"
EXPORTS = ROOT / "data" / "exports"
FIGURES = ROOT / "images" / "figures"

for d in [PROCESSED, DATAMARTS, EXPORTS, FIGURES]:
    d.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 140,
    "savefig.bbox": "tight",
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
})

CHANNEL_COLORS = {
    "Organic Search": "#4285F4",
    "Direct":         "#34A853",
    "Paid Search":    "#EA4335",
    "Social":         "#9C27B0",
    "Email":          "#FF9800",
    "Referral":       "#00BCD4",
    "Display":        "#795548",
}
DEVICE_COLORS = {"mobile": "#3498db", "desktop": "#9b59b6", "tablet": "#e67e22"}

# ============================================================
# 1. CHARGEMENT
# ============================================================
print("▶ [1/4] Chargement des données…")
sessions = pd.read_csv(RAW / "sessions.csv", parse_dates=["session_start", "session_date"])
events = pd.read_csv(RAW / "events.csv", parse_dates=["event_timestamp"])
trans = pd.read_csv(RAW / "transactions.csv", parse_dates=["transaction_date"])

print(f"   Sessions     : {len(sessions):,}")
print(f"   Events       : {len(events):,}")
print(f"   Transactions : {len(trans):,}")

# ============================================================
# 2. ENRICHISSEMENT
# ============================================================
print("▶ [2/4] Enrichissement…")

# Revenu par session
sess_revenue = trans.groupby("session_id")["revenue_usd"].sum().reset_index() \
                    .rename(columns={"revenue_usd": "session_revenue_usd"})
sessions = sessions.merge(sess_revenue, on="session_id", how="left")
sessions["session_revenue_usd"] = sessions["session_revenue_usd"].fillna(0)

# Features temporelles
sessions["session_day_of_week"] = sessions["session_date"].dt.day_name()
sessions["session_hour"] = sessions["session_start"].dt.hour
sessions["year_month"] = sessions["session_date"].dt.strftime("%Y-%m")
sessions["year_week"] = sessions["session_date"].dt.strftime("%Y-W%U")
sessions["is_weekend"] = sessions["session_date"].dt.dayofweek >= 5

# Engagement bucket
sessions["engagement_level"] = pd.cut(
    sessions["page_views"], bins=[0, 1, 3, 7, 999],
    labels=["bounced", "low", "medium", "high"]
)

sessions.to_csv(PROCESSED / "sessions_enriched.csv", index=False)
print(f"   ✓ Sessions enrichies : {PROCESSED / 'sessions_enriched.csv'}")

# ============================================================
# 3. DATAMARTS
# ============================================================
print("▶ [3/4] Construction des 12 datamarts…")

# DM1 : KPIs globaux
dm_kpi = pd.DataFrame([{
    "total_sessions":     len(sessions),
    "total_users":        sessions["user_id"].nunique(),
    "total_pageviews":    int(sessions["page_views"].sum()),
    "total_transactions": len(trans["session_id"].unique()) if len(trans) else 0,
    "total_revenue_usd":  round(trans["revenue_usd"].sum(), 2),
    "total_cost_usd":     round(sessions["session_cost_usd"].sum(), 2),
    "avg_session_duration_sec": round(sessions["duration_seconds"].mean(), 0),
    "bounce_rate_pct":    round(100 * sessions["bounced"].mean(), 2),
    "conversion_rate_pct": round(100 * sessions["converted"].mean(), 2),
    "avg_order_value":    round(trans["revenue_usd"].sum() /
                                 max(len(trans["session_id"].unique()), 1), 2),
    "revenue_per_session": round(trans["revenue_usd"].sum() / len(sessions), 2),
    "pct_new_users":      round(100 * sessions["is_new_user"].mean(), 2),
    "first_session_date": str(sessions["session_date"].min().date()),
    "last_session_date":  str(sessions["session_date"].max().date()),
}])
dm_kpi.to_csv(DATAMARTS / "dm_global_kpis.csv", index=False)

# DM2 : Trafic par canal
dm_channel = sessions.groupby("channel", observed=True).agg(
    sessions=("session_id", "count"),
    users=("user_id", "nunique"),
    avg_pageviews=("page_views", "mean"),
    avg_duration_sec=("duration_seconds", "mean"),
    bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
    conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
    revenue_usd=("session_revenue_usd", "sum"),
    cost_usd=("session_cost_usd", "sum"),
).round(2).reset_index()
dm_channel["traffic_share_pct"] = (100 * dm_channel["sessions"] /
                                    dm_channel["sessions"].sum()).round(2)
dm_channel["roas"] = np.where(dm_channel["cost_usd"] > 0,
                               (dm_channel["revenue_usd"] / dm_channel["cost_usd"]).round(2),
                               np.nan)
dm_channel = dm_channel.sort_values("sessions", ascending=False)
dm_channel.to_csv(DATAMARTS / "dm_traffic_by_channel.csv", index=False)

# DM3 : Trafic par device
dm_device = sessions.groupby("device", observed=True).agg(
    sessions=("session_id", "count"),
    bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
    avg_duration_sec=("duration_seconds", "mean"),
    conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
    revenue_usd=("session_revenue_usd", "sum"),
).round(2).reset_index()
dm_device["share_pct"] = (100 * dm_device["sessions"] / dm_device["sessions"].sum()).round(2)
dm_device.to_csv(DATAMARTS / "dm_traffic_by_device.csv", index=False)

# DM4 : Trafic par pays
dm_country = sessions.groupby("country", observed=True).agg(
    sessions=("session_id", "count"),
    users=("user_id", "nunique"),
    conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
    revenue_usd=("session_revenue_usd", "sum"),
).round(2).reset_index().sort_values("sessions", ascending=False)
dm_country.to_csv(DATAMARTS / "dm_traffic_by_country.csv", index=False)

# DM5 : Trafic quotidien (timeline)
dm_daily = sessions.groupby("session_date", observed=True).agg(
    sessions=("session_id", "count"),
    users=("user_id", "nunique"),
    new_users=("is_new_user", "sum"),
    transactions=("converted", "sum"),
    revenue_usd=("session_revenue_usd", "sum"),
    avg_duration_sec=("duration_seconds", "mean"),
    bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
).round(2).reset_index().sort_values("session_date")
dm_daily.to_csv(DATAMARTS / "dm_daily_traffic.csv", index=False)

# DM6 : Funnel de conversion (à partir des events)
funnel_steps = ["page_view", "view_item", "add_to_cart", "begin_checkout", "purchase"]
funnel_counts = []
for step in funnel_steps:
    n_sessions_with_step = events[events["event_name"] == step]["session_id"].nunique()
    funnel_counts.append({
        "step": step,
        "sessions": n_sessions_with_step,
        "pct_of_total": round(100 * n_sessions_with_step / len(sessions), 2),
    })
dm_funnel = pd.DataFrame(funnel_counts)
# Drop-off entre étapes
dm_funnel["dropoff_pct_from_previous"] = (
    100 * (1 - dm_funnel["sessions"] / dm_funnel["sessions"].shift(1).fillna(dm_funnel["sessions"].iloc[0]))
).round(2)
dm_funnel.to_csv(DATAMARTS / "dm_conversion_funnel.csv", index=False)

# DM7 : Performance des campagnes payantes
paid = sessions[sessions["session_cost_usd"] > 0].copy()
dm_campaign = paid.groupby(["channel", "campaign"], observed=True).agg(
    sessions=("session_id", "count"),
    cost_usd=("session_cost_usd", "sum"),
    transactions=("converted", "sum"),
    revenue_usd=("session_revenue_usd", "sum"),
).round(2).reset_index()
dm_campaign["cpa_usd"] = np.where(dm_campaign["transactions"] > 0,
                                   (dm_campaign["cost_usd"] / dm_campaign["transactions"]).round(2),
                                   np.nan)
dm_campaign["roas"] = np.where(dm_campaign["cost_usd"] > 0,
                                (dm_campaign["revenue_usd"] / dm_campaign["cost_usd"]).round(2),
                                np.nan)
dm_campaign["conversion_rate_pct"] = (100 * dm_campaign["transactions"] /
                                       dm_campaign["sessions"]).round(2)
dm_campaign = dm_campaign.sort_values("revenue_usd", ascending=False)
dm_campaign.to_csv(DATAMARTS / "dm_campaign_performance.csv", index=False)

# DM8 : Top pages
page_views = events[events["event_name"] == "page_view"]
dm_pages = page_views.groupby("page_path", observed=True).agg(
    page_views=("event_id", "count"),
    unique_sessions=("session_id", "nunique"),
).reset_index().sort_values("page_views", ascending=False).head(20)
dm_pages["share_pct"] = (100 * dm_pages["page_views"] / page_views.shape[0]).round(2)
dm_pages.to_csv(DATAMARTS / "dm_top_pages.csv", index=False)

# DM9 : Top produits
dm_products = trans.groupby(["product_sku", "product_name", "category"], observed=True).agg(
    units_sold=("quantity", "sum"),
    transactions=("transaction_id", "count"),
    revenue_usd=("revenue_usd", "sum"),
    avg_unit_price=("unit_price_usd", "mean"),
).round(2).reset_index().sort_values("revenue_usd", ascending=False)
dm_products["revenue_share_pct"] = (100 * dm_products["revenue_usd"] /
                                     dm_products["revenue_usd"].sum()).round(2)
dm_products.to_csv(DATAMARTS / "dm_top_products.csv", index=False)

# DM10 : Cohort retention (semaine d'acquisition × semaine d'activité)
print("   • Calcul des cohortes…")
sessions["cohort_week"] = sessions.groupby("user_id")["session_date"] \
                                   .transform("min").dt.to_period("W").astype(str)
sessions["activity_week"] = sessions["session_date"].dt.to_period("W").astype(str)

# On compte les utilisateurs uniques par (cohort, activity)
cohort_table = sessions.groupby(["cohort_week", "activity_week"])["user_id"].nunique().reset_index()
cohort_pivot = cohort_table.pivot(index="cohort_week", columns="activity_week",
                                   values="user_id").fillna(0)

# Conversion en taux de rétention (semaine 0 = 100%)
cohort_size = cohort_pivot.iloc[:, 0]  # ATTENTION: ça ne marche que si la première colonne = cohort
# Méthode plus robuste : pour chaque cohort, identifier sa propre semaine 0
def to_retention(row):
    first_val = next((v for v in row if v > 0), 1)
    return (100 * row / first_val).round(2)
cohort_retention = cohort_pivot.apply(to_retention, axis=1)
cohort_retention.to_csv(DATAMARTS / "dm_cohort_retention.csv")

# On reconstruit aussi un format long (plus facile pour Looker)
cohort_long = cohort_table.copy()
cohort_long.columns = ["cohort_week", "activity_week", "active_users"]
# Joindre la taille de cohort
cohort_size_df = cohort_long.groupby("cohort_week")["active_users"].max().reset_index() \
                              .rename(columns={"active_users": "cohort_size"})
cohort_long = cohort_long.merge(cohort_size_df, on="cohort_week")
cohort_long["retention_pct"] = (100 * cohort_long["active_users"] /
                                 cohort_long["cohort_size"]).round(2)
cohort_long.to_csv(DATAMARTS / "dm_cohort_long.csv", index=False)

# DM11 : Engagement par new vs returning
dm_user_type = sessions.groupby("is_new_user", observed=True).agg(
    sessions=("session_id", "count"),
    avg_pageviews=("page_views", "mean"),
    avg_duration_sec=("duration_seconds", "mean"),
    bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
    conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
    revenue_usd=("session_revenue_usd", "sum"),
).round(2).reset_index()
dm_user_type["user_type"] = dm_user_type["is_new_user"].map({True: "new", False: "returning"})
dm_user_type = dm_user_type[["user_type", "sessions", "avg_pageviews", "avg_duration_sec",
                              "bounce_rate_pct", "conversion_rate_pct", "revenue_usd"]]
dm_user_type.to_csv(DATAMARTS / "dm_new_vs_returning.csv", index=False)

# DM12 : Heatmap heure × jour de semaine (engagement)
dm_hourly = sessions.groupby(["session_day_of_week", "session_hour"]).agg(
    sessions=("session_id", "count"),
).reset_index()
dm_hourly.to_csv(DATAMARTS / "dm_hourly_heatmap.csv", index=False)

print(f"   ✓ 12 datamarts dans {DATAMARTS}/")

# Exports Looker
sessions.to_csv(EXPORTS / "main_sessions.csv", index=False)
trans.to_csv(EXPORTS / "main_transactions.csv", index=False)
dm_kpi.to_csv(EXPORTS / "global_kpis.csv", index=False)
dm_channel.to_csv(EXPORTS / "by_channel.csv", index=False)
dm_device.to_csv(EXPORTS / "by_device.csv", index=False)
dm_daily.to_csv(EXPORTS / "daily_traffic.csv", index=False)
dm_funnel.to_csv(EXPORTS / "funnel.csv", index=False)
dm_campaign.to_csv(EXPORTS / "campaigns.csv", index=False)
dm_products.to_csv(EXPORTS / "products.csv", index=False)
cohort_long.to_csv(EXPORTS / "cohort_long.csv", index=False)

# ============================================================
# 4. FIGURES
# ============================================================
print("▶ [4/4] Génération des 12 figures…")

# Fig 1 : Trafic quotidien
fig, ax = plt.subplots(figsize=(14, 5.5))
ax.plot(dm_daily["session_date"], dm_daily["sessions"],
        linewidth=2, color="#2c3e50", marker="o", markersize=3)
ax.fill_between(dm_daily["session_date"], dm_daily["sessions"], alpha=0.2, color="#3498db")
ax.set_title("Évolution quotidienne des sessions (jan-juin 2025)")
ax.set_xlabel("Date"); ax.set_ylabel("Sessions")
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
plt.savefig(FIGURES / "01_daily_traffic.png")
plt.close()

# Fig 2 : Trafic par canal (donut)
fig, ax = plt.subplots(figsize=(10, 7))
colors_c = [CHANNEL_COLORS.get(c, "#888") for c in dm_channel["channel"]]
wedges, _, autotexts = ax.pie(
    dm_channel["sessions"], labels=dm_channel["channel"], autopct="%.1f%%",
    colors=colors_c, startangle=90,
    wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
    textprops={"fontweight": "bold", "fontsize": 10}
)
ax.set_title("Répartition du trafic par canal d'acquisition")
plt.savefig(FIGURES / "02_traffic_by_channel.png")
plt.close()

# Fig 3 : Funnel de conversion
fig, ax = plt.subplots(figsize=(11, 6))
data = dm_funnel.iloc[::-1]  # inverser pour avoir page_view en bas
colors_f = ["#2ecc71", "#3498db", "#9b59b6", "#f39c12", "#e74c3c"]
bars = ax.barh(data["step"], data["sessions"], color=colors_f, edgecolor="black")
for bar, val, pct in zip(bars, data["sessions"], data["pct_of_total"]):
    ax.text(val + 1000, bar.get_y() + bar.get_height()/2,
            f"{val:,} ({pct:.1f}%)", va="center", fontweight="bold")
ax.set_title("Funnel de conversion : du page_view à l'achat")
ax.set_xlabel("Sessions atteignant cette étape")
plt.savefig(FIGURES / "03_conversion_funnel.png")
plt.close()

# Fig 4 : Conversion rate par canal
fig, ax = plt.subplots(figsize=(11, 6))
data = dm_channel.sort_values("conversion_rate_pct")
colors_c = [CHANNEL_COLORS.get(c, "#888") for c in data["channel"]]
bars = ax.barh(data["channel"], data["conversion_rate_pct"],
               color=colors_c, edgecolor="black")
for bar, val in zip(bars, data["conversion_rate_pct"]):
    ax.text(val + 0.05, bar.get_y() + bar.get_height()/2,
            f"{val:.2f}%", va="center", fontweight="bold")
ax.set_title("Taux de conversion par canal d'acquisition")
ax.set_xlabel("Taux de conversion (%)")
plt.savefig(FIGURES / "04_conversion_rate_by_channel.png")
plt.close()

# Fig 5 : Bounce rate par device
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
data = dm_device.sort_values("share_pct", ascending=False)

# Volume sessions
colors_d = [DEVICE_COLORS.get(d, "#888") for d in data["device"]]
bars = axes[0].bar(data["device"], data["sessions"], color=colors_d, edgecolor="black")
for bar, val, pct in zip(bars, data["sessions"], data["share_pct"]):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                 f"{val:,}\n({pct:.1f}%)", ha="center", fontweight="bold")
axes[0].set_title("Sessions par device")
axes[0].set_ylabel("Sessions")

# Bounce rate
bars = axes[1].bar(data["device"], data["bounce_rate_pct"], color=colors_d, edgecolor="black")
for bar, val in zip(bars, data["bounce_rate_pct"]):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f"{val:.1f}%", ha="center", fontweight="bold")
axes[1].set_title("Bounce rate par device")
axes[1].set_ylabel("Bounce rate (%)")
plt.suptitle("Performance par device", fontweight="bold", fontsize=15)
plt.savefig(FIGURES / "05_device_performance.png")
plt.close()

# Fig 6 : ROAS par campagne
fig, ax = plt.subplots(figsize=(11, 6))
data = dm_campaign.dropna(subset=["roas"]).sort_values("roas").tail(10)
colors_r = ["#e74c3c" if r < 1 else "#f39c12" if r < 3 else "#2ecc71" for r in data["roas"]]
bars = ax.barh(data["campaign"] + " (" + data["channel"] + ")", data["roas"],
               color=colors_r, edgecolor="black")
ax.axvline(1, color="black", linestyle="--", label="Break-even (ROAS=1)")
for bar, val, cost, rev in zip(bars, data["roas"], data["cost_usd"], data["revenue_usd"]):
    ax.text(val + 0.1, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}x (${rev:.0f}/${cost:.0f})", va="center",
            fontweight="bold", fontsize=9)
ax.set_title("Top 10 campagnes par ROAS\n(rouge = perte, vert = ROAS > 3x)")
ax.set_xlabel("ROAS (Return on Ad Spend)")
ax.legend()
plt.savefig(FIGURES / "06_roas_by_campaign.png")
plt.close()

# Fig 7 : Cohort retention heatmap (limité aux ~12 premières semaines pour lisibilité)
fig, ax = plt.subplots(figsize=(13, 8))
# Prendre les 12 premières cohortes et 12 premières semaines
top_cohorts = cohort_retention.iloc[:12, :12]
sns.heatmap(top_cohorts, annot=True, fmt=".0f", cmap="YlGnBu",
            cbar_kws={"label": "% rétention"}, ax=ax,
            vmin=0, vmax=100, linewidths=0.4)
ax.set_title("Cohort retention — % d'utilisateurs actifs par semaine après acquisition")
ax.set_xlabel("Semaine d'activité"); ax.set_ylabel("Semaine d'acquisition (cohort)")
plt.savefig(FIGURES / "07_cohort_retention.png")
plt.close()

# Fig 8 : Heatmap heure × jour de semaine (engagement)
fig, ax = plt.subplots(figsize=(13, 5))
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
heatmap_data = sessions.pivot_table(values="session_id", index="session_day_of_week",
                                     columns="session_hour", aggfunc="count", fill_value=0)
heatmap_data = heatmap_data.reindex(day_order)
sns.heatmap(heatmap_data, cmap="YlOrRd", ax=ax,
            cbar_kws={"label": "Nombre de sessions"}, linewidths=0.2)
ax.set_title("Heatmap d'engagement : sessions par heure et jour de la semaine")
ax.set_xlabel("Heure"); ax.set_ylabel("")
plt.savefig(FIGURES / "08_engagement_heatmap.png")
plt.close()

# Fig 9 : Top pages
fig, ax = plt.subplots(figsize=(11, 7))
data = dm_pages.head(10).sort_values("page_views")
bars = ax.barh(data["page_path"], data["page_views"],
               color=sns.color_palette("rocket_r", len(data)), edgecolor="black")
for bar, val, pct in zip(bars, data["page_views"], data["share_pct"]):
    ax.text(val + 200, bar.get_y() + bar.get_height()/2,
            f"{val:,} ({pct:.1f}%)", va="center", fontweight="bold", fontsize=9)
ax.set_title("Top 10 pages par nombre de vues")
ax.set_xlabel("Vues")
plt.savefig(FIGURES / "09_top_pages.png")
plt.close()

# Fig 10 : Top produits par revenus
fig, ax = plt.subplots(figsize=(11, 7))
data = dm_products.head(10).sort_values("revenue_usd")
bars = ax.barh(data["product_name"], data["revenue_usd"],
               color=sns.color_palette("viridis", len(data)), edgecolor="black")
for bar, val, units, pct in zip(bars, data["revenue_usd"], data["units_sold"], data["revenue_share_pct"]):
    ax.text(val + 200, bar.get_y() + bar.get_height()/2,
            f"${val:,.0f} ({int(units)} u., {pct:.1f}%)", va="center",
            fontweight="bold", fontsize=9)
ax.set_title("Top 10 produits par revenus")
ax.set_xlabel("Revenus (USD)")
plt.savefig(FIGURES / "10_top_products.png")
plt.close()

# Fig 11 : New vs returning
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, metric, title in zip(
    axes,
    ["sessions", "conversion_rate_pct", "avg_pageviews"],
    ["Sessions", "Taux de conversion (%)", "Pages vues moyennes"],
):
    colors_u = ["#3498db", "#e67e22"]
    bars = ax.bar(dm_user_type["user_type"], dm_user_type[metric],
                  color=colors_u, edgecolor="black")
    for bar, val in zip(bars, dm_user_type[metric]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02 * max(dm_user_type[metric]),
                f"{val:,.2f}" if isinstance(val, float) else f"{val:,}",
                ha="center", fontweight="bold")
    ax.set_title(title)
plt.suptitle("New vs Returning users", fontweight="bold", fontsize=15)
plt.savefig(FIGURES / "11_new_vs_returning.png")
plt.close()

# Fig 12 : Revenu quotidien + cumul
fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(dm_daily["session_date"], dm_daily["revenue_usd"],
       color="#3498db", alpha=0.6, label="Revenu quotidien")
ax.set_xlabel("Date"); ax.set_ylabel("Revenu quotidien (USD)", color="#3498db")
ax.tick_params(axis="y", labelcolor="#3498db")

ax2 = ax.twinx()
ax2.plot(dm_daily["session_date"], dm_daily["revenue_usd"].cumsum(),
         color="#e74c3c", linewidth=2.5, label="Revenu cumulé")
ax2.set_ylabel("Revenu cumulé (USD)", color="#e74c3c")
ax2.tick_params(axis="y", labelcolor="#e74c3c")
ax.set_title("Revenu quotidien et cumulé")
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
plt.savefig(FIGURES / "12_revenue_timeline.png")
plt.close()

print(f"   ✓ 12 figures dans {FIGURES}/")
print("\n✨ Pipeline terminé !")