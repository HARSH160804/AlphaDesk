import type { ReactNode } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/cn";

export interface Column<T> {
  key: string;
  label: ReactNode;
  render: (row: T) => ReactNode;
  numeric?: boolean;
  sortable?: boolean;
  className?: string;
  width?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  sortKey?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (key: string) => void;
  stickyHeader?: boolean;
  className?: string;
}

export function Table<T>({
  columns,
  rows,
  rowKey,
  sortKey,
  sortOrder,
  onSort,
  stickyHeader = true,
  className,
}: TableProps<T>): JSX.Element {
  return (
    <div
      className={cn(
        "overflow-auto rounded border border-hairline bg-surface",
        className,
      )}
    >
      <table className="w-full border-collapse text-sm">
        <thead
          className={cn(
            "bg-surface-sunken text-2xs font-medium uppercase tracking-wide text-fg-subtle",
            stickyHeader && "sticky top-0 z-10",
          )}
        >
          <tr>
            {columns.map((col) => {
              const isSorted = sortKey === col.key;
              const sortable = col.sortable && !!onSort;
              return (
                <th
                  key={col.key}
                  scope="col"
                  style={{ width: col.width }}
                  className={cn(
                    "border-b border-hairline px-1.5 py-[10px]",
                    col.numeric ? "num text-right" : "text-left",
                    sortable && "cursor-pointer select-none hover:text-fg",
                    col.className,
                  )}
                  onClick={sortable ? () => onSort!(col.key) : undefined}
                >
                  <span className={cn("inline-flex items-center gap-[4px]", col.numeric && "justify-end w-full")}>
                    {col.label}
                    {sortable && (
                      <SortIcon active={isSorted} order={sortOrder} />
                    )}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              className="group transition-colors duration-quick hover:bg-surface-raised"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "border-b border-hairline px-1.5 py-1.5 text-sm",
                    col.numeric ? "num" : "text-fg",
                    col.className,
                  )}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SortIcon({
  active,
  order,
}: {
  active?: boolean;
  order?: "asc" | "desc";
}): JSX.Element {
  if (!active) return <ArrowUpDown size={11} className="text-fg-subtle" aria-hidden />;
  return order === "asc" ? (
    <ArrowUp size={11} className="text-fg" aria-hidden />
  ) : (
    <ArrowDown size={11} className="text-fg" aria-hidden />
  );
}
