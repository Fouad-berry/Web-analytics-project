"""
preprocessing.py
----------------
Enrichissement des sessions avec features temporelles, revenu et engagement.
"""

import pandas as pd


def add_revenue_per_session(sessions: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """Joindre le revenu par session depuis la table transactions."""
    sess_rev = transactions.groupby("session_id")["revenue_usd"].sum().reset_index() \
                .rename(columns={"revenue_usd": "session_revenue_usd"})
    sessions = sessions.merge(sess_rev, on="session_id", how="left")
    sessions["session_revenue_usd"] = sessions["session_revenue_usd"].fillna(0)
    return sessions


def add_time_features(sessions: pd.DataFrame) -> pd.DataFrame:
    """Ajoute toutes les features temporelles utiles pour les analyses."""
    sessions = sessions.copy()
    sessions["session_day_of_week"] = sessions["session_date"].dt.day_name()
    sessions["session_hour"] = sessions["session_start"].dt.hour
    sessions["year_month"] = sessions["session_date"].dt.strftime("%Y-%m")
    sessions["year_week"] = sessions["session_date"].dt.strftime("%Y-W%U")
    sessions["is_weekend"] = sessions["session_date"].dt.dayofweek >= 5
    return sessions


def add_engagement_level(sessions: pd.DataFrame) -> pd.DataFrame:
    """
    Catégorise l'engagement selon le nombre de pages vues :
    - bounced : 1 page
    - low     : 2-3 pages
    - medium  : 4-7 pages
    - high    : 8+ pages
    """
    sessions = sessions.copy()
    sessions["engagement_level"] = pd.cut(
        sessions["page_views"],
        bins=[0, 1, 3, 7, 999],
        labels=["bounced", "low", "medium", "high"]
    )
    return sessions


def add_cohort_week(sessions: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute la cohort_week (semaine de la première session de l'utilisateur)
    et activity_week (semaine de la session courante).
    """
    sessions = sessions.copy()
    sessions["cohort_week"] = sessions.groupby("user_id")["session_date"] \
                                       .transform("min").dt.to_period("W").astype(str)
    sessions["activity_week"] = sessions["session_date"].dt.to_period("W").astype(str)
    return sessions


def enrich(sessions: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    """Pipeline complet d'enrichissement."""
    sessions = add_revenue_per_session(sessions, transactions)
    sessions = add_time_features(sessions)
    sessions = add_engagement_level(sessions)
    sessions = add_cohort_week(sessions)
    return sessions