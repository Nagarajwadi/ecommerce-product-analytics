-- ShopFlow category performance (SQLite).
-- Business question:
-- Which product categories attract product views and cart activity,
-- and how do purchase events and event-based revenue vary by category?
--
-- Important interpretation notes:
-- * These are event counts, not unique users, except purchasing_users.
-- * Event counts do not establish that the same users progressed through
--   each stage; do not interpret cart/view counts as funnel conversion rates.
-- * Revenue is the sum of price * quantity on purchase events only.
-- * Results describe synthetic project data, not real business performance.

SELECT
    category,
    COUNT(CASE WHEN event_name = 'view_product' THEN 1 END)
        AS product_view_events,
    COUNT(CASE WHEN event_name = 'add_to_cart' THEN 1 END)
        AS add_to_cart_events,
    COUNT(CASE WHEN event_name = 'checkout_start' THEN 1 END)
        AS checkout_start_events,
    COUNT(CASE WHEN event_name = 'purchase' THEN 1 END)
        AS purchase_events,
    COUNT(DISTINCT CASE
        WHEN event_name = 'purchase' THEN user_id
    END) AS purchasing_users,
    ROUND(SUM(CASE
        WHEN event_name = 'purchase' THEN price * quantity
        ELSE 0
    END), 2) AS purchase_event_revenue
FROM events
WHERE event_name IN (
    'view_product',
    'add_to_cart',
    'checkout_start',
    'purchase'
)
AND category IS NOT NULL
GROUP BY category
ORDER BY purchase_event_revenue DESC;
