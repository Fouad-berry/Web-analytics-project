"""
datamarts.py
------------
Construction des 12 datamarts web analytics.

Organisés en 3 thèmes :
  • Trafic       : channel, device, country, daily, hourly heatmap
  • Conversions  : funnel, campaigns, top pages, top products
  • Engagement   : cohort retention, new vs returning
  • KPIs         : globaux
"""

import pandas as pd
import numpy as np


# ============================================================
# KPIs globaux
# ============================================================
def build_global_kpis(sessions: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """KPIs principaux pour les scorecards Looker."""
    return pd.DataFrame([{
        "total_sessions":     len(sessions),
        "total_users":        sessions["user_id"].nunique(),
        "total_pageviews":    int(sessions["page_views"].sum()),
        "total_transactions": int(sessions["converted"].sum()),
        "total_revenue_usd":  round(transactions["revenue_usd"].sum(), 2),
        "total_cost_usd":     round(sessions["session_cost_usd"].sum(), 2),
        "avg_session_duration_sec": round(sessions["duration_seconds"].mean(), 0),
        "bounce_rate_pct":    round(100 * sessions["bounced"].mean(), 2),
        "conversion_rate_pct": round(100 * sessions["converted"].mean(), 2),
        "avg_order_value":    round(transactions["revenue_usd"].sum() /
                                     max(sessions["converted"].sum(), 1), 2),
        "revenue_per_session": round(transactions["revenue_usd"].sum() / len(sessions), 2),
        "pct_new_users":      round(100 * sessions["is_new_user"].mean(), 2),
    }])


# ============================================================
# Trafic
# ============================================================
def build_traffic_by_channel(sessions: pd.DataFrame) -> pd.DataFrame:
    """Performance par canal d'acquisition + ROAS."""
    out = sessions.groupby("channel", observed=True).agg(
        sessions=("session_id", "count"),
        users=("user_id", "nunique"),
        avg_pageviews=("page_views", "mean"),
        avg_duration_sec=("duration_seconds", "mean"),
        bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
        conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
        revenue_usd=("session_revenue_usd", "sum"),
        cost_usd=("session_cost_usd", "sum"),
    ).round(2).reset_index()
    out["traffic_share_pct"] = (100 * out["sessions"] / out["sessions"].sum()).round(2)
    out["roas"] = np.where(out["cost_usd"] > 0,
                            (out["revenue_usd"] / out["cost_usd"]).round(2), np.nan)
    return out.sort_values("sessions", ascending=False)


def build_traffic_by_device(sessions: pd.DataFrame) -> pd.DataFrame:
    out = sessions.groupby("device", observed=True).agg(
        sessions=("session_id", "count"),
        bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
        avg_duration_sec=("duration_seconds", "mean"),
        conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
        revenue_usd=("session_revenue_usd", "sum"),
    ).round(2).reset_index()
    out["share_pct"] = (100 * out["sessions"] / out["sessions"].sum()).round(2)
    return out


def build_traffic_by_country(sessions: pd.DataFrame) -> pd.DataFrame:
    return sessions.groupby("country", observed=True).agg(
        sessions=("session_id", "count"),
        users=("user_id", "nunique"),
        conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
        revenue_usd=("session_revenue_usd", "sum"),
    ).round(2).reset_index().sort_values("sessions", ascending=False)


def build_daily_traffic(sessions: pd.DataFrame) -> pd.DataFrame:
    """Trafic quotidien (saisonnalité, tendance)."""
    return sessions.groupby("session_date", observed=True).agg(
        sessions=("session_id", "count"),
        users=("user_id", "nunique"),
        new_users=("is_new_user", "sum"),
        transactions=("converted", "sum"),
        revenue_usd=("session_revenue_usd", "sum"),
        avg_duration_sec=("duration_seconds", "mean"),
        bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
    ).round(2).reset_index().sort_values("session_date")


def build_hourly_heatmap(sessions: pd.DataFrame) -> pd.DataFrame:
    """Heatmap heure × jour de semaine (engagement)."""
    return sessions.groupby(["session_day_of_week", "session_hour"]).agg(
        sessions=("session_id", "count"),
    ).reset_index()


# ============================================================
# Conversions
# ============================================================
def build_conversion_funnel(sessions: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Funnel : page_view → view_item → add_to_cart → begin_checkout → purchase."""
    steps = ["page_view", "view_item", "add_to_cart", "begin_checkout", "purchase"]
    rows = []
    for step in steps:
        n_sessions = events[events["event_name"] == step]["session_id"].nunique()
        rows.append({
            "step": step,
            "sessions": n_sessions,
            "pct_of_total": round(100 * n_sessions / len(sessions), 2),
        })
    df = pd.DataFrame(rows)
    df["dropoff_pct_from_previous"] = (
        100 * (1 - df["sessions"] / df["sessions"].shift(1).fillna(df["sessions"].iloc[0]))
    ).round(2)
    return df


def build_campaign_performance(sessions: pd.DataFrame) -> pd.DataFrame:
    """ROAS par campagne payante."""
    paid = sessions[sessions["session_cost_usd"] > 0].copy()
    out = paid.groupby(["channel", "campaign"], observed=True).agg(
        sessions=("session_id", "count"),
        cost_usd=("session_cost_usd", "sum"),
        transactions=("converted", "sum"),
        revenue_usd=("session_revenue_usd", "sum"),
    ).round(2).reset_index()
    out["cpa_usd"] = np.where(out["transactions"] > 0,
                               (out["cost_usd"] / out["transactions"]).round(2), np.nan)
    out["roas"] = np.where(out["cost_usd"] > 0,
                            (out["revenue_usd"] / out["cost_usd"]).round(2), np.nan)
    out["conversion_rate_pct"] = (100 * out["transactions"] / out["sessions"]).round(2)
    return out.sort_values("revenue_usd", ascending=False)


def build_top_pages(events: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Top pages par nombre de vues."""
    page_views = events[events["event_name"] == "page_view"]
    out = page_views.groupby("page_path", observed=True).agg(
        page_views=("event_id", "count"),
        unique_sessions=("session_id", "nunique"),
    ).reset_index().sort_values("page_views", ascending=False).head(top_n)
    out["share_pct"] = (100 * out["page_views"] / page_views.shape[0]).round(2)
    return out


def build_top_products(transactions: pd.DataFrame) -> pd.DataFrame:
    """Top produits par revenus."""
    out = transactions.groupby(["product_sku", "product_name", "category"], observed=True).agg(
        units_sold=("quantity", "sum"),
        transactions=("transaction_id", "count"),
        revenue_usd=("revenue_usd", "sum"),
        avg_unit_price=("unit_price_usd", "mean"),
    ).round(2).reset_index().sort_values("revenue_usd", ascending=False)
    out["revenue_share_pct"] = (100 * out["revenue_usd"] / out["revenue_usd"].sum()).round(2)
    return out


# ============================================================
# Engagement & cohorts
# ============================================================
def build_cohort_retention_pivot(sessions: pd.DataFrame) -> pd.DataFrame:
    """Pivot table cohort retention (heatmap-ready)."""
    cohort_table = sessions.groupby(["cohort_week", "activity_week"])["user_id"] \
                            .nunique().reset_index()
    pivot = cohort_table.pivot(index="cohort_week", columns="activity_week",
                                values="user_id").fillna(0)

    def to_retention(row):
        first_val = next((v for v in row if v > 0), 1)
        return (100 * row / first_val).round(2)

    return pivot.apply(to_retention, axis=1)


def build_cohort_long(sessions: pd.DataFrame) -> pd.DataFrame:
    """Cohort retention en format long (Looker-friendly)."""
    cohort_table = sessions.groupby(["cohort_week", "activity_week"])["user_id"] \
                            .nunique().reset_index() \
                            .rename(columns={"user_id": "active_users"})
    sizes = cohort_table.groupby("cohort_week")["active_users"].max().reset_index() \
                .rename(columns={"active_users": "cohort_size"})
    out = cohort_table.merge(sizes, on="cohort_week")
    out["retention_pct"] = (100 * out["active_users"] / out["cohort_size"]).round(2)
    return out


def build_new_vs_returning(sessions: pd.DataFrame) -> pd.DataFrame:
    """Comparaison nouveaux vs récurrents."""
    out = sessions.groupby("is_new_user", observed=True).agg(
        sessions=("session_id", "count"),
        avg_pageviews=("page_views", "mean"),
        avg_duration_sec=("duration_seconds", "mean"),
        bounce_rate_pct=("bounced", lambda s: 100 * s.mean()),
        conversion_rate_pct=("converted", lambda s: 100 * s.mean()),
        revenue_usd=("session_revenue_usd", "sum"),
    ).round(2).reset_index()
    out["user_type"] = out["is_new_user"].map({True: "new", False: "returning"})
    return out[["user_type", "sessions", "avg_pageviews", "avg_duration_sec",
                "bounce_rate_pct", "conversion_rate_pct", "revenue_usd"]]


def build_all(sessions: pd.DataFrame, events: pd.DataFrame,
              transactions: pd.DataFrame) -> dict:
    """Construit les 12 datamarts d'un coup."""
    return {
        "global_kpis":           build_global_kpis(sessions, transactions),
        "traffic_by_channel":    build_traffic_by_channel(sessions),
        "traffic_by_device":     build_traffic_by_device(sessions),
        "traffic_by_country":    build_traffic_by_country(sessions),
        "daily_traffic":         build_daily_traffic(sessions),
        "conversion_funnel":     build_conversion_funnel(sessions, events),
        "campaign_performance":  build_campaign_performance(sessions),
        "top_pages":             build_top_pages(events),
        "top_products":          build_top_products(transactions),
        "cohort_retention":      build_cohort_retention_pivot(sessions),
        "cohort_long":           build_cohort_long(sessions),
        "new_vs_returning":      build_new_vs_returning(sessions),
        "hourly_heatmap":        build_hourly_heatmap(sessions),
    }