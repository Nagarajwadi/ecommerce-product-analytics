-- Retention cohorts by first observed activity month.
-- This is an activity-based proxy, NOT signup retention: the events table
-- does not necessarily contain a trustworthy signup timestamp.
-- SQLite dialect. D1/D7/D30 mean activity on exactly day 1/7/30 after first event.
WITH first_activity AS (
    SELECT user_id, MIN(date(timestamp)) AS cohort_date
    FROM events
    GROUP BY user_id
),
activity_days AS (
    SELECT DISTINCT user_id, date(timestamp) AS activity_date
    FROM events
),
retention AS (
    SELECT
        f.user_id,
        strftime('%Y-%m', f.cohort_date) AS cohort_month,
        CAST(julianday(a.activity_date) - julianday(f.cohort_date) AS INTEGER) AS days_since_first
    FROM first_activity f
    JOIN activity_days a ON a.user_id = f.user_id
)
SELECT
    cohort_month,
    COUNT(DISTINCT CASE WHEN days_since_first = 0 THEN user_id END) AS cohort_users,
    COUNT(DISTINCT CASE WHEN days_since_first = 1 THEN user_id END) AS d1_users,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN days_since_first = 1 THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN days_since_first = 0 THEN user_id END), 0), 2) AS d1_retention_pct,
    COUNT(DISTINCT CASE WHEN days_since_first = 7 THEN user_id END) AS d7_users,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN days_since_first = 7 THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN days_since_first = 0 THEN user_id END), 0), 2) AS d7_retention_pct,
    COUNT(DISTINCT CASE WHEN days_since_first = 30 THEN user_id END) AS d30_users,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN days_since_first = 30 THEN user_id END)
        / NULLIF(COUNT(DISTINCT CASE WHEN days_since_first = 0 THEN user_id END), 0), 2) AS d30_retention_pct
FROM retention
GROUP BY cohort_month
ORDER BY cohort_month;
