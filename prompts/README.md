# NHI Prompts for Claude Code CLI

These are **self-contained prompts** you paste into a fresh `claude` session inside this repo. Each builds one feature, has acceptance criteria, and references only file paths (not chat history).

Run them in order. After each, verify the acceptance criteria, commit, then move to the next.

| # | Prompt | What it builds |
|---|---|---|
| 00 | [bootstrap](00-bootstrap.md) | uv project, pyproject, gitignore, env, license, makefile |
| 01 | [config-and-secrets](01-config-and-secrets.md) | pydantic-settings, structlog, localhost guard |
| 02 | [alpaca-historical](02-alpaca-historical.md) | StockHistoricalDataClient wrapper |
| 03 | [alpaca-streaming](03-alpaca-streaming.md) | WS stream manager + fan-out |
| 04 | [grok-client](04-grok-client.md) | xai-sdk async wrapper |
| 05 | [tools-and-orchestrator](05-tools-and-orchestrator.md) | Tool defs + tool-call loop |
| 06 | [indicators-and-stats](06-indicators-and-stats.md) | pandas-ta indicators + perf stats |
| 07 | [fastapi-routes](07-fastapi-routes.md) | /api/v1/* including SSE chat |
| 08 | [frontend-scaffold](08-frontend-scaffold.md) | Vite + React + Tailwind + shadcn |
| 09 | [chat-panel](09-chat-panel.md) | Streaming chat UI w/ tool calls + artifacts |
| 10 | [charts](10-charts.md) | Lightweight Charts + Plotly-React |
| 11 | [live-stream](11-live-stream.md) | WebSocket hook + live ticks |
| 12 | [watchlist-snapshot](12-watchlist-snapshot.md) | Watchlist CRUD + snapshot panel |
| 13 | [reports-artifacts](13-reports-artifacts.md) | md/html/xlsx/pdf/pptx generation |
| 14 | [skills-bridge](14-skills-bridge.md) | Document skill-to-module mapping |
| 15 | [tests-ci](15-tests-ci.md) | pytest + vitest + playwright + CI |
| 16 | [docs-and-readme](16-docs-and-readme.md) | README, ARCHITECTURE, PROMPTS, SKILLS |
| 17 | [publish-to-github](17-publish-to-github.md) | Initial commit + gh repo create |

## How to use

```bash
cd /path/to/grok-alpaca
claude
# paste the contents of prompts/00-bootstrap.md
# wait, verify, commit
# paste 01, repeat
```
