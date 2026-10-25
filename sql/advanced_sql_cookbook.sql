-- ShopFlow advanced SQL cookbook (SQLite).
-- Run each query separately against the existing events table.

-- 1. Per-user funnel: counts users who have each event type, not strict
-- ordered conversion. Strict funnel sequencing should compare event timestamps.
WITH user_flags AS (
    SELECT user_id,
        MAX(event_name = 'app_open') AS opened,
        MAX(event_name = 'view_product') AS viewed,
        MAX(event_name = 'add_to_cart') AS carted,
        MAX(event_name = 'checkout_start') AS checked_out,
        MAX(event_name = 'purchase') AS purchased
    FROM events
    GROUP BY user_id
)
SELECT
    COUNT(*) AS users,
    SUM(opened) AS opened_users,
    SUM(viewed) AS viewed_users,
    SUM(carted) AS carted_users,
    SUM(checked_out) AS checkout_users,
    SUM(purchased) AS purchasers
FROM user_flags;

-- 2. Daily purchase revenue with a 7-day rolling total.
WITH daily AS (
    SELECT date(timestamp) AS activity_date,
           SUM(CASE WHEN event_name = 'purchase' THEN price * quantity ELSE 0 END) AS revenue
    FROM events
    GROUP BY date(timestamp)
)
SELECT activity_date, revenue,
       SUM(revenue) OVER (
           ORDER BY activity_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) AS rolling_7_day_revenue
FROM daily
ORDER BY activity_date;

-- 3. Channel-level metrics using conditional aggregation.
SELECT traffic_source,
       COUNT(DISTINCT user_id) AS users,
       COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN user_id END) AS purchasers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN user_id END)
             / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS purchaser_rate_pct,
       SUM(CASE WHEN event_name = 'purchase' THEN price * quantity ELSE 0 END) AS revenue
FROM events
GROUP BY traffic_source
ORDER BY revenue DESC;

-- 4. Latest event per user using ROW_NUMBER.
WITH ranked AS (
    SELECT user_id, timestamp, event_name, device, traffic_source,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp DESC) AS rn
    FROM events
)
SELECT user_id, timestamp AS latest_event_at, event_name AS latest_event,
       device, traffic_source
FROM ranked
WHERE rn = 1;

-- 5. Session engagement: use a CTE before joining to session-level summaries.
WITH session_summary AS (
    SELECT session_id, user_id,
           MIN(timestamp) AS session_start,
           MAX(timestamp) AS session_end,
           COUNT(*) AS event_count,
           MAX(event_name = 'purchase') AS purchased
    FROM events
    GROUP BY session_id, user_id
)
SELECT user_id, COUNT(*) AS sessions,
       AVG(event_count) AS avg_events_per_session,
       SUM(purchased) AS purchasing_sessions
FROM session_summary
GROUP BY user_id
ORDER BY sessions DESC;

-- 6. Daily engagement joined to daily purchase metrics.
-- Business question:
-- How do daily event activity and active users compare with purchases
-- and purchase-event revenue?
--
-- Join safety:
-- Both CTEs return at most one row per activity_date, so the join does not
-- multiply event rows. LEFT JOIN preserves dates with activity but no
-- purchase events; COALESCE reports zero purchases/revenue on those dates.
-- Revenue is event-based (price * quantity on purchase events).
-- These results describe synthetic project data, not real business outcomes.

WITH daily_activity AS (
    SELECT
        date(timestamp) AS activity_date,
        COUNT(*) AS total_events,
        COUNT(DISTINCT user_id) AS active_users
    FROM events
    GROUP BY date(timestamp)
),
daily_purchases AS (
    SELECT
        date(timestamp) AS activity_date,
        COUNT(*) AS purchase_events,
        COUNT(DISTINCT user_id) AS purchasing_users,
        SUM(price * quantity) AS purchase_event_revenue
    FROM events
    WHERE event_name = 'purchase'
    GROUP BY date(timestamp)
)
SELECT
    activity.activity_date,
    activity.total_events,
    activity.active_users,
    COALESCE(purchases.purchase_events, 0) AS purchase_events,
    COALESCE(purchases.purchasing_users, 0) AS purchasing_users,
    ROUND(COALESCE(purchases.purchase_event_revenue, 0), 2)
        AS purchase_event_revenue
FROM daily_activity AS activity
LEFT JOIN daily_purchases AS purchases
    ON activity.activity_date = purchases.activity_date
ORDER BY activity.activity_date;


-- 7. Category revenue ranking with window functions.
-- Revenue is event-based: price * quantity for purchase events.
WITH category_revenue AS (
    SELECT
        category,
        SUM(price * quantity) AS revenue
    FROM events
    WHERE event_name = 'purchase'
      AND category IS NOT NULL
    GROUP BY category
),
ranked_categories AS (
    SELECT
        category,
        ROUND(revenue, 2) AS revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, category ASC
        ) AS row_num,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank,
        DENSE_RANK() OVER (
            ORDER BY revenue DESC
        ) AS dense_rank
    FROM category_revenue
)
SELECT
    category,
    revenue,
    row_num,
    revenue_rank,
    dense_rank
FROM ranked_categories
ORDER BY revenue DESC, category ASC;