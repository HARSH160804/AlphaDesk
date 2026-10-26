import { Moon, Search, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";
import { Button } from "./Button";
import { Input } from "./Input";

export function TopBar(): JSX.Element {
  const [theme, setTheme] = useTheme();
  return (
    <header className="sticky top-0 z-20 flex h-[52px] items-center gap-2 border-b border-hairline bg-surface px-2 backdrop-blur">
      <div className="flex-1 max-w-md">
        <Input
          leading={<Search size={14} />}
          placeholder="Search funds, categories…"
          trailing={<kbd className="rounded border border-hairline bg-surface-raised px-[6px] font-mono">⌘K</kbd>}
        />
      </div>
      <div className="ml-auto flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          aria-label="Toggle theme"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
        >
          {theme === "light" ? <Moon size={14} /> : <Sun size={14} />}
        </Button>
      </div>
    </header>
  );
}
