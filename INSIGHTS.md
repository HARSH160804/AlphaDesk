# AlphaDesk — Insights

Six findings pulled from the real NAV history ingested in Phase 1 (29 funds, 13 years of daily data). Every number here is computed in [notebooks/insights.ipynb](notebooks/insights.ipynb) and reproducible by running the matching SQL in [backend/sql/](backend/sql/).

As-of date in the data: **2026-10-23**.

---

## 1. Three Nifty 50 index funds — their returns are the same number

Over the last 5 years, HDFC, UTI and Nippon India's Nifty 50 index funds (Direct–Growth) delivered:

| Fund | 5Y CAGR | Annualised vol | Max drawdown |
| --- | ---: | ---: | ---: |
| Nippon India Index Fund – Nifty 50 Plan | 5.54% | 15.95% | −38.17% |
| UTI Nifty 50 Index Fund | 5.53% | 16.03% | −38.42% |
| HDFC Nifty 50 Index Fund | 5.48% | 16.01% | −38.36% |

The 5Y CAGR spread across the three is **0.06 percentage points** — about 6 basis points of annualised return separates the best from the worst. Vol spreads 8 bps; max-drawdown spreads 25 bps.

**So what for an investor.** Once an investor has decided to buy the Nifty 50, the choice of plan is dominated by the one lever the fund house actually controls: expense ratio. Any discussion of "which Nifty 50 index fund has better returns" is spurious at this precision.

---

## 2. Parag Parikh Flexi Cap earned nearly 2× the Sharpe of its peers

Across the four Flexi Cap funds in the universe:

| Fund | 3Y CAGR | 5Y CAGR | Vol | Max drawdown | Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: |
| HDFC Flexi Cap | 14.39% | 14.29% | 17.06% | −41.84% | 0.57 |
| **Parag Parikh Flexi Cap** | **12.29%** | **10.47%** | **11.88%** | **−31.20%** | **0.94** |
| Kotak Flexi Cap | 10.32% | 8.95% | 15.75% | −37.31% | 0.57 |
| UTI Flexi Cap | 7.06% | 3.02% | 14.87% | −33.86% | 0.47 |

PPFC's drawdown was ~**6.5 pp shallower** than the Flexi Cap peer average (−37.7%), and its Sharpe (0.94, rf = 6.5%) was **1.7× the peer average** (0.54). HDFC Flexi Cap delivered more absolute return, but PPFC earned far more return per unit of risk — a function of its ~30% international allocation that reduced correlation with Nifty 50 (its β is 0.57, vs 0.98 for HDFC).

**So what for an investor.** For a client who cares about the depth of the hole they fall into, PPFC has done more with less in this cycle. For a client who maximises absolute return and tolerates volatility, HDFC Flexi Cap wins the horse race.

---

## 3. Mid-cap manager selection is worth 6.6 pp per year

Within the Mid Cap peer group, 3Y CAGR ranges from:

| Fund | 3Y CAGR | 5Y CAGR | Max drawdown |
| --- | ---: | ---: | ---: |
| **Edelweiss Mid Cap** | **18.18%** | 15.43% | −39.21% |
| HDFC Mid Cap | 15.27% | 16.50% | −39.51% |
| Axis Midcap | 14.73% | 11.07% | −29.36% |
| Kotak Mid Cap | 13.91% | 13.82% | −35.97% |
| **DSP Midcap** | **11.54%** | 9.38% | −32.72% |

The top-to-bottom 3Y CAGR gap is **6.64 percentage points annualised**. On a ₹10 lakh allocation held 3 years, that's roughly ₹2.3 lakh of difference, same category, same risk mandate.

**So what for an investor.** Unlike the index group, Mid Cap manager choice is a load-bearing decision. The returns dispersion also doesn't track the risk dispersion cleanly: Axis Midcap has the lowest drawdown but one of the lowest 5Y returns; HDFC Mid Cap has the highest 5Y return and a middle-of-the-pack drawdown.

---

## 4. Every small-cap fund has handed investors a 34–49% drawdown

All five Small Cap funds in the universe have, at some point in the past decade, lost more than a third of their value:

| Fund | Max drawdown | 5Y CAGR |
| --- | ---: | ---: |
| DSP Small Cap | −49.06% | 15.59% |
| Nippon India Small Cap | −48.58% | 16.48% |
| Kotak Small Cap | −40.61% | 10.48% |
| SBI Small Cap | −40.26% | 11.34% |
| Axis Small Cap | −34.64% | 13.95% |

5-year returns are strong (10.5–16.5% CAGR). But the headline obscures the trough: **two of the five funds** have cut investor capital nearly in half at some point.

**So what for an investor.** The "small caps compounded at 15% over 5 years" sentence is true and misleading. An investor who sold near the 2020 trough locked in the drawdown rather than the recovery. A small-cap allocation only works for investors who have both the time horizon and the stomach for the trough.

---

## 5. Short-duration debt is a flat distribution — pick the cheapest

Short Duration Debt returns are tightly clustered:

| Fund | 5Y CAGR | Vol | Max drawdown | Sharpe |
| --- | ---: | ---: | ---: | ---: |
| ICICI Pru Short Term | 6.96% | 1.60% | −3.38% | 1.27 |
| Aditya Birla SL Short Term | 6.72% | 1.60% | −2.75% | 1.30 |
| Axis Short Term | 6.68% | 1.46% | −2.60% | 1.18 |
| HDFC Short Term | 6.43% | 1.34% | −2.67% | 1.18 |
| SBI Short Term | 6.26% | 1.37% | −2.35% | 0.98 |

5Y CAGR spread: **0.70 pp**. Vol spread: 26 bps. Max drawdown spread: 103 bps. Sharpe spread 0.32.

**So what for an investor.** As with the index group, the economically relevant choice is cost. The vol dispersion is small enough that stepping up to a fractionally riskier-looking fund isn't buying meaningfully more risk — it is buying meaningfully more net return for a client who holds for ≥ 3 years.

---

## 6. 5 of 20 active equity funds beat their benchmark in every one of the last 5 calendar years

Over the 5 full calendar years before the current one (2020-2024), the funds that cleared the bar every year:

| Fund | Category | Benchmark |
| --- | --- | --- |
| HDFC Flexi Cap | flexi_cap | Nifty 50 |
| Kotak Flexi Cap | flexi_cap | Nifty 50 |
| SBI Large Cap | large_cap | Nifty 50 |
| ICICI Pru Large Cap (ex-Bluechip) | large_cap | Nifty 50 |
| Nippon India Small Cap | small_cap | Nifty Smallcap 250 |

That's **5 of 20 active equity funds (25%)** — and 15 of 20 missed at least one year. The remaining 4 funds that appear in the SQL query are passive index funds beating their benchmark by their small tracking advantage (TRI vs price index).

**So what for an investor.** A majority of equity managers in this universe failed the "consistency across the cycle" test. Backward-looking rolling-return filters (3Y, 5Y) obscure this, because one or two very good years can carry a fund for a decade of marketing material. The 5-of-5 filter is a stricter screen and shrinks the "proven" pool to a handful.

As a reality check on the drawdowns in insights 2–4: in **March 2020** alone, the category-average single-month return was **−22% (large cap)**, **−23% (flexi)**, **−24% (index)**, **−25% (mid cap)** and **−29% (small cap)**. Short-duration debt's worst month in the whole 13-year window was **−1.6% (July 2013)**. That is the risk gap between equity and short debt, measured in a single month.

---

## How to reproduce

```bash
make ingest                             # populates data/alphadesk.db
cd backend && .venv/bin/jupyter nbconvert --to notebook --execute ../notebooks/insights.ipynb --output insights.ipynb
# or run against the API:
make dev-api
curl -s localhost:8000/api/sql/category_leaderboard_3y | jq '.rows[]'
curl -s localhost:8000/api/sql/beats_benchmark_last_5y
```

Every number above comes from one of the SQL queries in `backend/sql/` or the metrics module in `backend/analytics/metrics.py`. No fabricated figures.
