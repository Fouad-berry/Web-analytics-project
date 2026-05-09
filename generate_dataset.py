"""
generate_dataset.py
-------------------
Génère un dataset web analytics synthétique réaliste pour un site e-commerce.

Trois tables produites (modèle GA4-like) :
  • sessions.csv      — 50 000 sessions sur 6 mois
  • events.csv        — ~400 000 événements (page_view, click, add_to_cart, purchase…)
  • transactions.csv  — ~3 000 commandes complétées

Pourquoi synthétique ?
- Pas de problème de scraping / RGPD / TOS
- Reproductible : `python generate_dataset.py` régénère les mêmes données
- Volume contrôlé pour démo
- Patterns réalistes : saisonnalité hebdo, funnel d'attrition réaliste, cohort retention décroissante

Pour un vrai projet : remplacer par un export GA4 BigQuery, une source Mixpanel, etc.
"""

from pathlib import Path
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

OUT = Path(__file__).resolve().parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

# ============================================================
# Configuration globale
# ============================================================
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 6, 30)
N_DAYS = (END_DATE - START_DATE).days + 1
N_USERS = 15_000
N_SESSIONS = 50_000

# ============================================================
# Référentiels
# ============================================================
CHANNELS = {
    # canal: (poids dans le mix, conversion_rate moyen)
    "Organic Search":  (0.32, 0.025),
    "Direct":          (0.22, 0.045),
    "Paid Search":     (0.12, 0.055),
    "Social":          (0.14, 0.018),
    "Email":           (0.08, 0.075),
    "Referral":        (0.07, 0.030),
    "Display":         (0.05, 0.012),
}
DEVICES = {"mobile": 0.62, "desktop": 0.30, "tablet": 0.08}
COUNTRIES = {
    "France": 0.40, "USA": 0.18, "UK": 0.12, "Germany": 0.10,
    "Spain": 0.08, "Italy": 0.06, "Belgium": 0.03, "Canada": 0.03,
}
BROWSERS = {"Chrome": 0.55, "Safari": 0.22, "Firefox": 0.10,
            "Edge": 0.08, "Samsung Internet": 0.05}
PAGES = {
    "/": 0.30,
    "/category/sneakers": 0.12,
    "/category/running": 0.10,
    "/category/boots": 0.07,
    "/product/nike-air-max": 0.08,
    "/product/adidas-ultraboost": 0.06,
    "/product/puma-suede": 0.05,
    "/cart": 0.06,
    "/checkout": 0.04,
    "/account": 0.04,
    "/blog/running-tips": 0.03,
    "/blog/shoe-care": 0.03,
    "/contact": 0.02,
}
PRODUCTS = [
    ("SKU001", "Nike Air Max", "Sneakers",   119.99),
    ("SKU002", "Adidas Ultraboost", "Running", 179.99),
    ("SKU003", "Puma Suede", "Casual",         79.99),
    ("SKU004", "Reebok Classic", "Casual",     69.99),
    ("SKU005", "New Balance 574", "Sneakers",  99.99),
    ("SKU006", "Skechers Sport", "Sports",     59.99),
    ("SKU007", "Timberland Boots", "Boots",   149.99),
    ("SKU008", "Vans Old Skool", "Casual",     64.99),
    ("SKU009", "Converse Chuck Taylor", "Casual", 54.99),
    ("SKU010", "Nike Pegasus", "Running",     129.99),
]
CAMPAIGNS = {
    "Paid Search": ["brand_search", "shoes_generic", "running_keywords", "competitor"],
    "Social":      ["fb_retargeting", "ig_lookalike", "tiktok_brand", "fb_prospecting"],
    "Email":       ["weekly_newsletter", "abandoned_cart", "win_back", "post_purchase"],
    "Display":     ["display_retarget", "youtube_brand", "programmatic"],
}

def weighted_choice(d: dict):
    keys = list(d.keys())
    weights = [d[k] if not isinstance(d[k], tuple) else d[k][0] for k in keys]
    return random.choices(keys, weights=weights)[0]

# ============================================================
# 1. SESSIONS
# ============================================================
print("▶ Génération des sessions…")
sessions_data = []

# Saisonnalité hebdo : moins le week-end, pic mardi-mercredi
def weekday_factor(date):
    return [1.10, 1.18, 1.20, 1.15, 1.05, 0.85, 0.78][date.weekday()]

# Tendance : croissance linéaire de +20% sur 6 mois
def trend_factor(day_idx):
    return 1.0 + 0.20 * (day_idx / N_DAYS)

# Sessions par jour
sessions_per_day = []
for i in range(N_DAYS):
    date = START_DATE + timedelta(days=i)
    base = N_SESSIONS / N_DAYS
    n = int(base * weekday_factor(date) * trend_factor(i) * np.random.uniform(0.85, 1.15))
    sessions_per_day.append((date, n))

# Réajuster pour atteindre exactement N_SESSIONS
total = sum(n for _, n in sessions_per_day)
ratio = N_SESSIONS / total
sessions_per_day = [(d, max(1, int(n * ratio))) for d, n in sessions_per_day]

# Pool d'utilisateurs (certains reviennent)
user_ids = [f"U{i:06d}" for i in range(1, N_USERS + 1)]

session_id_counter = 1
for date, n_sessions_today in sessions_per_day:
    for _ in range(n_sessions_today):
        session_id = f"S{session_id_counter:07d}"
        session_id_counter += 1

        user_id = random.choice(user_ids)  # certains users auront plusieurs sessions
        is_new_user = random.random() < 0.55  # 55 % new visitors
        channel = weighted_choice(CHANNELS)
        device = weighted_choice(DEVICES)
        country = weighted_choice(COUNTRIES)
        browser = weighted_choice(BROWSERS)

        # Heure aléatoire dans la journée (biais vers heures de bureau)
        hour_weights = np.array([1, 0.5, 0.5, 0.5, 1, 2, 3, 4,
                                  5, 7, 8, 9, 8, 7, 7, 6,
                                  6, 6, 6, 5, 4, 3, 2, 1.5])
        hour_weights = hour_weights / hour_weights.sum()
        hour = int(np.random.choice(range(24), p=hour_weights))
        minute = random.randint(0, 59)
        session_start = date.replace(hour=hour, minute=minute,
                                     second=random.randint(0, 59))

        # Durée et pages vues : dépendent du device et du channel
        if channel in ["Email", "Direct"]:
            n_pages = max(1, int(np.random.exponential(scale=4)))
            duration_sec = max(20, int(np.random.gamma(2, 90)))
        else:
            n_pages = max(1, int(np.random.exponential(scale=2.5)))
            duration_sec = max(10, int(np.random.gamma(1.5, 80)))

        if device == "mobile":
            duration_sec = int(duration_sec * 0.85)

        bounced = (n_pages == 1)

        # Conversion ?
        base_conv = CHANNELS[channel][1]
        if device == "desktop":
            base_conv *= 1.4
        if country in ["France", "USA"]:
            base_conv *= 1.2
        if is_new_user:
            base_conv *= 0.6
        converted = (random.random() < base_conv) and (n_pages >= 3)

        # Campagne (seulement pour les canaux paid)
        campaign = None
        if channel in CAMPAIGNS:
            campaign = random.choice(CAMPAIGNS[channel])

        # Coût d'acquisition (uniquement paid)
        cost = 0.0
        if channel == "Paid Search":
            cost = round(np.random.uniform(0.45, 2.50), 2)
        elif channel == "Social":
            cost = round(np.random.uniform(0.25, 1.20), 2)
        elif channel == "Display":
            cost = round(np.random.uniform(0.05, 0.40), 2)

        sessions_data.append({
            "session_id":      session_id,
            "user_id":         user_id,
            "session_start":   session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "session_date":    date.strftime("%Y-%m-%d"),
            "channel":         channel,
            "campaign":        campaign or "",
            "device":          device,
            "country":         country,
            "browser":         browser,
            "is_new_user":     is_new_user,
            "page_views":      n_pages,
            "duration_seconds": duration_sec,
            "bounced":         bounced,
            "converted":       converted,
            "session_cost_usd": cost,
        })

df_sessions = pd.DataFrame(sessions_data)
df_sessions.to_csv(OUT / "sessions.csv", index=False)
print(f"   ✓ {len(df_sessions)} sessions → {OUT / 'sessions.csv'}")

# ============================================================
# 2. TRANSACTIONS (uniquement les sessions converties)
# ============================================================
print("▶ Génération des transactions…")
trans_data = []
trans_id = 1
for _, s in df_sessions[df_sessions["converted"]].iterrows():
    n_items = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]
    products = random.sample(PRODUCTS, k=min(n_items, len(PRODUCTS)))
    for sku, name, cat, price in products:
        qty = random.choices([1, 2, 3], weights=[0.80, 0.15, 0.05])[0]
        # Discount aléatoire (souvent 0)
        discount = round(random.choices([0, 0.10, 0.15, 0.20],
                                        weights=[0.65, 0.18, 0.12, 0.05])[0] * price * qty, 2)
        revenue = round(price * qty - discount, 2)
        trans_data.append({
            "transaction_id":   f"T{trans_id:06d}",
            "session_id":       s["session_id"],
            "user_id":          s["user_id"],
            "transaction_date": s["session_date"],
            "product_sku":      sku,
            "product_name":     name,
            "category":         cat,
            "quantity":         qty,
            "unit_price_usd":   price,
            "discount_usd":     discount,
            "revenue_usd":      revenue,
        })
        trans_id += 1

df_trans = pd.DataFrame(trans_data)
df_trans.to_csv(OUT / "transactions.csv", index=False)
print(f"   ✓ {len(df_trans)} lignes de transaction → {OUT / 'transactions.csv'}")

# ============================================================
# 3. EVENTS (page_view, click, add_to_cart, begin_checkout, purchase)
# ============================================================
print("▶ Génération des événements (peut prendre ~30s)…")
events_data = []
event_id = 1

for _, s in df_sessions.iterrows():
    session_start = datetime.strptime(s["session_start"], "%Y-%m-%d %H:%M:%S")

    # page_view events (1 par page vue)
    n_views = s["page_views"]
    for i in range(n_views):
        page = weighted_choice(PAGES)
        ts = session_start + timedelta(seconds=int(s["duration_seconds"] * i / max(n_views, 1)))
        events_data.append({
            "event_id":        f"E{event_id:08d}",
            "session_id":      s["session_id"],
            "user_id":         s["user_id"],
            "event_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event_name":      "page_view",
            "page_path":       page,
            "value":           0,
        })
        event_id += 1

    # Funnel : view_item → add_to_cart → begin_checkout → purchase
    if s["page_views"] >= 2 and random.random() < 0.30:
        ts = session_start + timedelta(seconds=int(s["duration_seconds"] * 0.3))
        events_data.append({
            "event_id":        f"E{event_id:08d}",
            "session_id":      s["session_id"],
            "user_id":         s["user_id"],
            "event_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event_name":      "view_item",
            "page_path":       random.choice(["/product/nike-air-max",
                                              "/product/adidas-ultraboost"]),
            "value":           0,
        })
        event_id += 1

    if s["page_views"] >= 3 and random.random() < 0.40:
        ts = session_start + timedelta(seconds=int(s["duration_seconds"] * 0.5))
        events_data.append({
            "event_id":        f"E{event_id:08d}",
            "session_id":      s["session_id"],
            "user_id":         s["user_id"],
            "event_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event_name":      "add_to_cart",
            "page_path":       "/cart",
            "value":           round(random.uniform(50, 200), 2),
        })
        event_id += 1

    if s["converted"]:
        ts = session_start + timedelta(seconds=int(s["duration_seconds"] * 0.7))
        events_data.append({
            "event_id":        f"E{event_id:08d}",
            "session_id":      s["session_id"],
            "user_id":         s["user_id"],
            "event_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event_name":      "begin_checkout",
            "page_path":       "/checkout",
            "value":           0,
        })
        event_id += 1

        ts = session_start + timedelta(seconds=int(s["duration_seconds"] * 0.9))
        sess_revenue = df_trans[df_trans["session_id"] == s["session_id"]]["revenue_usd"].sum()
        events_data.append({
            "event_id":        f"E{event_id:08d}",
            "session_id":      s["session_id"],
            "user_id":         s["user_id"],
            "event_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "event_name":      "purchase",
            "page_path":       "/checkout/success",
            "value":           round(sess_revenue, 2),
        })
        event_id += 1

df_events = pd.DataFrame(events_data)
df_events.to_csv(OUT / "events.csv", index=False)
print(f"   ✓ {len(df_events)} événements → {OUT / 'events.csv'}")

print("\n✨ Datasets générés !")
print(f"   Sessions     : {len(df_sessions):,}")
print(f"   Events       : {len(df_events):,}")
print(f"   Transactions : {len(df_trans):,}")
print(f"   Conversion rate : {100 * df_sessions['converted'].mean():.2f}%")
print(f"   Total revenue   : ${df_trans['revenue_usd'].sum():,.0f}")