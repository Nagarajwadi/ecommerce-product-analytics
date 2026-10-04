-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- A/B TEST ANALYSIS
-- ============================================================

WITH experiment AS (

    SELECT
        experiment_group,

        COUNT(DISTINCT user_id) AS users,

        COUNT(DISTINCT CASE
            WHEN event_name = 'purchase'
            THEN user_id
        END) AS purchasers

    FROM events

    GROUP BY experiment_group
)

SELECT
    experiment_group,
    users,
    purchasers,

    ROUND(
        100.0 * purchasers / users,
        2
    ) AS conversion_rate_pct

FROM experiment

ORDER BY experiment_group;
