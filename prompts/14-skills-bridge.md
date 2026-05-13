# Prompt 14 — Skills bridge (documentation only)

## Goal
Document the relationship between Anthropic Skills (build-time guidance for Claude Code) and the runtime modules they mirror in this repo. This is not runtime code — it's a map for future contributors.

## Reference
Skills repo: https://github.com/anthropics/skills/tree/main/skills

## Tasks
1. Create `docs/SKILLS.md`. For each relevant skill:
   - **Skill name** + link
   - **Build-time use**: when a contributor (or Claude Code) should invoke it
   - **Runtime mirror**: the Python module in this repo that produces equivalent output

   Cover at minimum:
   - `web-artifacts-builder` → `backend/app/services/reports/html_artifact.py`
   - `frontend-design` → `frontend/src/components/layout/` and `globals.css`
   - `webapp-testing` → `frontend/tests/e2e/` (playwright)
   - `canvas-design` → `frontend/src/components/chart/IndicatorPanel.tsx` (Plotly visuals)
   - `xlsx` → `backend/app/services/reports/xlsx_export.py`
   - `pdf` → `backend/app/services/reports/pdf_export.py`
   - `pptx` → `backend/app/services/reports/pptx_export.py`
   - `docx` → *(not implemented; add `docx_export.py` when needed)*
   - `claude-api` → *(not implemented; we use xAI, not Claude, at runtime — but the build-time skill is useful if/when adding a Claude provider)*
   - `mcp-builder` → *(not implemented; an MCP server in front of these tools is a future extension)*
   - `brand-guidelines` → `frontend/tailwind.config.ts` palette + `frontend/src/styles/globals.css`
   - `theme-factory` → *(not implemented; useful if adding light/dark theme switcher)*

2. Add a "How to extend" section showing the pattern:
   - Identify the skill that fits the new capability
   - Invoke it (`claude` will load it on a matching natural-language prompt)
   - Add a runtime mirror module under `backend/app/services/reports/` (or wherever appropriate)
   - Register a new tool in `backend/app/services/grok/tools.py` so Grok can call it

## Acceptance
- `docs/SKILLS.md` exists, renders on GitHub, lists every skill above with the mapping.
