"""
data_loader.py
--------------
Chargement des 3 tables GA4-like + datamarts.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DATAMARTS_DIR = DATA_DIR / "datamarts"
EXPORTS_DIR = DATA_DIR / "exports"


def load_sessions() -> pd.DataFrame:
    """Charge la table sessions (granularité : 1 ligne par session)."""
    path = RAW_DIR / "sessions.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Introuvable : {path}. Lance `python generate_dataset.py` d'abord."
        )
    return pd.read_csv(path, parse_dates=["session_start", "session_date"])


def load_events() -> pd.DataFrame:
    """Charge la table events (granularité : 1 ligne par événement utilisateur)."""
    path = RAW_DIR / "events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Introuvable : {path}")
    return pd.read_csv(path, parse_dates=["event_timestamp"])


def load_transactions() -> pd.DataFrame:
    """Charge la table transactions (granularité : 1 ligne par produit acheté)."""
    path = RAW_DIR / "transactions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Introuvable : {path}")
    return pd.read_csv(path, parse_dates=["transaction_date"])


def load_processed_sessions() -> pd.DataFrame:
    """Charge les sessions enrichies (après build_project.py)."""
    path = PROCESSED_DIR / "sessions_enriched.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Introuvable : {path}. Lance `python build_project.py` d'abord."
        )
    return pd.read_csv(path, parse_dates=["session_start", "session_date"])


def load_datamart(name: str) -> pd.DataFrame:
    """Charge un datamart par son nom court."""
    filename = name if name.startswith("dm_") else f"dm_{name}"
    if not filename.endswith(".csv"):
        filename += ".csv"
    path = DATAMARTS_DIR / filename
    if not path.exists():
        available = [p.stem for p in DATAMARTS_DIR.glob("dm_*.csv")]
        raise FileNotFoundError(f"Introuvable : {path}\nDisponibles : {available}")
    return pd.read_csv(path)


def save_datamart(df: pd.DataFrame, name: str) -> Path:
    DATAMARTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = name if name.startswith("dm_") else f"dm_{name}"
    if not filename.endswith(".csv"):
        filename += ".csv"
    path = DATAMARTS_DIR / filename
    df.to_csv(path, index=False)
    return path


def save_export(df: pd.DataFrame, filename: str) -> Path:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORTS_DIR / filename
    df.to_csv(path, index=False)
    return path