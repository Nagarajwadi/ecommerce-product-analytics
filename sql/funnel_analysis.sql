-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- FUNNEL CONVERSION & DROP-OFF ANALYSIS
-- ============================================================

WITH funnel AS (

    SELECT
        'app_open' AS stage,
        1 AS stage_order,
        COUNT(DISTINCT user_id) AS users
    FROM events
    WHERE event_name = 'app_open'

    UNION ALL

    SELECT
        'view_product',
        2,
        COUNT(DISTINCT user_id)
    FROM events
    WHERE event_name = 'view_product'

    UNION ALL

    SELECT
        'add_to_cart',
        3,
        COUNT(DISTINCT user_id)
    FROM events
    WHERE event_name = 'add_to_cart'

    UNION ALL

    SELECT
        'checkout_start',
        4,
        COUNT(DISTINCT user_id)
    FROM events
    WHERE event_name = 'checkout_start'

    UNION ALL

    SELECT
        'purchase',
        5,
        COUNT(DISTINCT user_id)
    FROM events
    WHERE event_name = 'purchase'
),

funnel_metrics AS (

    SELECT
        stage,
        stage_order,
        users,

        LAG(users) OVER (
            ORDER BY stage_order
        ) AS previous_stage_users,

        FIRST_VALUE(users) OVER (
            ORDER BY stage_order
        ) AS first_stage_users

    FROM funnel
)

SELECT
    stage,
    users,

    ROUND(
        100.0 * users / previous_stage_users,
        2
    ) AS conversion_from_previous_pct,

    previous_stage_users - users AS drop_off_users,

    ROUND(
        100.0 * (previous_stage_users - users)
        / previous_stage_users,
        2
    ) AS drop_off_pct,

    ROUND(
        100.0 * users / first_stage_users,
        2
    ) AS overall_conversion_pct

FROM funnel_metrics
ORDER BY stage_order;