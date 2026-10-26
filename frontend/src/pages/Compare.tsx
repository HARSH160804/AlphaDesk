import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, X } from "lucide-react";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Delta } from "@/components/Delta";
import { PageHeader, Panel } from "@/components/PageHeader";
import { Select } from "@/components/Select";
import { ErrorState, EmptyState, Skeleton, SkeletonText } from "@/components/States";
import { Table, type Column } from "@/components/Table";
import { LineChart, type LinePoint } from "@/components/charts/LineChart";
import { useCompare, useFunds } from "@/hooks/queries";
import type { CompareResponse, FundSummary } from "@/types/api";
import { CATEGORY_LABEL } from "@/types/api";
import { formatNumber, formatPercent } from "@/lib/format";

export default function ComparePage(): JSX.Element {
  const [params, setParams] = useSearchParams();
  const [codes, setCodes] = useState<number[]>(
    (params.get("codes") ?? "")
      .split(",")
      .map((s) => parseInt(s, 10))
      .filter((n) => !Number.isNaN(n)),
  );
  const funds = useFunds({ sort: "3Y", order: "desc", limit: 100 });

  const compare = useCompare(codes);

  const options = useMemo(() => {
    if (!funds.data) return [{ label: "Loading…", value: "" }];
    return [
      { label: "Add fund…", value: "" },
      ...funds.data
        .filter((f) => !codes.includes(f.scheme_code))
        .map((f) => ({
          label: `${f.name.split(" - ")[0]} · ${CATEGORY_LABEL[f.category]}`,
          value: String(f.scheme_code),
        })),
    ];
  }, [funds.data, codes]);

  const addCode = (code: number) => {
    if (codes.length >= 6) return;
    const next = [...codes, code];
    setCodes(next);
    const p = new URLSearchParams(params);
    p.set("codes", next.join(","));
    setParams(p, { replace: true });
  };

  const removeCode = (code: number) => {
    const next = codes.filter((c) => c !== code);
    setCodes(next);
    const p = new URLSearchParams(params);
    if (next.length > 0) p.set("codes", next.join(","));
    else p.delete("codes");
    setParams(p, { replace: true });
  };

  return (
    <div className="flex flex-col gap-3">
      <PageHeader
        eyebrow="Compare"
        title="Side-by-side"
        subtitle="Pick 2 to 6 funds. The chart rebases every fund to 100 on their common start date; the table shows aligned metrics."
      />

      <Panel title="Selection" caption={`${codes.length} / 6`}>
        <div className="flex flex-wrap items-center gap-1">
          {codes.map((code) => {
            const meta = funds.data?.find((f) => f.scheme_code === code);
            return (
              <Badge key={code} tone="accent" className="pr-[2px]">
                <span>{meta?.name.split(" - ")[0] ?? `#${code}`}</span>
                <button
                  onClick={() => removeCode(code)}
                  className="ml-[4px] rounded px-[4px] text-fg-muted hover:bg-surface-sunken hover:text-fg"
                  aria-label={`Remove ${code}`}
                >
                  <X size={10} />
                </button>
              </Badge>
            );
          })}
          <Select
            value=""
            onChange={(e) => {
              if (!e.target.value) return;
              addCode(parseInt(e.target.value, 10));
            }}
            options={options}
            disabled={codes.length >= 6}
            aria-label="Add fund"
          />
          {codes.length > 0 && (
            <Button variant="ghost" size="sm" onClick={() => { setCodes([]); const p = new URLSearchParams(params); p.delete("codes"); setParams(p, { replace: true }); }}>
              Clear all
            </Button>
          )}
        </div>
      </Panel>

      {codes.length < 2 && (
        <EmptyState
          title="Pick at least two funds"
          description="Comparison needs two or more schemes to align on."
          icon={<Plus size={18} />}
        />
      )}

      {codes.length >= 2 && (
        <>
          <Panel title="Rebased to 100" caption={compare.data ? `${compare.data.aligned_start} → ${compare.data.aligned_end}` : "Aligning…"}>
            {compare.isLoading && <Skeleton className="h-72 w-full" />}
            {compare.error && <ErrorState message={(compare.error as Error).message} onRetry={() => compare.refetch()} />}
            {compare.data && <CompareChart data={compare.data} />}
          </Panel>

          <Panel title="Metrics" caption="Trailing + risk, computed on the aligned window">
            {compare.isLoading && <SkeletonText lines={5} />}
            {compare.data && (
              <Table<FundSummary>
                columns={metricCols}
                rows={compare.data.metrics}
                rowKey={(r) => r.scheme_code}
              />
            )}
          </Panel>
        </>
      )}
    </div>
  );
}

const metricCols: Column<FundSummary>[] = [
  {
    key: "name",
    label: "Fund",
    render: (r) => (
      <div className="flex flex-col">
        <span className="text-fg">{r.name.split(" - ")[0]}</span>
        <span className="text-2xs text-fg-subtle">{CATEGORY_LABEL[r.category]} · #{r.scheme_code}</span>
      </div>
    ),
  },
  { key: "1Y",   label: "1Y",      numeric: true, render: (r) => <Delta value={r.trailing["1Y"].value} /> },
  { key: "3Y",   label: "3Y CAGR", numeric: true, render: (r) => <Delta value={r.trailing["3Y"].value} /> },
  { key: "5Y",   label: "5Y CAGR", numeric: true, render: (r) => <Delta value={r.trailing["5Y"].value} /> },
  { key: "vol",  label: "Vol",     numeric: true, render: (r) => <span className="num text-fg-muted">{formatPercent(r.volatility.value)}</span> },
  { key: "dd",   label: "Max DD",  numeric: true, render: (r) => <Delta value={r.max_drawdown.value} /> },
  { key: "sharpe", label: "Sharpe", numeric: true, render: (r) => <span className="num">{r.sharpe.value === null ? "—" : formatNumber(r.sharpe.value, { decimals: 2 })}</span> },
  { key: "beta", label: "β",       numeric: true, render: (r) => <span className="num">{r.beta.value === null ? "—" : formatNumber(r.beta.value, { decimals: 2 })}</span> },
];

interface CompareChartProps { data: CompareResponse }
function CompareChart({ data }: CompareChartProps): JSX.Element {
  // Use the first label's series as the canonical fund line; render others as additional dashed lines.
  // LineChart only knows fund+bench, so for N-way compare we build an SVG manually.
  const labels = data.labels;
  if (labels.length === 2) {
    const [a, b] = labels;
    const points: LinePoint[] = data.rebased.map((p) => ({
      date: p.date,
      fund: p.values[a],
      bench: p.values[b] ?? null,
    }));
    return <LineChart data={points} height={320} fundLabel={a} benchLabel={b} />;
  }
  return <MultiLine data={data} />;
}

function MultiLine({ data }: CompareChartProps): JSX.Element {
  const width = 1200;
  const height = 320;
  const padL = 48;
  const padR = 16;
  const padT = 12;
  const padB = 24;
  const inner = width - padL - padR;
  const innerH = height - padT - padB;

  const palette = [
    "rgb(var(--chart-fund))",
    "rgb(var(--chart-bench))",
    "rgb(var(--warn))",
    "rgb(var(--pos))",
    "rgb(var(--neg))",
    "rgb(var(--accent-muted))",
  ];

  const all = data.rebased.flatMap((p) => data.labels.map((l) => p.values[l]).filter((v) => Number.isFinite(v)));
  const yMin = Math.min(...all);
  const yMax = Math.max(...all);
  const yPad = (yMax - yMin) * 0.05 || 1;
  const yLo = yMin - yPad;
  const yHi = yMax + yPad;

  const x = (i: number) => padL + (i / (data.rebased.length - 1 || 1)) * inner;
  const y = (v: number) => padT + ((yHi - v) / (yHi - yLo)) * innerH;

  const yTicks = 4;
  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => yLo + ((yHi - yLo) * i) / yTicks);

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="none" style={{ height }}>
        {/* grid */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line
              x1={padL}
              x2={width - padR}
              y1={y(t)}
              y2={y(t)}
              stroke="rgb(var(--chart-grid))"
              strokeWidth={1}
            />
            <text
              x={padL - 6}
              y={y(t) + 3}
              fontSize={11}
              textAnchor="end"
              fill="rgb(var(--fg-subtle))"
            >
              {t.toFixed(0)}
            </text>
          </g>
        ))}
        {/* lines */}
        {data.labels.map((label, idx) => {
          const colour = palette[idx % palette.length];
          const dash = idx === 0 ? "0" : "4 3";
          const d = data.rebased
            .map((p, i) => {
              const v = p.values[label];
              return `${i === 0 ? "M" : "L"}${x(i).toFixed(2)},${y(v).toFixed(2)}`;
            })
            .join(" ");
          return (
            <path
              key={label}
              d={d}
              fill="none"
              stroke={colour}
              strokeWidth={1.4}
              strokeDasharray={dash}
            />
          );
        })}
      </svg>
      <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
        {data.labels.map((label, idx) => (
          <div key={label} className="inline-flex items-center gap-[6px]">
            <span
              className="inline-block h-[2px] w-3"
              style={{ background: palette[idx % palette.length] }}
            />
            <span className="text-fg">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
