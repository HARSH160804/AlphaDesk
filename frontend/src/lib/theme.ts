import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "alphadesk-theme";

export function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const t = window.localStorage.getItem(STORAGE_KEY);
  return t === "dark" ? "dark" : "light";
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
}

export function useTheme(): [Theme, (t: Theme) => void] {
  const [theme, setTheme] = useState<Theme>(getStoredTheme);

  useEffect(() => {
    applyTheme(theme);
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* storage unavailable (private mode) — just ignore */
    }
  }, [theme]);

  return [theme, setTheme];
}
