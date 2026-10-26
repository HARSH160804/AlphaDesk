import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Badge } from "@/components/Badge";
import { Delta } from "@/components/Delta";
import { PageHeader, Panel } from "@/components/PageHeader";
import { Segmented } from "@/components/Select";
import { StatCard } from "@/components/StatCard";
import { ErrorState, Skeleton, SkeletonText } from "@/components/States";
import { LineChart, type LinePoint } from "@/components/charts/LineChart";
import { useFund } from "@/hooks/queries";
import { CATEGORY_LABEL, type FundDetail, type MetricPayload } from "@/types/api";
import { formatDate, formatNumber, formatPercent } from "@/lib/format";

type Period = "1Y" | "3Y" | "5Y" | "ALL";

export default function FundDetailPage(): JSX.Element {
  const { code } = useParams<{ code: string }>();
  const schemeCode = code ? parseInt(code, 10) : null;
  const query = useFund(schemeCode);
  const [period, setPeriod] = useState<Period>("3Y");

  if (!schemeCode || Number.isNaN(schemeCode)) {
    return <ErrorState message="Invalid scheme code." />;
  }

  if (query.error) {
    return (
      <div className="flex flex-col gap-2">
        <BackLink />
        <ErrorState message={(query.error as Error).message} onRetry={() => query.refetch()} />
      </div>
    );
  }

  if (query.isLoading || !query.data) {
    return (
      <div className="flex flex-col gap-2">
        <BackLink />
        <Skeleton className="h-8 w-80" />
        <Skeleton className="h-5 w-56" />
        <div className="mt-2 grid grid-cols-2 gap-1.5 md:grid-cols-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
        <Skeleton className="mt-2 h-72" />
      </div>
    );
  }

  const fund = query.data;
  const navWindow = sliceByPeriod(fund.nav_series, period);
  const benchWindow = sliceByPeriod(fund.bench_series, period);
  const chartData = mergeFundBench(navWindow, benchWindow);
  const drawdownWindow = sliceByPeriod(fund.drawdown_series, period, "drawdown");

  return (
    <div className="flex flex-col gap-3">
      <BackLink />
      <PageHeader
        eyebrow={`${CATEGORY_LABEL[fund.category]} · #${fund.scheme_code}`}
        title={fund.name.replace(" - Direct Plan - Growth Option", "").replace(" - Direct Plan - Growth", "")}
        subtitle={`${fund.amc ?? "—"} · benchmarked against ${fund.benchmark_id ?? "none"} · as of ${fund.as_of ? formatDate(fund.as_of) : "—"}`}
        actions={
          <Link to={`/compare?codes=${fund.scheme_code}`} className="text-xs text-accent hover:underline">
            Add to compare →
          </Link>
        }
      />

      <div className="grid grid-cols-2 gap-1.5 md:grid-cols-4">
        <TrailingTile label="1Y" mv={fund.trailing["1Y"]} />
        <TrailingTile label="3Y CAGR" mv={fund.trailing["3Y"]} />
        <TrailingTile label="5Y CAGR" mv={fund.trailing["5Y"]} />
        <StatCard
          label="Peer rank (3Y)"
          value={
            fund.pct_rank_3y === null
              ? "—"
              : `${Math.round(fund.pct_rank_3y)}th`
          }
          secondary={`within ${CATEGORY_LABEL[fund.category]}`}
        />
      </div>

      <Panel
        title="NAV rebased to 100"
        caption={fund.benchmark_id ? `vs ${fund.benchmark_id}` : "No benchmark"}
        actions={
          <Segmented<Period>
            value={period}
            onChange={setPeriod}
            options={[
              { label: "1Y", value: "1Y" },
              { label: "3Y", value: "3Y" },
              { label: "5Y", value: "5Y" },
              { label: "All", value: "ALL" },
            ]}
          />
        }
      >
        {chartData.length === 0 ? (
          <SkeletonText lines={5} />
        ) : (
          <LineChart
            data={rebaseLine(chartData)}
            height={280}
            fundLabel={fund.name.split(" - ")[0]}
            benchLabel={fund.benchmark_id ?? "Bench"}
          />
        )}
      </Panel>

      <div className="grid grid-cols-1 gap-2 lg:grid-cols-3">
        <Panel title="Risk" caption="Sample statistics on daily returns">
          <StatList
            rows={[
              { label: "Volatility (ann.)", value: formatPercent(fund.volatility.value), muted: !fund.volatility.value },
              { label: "Max drawdown",       value: <Delta value={fund.max_drawdown.value} size="base" /> },
              { label: "Sharpe",             value: fund.sharpe.value === null ? "—" : formatNumber(fund.sharpe.value, { decimals: 2 }) },
              { label: "Sortino",            value: fund.sortino.value === null ? "—" : formatNumber(fund.sortino.value, { decimals: 2 }) },
            ]}
          />
        </Panel>

        <Panel title="vs Benchmark" caption={fund.benchmark_id ?? "—"}>
          <StatList
            rows={[
              { label: "Beta",             value: metricNumber(fund.beta) },
              { label: "Jensen's α (ann.)", value: fund.alpha.value === null ? "—" : <Delta value={fund.alpha.value} size="base" /> },
              { label: "Tracking error",   value: formatPercent(fund.tracking_error.value) },
              { label: "Information ratio", value: metricNumber(fund.information_ratio) },
              { label: "Up / Down capture", value: fund.up_capture.value === null ? "—" : `${formatNumber(fund.up_capture.value, { decimals: 2 })} / ${formatNumber(fund.down_capture.value, { decimals: 2 })}` },
            ]}
          />
        </Panel>

        <Panel title="Worst drawdown">
          {fund.worst_drawdown === null ? (
            <div className="text-sm text-fg-muted">Not available.</div>
          ) : (
            <StatList
              rows={[
                { label: "Depth",     value: <Delta value={fund.worst_drawdown.max_drawdown} size="base" /> },
                { label: "Peak",      value: formatDate(fund.worst_drawdown.peak_date) },
                { label: "Trough",    value: formatDate(fund.worst_drawdown.trough_date) },
                { label: "Recovered", value: fund.worst_drawdown.recovery_date ? formatDate(fund.worst_drawdown.recovery_date) : <Badge tone="warn">Not recovered</Badge> },
              ]}
            />
          )}
        </Panel>
      </div>

      <Panel title="Drawdown over time" caption="Peak-to-current drawdown">
        {drawdownWindow.length === 0 ? (
          <SkeletonText lines={5} />
        ) : (
          <LineChart
            data={drawdownToLine(drawdownWindow)}
            height={200}
            fundLabel="Drawdown"
            yFormatter={(v) => formatPercent(v)}
          />
        )}
      </Panel>

      <Panel title="Rolling 3Y CAGR" caption="Each date = CAGR over the trailing 3 years">
        {fund.rolling_3y.length === 0 ? (
          <SkeletonText lines={4} />
        ) : (
          <LineChart
            data={rollingToLine(sliceByPeriod(fund.rolling_3y as unknown as RollingLikePoint[], period, "fund"))}
            height={200}
            fundLabel={fund.name.split(" - ")[0]}
            benchLabel={fund.benchmark_id ?? "Bench"}
            yFormatter={(v) => formatPercent(v)}
          />
        )}
      </Panel>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface RollingLikePoint {
  date: string;
  fund?: number | null;
  bench?: number | null;
  drawdown?: number | null;
  nav?: number | null;
}

function BackLink() {
  return (
    <Link to="/funds" className="inline-flex items-center gap-[4px] text-xs text-fg-muted transition-colors hover:text-fg">
      <ArrowLeft size={12} /> Back to funds
    </Link>
  );
}

function TrailingTile({ label, mv }: { label: string; mv: MetricPayload }): JSX.Element {
  return (
    <StatCard
      label={label}
      value={mv.value === null ? "—" : formatPercent(mv.value, { signed: true })}
      secondary={mv.reason ?? undefined}
    />
  );
}

function StatList({ rows }: { rows: Array<{ label: string; value: React.ReactNode; muted?: boolean }> }): JSX.Element {
  return (
    <dl className="flex flex-col divide-y divide-hairline">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center justify-between py-1 first:pt-0 last:pb-0">
          <dt className="text-xs text-fg-muted">{r.label}</dt>
          <dd className="text-sm text-fg">{r.value}</dd>
        </div>
      ))}
    </dl>
  );
}

function metricNumber(mv: MetricPayload): React.ReactNode {
  if (mv.value === null) return <span className="text-fg-subtle">—</span>;
  return <span className="num text-fg">{formatNumber(mv.value, { decimals: 2 })}</span>;
}

function cutoffDate(period: Period, latestIso: string): string | null {
  if (period === "ALL") return null;
  const d = new Date(latestIso);
  const years = period === "1Y" ? 1 : period === "3Y" ? 3 : 5;
  d.setFullYear(d.getFullYear() - years);
  return d.toISOString().slice(0, 10);
}

function sliceByPeriod<T extends { date: string }>(
  series: T[],
  period: Period,
  _key?: string,
): T[] {
  if (series.length === 0) return series;
  const latest = series[series.length - 1].date;
  const cutoff = cutoffDate(period, latest);
  if (cutoff === null) return series;
  return series.filter((p) => p.date >= cutoff);
}

function mergeFundBench(nav: { date: string; nav: number }[], bench: { date: string; nav: number }[]): LinePoint[] {
  if (nav.length === 0) return [];
  const benchMap = new Map(bench.map((b) => [b.date, b.nav]));
  return nav.map((n) => ({ date: n.date, fund: n.nav, bench: benchMap.get(n.date) ?? null }));
}

function rebaseLine(points: LinePoint[]): LinePoint[] {
  if (points.length === 0) return points;
  const f0 = points[0].fund;
  const firstBench = points.find((p) => p.bench !== null && p.bench !== undefined)?.bench ?? null;
  return points.map((p) => ({
    date: p.date,
    fund: (p.fund / f0) * 100,
    bench: p.bench && firstBench ? (p.bench / firstBench) * 100 : null,
  }));
}

function drawdownToLine(points: { date: string; drawdown: number }[]): LinePoint[] {
  return points.map((p) => ({ date: p.date, fund: p.drawdown }));
}

function rollingToLine(points: RollingLikePoint[]): LinePoint[] {
  return points.map((p) => ({
    date: p.date,
    fund: p.fund ?? 0,
    bench: p.bench ?? null,
  }));
}

export type { FundDetail };
