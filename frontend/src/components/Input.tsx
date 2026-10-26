import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leading?: ReactNode;
  trailing?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { leading, trailing, className, ...rest },
  ref,
) {
  return (
    <div
      className={cn(
        "flex h-8 items-center gap-1 rounded border border-hairline bg-surface-raised px-1.5",
        "text-sm text-fg placeholder:text-fg-subtle",
        "focus-within:border-hairline-strong",
        className,
      )}
    >
      {leading && <span className="text-fg-subtle">{leading}</span>}
      <input
        ref={ref}
        className="h-full flex-1 bg-transparent outline-none placeholder:text-fg-subtle"
        {...rest}
      />
      {trailing && <span className="text-fg-subtle text-2xs">{trailing}</span>}
    </div>
  );
});
