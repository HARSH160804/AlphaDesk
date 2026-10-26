import { AlertTriangle, CheckCircle2, PlayCircle } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader, Panel } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { StatCard } from "@/components/StatCard";
import { ErrorState, SkeletonText } from "@/components/States";
import { useIngestStatus, useStats } from "@/hooks/queries";
import { api } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";

export default function DataHealthPage(): JSX.Element {
  const stats = useStats();
  const status = useIngestStatus();
  const client = useQueryClient();

  const trigger = useMutation({
    mutationFn: api.triggerIngest,
    onSuccess: () => {
      // Refetch status quickly and let the auto-poll take over.
      setTimeout(() => client.invalidateQueries(), 500);
    },
  });

  const latest = status.data;
  const running = latest?.status === "running";

  return (
    <div className="flex flex-col gap-3">
      <PageHeader
        eyebrow="Pipeline"
        title="Data Health"
        subtitle="Analysts trust what they can audit. Every ingest leaves a row here with its warnings, errors, and row counts."
        actions={
          <Button
            onClick={() => trigger.mutate()}
            loading={trigger.isPending || running}
            disabled={running}
          >
            <PlayCircle size={14} /> Refresh now
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-1.5 md:grid-cols-4">
        <StatCard
          label="Funds in universe"
          value={formatNumber(stats.data?.funds ?? 0, { decimals: 0 })}
        />
        <StatCard
          label="NAV rows total"
          value={formatNumber(stats.data?.nav_rows ?? 0, { decimals: 0 })}
        />
        <StatCard
          label="Last status"
          value={
            !latest ? "—" : (
              <span className="inline-flex items-center gap-1 text-base">
                {latest.status === "success" && <CheckCircle2 className="text-pos" size={16} />}
                {latest.status === "failed" && <AlertTriangle className="text-neg" size={16} />}
                {latest.status === "running" && (
                  <span className="h-3 w-3 animate-spin rounded-full border border-fg-muted border-t-transparent" aria-hidden />
                )}
                <span className="capitalize">{latest.status}</span>
              </span>
            )
          }
          secondary={latest?.finished_at ? `Finished ${formatDate(latest.finished_at)}` : latest ? "In progress" : undefined}
        />
        <StatCard
          label="Rows upserted"
          value={formatNumber(latest?.rows_inserted ?? 0, { decimals: 0 })}
          secondary={latest ? `Run #${latest.id}` : undefined}
        />
      </div>

      <Panel title="Latest ingestion run" caption="Audit record from the backend's ingestion_runs table">
        {status.isLoading && <SkeletonText lines={6} />}
        {status.error && <ErrorState message={(status.error as Error).message} onRetry={() => status.refetch()} />}
        {status.data && (
          <dl className="grid gap-2 md:grid-cols-2">
            <Row label="Run ID"       value={`#${status.data.id}`} />
            <Row label="Status"       value={<Badge tone={status.data.status === "success" ? "pos" : status.data.status === "failed" ? "neg" : "warn"}>{status.data.status}</Badge>} />
            <Row label="Started"      value={formatDate(status.data.started_at)} />
            <Row label="Finished"     value={status.data.finished_at ? formatDate(status.data.finished_at) : <Badge tone="warn">Running</Badge>} />
            <Row label="Funds processed"      value={<span className="num">{status.data.funds_processed}</span>} />
            <Row label="Benchmarks processed" value={<span className="num">{status.data.benchmarks_processed}</span>} />
            <Row label="Rows upserted" value={<span className="num">{formatNumber(status.data.rows_inserted, { decimals: 0 })}</span>} />
          </dl>
        )}
      </Panel>

      {status.data?.warnings && status.data.warnings.length > 0 && (
        <Panel title={`Warnings (${status.data.warnings.length})`} caption="Not errors — things the validator caught and logged for review">
          <ul className="flex flex-col divide-y divide-hairline">
            {status.data.warnings.map((w, i) => (
              <li key={i} className="flex gap-1 py-1 text-xs text-fg">
                <AlertTriangle size={12} className="shrink-0 text-warn" />
                <span className="break-all">{w}</span>
              </li>
            ))}
          </ul>
        </Panel>
      )}

      {status.data?.errors && status.data.errors.length > 0 && (
        <Panel title={`Errors (${status.data.errors.length})`}>
          <ul className="flex flex-col divide-y divide-hairline">
            {status.data.errors.map((e, i) => (
              <li key={i} className="flex gap-1 py-1 text-xs text-neg">
                <AlertTriangle size={12} className="shrink-0" />
                <span className="break-all">{e}</span>
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }): JSX.Element {
  return (
    <div className="flex items-center justify-between border-b border-hairline py-1 text-sm last:border-b-0">
      <dt className="text-xs text-fg-muted">{label}</dt>
      <dd className="text-fg">{value}</dd>
    </div>
  );
}
