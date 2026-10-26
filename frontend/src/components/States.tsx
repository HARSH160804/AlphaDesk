import type { ReactNode } from "react";
import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/cn";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps): JSX.Element {
  return (
    <div
      className={cn(
        "animate-pulse rounded bg-surface-sunken",
        className,
      )}
      aria-hidden
    />
  );
}

export function SkeletonText({
  lines = 3,
  className,
}: {
  lines?: number;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("flex flex-col gap-[6px]", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-[14px] w-full" />
      ))}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps): JSX.Element {
  return (
    <div className="flex flex-col items-center gap-1 rounded border border-dashed border-hairline bg-surface-raised px-3 py-5 text-center">
      <div className="text-fg-subtle">{icon ?? <Inbox size={20} />}</div>
      <div className="text-sm font-medium text-fg">{title}</div>
      {description && (
        <div className="max-w-sm text-xs text-fg-muted">{description}</div>
      )}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorStateProps): JSX.Element {
  return (
    <div className="flex items-start gap-1.5 rounded border border-hairline bg-neg-bg/60 p-2">
      <AlertTriangle className="shrink-0 text-neg" size={16} />
      <div className="flex-1">
        <div className="text-sm font-medium text-fg">{title}</div>
        <div className="mt-[2px] text-xs text-fg-muted">{message}</div>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RefreshCw size={12} /> Retry
        </Button>
      )}
    </div>
  );
}
