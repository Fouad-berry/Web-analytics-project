-- ============================================
-- create_tables.sql
-- Schéma BigQuery au format GA4 (3 tables liées).
-- Branchable directement à Looker Studio en mode entrepôt.
-- ============================================

CREATE SCHEMA IF NOT EXISTS `web_analytics`;

-- ============================================
-- Table sessions : 1 ligne par session
-- ============================================
CREATE OR REPLACE TABLE `web_analytics.sessions` (
    session_id          STRING    NOT NULL,
    user_id             STRING    NOT NULL,
    session_start       TIMESTAMP NOT NULL,
    session_date        DATE      NOT NULL,
    channel             STRING,
    campaign            STRING,
    device              STRING,
    country             STRING,
    browser             STRING,
    is_new_user         BOOL,
    page_views          INT64,
    duration_seconds    INT64,
    bounced             BOOL,
    converted           BOOL,
    session_cost_usd    FLOAT64,

    -- Features dérivées
    session_revenue_usd FLOAT64,
    session_day_of_week STRING,
    session_hour        INT64,
    year_month          STRING,
    year_week           STRING,
    is_weekend          BOOL,
    engagement_level    STRING,
    cohort_week         STRING,
    activity_week       STRING
)
PARTITION BY session_date
CLUSTER BY channel, country, device;


-- ============================================
-- Table events : 1 ligne par event
-- ============================================
CREATE OR REPLACE TABLE `web_analytics.events` (
    event_id        STRING    NOT NULL,
    session_id      STRING    NOT NULL,
    user_id         STRING    NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    event_name      STRING    NOT NULL,
    page_path       STRING,
    value           FLOAT64
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY event_name, session_id;


-- ============================================
-- Table transactions : 1 ligne par produit acheté
-- ============================================
CREATE OR REPLACE TABLE `web_analytics.transactions` (
    transaction_id   STRING    NOT NULL,
    session_id       STRING    NOT NULL,
    user_id          STRING    NOT NULL,
    transaction_date DATE      NOT NULL,
    product_sku      STRING,
    product_name     STRING,
    category         STRING,
    quantity         INT64,
    unit_price_usd   FLOAT64,
    discount_usd     FLOAT64,
    revenue_usd      FLOAT64
)
PARTITION BY transaction_date
CLUSTER BY product_sku;


-- ============================================
-- Vues utiles pour Looker
-- ============================================

-- Vue sessions enrichies du revenu (jointure typique en web analytics)
CREATE OR REPLACE VIEW `web_analytics.v_sessions_with_revenue` AS
SELECT
    s.*,
    COALESCE(SUM(t.revenue_usd), 0) AS revenue_from_session
FROM `web_analytics.sessions` s
LEFT JOIN `web_analytics.transactions` t USING (session_id)
GROUP BY s.session_id, s.user_id, s.session_start, s.session_date, s.channel,
         s.campaign, s.device, s.country, s.browser, s.is_new_user, s.page_views,
         s.duration_seconds, s.bounced, s.converted, s.session_cost_usd,
         s.session_revenue_usd, s.session_day_of_week, s.session_hour,
         s.year_month, s.year_week, s.is_weekend, s.engagement_level,
         s.cohort_week, s.activity_week;


-- Vue : nombre de sessions par étape de funnel
CREATE OR REPLACE VIEW `web_analytics.v_funnel` AS
SELECT
    event_name,
    COUNT(DISTINCT session_id) AS sessions_at_step
FROM `web_analytics.events`
WHERE event_name IN ('page_view', 'view_item', 'add_to_cart',
                     'begin_checkout', 'purchase')
GROUP BY event_name;