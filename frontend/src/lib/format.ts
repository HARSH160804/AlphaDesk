/**
 * Number formatting helpers. Indian conventions where applicable;
 * consistent sign display (+1.24% / −0.87%, using the proper Unicode minus).
 */

const MINUS = "−"; // U+2212 — the real minus sign, not hyphen-minus
const EN_DASH = "–";

export function formatPercent(
  value: number | null | undefined,
  opts: { decimals?: number; signed?: boolean } = {},
): string {
  const decimals = opts.decimals ?? 2;
  if (value === null || value === undefined || Number.isNaN(value)) {
    return EN_DASH;
  }
  const pct = value * 100;
  const abs = Math.abs(pct).toFixed(decimals);
  if (!opts.signed) {
    return `${pct < 0 ? MINUS : ""}${abs}%`;
  }
  if (pct > 0) return `+${abs}%`;
  if (pct < 0) return `${MINUS}${abs}%`;
  return `0.00%`;
}

export function formatNumber(
  value: number | null | undefined,
  opts: { decimals?: number } = {},
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EN_DASH;
  const d = opts.decimals ?? 2;
  return value.toLocaleString("en-IN", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

/** Lakh/crore grouping; useful when we start showing INR AUM later. */
export function formatInrShort(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EN_DASH;
  const abs = Math.abs(value);
  if (abs >= 1e7) return `${(value / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${(value / 1e5).toFixed(2)} L`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(2)} K`;
  return value.toFixed(2);
}

export function formatDate(value: string | Date): string {
  const d = typeof value === "string" ? new Date(value) : value;
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function returnTone(value: number | null | undefined): "pos" | "neg" | "neutral" {
  if (value === null || value === undefined || Number.isNaN(value)) return "neutral";
  if (value > 0) return "pos";
  if (value < 0) return "neg";
  return "neutral";
}
