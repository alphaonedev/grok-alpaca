# Prompt 16 — Docs + README

## Goal
Make this project legible from the GitHub homepage.

## Tasks
1. `README.md` — top-level. Must include:
   - One-paragraph hero: what this is, who it's for.
   - Screenshot or animated GIF placeholder (path under `docs/img/`).
   - **30-second quickstart**:
     ```bash
     git clone https://github.com/<you>/grok-alpaca && cd grok-alpaca
     cp .env.example .env  # fill XAI_API_KEY, ALPACA_API_KEY, ALPACA_SECRET_KEY
     make install
     make dev
     open http://127.0.0.1:5173
     ```
   - **Features** list with checkmarks.
   - **Architecture** diagram (mermaid).
   - **Security posture**: localhost-only, read-only, no trading.
   - **NHI prompts** section pointing at `prompts/`.
   - **License** (MIT).

2. `docs/ARCHITECTURE.md` — module-by-module walkthrough, the orchestrator event loop, the chart-spec union, the report registry.

3. `docs/PROMPTS.md` — pointer to `prompts/` plus tips for writing new NHI prompts (scope, acceptance criteria, file paths, no chat-history references).

4. `docs/SKILLS.md` — from Prompt 14.

5. `docs/img/` — placeholder screenshots (can be a simple PNG of the running app once finished).

## Acceptance
- Open `README.md` on github.com — the rendering is clean, mermaid diagram renders, no broken anchors.
- A first-time reader can get the app running in under 5 minutes.
