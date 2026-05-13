# Prompt 08 — Frontend scaffold (Vite + React + TS + Tailwind + shadcn/ui)

## Goal
Stand up a polished, dark-themed, finance-terminal-style React SPA scaffold. **Invoke the `frontend-design` skill** for design decisions.

## Tasks
1. `cd frontend && npm create vite@latest . -- --template react-ts` (overwrite when prompted).
2. Install:
   - Runtime: `@tanstack/react-query` `zustand` `react-markdown` `remark-gfm` `rehype-highlight` `rehype-katex` `remark-math` `lightweight-charts` `react-plotly.js` `plotly.js-dist-min` `clsx` `tailwind-merge` `lucide-react` `dayjs` `zod`
   - Dev: `tailwindcss` `postcss` `autoprefixer` `@types/plotly.js` `prettier` `eslint` `@typescript-eslint/parser` `@typescript-eslint/eslint-plugin` `vitest` `@testing-library/react` `@playwright/test` `openapi-typescript`
3. Initialize Tailwind: `npx tailwindcss init -p`. Configure `darkMode: ["class"]`, `content: ["./index.html","./src/**/*.{ts,tsx}"]`.
4. Initialize shadcn/ui: `npx shadcn@latest init` (defaults: TypeScript, Tailwind, slate theme). Add components: `button card input scroll-area separator badge tabs sheet dialog tooltip toast`.
5. `vite.config.ts` — proxy `/api` and `/ws` to `http://127.0.0.1:8000`. Bind dev server to `127.0.0.1`.
6. `src/api/types.ts` — generated from FastAPI's OpenAPI (`npx openapi-typescript http://127.0.0.1:8000/api/openapi.json -o src/api/types.ts`).
7. `src/api/client.ts` — minimal `fetch` wrapper with JSON helpers and SSE helper (`streamSSE(url, body, onEvent)`).
8. `src/components/layout/AppShell.tsx` — three-pane layout: left rail (watchlist), center (tabs: Chart / Analysis / Reports), right rail (Chat). Top bar with logo, market clock (live), connection status.
9. `src/App.tsx` mounts `<QueryClientProvider>` + `<AppShell>`.
10. `src/styles/globals.css` — Tailwind base + a "finance terminal" dark palette (deep navy, soft cyan accents, red/green for ticks).
11. `package.json` scripts: `dev`, `build`, `preview`, `lint`, `format`, `test`, `e2e`, `gen-types`.
12. `playwright.config.ts` — uses `webServer` to start vite, baseURL `http://127.0.0.1:5173`.

## Constraints
- Dark mode enforced. No light-mode toggle yet.
- No build errors; no console warnings.
- Vite proxy keeps everything same-origin from the browser.

## Acceptance
- `npm run dev` starts on `http://127.0.0.1:5173` and renders the empty shell.
- `npm run lint` passes.
- Generated OpenAPI types compile.
