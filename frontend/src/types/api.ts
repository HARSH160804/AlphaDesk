/**
 * Server response types — mirrors the Pydantic schemas in backend/app/schemas.py.
 */

export type Category =
  | "large_cap"
  | "mid_cap"
  | "small_cap"
  | "flexi_cap"
  | "index"
  | "short_debt";

export const CATEGORY_LABEL: Record<Category, string> = {
  large_cap:  "Large Cap",
  mid_cap:    "Mid Cap",
  small_cap:  "Small Cap",
  flexi_cap:  "Flexi Cap",
  index:      "Index",
  short_debt: "Short Duration Debt",
};

export interface MetricPayload {
  value: number | null;
  reason: string | null;
}

export interface TrailingReturns {
  "1M": MetricPayload;
  "3M": MetricPayload;
  "6M": MetricPayload;
  "1Y": MetricPayload;
  "3Y": MetricPayload;
  "5Y": MetricPayload;
}

export interface FundSummary {
  scheme_code: number;
  name: string;
  category: Category;
  amc: string | null;
  benchmark_id: string | null;
  as_of: string | null;
  trailing: TrailingReturns;
  volatility: MetricPayload;
  max_drawdown: MetricPayload;
  sharpe: MetricPayload;
  sortino: MetricPayload;
  beta: MetricPayload;
  alpha: MetricPayload;
  pct_rank_3y: number | null;
}

export interface NavPoint {
  date: string;
  nav: number;
}

export interface DrawdownPoint {
  date: string;
  drawdown: number;
}

export interface RollingPoint {
  date: string;
  fund: number;
  bench: number | null;
}

export interface DrawdownEpisode {
  peak_date: string;
  trough_date: string;
  recovery_date: string | null;
  max_drawdown: number;
}

export interface FundDetail extends FundSummary {
  tracking_error: MetricPayload;
  information_ratio: MetricPayload;
  up_capture: MetricPayload;
  down_capture: MetricPayload;
  nav_series: NavPoint[];
  bench_series: NavPoint[];
  drawdown_series: DrawdownPoint[];
  worst_drawdown: DrawdownEpisode | null;
  rolling_1y: RollingPoint[];
  rolling_3y: RollingPoint[];
}

export interface CompareSeriesPoint {
  date: string;
  values: Record<string, number>;
}

export interface CompareResponse {
  labels: string[];
  aligned_start: string;
  aligned_end: string;
  rebased: CompareSeriesPoint[];
  metrics: FundSummary[];
}

export interface CategoryBest {
  scheme_code: number;
  name: string;
  value: number;
}

export interface CategorySummary {
  category: Category;
  fund_count: number;
  avg_1y: number | null;
  avg_3y: number | null;
  avg_5y: number | null;
  avg_vol: number | null;
  avg_max_drawdown: number | null;
  best_3y: CategoryBest | null;
  worst_3y: CategoryBest | null;
}

export interface IngestionStatus {
  id: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  funds_processed: number;
  benchmarks_processed: number;
  rows_inserted: number;
  errors: string[] | null;
  warnings: string[] | null;
}

export interface Stats {
  funds: number;
  nav_rows: number;
  latest_ingestion: {
    id: number;
    status: string;
    started_at: string | null;
    finished_at: string | null;
    rows_inserted: number;
  } | null;
}

export type SortKey =
  | "name" | "category"
  | "1Y" | "3Y" | "5Y"
  | "vol" | "sharpe" | "sortino" | "beta" | "alpha" | "max_dd";
