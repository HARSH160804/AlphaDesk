import type { ReactNode } from "react";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, subtitle, actions }: PageHeaderProps): JSX.Element {
  return (
    <div className="flex items-start justify-between gap-2 pb-2">
      <div>
        {eyebrow && (
          <div className="text-2xs font-medium uppercase tracking-wide text-fg-subtle">
            {eyebrow}
          </div>
        )}
        <h1 className="text-xl font-semibold tracking-tight text-fg">{title}</h1>
        {subtitle && (
          <p className="mt-[2px] max-w-xl text-xs text-fg-muted">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-1 shrink-0">{actions}</div>}
    </div>
  );
}


interface PanelProps {
  title?: string;
  caption?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, caption, actions, children, className }: PanelProps): JSX.Element {
  return (
    <section
      className={`rounded border border-hairline bg-surface ${className ?? ""}`}
    >
      {(title || actions) && (
        <header className="flex items-center justify-between gap-1 border-b border-hairline px-2 py-1.5">
          <div>
            {title && (
              <h2 className="text-sm font-semibold tracking-tight text-fg">{title}</h2>
            )}
            {caption && <div className="text-2xs text-fg-muted">{caption}</div>}
          </div>
          {actions && <div className="flex items-center gap-1">{actions}</div>}
        </header>
      )}
      <div className="p-2">{children}</div>
    </section>
  );
}
