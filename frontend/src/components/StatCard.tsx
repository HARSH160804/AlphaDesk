import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Delta } from "./Delta";

interface StatCardProps {
  label: string;
  value: ReactNode;
  delta?: number | null;
  secondary?: ReactNode;
  hint?: ReactNode;
  className?: string;
}

export function StatCard({
  label,
  value,
  delta,
  secondary,
  hint,
  className,
}: StatCardProps): JSX.Element {
  return (
    <div
      className={cn(
        "flex flex-col gap-[6px] rounded border border-hairline bg-surface-raised p-2",
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">
          {label}
        </span>
        {hint && <span className="text-2xs text-fg-subtle">{hint}</span>}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="num text-xl font-semibold text-fg">{value}</span>
        {delta !== undefined && <Delta value={delta} />}
      </div>
      {secondary && <div className="text-xs text-fg-muted">{secondary}</div>}
    </div>
  );
}
