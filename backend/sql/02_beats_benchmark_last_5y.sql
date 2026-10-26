-- Funds that beat their benchmark in every one of the last 5 completed calendar
-- years. "Completed" means years strictly before the latest year in the data.
--
-- Builds fund calendar-year returns and benchmark calendar-year returns from
-- the same FIRST_VALUE pattern, aligns them per (scheme, benchmark, year),
-- then uses a windowed count to require a clean 5-of-5 sweep.
--
-- Dialect: SQLite.
WITH f_yearly AS (
    SELECT
        n.scheme_code,
        f.benchmark_id,
        CAST(strftime('%Y', n.date) AS INTEGER) AS year,
        FIRST_VALUE(n.nav) OVER (
            PARTITION BY n.scheme_code, strftime('%Y', n.date)
            ORDER BY n.date ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS nav_open,
        FIRST_VALUE(n.nav) OVER (
            PARTITION BY n.scheme_code, strftime('%Y', n.date)
            ORDER BY n.date DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS nav_close
    FROM nav_history n
    JOIN funds f ON f.scheme_code = n.scheme_code
),
b_yearly AS (
    SELECT
        bh.benchmark_id,
        CAST(strftime('%Y', bh.date) AS INTEGER) AS year,
        FIRST_VALUE(bh.close) OVER (
            PARTITION BY bh.benchmark_id, strftime('%Y', bh.date)
            ORDER BY bh.date ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS bo,
        FIRST_VALUE(bh.close) OVER (
            PARTITION BY bh.benchmark_id, strftime('%Y', bh.date)
            ORDER BY bh.date DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS bc
    FROM benchmark_history bh
),
fund_cy  AS (SELECT DISTINCT scheme_code, benchmark_id, year, nav_close/nav_open - 1.0 AS fret FROM f_yearly),
bench_cy AS (SELECT DISTINCT benchmark_id, year, bc/bo - 1.0 AS bret FROM b_yearly),
latest   AS (SELECT MAX(year) AS last_year FROM fund_cy),
window5  AS (
    SELECT last_year - 1 AS year FROM latest
    UNION ALL SELECT last_year - 2 FROM latest
    UNION ALL SELECT last_year - 3 FROM latest
    UNION ALL SELECT last_year - 4 FROM latest
    UNION ALL SELECT last_year - 5 FROM latest
),
compare AS (
    SELECT
        fc.scheme_code,
        fc.benchmark_id,
        fc.year,
        fc.fret,
        bc.bret,
        CASE WHEN fc.fret > bc.bret THEN 1 ELSE 0 END AS beat_flag
    FROM fund_cy fc
    JOIN window5 w USING (year)
    JOIN bench_cy bc ON bc.benchmark_id = fc.benchmark_id AND bc.year = fc.year
),
rolled AS (
    SELECT
        scheme_code,
        benchmark_id,
        SUM(beat_flag)     AS years_beaten,
        COUNT(*)           AS years_covered,
        GROUP_CONCAT(year || ':' || ROUND(fret - bret, 4), '|') AS gaps
    FROM compare
    GROUP BY scheme_code, benchmark_id
)
SELECT
    f.scheme_code,
    f.name,
    f.category,
    r.benchmark_id,
    r.years_beaten,
    r.years_covered,
    r.gaps
FROM rolled r
JOIN funds f ON f.scheme_code = r.scheme_code
WHERE r.years_covered = 5 AND r.years_beaten = 5
ORDER BY f.category, f.scheme_code;
