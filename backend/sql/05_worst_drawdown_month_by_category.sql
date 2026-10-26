-- For each category, which single (year, month) was the worst for its average
-- fund, and how bad was the single worst fund in that same month?
--
-- Reuses the monthly-return CTE from query 04 and aggregates per
-- (category, year, month), then picks the one month per category with the
-- lowest category-average return.
--
-- Dialect: SQLite.
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
closes AS (SELECT scheme_code, year, month, year_month, nav AS mo_close FROM mth WHERE rn_c = 1),
monthly AS (
    SELECT
        f.category,
        o.scheme_code,
        o.year, o.month, o.year_month,
        c.mo_close / o.mo_open - 1.0 AS monthly_return
    FROM opens o
    JOIN closes c USING (scheme_code, year, month)
    JOIN funds  f ON f.scheme_code = o.scheme_code
),
category_monthly AS (
    SELECT
        category,
        year, month, year_month,
        AVG(monthly_return) AS cat_avg_return,
        MIN(monthly_return) AS cat_worst_fund_return,
        COUNT(*)            AS n_funds
    FROM monthly
    GROUP BY category, year, month, year_month
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY category ORDER BY cat_avg_return ASC) AS rk_worst,
        LAG(cat_avg_return) OVER (PARTITION BY category ORDER BY year, month) AS prev_month_return
    FROM category_monthly
)
SELECT
    category,
    year_month,
    n_funds,
    ROUND(cat_avg_return, 6)        AS cat_avg_return,
    ROUND(cat_worst_fund_return, 6) AS cat_worst_fund_return,
    ROUND(prev_month_return, 6)     AS prev_month_return
FROM ranked
WHERE rk_worst = 1
ORDER BY cat_avg_return ASC;
