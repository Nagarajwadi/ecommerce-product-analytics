-- User-level conversion by device and traffic source (SQLite).
-- Each user is assigned to the device/source on their earliest observed event.
-- This is a descriptive segmentation, not a causal estimate or validated acquisition attribution.
WITH ranked_events AS (
    SELECT
        user_id,
        device,
        traffic_source,
        event_name,
        timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY timestamp, session_id, event_name
        ) AS event_rank,
        MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END)
            OVER (PARTITION BY user_id) AS purchased
    FROM events
    WHERE user_id IS NOT NULL
),
user_level AS (
    SELECT
        user_id,
        device,
        traffic_source,
        purchased
    FROM ranked_events
    WHERE event_rank = 1
),
segments AS (
    SELECT
        'device' AS segment_type,
        COALESCE(device, 'unknown') AS segment,
        COUNT(*) AS users,
        SUM(purchased) AS purchasers
    FROM user_level
    GROUP BY COALESCE(device, 'unknown')

    UNION ALL

    SELECT
        'traffic_source' AS segment_type,
        COALESCE(traffic_source, 'unknown') AS segment,
        COUNT(*) AS users,
        SUM(purchased) AS purchasers
    FROM user_level
    GROUP BY COALESCE(traffic_source, 'unknown')
)
SELECT
    segment_type,
    segment,
    users,
    purchasers,
    users - purchasers AS non_purchasers,
    ROUND(100.0 * purchasers / NULLIF(users, 0), 2) AS conversion_pct
FROM segments
ORDER BY segment_type, users DESC, segment;
