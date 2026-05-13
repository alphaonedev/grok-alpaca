# Prompt 17 — Publish to GitHub

## Goal
Initial commit, public repo, push, topics set, README rendering.

## Tasks
1. Verify `.gitignore` excludes `.env`, `.venv`, `node_modules`, `dist`, `~/.grok-alpaca`.
2. `git init -b main`
3. `git add .` then `git status` — sanity check: no secrets, no node_modules, no .venv.
4. `git commit -m "feat: initial public release of grok-alpaca"`
5. `gh repo create grok-alpaca --public --source=. --remote=origin --push --description "Localhost financial analysis: xAI Grok + Alpaca real-time market data, React web UI."`
6. `gh repo edit --add-topic grok --add-topic xai --add-topic alpaca --add-topic financial-analysis --add-topic fastapi --add-topic react --add-topic ai-agents --add-topic algorithmic-trading --add-topic localhost`
7. Open `gh repo view --web` and verify README, mermaid diagram, badges.

## Acceptance
- `https://github.com/<user>/grok-alpaca` is public.
- README renders.
- CI badge (after first run) is green.
- Topics applied.
