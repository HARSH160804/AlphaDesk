/**
 * /design — single-page gallery of every design-system primitive the rest
 * of the app will consume. Numbers used in the demos come from the actual
 * Phase 2 scorecards (Parag Parikh Flexi Cap, Nifty 50 index funds, etc.)
 * so this page is a review surface, not a lorem-ipsum mockup.
 */
import { useMemo, useState } from "react";
import { TrendingUp, Filter, Download } from "lucide-react";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Delta } from "@/components/Delta";
import { Input } from "@/components/Input";
import { Segmented, Select } from "@/components/Select";
import { Sparkline } from "@/components/Sparkline";
import { StatCard } from "@/components/StatCard";
import { Table, type Column } from "@/components/Table";
import { LineChart, type LinePoint } from "@/components/charts/LineChart";
import { EmptyState, ErrorState, SkeletonText } from "@/components/States";
import { formatPercent } from "@/lib/format";

// Hand-picked rows from the live /api/funds output.
interface Row {
  code: number;
  name: string;
  category: string;
  y1: number;
  y3: number;
  y5: number;
  vol: number;
  maxDd: number;
  sharpe: number;
  spark: number[];
}

const ROWS: Row[] = [
  {
    code: 122639,
    name: "Parag Parikh Flexi Cap",
    category: "Flexi Cap",
    y1: -0.0668,
    y3: 0.1229,
    y5: 0.1047,
    vol: 0.1188,
    maxDd: -0.3120,
    sharpe: 0.936,
    spark: [100, 103, 108, 104, 110, 118, 121, 123, 120, 126, 131, 128],
  },
  {
    code: 118955,
    name: "HDFC Flexi Cap",
    category: "Flexi Cap",
    y1: -0.0676,
    y3: 0.1439,
    y5: 0.1429,
    vol: 0.1706,
    maxDd: -0.4184,
    sharpe: 0.572,
    spark: [100, 102, 109, 100, 109, 118, 122, 118, 125, 134, 131, 139],
  },
  {
    code: 140228,
    name: "Edelweiss Mid Cap",
    category: "Mid Cap",
    y1: -0.0368,
    y3: 0.1818,
    y5: 0.1543,
    vol: 0.1715,
    maxDd: -0.3921,
    sharpe: 0.747,
    spark: [100, 97, 103, 109, 114, 121, 128, 132, 141, 148, 153, 162],
  },
  {
    code: 119212,
    name: "DSP Small Cap",
    category: "Small Cap",
    y1: 0.0986,
    y3: 0.1542,
    y5: 0.1559,
    vol: 0.1652,
    maxDd: -0.4906,
    sharpe: 0.863,
    spark: [100, 94, 108, 115, 122, 118, 130, 141, 149, 155, 162, 171],
  },
  {
    code: 120716,
    name: "UTI Nifty 50 Index",
    category: "Index",
    y1: -0.1192,
    y3: 0.0645,
    y5: 0.0553,
    vol: 0.1603,
    maxDd: -0.3842,
    sharpe: 0.358,
    spark: [100, 101, 105, 97, 103, 108, 112, 110, 115, 118, 113, 109],
  },
];

const columns: Column<Row>[] = [
  {
    key: "name",
    label: "Fund",
    render: (r) => (
      <div className="flex flex-col">
        <span className="font-medium text-fg">{r.name}</span>
        <span className="text-2xs text-fg-subtle">#{r.code}</span>
      </div>
    ),
    sortable: true,
    width: "28%",
  },
  { key: "category", label: "Category", render: (r) => <Badge>{r.category}</Badge>, width: "14%" },
  { key: "1Y", label: "1Y", numeric: true, sortable: true, render: (r) => <Delta value={r.y1} /> },
  { key: "3Y", label: "3Y CAGR", numeric: true, sortable: true, render: (r) => <Delta value={r.y3} /> },
  { key: "5Y", label: "5Y CAGR", numeric: true, sortable: true, render: (r) => <Delta value={r.y5} /> },
  {
    key: "vol",
    label: "Vol",
    numeric: true,
    sortable: true,
    render: (r) => <span className="num text-fg-muted">{formatPercent(r.vol)}</span>,
  },
  {
    key: "max_dd",
    label: "Max DD",
    numeric: true,
    sortable: true,
    render: (r) => <Delta value={r.maxDd} />,
  },
  {
    key: "spark",
    label: "1Y Trend",
    render: (r) => <Sparkline values={r.spark} />,
    width: "92px",
    className: "text-right",
  },
];

// Synthetic NAV series — a 5-year walk that mirrors the real fund-vs-bench shape.
function buildSeries(): LinePoint[] {
  const out: LinePoint[] = [];
  let fund = 100;
  let bench = 100;
  const start = new Date("2021-10-27");
  for (let i = 0; i < 60; i++) {
    const d = new Date(start);
    d.setMonth(d.getMonth() + i);
    // Monthly drifts drawn from a deterministic seed.
    const sinF = Math.sin((i + 3) / 3.2) * 2.1;
    const sinB = Math.sin((i + 1) / 2.9) * 2.6;
    fund += 1.1 + sinF;
    bench += 0.8 + sinB;
    out.push({
      date: d.toISOString().slice(0, 10),
      fund: Math.round(fund * 100) / 100,
      bench: Math.round(bench * 100) / 100,
    });
  }
  return out;
}

export default function DesignPage(): JSX.Element {
  const [sortKey, setSortKey] = useState<string>("3Y");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [period, setPeriod] = useState<"1Y" | "3Y" | "5Y">("3Y");

  const sortedRows = useMemo(() => {
    const copy = [...ROWS];
    copy.sort((a, b) => {
      const map: Record<string, number> = {
        "1Y": 0,
        "3Y": 1,
        "5Y": 2,
        vol: 3,
        max_dd: 4,
      };
      const idx = map[sortKey];
      if (idx === undefined) {
        return sortOrder === "asc"
          ? a.name.localeCompare(b.name)
          : b.name.localeCompare(a.name);
      }
      const va = [a.y1, a.y3, a.y5, a.vol, a.maxDd][idx];
      const vb = [b.y1, b.y3, b.y5, b.vol, b.maxDd][idx];
      return sortOrder === "asc" ? va - vb : vb - va;
    });
    return copy;
  }, [sortKey, sortOrder]);

  const toggleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  const series = useMemo(buildSeries, []);

  return (
    <div className="flex flex-col gap-5">
      <PageHeading />

      <Section title="Design tokens" caption="RGB triplets in src/styles/tokens.css, consumed by Tailwind utilities.">
        <TokensPanel />
      </Section>

      <Section title="Type scale" caption="12 / 13 / 14 / 16 / 20 / 24 / 32. Numbers use tabular-nums everywhere.">
        <TypePanel />
      </Section>

      <Section title="Buttons" caption="Primary, secondary, ghost, destructive. 150–200ms transitions.">
        <div className="flex flex-wrap items-center gap-1">
          <Button>Generate Report</Button>
          <Button variant="secondary">
            <Download size={14} /> Export CSV
          </Button>
          <Button variant="ghost">
            <Filter size={14} /> Filters
          </Button>
          <Button variant="destructive">Delete</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button size="sm" variant="secondary">
            Small
          </Button>
        </div>
      </Section>

      <Section title="Inputs" caption="Hairline border on hover/focus, no glow.">
        <div className="flex flex-wrap items-center gap-1">
          <Input placeholder="Search funds…" className="w-64" />
          <Select
            options={[
              { label: "All categories", value: "" },
              { label: "Large Cap", value: "large_cap" },
              { label: "Mid Cap", value: "mid_cap" },
              { label: "Small Cap", value: "small_cap" },
            ]}
          />
          <Segmented
            value={period}
            onChange={setPeriod}
            options={[
              { label: "1Y", value: "1Y" },
              { label: "3Y", value: "3Y" },
              { label: "5Y", value: "5Y" },
            ]}
          />
        </div>
      </Section>

      <Section title="Stat cards" caption="Label small-caps, value in 20px tabular, optional delta.">
        <div className="grid grid-cols-2 gap-1.5 md:grid-cols-4">
          <StatCard
            label="3Y CAGR"
            value={formatPercent(0.1229)}
            delta={0.0229}
            secondary="vs Nifty 50"
          />
          <StatCard
            label="Max drawdown"
            value={formatPercent(-0.3120)}
            secondary="Feb → Jul 2020"
          />
          <StatCard
            label="Volatility (ann.)"
            value={formatPercent(0.1188)}
            hint="rf 6.5%"
            secondary="Sharpe 0.94 · Sortino 1.38"
          />
          <StatCard
            label="% Beat 3Y"
            value={formatPercent(0.78, { signed: false })}
            delta={0.12}
            secondary="rolling 3Y windows"
          />
        </div>
      </Section>

      <Section
        title="Chart"
        caption="Thin 1.5px line, dashed benchmark, hairline gridlines, custom tooltip with crosshair."
      >
        <div className="rounded border border-hairline bg-surface p-2">
          <div className="mb-1 flex items-center justify-between">
            <div>
              <div className="text-xs text-fg-subtle">Parag Parikh Flexi Cap vs Nifty 50</div>
              <div className="num text-lg font-semibold">
                {series[series.length - 1].fund.toFixed(2)}
              </div>
            </div>
            <Segmented
              value={period}
              onChange={setPeriod}
              options={[
                { label: "1Y", value: "1Y" },
                { label: "3Y", value: "3Y" },
                { label: "5Y", value: "5Y" },
              ]}
            />
          </div>
          <LineChart data={series} height={240} benchLabel="Nifty 50" fundLabel="PPFC" />
        </div>
      </Section>

      <Section
        title="Data table"
        caption="Sticky header, sortable, right-aligned numbers, inline 1Y sparkline. Colour only on return deltas."
      >
        <Table<Row>
          columns={columns}
          rows={sortedRows}
          rowKey={(r) => r.code}
          sortKey={sortKey}
          sortOrder={sortOrder}
          onSort={toggleSort}
        />
      </Section>

      <Section
        title="Async states"
        caption="Every data view needs these three. No spinners floating in empty space."
      >
        <div className="grid gap-1.5 md:grid-cols-3">
          <div className="rounded border border-hairline bg-surface-raised p-2">
            <div className="mb-1 text-2xs font-medium uppercase tracking-wide text-fg-subtle">
              Loading
            </div>
            <SkeletonText lines={4} />
          </div>
          <div className="rounded border border-hairline bg-surface-raised p-2">
            <div className="mb-1 text-2xs font-medium uppercase tracking-wide text-fg-subtle">
              Empty
            </div>
            <EmptyState
              title="No funds match your filters"
              description="Try broadening the category or clearing the search box."
              action={<Button variant="secondary" size="sm">Reset filters</Button>}
            />
          </div>
          <div className="rounded border border-hairline bg-surface-raised p-2">
            <div className="mb-1 text-2xs font-medium uppercase tracking-wide text-fg-subtle">
              Error
            </div>
            <ErrorState
              message="The API returned a 500 while loading the fund list."
              onRetry={() => undefined}
            />
          </div>
        </div>
      </Section>

      <Section title="Badges" caption="Pos / neg use muted bg + saturated text, not neon fills.">
        <div className="flex flex-wrap items-center gap-1">
          <Badge>Flexi Cap</Badge>
          <Badge tone="pos">
            <TrendingUp size={11} /> Beats benchmark 5/5
          </Badge>
          <Badge tone="neg">Underperformer</Badge>
          <Badge tone="warn">Stale NAV</Badge>
          <Badge tone="accent">Direct · Growth</Badge>
        </div>
      </Section>
    </div>
  );
}

function PageHeading(): JSX.Element {
  return (
    <div>
      <div className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">
        /design
      </div>
      <h1 className="text-xl font-semibold tracking-tight text-fg">Design system</h1>
      <p className="mt-[2px] max-w-xl text-sm text-fg-muted">
        A single-page gallery of every primitive the dashboard will use —
        tokens, type scale, components, chart, and the three async states.
        If anything looks inconsistent here, it will look inconsistent in
        production.
      </p>
    </div>
  );
}

function Section({
  title,
  caption,
  children,
}: {
  title: string;
  caption?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <section className="flex flex-col gap-1.5">
      <div>
        <h2 className="text-sm font-semibold tracking-tight text-fg">{title}</h2>
        {caption && <p className="text-xs text-fg-muted">{caption}</p>}
      </div>
      {children}
    </section>
  );
}

function TokensPanel(): JSX.Element {
  const groups: Array<{ heading: string; swatches: Array<{ name: string; cls: string; token: string }> }> = [
    {
      heading: "Surface",
      swatches: [
        { name: "surface", cls: "bg-surface border-hairline", token: "--surface" },
        { name: "surface-raised", cls: "bg-surface-raised", token: "--surface-raised" },
        { name: "surface-sunken", cls: "bg-surface-sunken", token: "--surface-sunken" },
      ],
    },
    {
      heading: "Foreground",
      swatches: [
        { name: "fg", cls: "bg-fg", token: "--fg" },
        { name: "fg-muted", cls: "bg-fg-muted", token: "--fg-muted" },
        { name: "fg-subtle", cls: "bg-fg-subtle", token: "--fg-subtle" },
      ],
    },
    {
      heading: "Lines",
      swatches: [
        { name: "hairline", cls: "bg-hairline", token: "--hairline" },
        { name: "hairline-strong", cls: "bg-hairline-strong", token: "--hairline-strong" },
      ],
    },
    {
      heading: "Accent",
      swatches: [
        { name: "accent", cls: "bg-accent", token: "--accent" },
        { name: "accent-muted", cls: "bg-accent-muted", token: "--accent-muted" },
      ],
    },
    {
      heading: "Semantic",
      swatches: [
        { name: "pos", cls: "bg-pos", token: "--pos" },
        { name: "pos-bg", cls: "bg-pos-bg", token: "--pos-bg" },
        { name: "neg", cls: "bg-neg", token: "--neg" },
        { name: "neg-bg", cls: "bg-neg-bg", token: "--neg-bg" },
        { name: "warn", cls: "bg-warn", token: "--warn" },
      ],
    },
  ];
  return (
    <div className="grid gap-2 md:grid-cols-5">
      {groups.map((g) => (
        <div key={g.heading} className="flex flex-col gap-[6px]">
          <div className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">
            {g.heading}
          </div>
          <div className="flex flex-col gap-[6px]">
            {g.swatches.map((s) => (
              <div key={s.name} className="flex items-center gap-1">
                <div
                  className={`${s.cls} h-5 w-5 rounded border border-hairline`}
                  aria-hidden
                />
                <div className="flex flex-col">
                  <span className="text-2xs text-fg">{s.name}</span>
                  <span className="font-mono text-2xs text-fg-subtle">{s.token}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function TypePanel(): JSX.Element {
  const rows = [
    { cls: "text-2xl font-semibold tracking-tight", name: "2xl / 32", role: "Dashboard hero" },
    { cls: "text-xl font-semibold tracking-tight",  name: "xl / 24",  role: "Page title" },
    { cls: "text-lg font-semibold tracking-tight",  name: "lg / 20",  role: "Stat value" },
    { cls: "text-base",                              name: "base / 16", role: "Body" },
    { cls: "text-sm",                                name: "sm / 14",   role: "Table cell" },
    { cls: "text-xs",                                name: "xs / 13",   role: "Secondary text" },
    { cls: "text-2xs uppercase tracking-wide text-fg-subtle", name: "2xs / 12", role: "Label" },
  ];
  return (
    <div className="flex flex-col divide-y divide-hairline rounded border border-hairline">
      {rows.map((r) => (
        <div key={r.name} className="flex items-baseline gap-2 px-2 py-[10px]">
          <div className={`${r.cls} flex-1`}>Mutual fund direct plan</div>
          <div className="w-24 text-2xs text-fg-subtle">{r.name}</div>
          <div className="w-32 text-2xs text-fg-muted">{r.role}</div>
        </div>
      ))}
      <div className="flex items-center gap-2 bg-surface-sunken px-2 py-1 text-2xs">
        <span className="font-medium text-fg">Numbers:</span>
        <span className="num">+12.29%</span>
        <span className="num">−31.20%</span>
        <span className="num">1,24,567.89</span>
        <span className="text-fg-subtle">tabular-nums, Indian grouping</span>
      </div>
    </div>
  );
}
