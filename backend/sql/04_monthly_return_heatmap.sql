-- Monthly returns per fund — long format for a heatmap renderer.
-- (year on one axis, month 1..12 on the other, scheme_code is the fund selector)
--
-- Uses ROW_NUMBER() per (scheme, year, month) partition to pin the month's
-- open and close NAVs. (year_month is kept for ordering / display.)
--
-- Dialect: SQLite (strftime).
WITH mth AS (
    SELECT
        scheme_code,
        CAST(strftime('%Y', date) AS INTEGER) AS year,
        CAST(strftime('%m', date) AS INTEGER) AS month,
        strftime('%Y-%m', date) AS year_month,
        date,
        nav,
        ROW_NUMBER() OVER (
            PARTITION BY scheme_code, strftime('%Y-%m', date) ORDER BY date ASC
        ) AS rn_o,
        ROW_NUMBER() OVER (
            PARTITION BY scheme_code, strftime('%Y-%m', date) ORDER BY date DESC
        ) AS rn_c
    FROM nav_history
),
opens  AS (SELECT scheme_code, year, month, year_month, nav AS mo_open  FROM mth WHERE rn_o = 1),
closes AS (SELECT scheme_code, year, month, year_month, nav AS mo_close FROM mth WHERE rn_c = 1)
SELECT
    f.scheme_code,
    f.name,
    f.category,
    o.year,
    o.month,
    o.year_month,
    ROUND(c.mo_close / o.mo_open - 1.0, 6) AS monthly_return
FROM opens o
JOIN closes c USING (scheme_code, year, month)
JOIN funds  f ON f.scheme_code = o.scheme_code
ORDER BY f.category, f.scheme_code, o.year, o.month;
