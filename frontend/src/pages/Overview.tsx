import { Link } from "react-router-dom";
import { ArrowUpRight, Database } from "lucide-react";
import { PageHeader, Panel } from "@/components/PageHeader";
import { Delta } from "@/components/Delta";
import { Badge } from "@/components/Badge";
import { StatCard } from "@/components/StatCard";
import { EmptyState, ErrorState, SkeletonText } from "@/components/States";
import { Table, type Column } from "@/components/Table";
import { useCategories, useFunds, useStats } from "@/hooks/queries";
import { CATEGORY_LABEL, type FundSummary } from "@/types/api";
import { formatDate, formatNumber, formatPercent } from "@/lib/format";

export default function OverviewPage(): JSX.Element {
  const stats = useStats();
  const categories = useCategories();
  const top = useFunds({ sort: "3Y", order: "desc", limit: 5 });

  const latest = stats.data?.latest_ingestion;

  return (
    <div className="flex flex-col gap-3">
      <PageHeader
        eyebrow="AlphaDesk"
        title="Overview"
        subtitle="29 Direct-Growth schemes across six categories, benchmarked daily against Nifty 50, Midcap 150 and Smallcap 250."
      />

      <div className="grid grid-cols-2 gap-1.5 md:grid-cols-4">
        <StatCard
          label="Funds tracked"
          value={stats.isLoading ? "—" : formatNumber(stats.data?.funds ?? 0, { decimals: 0 })}
          secondary="Direct Plan · Growth"
        />
        <StatCard
          label="NAV rows"
          value={stats.isLoading ? "—" : formatNumber(stats.data?.nav_rows ?? 0, { decimals: 0 })}
          secondary="Daily history, 13y"
        />
        <StatCard
          label="Latest ingest"
          value={
            !latest
              ? "—"
              : latest.finished_at
              ? formatDate(latest.finished_at)
              : "Running"
          }
          secondary={latest ? `${formatNumber(latest.rows_inserted, { decimals: 0 })} rows upserted` : "No run"}
        />
        <StatCard
          label="Pipeline status"
          value={
            latest ? (
              <span className="inline-flex items-center gap-1">
                <span className={`h-2 w-2 rounded-full ${latest.status === "success" ? "bg-pos" : "bg-neg"}`} />
                <span className="text-base capitalize">{latest.status}</span>
              </span>
            ) : (
              "—"
            )
          }
          hint={<Link to="/data-health" className="text-accent hover:underline inline-flex items-center gap-[2px]">Audit <ArrowUpRight size={10} /></Link>}
        />
      </div>

      <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
        <Panel title="Top performers (3Y CAGR)" caption="Across every category" actions={<Link to="/funds" className="text-xs text-accent hover:underline">All funds →</Link>}>
          {top.isLoading && <SkeletonText lines={5} />}
          {top.error && <ErrorState message={(top.error as Error).message} onRetry={() => top.refetch()} />}
          {top.data && (
            top.data.length === 0 ? (
              <EmptyState title="No funds" icon={<Database size={18} />} />
            ) : (
              <Table<FundSummary>
                columns={topColumns}
                rows={top.data}
                rowKey={(r) => r.scheme_code}
              />
            )
          )}
        </Panel>

        <Panel title="Category snapshot" caption="Average 3Y CAGR, max drawdown and fund count by peer group">
          {categories.isLoading && <SkeletonText lines={6} />}
          {categories.error && <ErrorState message={(categories.error as Error).message} onRetry={() => categories.refetch()} />}
          {categories.data && (
            <div className="flex flex-col divide-y divide-hairline">
              {categories.data.map((c) => (
                <Link
                  key={c.category}
                  to={`/funds?category=${c.category}`}
                  className="group grid grid-cols-6 items-center gap-1 py-1.5 transition-colors duration-quick first:pt-0 last:pb-0 hover:bg-surface-raised"
                >
                  <div className="col-span-2">
                    <div className="text-sm font-medium text-fg group-hover:text-accent">
                      {CATEGORY_LABEL[c.category]}
                    </div>
                    <div className="text-2xs text-fg-subtle">{c.fund_count} funds</div>
                  </div>
                  <div className="num col-span-1 text-xs text-fg-muted">
                    <div className="text-2xs text-fg-subtle">Avg 3Y</div>
                    <Delta value={c.avg_3y} />
                  </div>
                  <div className="num col-span-1 text-xs text-fg-muted">
                    <div className="text-2xs text-fg-subtle">Avg vol</div>
                    <span className="num">{formatPercent(c.avg_vol)}</span>
                  </div>
                  <div className="num col-span-1 text-xs text-fg-muted">
                    <div className="text-2xs text-fg-subtle">Avg DD</div>
                    <Delta value={c.avg_max_drawdown} />
                  </div>
                  <div className="col-span-1 text-right text-xs text-fg-muted">
                    <div className="text-2xs text-fg-subtle">Leader</div>
                    <div className="truncate text-xs text-fg">
                      {c.best_3y?.name.split(" - ")[0] ?? "—"}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

const topColumns: Column<FundSummary>[] = [
  {
    key: "name",
    label: "Fund",
    render: (r) => (
      <Link to={`/funds/${r.scheme_code}`} className="flex flex-col transition-colors hover:text-accent">
        <span className="font-medium text-fg group-hover:text-accent">{r.name.split(" - ")[0]}</span>
        <span className="text-2xs text-fg-subtle">#{r.scheme_code}</span>
      </Link>
    ),
    width: "42%",
  },
  {
    key: "category",
    label: "Category",
    render: (r) => <Badge>{CATEGORY_LABEL[r.category]}</Badge>,
    width: "22%",
  },
  {
    key: "3Y",
    label: "3Y",
    numeric: true,
    render: (r) => <Delta value={r.trailing["3Y"].value} />,
  },
  {
    key: "sharpe",
    label: "Sharpe",
    numeric: true,
    render: (r) => (
      <span className="num text-fg-muted">
        {r.sharpe.value === null ? "—" : formatNumber(r.sharpe.value, { decimals: 2 })}
      </span>
    ),
  },
];
