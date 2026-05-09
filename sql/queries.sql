-- ============================================
-- queries.sql
-- 10 requêtes types pour un web analyst
-- ============================================

-- 1. KPIs globaux
SELECT
    COUNT(*) AS total_sessions,
    COUNT(DISTINCT user_id) AS total_users,
    SUM(page_views) AS total_pageviews,
    SUM(IF(converted, 1, 0)) AS total_transactions,
    ROUND(100 * AVG(IF(converted, 1, 0)), 2) AS conversion_rate_pct,
    ROUND(100 * AVG(IF(bounced, 1, 0)), 2) AS bounce_rate_pct,
    ROUND(AVG(duration_seconds), 0) AS avg_session_duration_sec
FROM `web_analytics.sessions`;


-- 2. Performance par canal d'acquisition (avec ROAS)
SELECT
    channel,
    COUNT(*) AS sessions,
    COUNT(DISTINCT user_id) AS users,
    ROUND(100 * AVG(IF(converted, 1, 0)), 2) AS conversion_rate_pct,
    ROUND(SUM(session_revenue_usd), 2) AS revenue,
    ROUND(SUM(session_cost_usd), 2) AS cost,
    ROUND(SAFE_DIVIDE(SUM(session_revenue_usd), SUM(session_cost_usd)), 2) AS roas
FROM `web_analytics.sessions`
GROUP BY channel
ORDER BY sessions DESC;


-- 3. Funnel de conversion (avec drop-off)
WITH funnel AS (
    SELECT
        event_name,
        COUNT(DISTINCT session_id) AS sessions
    FROM `web_analytics.events`
    WHERE event_name IN ('page_view', 'view_item', 'add_to_cart',
                         'begin_checkout', 'purchase')
    GROUP BY event_name
),
ordered AS (
    SELECT
        event_name,
        sessions,
        CASE event_name
            WHEN 'page_view' THEN 1
            WHEN 'view_item' THEN 2
            WHEN 'add_to_cart' THEN 3
            WHEN 'begin_checkout' THEN 4
            WHEN 'purchase' THEN 5
        END AS step_order
    FROM funnel
)
SELECT
    event_name AS step,
    sessions,
    ROUND(100 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY step_order), 2) AS pct_of_total,
    ROUND(100 * (1 - SAFE_DIVIDE(sessions, LAG(sessions) OVER (ORDER BY step_order))), 2) AS dropoff_pct
FROM ordered
ORDER BY step_order;


-- 4. Top 10 pages par vues
SELECT
    page_path,
    COUNT(*) AS page_views,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM `web_analytics.events`
WHERE event_name = 'page_view'
GROUP BY page_path
ORDER BY page_views DESC
LIMIT 10;


-- 5. Performance mobile vs desktop
SELECT
    device,
    COUNT(*) AS sessions,
    ROUND(100 * AVG(IF(bounced, 1, 0)), 2) AS bounce_rate_pct,
    ROUND(100 * AVG(IF(converted, 1, 0)), 2) AS conversion_rate_pct,
    ROUND(AVG(duration_seconds), 0) AS avg_duration_sec
FROM `web_analytics.sessions`
GROUP BY device
ORDER BY sessions DESC;


-- 6. ROAS par campagne (uniquement campagnes payantes)
SELECT
    channel,
    campaign,
    COUNT(*) AS sessions,
    SUM(IF(converted, 1, 0)) AS transactions,
    ROUND(SUM(session_cost_usd), 2) AS cost,
    ROUND(SUM(session_revenue_usd), 2) AS revenue,
    ROUND(SAFE_DIVIDE(SUM(session_revenue_usd), SUM(session_cost_usd)), 2) AS roas,
    ROUND(SAFE_DIVIDE(SUM(session_cost_usd), SUM(IF(converted, 1, 0))), 2) AS cpa
FROM `web_analytics.sessions`
WHERE session_cost_usd > 0
GROUP BY channel, campaign
ORDER BY revenue DESC;


-- 7. Top produits par revenu
SELECT
    product_sku,
    product_name,
    category,
    SUM(quantity) AS units_sold,
    COUNT(*) AS transactions,
    ROUND(SUM(revenue_usd), 2) AS revenue
FROM `web_analytics.transactions`
GROUP BY product_sku, product_name, category
ORDER BY revenue DESC
LIMIT 10;


-- 8. Cohort retention par semaine
WITH cohorts AS (
    SELECT
        user_id,
        FORMAT_DATE('%Y-W%U', MIN(session_date)) AS cohort_week
    FROM `web_analytics.sessions`
    GROUP BY user_id
),
sessions_with_cohort AS (
    SELECT
        s.user_id,
        c.cohort_week,
        FORMAT_DATE('%Y-W%U', s.session_date) AS activity_week
    FROM `web_analytics.sessions` s
    JOIN cohorts c USING (user_id)
)
SELECT
    cohort_week,
    activity_week,
    COUNT(DISTINCT user_id) AS active_users
FROM sessions_with_cohort
GROUP BY cohort_week, activity_week
ORDER BY cohort_week, activity_week;


-- 9. Heatmap engagement heure × jour
SELECT
    FORMAT_TIMESTAMP('%A', session_start) AS day_of_week,
    EXTRACT(HOUR FROM session_start) AS hour,
    COUNT(*) AS sessions
FROM `web_analytics.sessions`
GROUP BY day_of_week, hour
ORDER BY day_of_week, hour;


-- 10. Performance new vs returning
SELECT
    IF(is_new_user, 'new', 'returning') AS user_type,
    COUNT(*) AS sessions,
    ROUND(AVG(page_views), 2) AS avg_pageviews,
    ROUND(AVG(duration_seconds), 0) AS avg_duration_sec,
    ROUND(100 * AVG(IF(bounced, 1, 0)), 2) AS bounce_rate_pct,
    ROUND(100 * AVG(IF(converted, 1, 0)), 2) AS conversion_rate_pct,
    ROUND(SUM(session_revenue_usd), 2) AS revenue
FROM `web_analytics.sessions`
GROUP BY user_type;