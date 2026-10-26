import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "destructive";
type Size = "sm" | "md";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const base =
  "inline-flex items-center justify-center gap-1 whitespace-nowrap rounded font-medium " +
  "transition-colors duration-quick select-none disabled:cursor-not-allowed disabled:opacity-50";

const sizes: Record<Size, string> = {
  sm: "h-7 px-1.5 text-xs",
  md: "h-8 px-2 text-sm",
};

const variants: Record<Variant, string> = {
  primary:
    "bg-accent text-accent-fg hover:brightness-[1.08] active:brightness-95 " +
    "border border-accent",
  secondary:
    "bg-surface-raised text-fg border border-hairline hover:bg-surface-sunken",
  ghost:
    "bg-transparent text-fg-muted hover:text-fg hover:bg-surface-sunken " +
    "border border-transparent",
  destructive:
    "bg-neg text-white border border-neg hover:brightness-110 active:brightness-95",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", loading, disabled, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(base, sizes[size], variants[variant], className)}
      {...rest}
    >
      {loading && (
        <span
          className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent"
          aria-hidden
        />
      )}
      {children}
    </button>
  );
});
