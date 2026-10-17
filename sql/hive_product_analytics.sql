-- Apache Hive examples. These are dialect examples and are not executed by
-- the SQLite application. Adjust database/table names and timestamp types
-- to match the target Hive catalog.

-- Example external table over partitioned Parquet event data.
-- CREATE EXTERNAL TABLE IF NOT EXISTS analytics.events (
--   user_id STRING,
--   timestamp TIMESTAMP,
--   session_id STRING,
--   event_name STRING,
--   product_id STRING,
--   category STRING,
--   price DOUBLE,
--   quantity INT,
--   device STRING,
--   country STRING,
--   traffic_source STRING,
--   experiment_group STRING
-- )
-- PARTITIONED BY (event_date STRING)
-- STORED AS PARQUET
-- LOCATION 's3a://YOUR-BUCKET/product-events/';

-- Daily channel metrics; partition predicate avoids scanning all dates.
SELECT event_date,
       traffic_source,
       COUNT(DISTINCT user_id) AS users,
       COUNT(DISTINCT CASE WHEN event_name = 'purchase' THEN user_id END) AS purchasers,
       SUM(CASE WHEN event_name = 'purchase' THEN price * quantity ELSE 0 END) AS revenue
FROM analytics.events
WHERE event_date >= '2026-01-01' AND event_date < '2026-07-01'
GROUP BY event_date, traffic_source;

-- Daily revenue and a seven-row rolling window over daily aggregates.
-- This is seven available date rows, not necessarily seven calendar days.
-- To guarantee calendar-day semantics, build a complete date spine and
-- fill missing dates with zero revenue before applying the window.
WITH daily AS (
  SELECT event_date,
         SUM(CASE WHEN event_name = 'purchase' THEN price * quantity ELSE 0 END) AS revenue
  FROM analytics.events
  WHERE event_date >= '2026-01-01' AND event_date < '2026-07-01'
  GROUP BY event_date
)
SELECT event_date, revenue,
       SUM(revenue) OVER (
         ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) AS rolling_7_day_revenue
FROM daily;

-- Hive notes:
-- * Partition filters should use the partition column directly.
-- * Use EXPLAIN to inspect stages and scans before tuning.
-- * DISTINCT counts may be expensive; approximate distinct functions are
--   engine/version-specific and change the precision contract.
-- * Confirm TIMESTAMP/date semantics, null handling, and window support on
--   the target Hive version before treating results as production-ready.
