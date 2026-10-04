-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- FUNNEL ANALYSIS BY TRAFFIC SOURCE
-- ============================================================

WITH funnel AS (

    SELECT
        traffic_source,

        COUNT(DISTINCT CASE
            WHEN event_name = 'app_open'
            THEN user_id
        END) AS app_open_users,

        COUNT(DISTINCT CASE
            WHEN event_name = 'view_product'
            THEN user_id
        END) AS view_product_users,

        COUNT(DISTINCT CASE
            WHEN event_name = 'add_to_cart'
            THEN user_id
        END) AS add_to_cart_users,

        COUNT(DISTINCT CASE
            WHEN event_name = 'checkout_start'
            THEN user_id
        END) AS checkout_users,

        COUNT(DISTINCT CASE
            WHEN event_name = 'purchase'
            THEN user_id
        END) AS purchase_users

    FROM events

    GROUP BY traffic_source
)

SELECT
    traffic_source,
    app_open_users,
    view_product_users,
    add_to_cart_users,
    checkout_users,
    purchase_users,

    ROUND(
        100.0 * add_to_cart_users / view_product_users,
        2
    ) AS view_to_cart_pct,

    ROUND(
        100.0 * checkout_users / add_to_cart_users,
        2
    ) AS cart_to_checkout_pct,

    ROUND(
        100.0 * purchase_users / checkout_users,
        2
    ) AS checkout_to_purchase_pct,

    ROUND(
        100.0 * purchase_users / app_open_users,
        2
    ) AS overall_conversion_pct

FROM funnel

ORDER BY overall_conversion_pct DESC;