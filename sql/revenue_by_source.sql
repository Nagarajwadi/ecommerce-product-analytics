-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- REVENUE BY TRAFFIC SOURCE
-- ============================================================

WITH purchase_data AS (

    SELECT
        user_id,
        traffic_source,
        price * quantity AS revenue

    FROM events

    WHERE event_name = 'purchase'
)

SELECT
    traffic_source,

    COUNT(*) AS purchases,

    COUNT(DISTINCT user_id) AS unique_purchasers,

    ROUND(
        SUM(revenue),
        2
    ) AS total_revenue,

    ROUND(
        SUM(revenue) / COUNT(*),
        2
    ) AS average_order_value,

    ROUND(
        SUM(revenue) / COUNT(DISTINCT user_id),
        2
    ) AS revenue_per_purchaser

FROM purchase_data

GROUP BY traffic_source

ORDER BY total_revenue DESC;
