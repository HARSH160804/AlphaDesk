import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart as RLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDate, formatNumber } from "@/lib/format";

export interface LinePoint {
  date: string; // ISO
  fund: number;
  bench?: number | null;
}

interface LineChartProps {
  data: LinePoint[];
  height?: number;
  yFormatter?: (v: number) => string;
  benchLabel?: string;
  fundLabel?: string;
}

/**
 * Fully custom-styled wrapper around Recharts: thin lines, hairline gridlines,
 * dashed benchmark, crosshair on hover, and a custom tooltip that mirrors
 * the design-system card style.
 */
export function LineChart({
  data,
  height = 240,
  yFormatter = (v) => formatNumber(v),
  benchLabel = "Benchmark",
  fundLabel = "Fund",
}: LineChartProps): JSX.Element {
  const hasBench = useMemo(
    () => data.some((d) => d.bench !== null && d.bench !== undefined),
    [data],
  );

  // Pick one tick per calendar year — the first observation of each year —
  // so the x-axis never shows "2024 2024 2024…" from densely sampled series.
  const yearTicks = useMemo(() => {
    const seen = new Set<string>();
    const picks: string[] = [];
    for (const p of data) {
      const y = p.date.slice(0, 4);
      if (!seen.has(y)) {
        seen.add(y);
        picks.push(p.date);
      }
    }
    return picks;
  }, [data]);

  const xTick = (iso: string) => iso.slice(0, 4);

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RLineChart
          data={data}
          margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
        >
          <CartesianGrid
            stroke="rgb(var(--chart-grid))"
            strokeDasharray="0"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tickFormatter={xTick}
            ticks={yearTicks}
            tick={{ fontSize: 11, fill: "rgb(var(--fg-subtle))" }}
            axisLine={{ stroke: "rgb(var(--hairline))" }}
            tickLine={false}
            interval={0}
          />
          <YAxis
            tickFormatter={(v) => yFormatter(Number(v))}
            tick={{ fontSize: 11, fill: "rgb(var(--fg-subtle))" }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip
            cursor={{
              stroke: "rgb(var(--chart-crosshair))",
              strokeWidth: 1,
              strokeDasharray: "2 2",
            }}
            content={(p: unknown) => {
              const tp = p as { active?: boolean; payload?: Array<{ value?: number; dataKey?: string; payload?: { date?: string } }> };
              return (
                <ChartTooltip
                  active={tp.active}
                  payload={tp.payload}
                  yFormatter={yFormatter}
                  fundLabel={fundLabel}
                  benchLabel={benchLabel}
                />
              );
            }}
          />
          <Line
            type="monotone"
            dataKey="fund"
            stroke="rgb(var(--chart-fund))"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
            name={fundLabel}
          />
          {hasBench && (
            <Line
              type="monotone"
              dataKey="bench"
              stroke="rgb(var(--chart-bench))"
              strokeWidth={1.25}
              strokeDasharray="4 3"
              dot={false}
              isAnimationActive={false}
              name={benchLabel}
            />
          )}
        </RLineChart>
      </ResponsiveContainer>
    </div>
  );
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ value?: number; dataKey?: string; payload?: { date?: string } }>;
  yFormatter: (v: number) => string;
  fundLabel: string;
  benchLabel: string;
}

function ChartTooltip({ active, payload, yFormatter, fundLabel, benchLabel }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const dateIso = payload[0].payload?.date;
  const fund = payload.find((p) => p.dataKey === "fund")?.value as number | undefined;
  const bench = payload.find((p) => p.dataKey === "bench")?.value as number | undefined;
  return (
    <div className="rounded border border-hairline-strong bg-surface px-1.5 py-1 shadow-soft">
      <div className="text-2xs text-fg-subtle">{dateIso ? formatDate(dateIso) : ""}</div>
      <div className="mt-[4px] flex flex-col gap-[2px]">
        {fund !== undefined && (
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="inline-flex items-center gap-1 text-fg">
              <span
                className="inline-block h-[2px] w-2 rounded"
                style={{ background: "rgb(var(--chart-fund))" }}
              />
              {fundLabel}
            </span>
            <span className="num text-fg">{yFormatter(fund)}</span>
          </div>
        )}
        {bench !== undefined && (
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="inline-flex items-center gap-1 text-fg-muted">
              <span
                className="inline-block h-[2px] w-2 rounded border-t border-dashed"
                style={{ borderColor: "rgb(var(--chart-bench))" }}
              />
              {benchLabel}
            </span>
            <span className="num text-fg-muted">{yFormatter(bench)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
