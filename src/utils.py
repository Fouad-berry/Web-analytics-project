"""
utils.py
--------
Utilitaires.
"""

import matplotlib.pyplot as plt
import seaborn as sns


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


def set_style():
    """Style cohérent pour toutes les figures."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({
        "figure.figsize": (11, 6),
        "figure.dpi": 110,
        "savefig.dpi": 140,
        "savefig.bbox": "tight",
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
    })


def print_section(title: str):
    line = "=" * 60
    print(f"\n{line}\n{title}\n{line}")


def format_pct(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}%"


def format_currency(value: float) -> str:
    return f"${value:,.2f}"