import { NavLink } from "react-router-dom";
import { Activity, GitCompareArrows, LayoutDashboard, FileText, Database, Palette } from "lucide-react";
import { cn } from "@/lib/cn";

const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/funds", label: "Funds", icon: Activity },
  { to: "/compare", label: "Compare", icon: GitCompareArrows },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/data-health", label: "Data Health", icon: Database },
];

const devLinks = [{ to: "/design", label: "Design", icon: Palette }];

export function Sidebar(): JSX.Element {
  return (
    <aside
      className="hidden md:flex md:w-[220px] shrink-0 flex-col border-r border-hairline bg-surface-raised"
      aria-label="Primary navigation"
    >
      <div className="flex h-[52px] items-center gap-1 border-b border-hairline px-2">
        <div className="h-2 w-2 rounded bg-accent" aria-hidden />
        <span className="text-sm font-semibold tracking-tight">AlphaDesk</span>
        <span className="ml-auto text-2xs text-fg-subtle">v0.1</span>
      </div>
      <nav className="flex flex-col gap-[2px] p-1">
        {links.map((l) => (
          <SidebarLink key={l.to} {...l} />
        ))}
      </nav>
      <div className="mt-auto border-t border-hairline p-1">
        <div className="px-1 pb-[6px] text-2xs font-medium uppercase tracking-wide text-fg-subtle">
          Dev
        </div>
        {devLinks.map((l) => (
          <SidebarLink key={l.to} {...l} />
        ))}
      </div>
    </aside>
  );
}

function SidebarLink({
  to,
  label,
  icon: Icon,
  end,
}: {
  to: string;
  label: string;
  icon: typeof Activity;
  end?: boolean;
}): JSX.Element {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "flex h-7 items-center gap-1 rounded px-1.5 text-xs font-medium transition-colors duration-quick",
          isActive
            ? "bg-surface text-fg shadow-soft"
            : "text-fg-muted hover:bg-surface hover:text-fg",
        )
      }
    >
      <Icon size={14} className="shrink-0" />
      {label}
    </NavLink>
  );
}
