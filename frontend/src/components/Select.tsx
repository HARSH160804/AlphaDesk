import { forwardRef, type SelectHTMLAttributes } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/cn";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: Array<{ label: string; value: string }>;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { options, className, ...rest },
  ref,
) {
  return (
    <div className="relative inline-flex h-8">
      <select
        ref={ref}
        className={cn(
          "h-full appearance-none rounded border border-hairline bg-surface-raised pl-1.5 pr-5 text-sm text-fg",
          "focus:border-hairline-strong",
          className,
        )}
        {...rest}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-1 top-1/2 -translate-y-1/2 text-fg-subtle"
        size={14}
      />
    </div>
  );
});


interface SegmentedProps<T extends string> {
  value: T;
  onChange: (v: T) => void;
  options: Array<{ label: string; value: T }>;
  className?: string;
}

export function Segmented<T extends string>({
  value,
  onChange,
  options,
  className,
}: SegmentedProps<T>): JSX.Element {
  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex h-8 items-center rounded border border-hairline bg-surface-raised p-[2px]",
        className,
      )}
    >
      {options.map((o) => {
        const active = value === o.value;
        return (
          <button
            key={o.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "h-full rounded-sm px-1.5 text-xs font-medium transition-colors duration-quick",
              active
                ? "bg-surface text-fg shadow-soft"
                : "text-fg-muted hover:text-fg",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
