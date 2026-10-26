import type { Config } from "tailwindcss";

/**
 * All colors come from CSS variables defined in src/styles/tokens.css,
 * so Tailwind utilities (bg-surface, text-fg-muted, border-hairline, ...)
 * recompose the design tokens without duplicating them in two places.
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", "[data-theme='dark']"],
  theme: {
    extend: {
      colors: {
        // surfaces
        surface:          "rgb(var(--surface) / <alpha-value>)",
        "surface-raised": "rgb(var(--surface-raised) / <alpha-value>)",
        "surface-sunken": "rgb(var(--surface-sunken) / <alpha-value>)",
        // foreground
        fg:               "rgb(var(--fg) / <alpha-value>)",
        "fg-muted":       "rgb(var(--fg-muted) / <alpha-value>)",
        "fg-subtle":      "rgb(var(--fg-subtle) / <alpha-value>)",
        // lines
        hairline:         "rgb(var(--hairline) / <alpha-value>)",
        "hairline-strong":"rgb(var(--hairline-strong) / <alpha-value>)",
        // accent (single, restrained — teal/slate)
        accent:           "rgb(var(--accent) / <alpha-value>)",
        "accent-fg":      "rgb(var(--accent-fg) / <alpha-value>)",
        "accent-muted":   "rgb(var(--accent-muted) / <alpha-value>)",
        // semantic returns (muted, not neon)
        pos:              "rgb(var(--pos) / <alpha-value>)",
        "pos-bg":         "rgb(var(--pos-bg) / <alpha-value>)",
        neg:              "rgb(var(--neg) / <alpha-value>)",
        "neg-bg":         "rgb(var(--neg-bg) / <alpha-value>)",
        warn:             "rgb(var(--warn) / <alpha-value>)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
      fontSize: {
        // Explicit scale: 12 / 13 / 14 / 16 / 20 / 24 / 32
        "2xs": ["12px", { lineHeight: "16px", letterSpacing: "0" }],
        xs:    ["13px", { lineHeight: "18px", letterSpacing: "0" }],
        sm:    ["14px", { lineHeight: "20px", letterSpacing: "0" }],
        base:  ["16px", { lineHeight: "24px", letterSpacing: "0" }],
        lg:    ["20px", { lineHeight: "28px", letterSpacing: "-0.01em" }],
        xl:    ["24px", { lineHeight: "32px", letterSpacing: "-0.015em" }],
        "2xl": ["32px", { lineHeight: "40px", letterSpacing: "-0.02em" }],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "10px",
      },
      spacing: {
        // 8px grid
        "0.5": "4px",
        "1":   "8px",
        "1.5": "12px",
        "2":   "16px",
        "3":   "24px",
        "4":   "32px",
        "5":   "40px",
        "6":   "48px",
        "7":   "56px",
        "8":   "64px",
      },
      maxWidth: {
        page: "1440px",
      },
      transitionDuration: {
        quick: "150ms",
        base: "200ms",
      },
      boxShadow: {
        none: "none",
        // deliberately subtle — hairline borders are the primary separator
        soft: "0 1px 2px rgba(15, 23, 42, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
