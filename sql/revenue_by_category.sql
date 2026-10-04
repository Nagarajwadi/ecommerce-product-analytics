-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- REVENUE BY PRODUCT CATEGORY
-- ============================================================

WITH purchase_data AS (

    SELECT
        category,
        product_id,
        user_id,
        price * quantity AS revenue

    FROM events

    WHERE event_name = 'purchase'
)

SELECT
    category,

    COUNT(*) AS purchases,

    COUNT(DISTINCT user_id) AS unique_purchasers,

    COUNT(DISTINCT product_id) AS products_sold,

    ROUND(
        SUM(revenue),
        2
    ) AS total_revenue,

    ROUND(
        SUM(revenue) / COUNT(*),
        2
    ) AS average_order_value

FROM purchase_data

GROUP BY category

ORDER BY total_revenue DESC;
