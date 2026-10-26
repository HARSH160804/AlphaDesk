-- Calendar-year returns per fund.
--
-- For every (scheme_code, year), compute year_open (first trading day's NAV)
-- and year_close (last trading day's NAV), then (close/open) - 1.
-- Uses ROW_NUMBER() in both directions over each (scheme, year) partition.
--
-- Dialect: SQLite (strftime). Postgres equivalent: EXTRACT(YEAR FROM date).
WITH yearly AS (
    SELECT
        n.scheme_code,
        CAST(strftime('%Y', n.date) AS INTEGER) AS year,
        n.date,
        n.nav,
        ROW_NUMBER() OVER (
            PARTITION BY n.scheme_code, strftime('%Y', n.date)
            ORDER BY n.date ASC
        ) AS rn_open,
        ROW_NUMBER() OVER (
            PARTITION BY n.scheme_code, strftime('%Y', n.date)
            ORDER BY n.date DESC
        ) AS rn_close
    FROM nav_history n
),
opens  AS (SELECT scheme_code, year, nav AS nav_open  FROM yearly WHERE rn_open  = 1),
closes AS (SELECT scheme_code, year, nav AS nav_close FROM yearly WHERE rn_close = 1)
SELECT
    f.scheme_code,
    f.name,
    f.category,
    o.year,
    ROUND(o.nav_open,  6)  AS nav_open,
    ROUND(c.nav_close, 6)  AS nav_close,
    ROUND(c.nav_close / o.nav_open - 1.0, 6) AS cal_year_return
FROM opens o
JOIN closes c ON c.scheme_code = o.scheme_code AND c.year = o.year
JOIN funds  f ON f.scheme_code = o.scheme_code
ORDER BY f.category, f.scheme_code, o.year;
