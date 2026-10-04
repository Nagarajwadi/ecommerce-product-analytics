-- ============================================================
-- E-COMMERCE PRODUCT ANALYTICS
-- D1 / D7 / D30 RETENTION
-- ============================================================

WITH first_activity AS (

    SELECT
        user_id,
        MIN(DATE(timestamp)) AS first_activity_date
    FROM events
    GROUP BY user_id
),

activity AS (

    SELECT DISTINCT
        user_id,
        DATE(timestamp) AS activity_date
    FROM events
),

retention_flags AS (

    SELECT
        fa.user_id,
        fa.first_activity_date,

        MAX(
            CASE
                WHEN a.activity_date =
                     DATE(fa.first_activity_date, '+1 day')
                THEN 1
                ELSE 0
            END
        ) AS retained_d1,

        MAX(
            CASE
                WHEN a.activity_date =
                     DATE(fa.first_activity_date, '+7 day')
                THEN 1
                ELSE 0
            END
        ) AS retained_d7,

        MAX(
            CASE
                WHEN a.activity_date =
                     DATE(fa.first_activity_date, '+30 day')
                THEN 1
                ELSE 0
            END
        ) AS retained_d30

    FROM first_activity fa

    LEFT JOIN activity a
        ON fa.user_id = a.user_id

    GROUP BY
        fa.user_id,
        fa.first_activity_date
)

SELECT

    COUNT(*) AS total_users,

    SUM(
        CASE
            WHEN DATE(first_activity_date, '+1 day')
                 <= DATE('2026-06-30')
            THEN 1
            ELSE 0
        END
    ) AS d1_eligible_users,

    SUM(
        CASE
            WHEN DATE(first_activity_date, '+1 day')
                 <= DATE('2026-06-30')
            THEN retained_d1
            ELSE 0
        END
    ) AS d1_retained_users,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN DATE(first_activity_date, '+1 day')
                     <= DATE('2026-06-30')
                THEN retained_d1
                ELSE 0
            END
        )
        /
        SUM(
            CASE
                WHEN DATE(first_activity_date, '+1 day')
                     <= DATE('2026-06-30')
                THEN 1
                ELSE 0
            END
        ),
        2
    ) AS d1_retention_pct,

    SUM(
        CASE
            WHEN DATE(first_activity_date, '+7 day')
                 <= DATE('2026-06-30')
            THEN 1
            ELSE 0
        END
    ) AS d7_eligible_users,

    SUM(
        CASE
            WHEN DATE(first_activity_date, '+7 day')
                 <= DATE('2026-06-30')
            THEN retained_d7
            ELSE 0
        END
    ) AS d7_retained_users,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN DATE(first_activity_date, '+7 day')
                     <= DATE('2026-06-30')
                THEN retained_d7
                ELSE 0
            END
        )
        /
        SUM(
            CASE
                WHEN DATE(first_activity_date, '+7 day')
                     <= DATE('2026-06-30')
                THEN 1
                ELSE 0
            END
        ),
        2
    ) AS d7_retention_pct,

    SUM(
        CASE
            WHEN DATE(first_activity_date, '+30 day')
                 <= DATE('2026-06-30')
            THEN 1
            ELSE 0
        END
    ) AS d30_eligible_users,

    SUM(
        CASE
            WHEN DATE(first_activity_date, '+30 day')
                 <= DATE('2026-06-30')
            THEN retained_d30
            ELSE 0
        END
    ) AS d30_retained_users,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN DATE(first_activity_date, '+30 day')
                     <= DATE('2026-06-30')
                THEN retained_d30
                ELSE 0
            END
        )
        /
        SUM(
            CASE
                WHEN DATE(first_activity_date, '+30 day')
                     <= DATE('2026-06-30')
                THEN 1
                ELSE 0
            END
        ),
        2
    ) AS d30_retention_pct

FROM retention_flags;
