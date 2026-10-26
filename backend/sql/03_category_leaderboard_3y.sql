-- 3-year CAGR leaderboard, ranked within each category.
--
-- For every fund, find its latest NAV and the NAV on the most recent trading
-- day that is on or before (latest_date - 3 years). CAGR is annualised using
-- the actual calendar-day gap between those two trading days.
--
-- Dialect: SQLite — uses `date(x, '-3 years')` and `julianday()`.
-- Postgres: use `latest_date - INTERVAL '3 years'` and `(latest_date - start_date)` for days.
WITH latest AS (
    SELECT scheme_code, MAX(date) AS last_date FROM nav_history GROUP BY scheme_code
),
anchors AS (
    SELECT
        scheme_code,
        last_date,
        date(last_date, '-3 years') AS target_date
    FROM latest
),
nav_end AS (
    SELECT a.scheme_code, a.last_date, n.nav AS nav_end
    FROM anchors a
    JOIN nav_history n ON n.scheme_code = a.scheme_code AND n.date = a.last_date
),
nav_start AS (
    SELECT
        a.scheme_code,
        MAX(n.date) AS start_date,
        -- correlated lookup: NAV on the most recent trading day <= target_date
        (SELECT nav FROM nav_history
          WHERE scheme_code = a.scheme_code AND date <= a.target_date
          ORDER BY date DESC LIMIT 1) AS nav_start
    FROM anchors a
    LEFT JOIN nav_history n ON n.scheme_code = a.scheme_code AND n.date <= a.target_date
    GROUP BY a.scheme_code
),
cagr AS (
    SELECT
        ne.scheme_code,
        ne.last_date  AS end_date,
        ns.start_date,
        ns.nav_start,
        ne.nav_end,
        (julianday(ne.last_date) - julianday(ns.start_date)) / 365.25 AS years,
        POWER(ne.nav_end / ns.nav_start,
              1.0 / ((julianday(ne.last_date) - julianday(ns.start_date)) / 365.25)) - 1.0 AS cagr_3y
    FROM nav_end ne
    JOIN nav_start ns USING (scheme_code)
    WHERE ns.nav_start IS NOT NULL
)
SELECT
    f.scheme_code,
    f.name,
    f.category,
    c.start_date,
    c.end_date,
    ROUND(c.years, 2)    AS years,
    ROUND(c.cagr_3y, 4)  AS cagr_3y,
    RANK() OVER (PARTITION BY f.category ORDER BY c.cagr_3y DESC) AS category_rank,
    NTILE(4) OVER (PARTITION BY f.category ORDER BY c.cagr_3y DESC) AS category_quartile
FROM cagr c
JOIN funds f ON f.scheme_code = c.scheme_code
ORDER BY f.category, category_rank;
