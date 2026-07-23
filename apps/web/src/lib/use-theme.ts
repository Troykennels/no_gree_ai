"use client";

import { useEffect, useState } from "react";

export type Theme = "light" | "dark";
const KEY = "nogree.theme";

/** Reads/writes the `.dark` class on <html> and persists the choice. Default light. */
export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    const stored = (typeof window !== "undefined"
      ? (localStorage.getItem(KEY) as Theme | null)
      : null);
    const current =
      stored ??
      (document.documentElement.classList.contains("dark") ? "dark" : "light");
    setThemeState(current);
  }, []);

  const setTheme = (t: Theme) => {
    setThemeState(t);
    try {
      localStorage.setItem(KEY, t);
    } catch {
      /* private mode - non-fatal */
    }
    document.documentElement.classList.toggle("dark", t === "dark");
  };

  const toggle = () => setTheme(theme === "dark" ? "light" : "dark");

  return { theme, setTheme, toggle };
}
