import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "pos" | "neg" | "warn" | "accent";

interface BadgeProps {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}

const tones: Record<Tone, string> = {
  neutral: "bg-surface-sunken text-fg-muted border-hairline",
  pos:     "bg-pos-bg text-pos border-pos/20",
  neg:     "bg-neg-bg text-neg border-neg/20",
  warn:    "bg-warn/10 text-warn border-warn/20",
  accent:  "bg-accent-muted text-accent border-accent/20",
};

export function Badge({ tone = "neutral", children, className }: BadgeProps): JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-[4px] rounded border px-1 text-2xs font-medium leading-5",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
