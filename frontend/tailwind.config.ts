import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#070b14",
          panel: "#0b1220",
          raised: "#0f1828",
          line: "#1f2a44",
        },
        ink: {
          DEFAULT: "#e6edf7",
          dim: "#8a96ad",
          accent: "#8fb6ff",
        },
        up: "#23c08a",
        down: "#ff5d5d",
      },
      fontFamily: {
        sans: ["SF Pro Text", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
