-- User-level purchase conversion by observed session-frequency segment (SQLite).
-- Engagement proxy: number of distinct observed sessions per user.
-- This is descriptive; observation windows differ and do not establish causality.
WITH user_activity AS (
    SELECT
        user_id,
        COUNT(DISTINCT session_id) AS session_count,
        MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS purchased
    FROM events
    WHERE user_id IS NOT NULL
    GROUP BY user_id
),
segmented_users AS (
    SELECT
        user_id,
        session_count,
        purchased,
        CASE
            WHEN session_count >= 3 THEN '3+ sessions'
            WHEN session_count = 2 THEN '2 sessions'
            ELSE '1 session'
        END AS engagement_segment
    FROM user_activity
)
SELECT
    engagement_segment AS segment,
    COUNT(*) AS users,
    SUM(purchased) AS purchasers,
    COUNT(*) - SUM(purchased) AS non_purchasers,
    ROUND(100.0 * SUM(purchased) / NULLIF(COUNT(*), 0), 2) AS conversion_pct,
    ROUND(1.0 * SUM(session_count) / COUNT(*), 2) AS avg_sessions_per_user
FROM segmented_users
GROUP BY engagement_segment
ORDER BY
    CASE engagement_segment
        WHEN '1 session' THEN 1
        WHEN '2 sessions' THEN 2
        ELSE 3
    END;
