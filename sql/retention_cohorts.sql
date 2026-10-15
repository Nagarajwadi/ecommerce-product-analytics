-- Retention cohorts by first observed activity month (SQLite).
-- This is NOT signup retention: the source has no signup timestamp.
-- D1/D7/D30 mean activity on exactly that day after first observed activity.
-- Each rate uses only users with enough observation time for that horizon.
WITH first_activity AS (
    SELECT user_id, MIN(date(timestamp)) AS first_date
    FROM events
    GROUP BY user_id
),
activity_days AS (
    SELECT DISTINCT user_id, date(timestamp) AS activity_date
    FROM events
),
max_observation AS (
    SELECT MAX(activity_date) AS max_date FROM activity_days
),
user_horizons AS (
    SELECT
        f.user_id,
        strftime('%Y-%m', f.first_date) AS cohort_month,
        f.first_date,
        date(f.first_date, '+1 day') AS d1_date,
        date(f.first_date, '+7 days') AS d7_date,
        date(f.first_date, '+30 days') AS d30_date,
        m.max_date,
        EXISTS (
            SELECT 1 FROM activity_days a
            WHERE a.user_id = f.user_id
              AND a.activity_date = date(f.first_date, '+1 day')
        ) AS d1_retained,
        EXISTS (
            SELECT 1 FROM activity_days a
            WHERE a.user_id = f.user_id
              AND a.activity_date = date(f.first_date, '+7 days')
        ) AS d7_retained,
        EXISTS (
            SELECT 1 FROM activity_days a
            WHERE a.user_id = f.user_id
              AND a.activity_date = date(f.first_date, '+30 days')
        ) AS d30_retained
    FROM first_activity f
    CROSS JOIN max_observation m
)
SELECT
    cohort_month,
    COUNT(*) AS cohort_users,
    SUM(CASE WHEN d1_date <= max_date THEN 1 ELSE 0 END) AS d1_eligible_users,
    SUM(CASE WHEN d1_date <= max_date AND d1_retained THEN 1 ELSE 0 END) AS d1_users,
    ROUND(100.0 * SUM(CASE WHEN d1_date <= max_date AND d1_retained THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN d1_date <= max_date THEN 1 ELSE 0 END), 0), 2) AS d1_retention_pct,
    SUM(CASE WHEN d7_date <= max_date THEN 1 ELSE 0 END) AS d7_eligible_users,
    SUM(CASE WHEN d7_date <= max_date AND d7_retained THEN 1 ELSE 0 END) AS d7_users,
    ROUND(100.0 * SUM(CASE WHEN d7_date <= max_date AND d7_retained THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN d7_date <= max_date THEN 1 ELSE 0 END), 0), 2) AS d7_retention_pct,
    SUM(CASE WHEN d30_date <= max_date THEN 1 ELSE 0 END) AS d30_eligible_users,
    SUM(CASE WHEN d30_date <= max_date AND d30_retained THEN 1 ELSE 0 END) AS d30_users,
    ROUND(100.0 * SUM(CASE WHEN d30_date <= max_date AND d30_retained THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN d30_date <= max_date THEN 1 ELSE 0 END), 0), 2) AS d30_retention_pct
FROM user_horizons
GROUP BY cohort_month
ORDER BY cohort_month;
