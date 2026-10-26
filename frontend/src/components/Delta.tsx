import { formatPercent, returnTone } from "@/lib/format";
import { cn } from "@/lib/cn";

interface DeltaProps {
  value: number | null | undefined;
  className?: string;
  size?: "sm" | "base";
}

/** Signed percent in tabular-nums with pos/neg colour. */
export function Delta({ value, className, size = "sm" }: DeltaProps): JSX.Element {
  const tone = returnTone(value);
  return (
    <span
      className={cn(
        "num font-medium",
        tone === "pos" && "text-pos",
        tone === "neg" && "text-neg",
        tone === "neutral" && "text-fg-muted",
        size === "base" ? "text-sm" : "text-xs",
        className,
      )}
    >
      {formatPercent(value, { signed: true })}
    </span>
  );
}
