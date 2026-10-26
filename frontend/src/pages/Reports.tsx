import { useState } from "react";
import { Link } from "react-router-dom";
import { Download, FileText, Loader2, Presentation } from "lucide-react";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { PageHeader, Panel } from "@/components/PageHeader";
import { Segmented, Select } from "@/components/Select";
import { EmptyState, ErrorState, SkeletonText } from "@/components/States";
import { useFunds } from "@/hooks/queries";
import { CATEGORY_LABEL } from "@/types/api";

type Format = "pptx" | "docx";
type Period = "1Y" | "3Y" | "5Y" | "SI";

interface PreviewResponse {
  fund: { scheme_code: number; name: string; benchmark_id: string | null; as_of: string };
  takeaways: string[];
  outline: Array<{ n: number; title: string; body: string }>;
}

const PHASES = [
  { n: 1, title: "Title",                   body: "Fund, AMC, benchmark, window" },
  { n: 2, title: "Executive summary",       body: "Three takeaways from the data" },
  { n: 3, title: "Performance vs benchmark",body: "Rebased line chart" },
  { n: 4, title: "Trailing returns",        body: "1M–5Y + risk summary" },
  { n: 5, title: "Calendar-year returns",   body: "Fund vs benchmark bars" },
  { n: 6, title: "Risk metrics",            body: "β · α · vol · Sharpe · Sortino" },
  { n: 7, title: "Drawdown chart",          body: "Worst-episode dates annotated" },
  { n: 8, title: "Rolling 3Y CAGR",         body: "Consistency check" },
  { n: 9, title: "Peer ranking",            body: "In-category leaderboard" },
  { n: 10,title: "Methodology & disclaimer",body: "Formulas, sources, legal" },
];

export default function ReportsPage(): JSX.Element {
  const funds = useFunds({ sort: "3Y", order: "desc", limit: 100 });
  const [schemeCode, setSchemeCode] = useState<number | null>(null);
  const [format, setFormat] = useState<Format>("pptx");
  const [period, setPeriod] = useState<Period>("3Y");
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chosen = funds.data?.find((f) => f.scheme_code === schemeCode);

  const loadPreview = async (code: number) => {
    setPreviewing(true);
    setError(null);
    try {
      const r = await fetch(`/api/reports/preview?codes=${code}&period=${period}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setPreview(await r.json());
    } catch (e) {
      setError((e as Error).message);
      setPreview(null);
    } finally {
      setPreviewing(false);
    }
  };

  const onPickFund = (v: string) => {
    const code = v ? parseInt(v, 10) : null;
    setSchemeCode(code);
    setPreview(null);
    if (code !== null) loadPreview(code);
  };

  const generate = async () => {
    if (schemeCode === null) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codes: [schemeCode], format, period }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(detail.detail ?? res.statusText);
      }
      const blob = await res.blob();
      const filename =
        res.headers.get("X-Report-Filename") ??
        parseContentDisposition(res.headers.get("Content-Disposition")) ??
        `AlphaDesk-report.${format}`;
      downloadBlob(blob, filename);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  };

  const options = [
    { label: "Pick a fund…", value: "" },
    ...(funds.data ?? []).map((f) => ({
      label: `${f.name.split(" - ")[0]} · ${CATEGORY_LABEL[f.category]}`,
      value: String(f.scheme_code),
    })),
  ];

  return (
    <div className="flex flex-col gap-3">
      <PageHeader
        eyebrow="Reports"
        title="Client-ready report generator"
        subtitle="Pick a fund, choose format and window, review the outline, then generate. Each report is produced live from the metrics module — no cached templates."
      />

      <Panel title="Configuration">
        <div className="grid gap-2 md:grid-cols-[1fr_auto_auto_auto]">
          <div className="flex flex-col gap-[4px]">
            <span className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">Fund</span>
            <Select
              value={schemeCode === null ? "" : String(schemeCode)}
              onChange={(e) => onPickFund(e.target.value)}
              options={options}
            />
          </div>
          <div className="flex flex-col gap-[4px]">
            <span className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">Window</span>
            <Segmented<Period>
              value={period}
              onChange={(p) => {
                setPeriod(p);
                if (schemeCode !== null) loadPreview(schemeCode);
              }}
              options={[
                { label: "1Y", value: "1Y" },
                { label: "3Y", value: "3Y" },
                { label: "5Y", value: "5Y" },
                { label: "SI", value: "SI" },
              ]}
            />
          </div>
          <div className="flex flex-col gap-[4px]">
            <span className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">Format</span>
            <Segmented<Format>
              value={format}
              onChange={setFormat}
              options={[
                { label: "PPTX", value: "pptx" },
                { label: "DOCX", value: "docx" },
              ]}
            />
          </div>
          <div className="flex items-end">
            <Button onClick={generate} loading={generating} disabled={schemeCode === null}>
              {format === "pptx" ? <Presentation size={14} /> : <FileText size={14} />}
              Generate
            </Button>
          </div>
        </div>
      </Panel>

      {error && <ErrorState message={error} />}

      {schemeCode === null && (
        <EmptyState
          title="Pick a fund to begin"
          description="You'll see the outline and the three takeaways before you generate the file."
          icon={<FileText size={18} />}
        />
      )}

      {schemeCode !== null && (
        <div className="grid gap-2 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <Panel title="Outline" caption="Ten sections, same structure for PPTX and DOCX">
              <ol className="flex flex-col divide-y divide-hairline">
                {PHASES.map((p) => (
                  <li key={p.n} className="flex items-center gap-2 py-1.5">
                    <span className="num w-5 text-right text-xs text-fg-subtle">{p.n}</span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-fg">{p.title}</div>
                      <div className="text-2xs text-fg-muted">{p.body}</div>
                    </div>
                  </li>
                ))}
              </ol>
            </Panel>
          </div>

          <div className="flex flex-col gap-2">
            <Panel title="Subject">
              {!chosen && !preview ? (
                <SkeletonText lines={3} />
              ) : (
                <div className="flex flex-col gap-1">
                  <div className="text-sm font-medium text-fg">
                    {(chosen?.name ?? preview?.fund.name)?.split(" - ")[0]}
                  </div>
                  <div className="text-2xs text-fg-subtle">
                    #{chosen?.scheme_code ?? preview?.fund.scheme_code} ·{" "}
                    {chosen ? CATEGORY_LABEL[chosen.category] : "—"}
                  </div>
                  {chosen?.benchmark_id && (
                    <Badge tone="accent">vs {chosen.benchmark_id}</Badge>
                  )}
                  {chosen && (
                    <Link to={`/funds/${chosen.scheme_code}`} className="mt-1 text-xs text-accent hover:underline">
                      Open fund →
                    </Link>
                  )}
                </div>
              )}
            </Panel>

            <Panel title="Takeaways" caption="Generated live from the data">
              {previewing && <SkeletonText lines={3} />}
              {!previewing && preview && (
                <ul className="flex flex-col gap-1">
                  {preview.takeaways.map((t, i) => (
                    <li key={i} className="flex gap-1 text-xs text-fg">
                      <span className="num text-fg-subtle">{i + 1}.</span>
                      <span>{t}</span>
                    </li>
                  ))}
                  {preview.takeaways.length === 0 && (
                    <li className="text-xs text-fg-muted">No takeaways surface for this window.</li>
                  )}
                </ul>
              )}
            </Panel>

            {!generating && (
              <div className="rounded border border-hairline bg-surface-raised p-2 text-2xs text-fg-muted">
                The generator produces real .{format} files (~400 KB) with four embedded chart images, matched to the AlphaDesk palette. The viewer's local Office font substitution applies.
              </div>
            )}
          </div>
        </div>
      )}

      {generating && (
        <div className="flex items-center gap-1 text-xs text-fg-muted">
          <Loader2 size={14} className="animate-spin" />
          Rendering charts, assembling .{format}…
        </div>
      )}

      {!generating && !error && schemeCode !== null && (
        <div className="text-2xs text-fg-subtle">
          Click Generate — the file is streamed back directly to your browser as a download. <Download size={10} className="inline" />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function parseContentDisposition(h: string | null): string | null {
  if (!h) return null;
  const m = h.match(/filename="([^"]+)"/);
  return m ? m[1] : null;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
