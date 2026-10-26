# SQL analysis

Five standalone queries that an analyst would run during a performance review.
Each uses CTEs + window functions so the shape is explicit on the page: no
ORM, no magic. The `/api/sql/{query_name}` endpoint executes any of them by
name and returns the rows.

| name | file | question answered |
| --- | --- | --- |
| `calendar_year_returns`         | 01_calendar_year_returns.sql         | Full-year returns per fund across the sample |
| `beats_benchmark_last_5y`       | 02_beats_benchmark_last_5y.sql       | Who beat their benchmark in every one of the last 5 completed years |
| `category_leaderboard_3y`       | 03_category_leaderboard_3y.sql       | Within-category 3-year CAGR leaderboard |
| `monthly_return_heatmap`        | 04_monthly_return_heatmap.sql        | Long-format monthly returns for heatmap rendering |
| `worst_drawdown_month_by_cat`   | 05_worst_drawdown_month_by_category.sql | For each category, which calendar month was the worst |

## Dialect

Queries use SQLite date functions (`strftime`, `julianday`, `date(..., '-N years')`) because that's the default local dev DB. The Postgres compose profile would need the three date-math call sites rewritten (notes inline). Everything else — CTEs, `ROW_NUMBER`, `RANK`, `FIRST_VALUE`, `LAG` — is standard SQL.
