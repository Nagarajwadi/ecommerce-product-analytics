-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- MONTHLY COHORT RETENTION ANALYSIS
-- ============================================================

WITH first_activity AS (

    SELECT
        user_id,
        MIN(DATE(timestamp)) AS first_activity_date
    FROM events
    GROUP BY user_id
),

user_activity AS (

    SELECT DISTINCT
        user_id,
        DATE(timestamp) AS activity_date
    FROM events
),

cohort_activity AS (

    SELECT
        ua.user_id,
        fa.first_activity_date,

        (
            (
                CAST(STRFTIME('%Y', ua.activity_date) AS INTEGER)
                - CAST(STRFTIME('%Y', fa.first_activity_date) AS INTEGER)
            ) * 12
            +
            (
                CAST(STRFTIME('%m', ua.activity_date) AS INTEGER)
                - CAST(STRFTIME('%m', fa.first_activity_date) AS INTEGER)
            )
        ) AS month_number

    FROM user_activity ua

    JOIN first_activity fa
        ON ua.user_id = fa.user_id
),

cohort_size AS (

    SELECT
        STRFTIME('%Y-%m', first_activity_date) AS cohort_month,
        COUNT(DISTINCT user_id) AS cohort_users
    FROM first_activity
    GROUP BY STRFTIME('%Y-%m', first_activity_date)
),

retention AS (

    SELECT
        STRFTIME('%Y-%m', first_activity_date) AS cohort_month,
        month_number,
        COUNT(DISTINCT user_id) AS retained_users

    FROM cohort_activity

    GROUP BY
        STRFTIME('%Y-%m', first_activity_date),
        month_number
)

SELECT
    r.cohort_month,
    r.month_number,
    c.cohort_users,
    r.retained_users,

    ROUND(
        100.0 * r.retained_users / c.cohort_users,
        2
    ) AS retention_pct

FROM retention r

JOIN cohort_size c
    ON r.cohort_month = c.cohort_month

ORDER BY
    r.cohort_month,
    r.month_number;