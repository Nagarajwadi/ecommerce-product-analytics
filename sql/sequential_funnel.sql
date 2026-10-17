-- Ordered funnel at session grain (SQLite).
-- A session advances only when each stage occurs strictly after the prior stage.
-- Counts are sessions, not unique users; a user may contribute multiple sessions.
-- Assumes session_id is stable and event timestamps are comparable ISO timestamps.
WITH session_events AS (
    SELECT
        user_id,
        session_id,
        MIN(CASE WHEN event_name = 'app_open' THEN timestamp END) AS app_open_ts,
        MIN(CASE WHEN event_name = 'view_product' THEN timestamp END) AS view_product_ts,
        MIN(CASE WHEN event_name = 'add_to_cart' THEN timestamp END) AS add_to_cart_ts,
        MIN(CASE WHEN event_name = 'checkout_start' THEN timestamp END) AS checkout_start_ts,
        MIN(CASE WHEN event_name = 'purchase' THEN timestamp END) AS purchase_ts
    FROM events
    WHERE session_id IS NOT NULL
    GROUP BY user_id, session_id
),
ordered_stages AS (
    SELECT
        user_id,
        session_id,
        CASE WHEN app_open_ts IS NOT NULL THEN 1 ELSE 0 END AS app_open,
        CASE WHEN app_open_ts IS NOT NULL
                  AND view_product_ts > app_open_ts THEN 1 ELSE 0 END AS view_product,
        CASE WHEN app_open_ts IS NOT NULL
                  AND view_product_ts > app_open_ts
                  AND add_to_cart_ts > view_product_ts THEN 1 ELSE 0 END AS add_to_cart,
        CASE WHEN app_open_ts IS NOT NULL
                  AND view_product_ts > app_open_ts
                  AND add_to_cart_ts > view_product_ts
                  AND checkout_start_ts > add_to_cart_ts THEN 1 ELSE 0 END AS checkout_start,
        CASE WHEN app_open_ts IS NOT NULL
                  AND view_product_ts > app_open_ts
                  AND add_to_cart_ts > view_product_ts
                  AND checkout_start_ts > add_to_cart_ts
                  AND purchase_ts > checkout_start_ts THEN 1 ELSE 0 END AS purchase
    FROM session_events
),
stage_counts AS (
    SELECT 1 AS stage_order, 'app_open' AS stage, SUM(app_open) AS sessions FROM ordered_stages
    UNION ALL
    SELECT 2, 'view_product', SUM(view_product) FROM ordered_stages
    UNION ALL
    SELECT 3, 'add_to_cart', SUM(add_to_cart) FROM ordered_stages
    UNION ALL
    SELECT 4, 'checkout_start', SUM(checkout_start) FROM ordered_stages
    UNION ALL
    SELECT 5, 'purchase', SUM(purchase) FROM ordered_stages
),
metrics AS (
    SELECT
        stage_order,
        stage,
        COALESCE(sessions, 0) AS sessions,
        LAG(COALESCE(sessions, 0)) OVER (ORDER BY stage_order) AS previous_stage_sessions,
        FIRST_VALUE(COALESCE(sessions, 0)) OVER (ORDER BY stage_order) AS entry_sessions
    FROM stage_counts
)
SELECT
    stage,
    sessions,
    previous_stage_sessions,
    CASE WHEN previous_stage_sessions > 0
        THEN ROUND(100.0 * sessions / previous_stage_sessions, 2)
        ELSE NULL END AS conversion_from_previous_pct,
    CASE WHEN previous_stage_sessions IS NOT NULL
        THEN previous_stage_sessions - sessions
        ELSE NULL END AS drop_off_sessions,
    CASE WHEN previous_stage_sessions > 0
        THEN ROUND(100.0 * (previous_stage_sessions - sessions) / previous_stage_sessions, 2)
        ELSE NULL END AS drop_off_pct,
    CASE WHEN entry_sessions > 0
        THEN ROUND(100.0 * sessions / entry_sessions, 2)
        ELSE NULL END AS conversion_from_entry_pct
FROM metrics
ORDER BY stage_order;
