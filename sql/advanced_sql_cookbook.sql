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
