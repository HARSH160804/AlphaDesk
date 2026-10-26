import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Download, Search } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Delta } from "@/components/Delta";
import { Input } from "@/components/Input";
import { Select } from "@/components/Select";
import { Table, type Column } from "@/components/Table";
import { EmptyState, ErrorState, Skeleton } from "@/components/States";
import { useFunds } from "@/hooks/queries";
import type { FundSummary, SortKey } from "@/types/api";
import { CATEGORY_LABEL } from "@/types/api";
import { formatNumber, formatPercent } from "@/lib/format";

const CATEGORY_OPTS = [
  { label: "All categories", value: "" },
  { label: "Large Cap",      value: "large_cap" },
  { label: "Mid Cap",        value: "mid_cap" },
  { label: "Small Cap",      value: "small_cap" },
  { label: "Flexi Cap",      value: "flexi_cap" },
  { label: "Index",          value: "index" },
  { label: "Short Duration Debt", value: "short_debt" },
];

export default function FundsPage(): JSX.Element {
  const [params, setParams] = useSearchParams();
  const category = params.get("category") ?? "";
  const [search, setSearch] = useState(params.get("search") ?? "");
  const [sort, setSort] = useState<SortKey>((params.get("sort") as SortKey) ?? "3Y");
  const [order, setOrder] = useState<"asc" | "desc">((params.get("order") as "asc" | "desc") ?? "desc");

  const query = useFunds({
    category: category || undefined,
    search: search || undefined,
    sort,
    order,
    limit: 100,
  });

  const toggleSort = (key: string) => {
    if (sort === key) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSort(key as SortKey);
      setOrder("desc");
    }
  };

  const onCategory = (v: string) => {
    const p = new URLSearchParams(params);
    if (v) p.set("category", v);
    else p.delete("category");
    setParams(p, { replace: true });
  };

  const exportCsv = () => {
    if (!query.data) return;
    const rows = [
      ["scheme_code", "name", "category", "1Y", "3Y", "5Y", "vol", "max_dd", "sharpe", "beta"].join(","),
      ...query.data.map((r) =>
        [
          r.scheme_code,
          JSON.stringify(r.name),
          r.category,
          r.trailing["1Y"].value ?? "",
          r.trailing["3Y"].value ?? "",
          r.trailing["5Y"].value ?? "",
          r.volatility.value ?? "",
          r.max_drawdown.value ?? "",
          r.sharpe.value ?? "",
          r.beta.value ?? "",
        ].join(","),
      ),
    ].join("\n");
    const blob = new Blob([rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "alphadesk-funds.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const columns = useMemo<Column<FundSummary>[]>(() => [
    {
      key: "name",
      label: "Fund",
      sortable: true,
      render: (r) => (
        <Link
          to={`/funds/${r.scheme_code}`}
          className="group flex flex-col text-fg transition-colors hover:text-accent"
        >
          <span className="font-medium text-fg group-hover:text-accent">
            {r.name.split(" - ")[0]}
          </span>
          <span className="text-2xs text-fg-subtle">
            #{r.scheme_code} · {r.amc ?? "—"}
          </span>
        </Link>
      ),
      width: "28%",
    },
    {
      key: "category",
      label: "Category",
      sortable: true,
      render: (r) => <Badge>{CATEGORY_LABEL[r.category]}</Badge>,
      width: "11%",
    },
    { key: "1Y", label: "1Y",       numeric: true, sortable: true, render: (r) => <Delta value={r.trailing["1Y"].value} /> },
    { key: "3Y", label: "3Y CAGR",  numeric: true, sortable: true, render: (r) => <Delta value={r.trailing["3Y"].value} /> },
    { key: "5Y", label: "5Y CAGR",  numeric: true, sortable: true, render: (r) => <Delta value={r.trailing["5Y"].value} /> },
    {
      key: "vol",
      label: "Vol",
      numeric: true,
      sortable: true,
      render: (r) => <span className="num text-fg-muted">{formatPercent(r.volatility.value)}</span>,
    },
    { key: "max_dd", label: "Max DD", numeric: true, sortable: true, render: (r) => <Delta value={r.max_drawdown.value} /> },
    {
      key: "sharpe",
      label: "Sharpe",
      numeric: true,
      sortable: true,
      render: (r) =>
        r.sharpe.value === null ? (
          <span className="num text-fg-subtle">—</span>
        ) : (
          <span className="num text-fg">{formatNumber(r.sharpe.value, { decimals: 2 })}</span>
        ),
    },
    {
      key: "pct_rank",
      label: "Rank",
      numeric: true,
      render: (r) => <PctRank value={r.pct_rank_3y} />,
      width: "9%",
    },
  ], []);

  return (
    <div className="flex flex-col gap-2">
      <PageHeader
        eyebrow="Universe"
        title="Funds"
        subtitle="Every scheme in the universe. Click any row for the full scorecard."
        actions={
          <Button variant="secondary" size="sm" onClick={exportCsv} disabled={!query.data}>
            <Download size={12} /> Export CSV
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-1">
        <Input
          leading={<Search size={14} />}
          placeholder="Search by fund name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-72"
        />
        <Select
          value={category}
          onChange={(e) => onCategory(e.target.value)}
          options={CATEGORY_OPTS}
        />
        <div className="ml-auto text-xs text-fg-muted">
          {query.data ? `${query.data.length} funds` : <Skeleton className="h-3 w-16" />}
        </div>
      </div>

      {query.error && (
        <ErrorState message={(query.error as Error).message} onRetry={() => query.refetch()} />
      )}

      {query.isLoading && (
        <div className="rounded border border-hairline p-2">
          <Skeleton className="mb-1 h-5 w-full" />
          <Skeleton className="mb-1 h-5 w-full" />
          <Skeleton className="h-5 w-full" />
        </div>
      )}

      {query.data && query.data.length === 0 && (
        <EmptyState
          title="No funds match your filters"
          description="Try broadening the category or clearing the search."
          action={<Button variant="secondary" size="sm" onClick={() => { setSearch(""); onCategory(""); }}>Reset filters</Button>}
        />
      )}

      {query.data && query.data.length > 0 && (
        <Table<FundSummary>
          columns={columns}
          rows={query.data}
          rowKey={(r) => r.scheme_code}
          sortKey={sort}
          sortOrder={order}
          onSort={toggleSort}
        />
      )}
    </div>
  );
}

function PctRank({ value }: { value: number | null }): JSX.Element {
  if (value === null) return <span className="num text-fg-subtle">—</span>;
  const pct = Math.round(value);
  return (
    <div className="flex items-center justify-end gap-1">
      <div className="h-[6px] w-10 rounded bg-surface-sunken">
        <div
          className="h-full rounded bg-accent"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="num text-2xs text-fg-muted">{pct}</span>
    </div>
  );
}

