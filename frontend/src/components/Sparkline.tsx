import { useId } from "react";
import { cn } from "@/lib/cn";

interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  className?: string;
  tone?: "neutral" | "pos" | "neg";
}

/**
 * Inline SVG sparkline. No tooltip, no axis — this is a "shape at a glance"
 * component to live inside a dense table row.
 */
export function Sparkline({
  values,
  width = 72,
  height = 20,
  className,
  tone,
}: SparklineProps): JSX.Element | null {
  const id = useId();
  if (!values || values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const stepX = width / (values.length - 1);

  const inferredTone =
    tone ?? (values[values.length - 1] >= values[0] ? "pos" : "neg");

  const colorVar =
    inferredTone === "pos" ? "var(--pos)" : inferredTone === "neg" ? "var(--neg)" : "var(--fg-muted)";

  const points = values.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / span) * (height - 2) - 1;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  const d = `M${points[0]} L${points.slice(1).join(" ")}`;
  const area = `M${points[0]} L${points.slice(1).join(" ")} L${(values.length - 1) * stepX},${height} L0,${height} Z`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={cn("inline-block align-middle", className)}
      aria-hidden
    >
      <defs>
        <linearGradient id={`spark-${id}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={`rgb(${colorVar})`} stopOpacity="0.14" />
          <stop offset="100%" stopColor={`rgb(${colorVar})`} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#spark-${id})`} />
      <path d={d} fill="none" stroke={`rgb(${colorVar})`} strokeWidth="1.3" />
    </svg>
  );
}
