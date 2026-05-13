# Skills

This project pairs **Anthropic Skills** (build-time guidance for Claude Code) with **runtime Python modules** that produce equivalent output for the live web app. Skills don't run inside `grok-alpaca`; they guide development.

Skills repo: https://github.com/anthropics/skills/tree/main/skills

## Mapping

| Anthropic Skill | Build-time use | Runtime mirror in this repo |
|---|---|---|
| [`web-artifacts-builder`](https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder) | Building HTML artifacts/reports | [`backend/app/services/reports/html_artifact.py`](../backend/app/services/reports/html_artifact.py) |
| [`frontend-design`](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Dashboard layout & visual decisions | [`frontend/src/components/layout/`](../frontend/src/components/layout/) + [`frontend/src/styles/globals.css`](../frontend/src/styles/globals.css) |
| [`webapp-testing`](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | End-to-end browser-driven tests | `frontend/tests/e2e/` (Playwright — see [prompts/15-tests-ci.md](../prompts/15-tests-ci.md)) |
| [`canvas-design`](https://github.com/anthropics/skills/tree/main/skills/canvas-design) | Custom chart/visual rendering | [`frontend/src/components/chart/CandleChart.tsx`](../frontend/src/components/chart/CandleChart.tsx) + Plotly-based indicator panels |
| [`xlsx`](https://github.com/anthropics/skills/tree/main/skills/xlsx) | Designing XLSX exports | [`backend/app/services/reports/xlsx_export.py`](../backend/app/services/reports/xlsx_export.py) |
| [`pdf`](https://github.com/anthropics/skills/tree/main/skills/pdf) | Designing PDF reports | [`backend/app/services/reports/pdf_export.py`](../backend/app/services/reports/pdf_export.py) |
| [`pptx`](https://github.com/anthropics/skills/tree/main/skills/pptx) | Designing slide decks | [`backend/app/services/reports/pptx_export.py`](../backend/app/services/reports/pptx_export.py) |
| [`docx`](https://github.com/anthropics/skills/tree/main/skills/docx) | (not implemented) Word memo exports | _Add `services/reports/docx_export.py` when needed._ |
| [`claude-api`](https://github.com/anthropics/skills/tree/main/skills/claude-api) | Adding a Claude provider (alt to Grok) | _Add `services/claude/client.py` alongside `services/grok/client.py`._ |
| [`mcp-builder`](https://github.com/anthropics/skills/tree/main/skills/mcp-builder) | Exposing tools over MCP | _Optional: wrap `services/grok/tools.py` as an MCP server._ |
| [`brand-guidelines`](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) | Palette / typography decisions | [`frontend/tailwind.config.ts`](../frontend/tailwind.config.ts) |
| [`theme-factory`](https://github.com/anthropics/skills/tree/main/skills/theme-factory) | (not implemented) Light/dark theme | _Dark-only today; add when a switcher is desired._ |
| [`algorithmic-art`](https://github.com/anthropics/skills/tree/main/skills/algorithmic-art) | (not implemented) Aesthetic visuals | _Not applicable._ |
| [`internal-comms`](https://github.com/anthropics/skills/tree/main/skills/internal-comms) | Writing release notes / announcements | _Use when drafting release notes._ |
| [`doc-coauthoring`](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) | Updating long docs collaboratively | _Use when iterating on ARCHITECTURE.md._ |
| [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | Building new skills | _Use when promoting a recurring pattern in this repo into a reusable skill._ |

## How to extend

1. Identify the skill that fits the new capability.
2. Invoke it in Claude Code (a natural-language prompt that mentions the use case will load the skill).
3. Add a runtime Python module under `backend/app/services/reports/` (or wherever appropriate).
4. Register a new tool in [`backend/app/services/grok/tools.py`](../backend/app/services/grok/tools.py) so Grok can call it.
5. Update this file to record the mapping.

## Why mirror at runtime?

Skills are designed for **Claude** following human instructions inside Claude Code. The runtime model in `grok-alpaca` is **Grok**, called via the xAI API. Grok can't invoke Anthropic skills, but it can call Python functions. So:

- During **development**: Claude Code uses skills to *write the code*.
- At **runtime**: Grok calls the resulting Python modules as tools.

The two paths converge on the same underlying libraries (openpyxl, weasyprint, python-pptx, etc.), giving consistent output whether a report is generated during a Claude Code session or by a user interacting with the running web app.
