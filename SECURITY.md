# Security

## Supply-chain posture

This project's dependencies have been audited against the npm supply-chain incidents of late-2025 / early-2026:

| Incident | Date | Our exposure | Reference |
|---|---|---|---|
| TanStack "Mini Shai-Hulud" — @tanstack router-family compromise | 2026-05-11 | **None.** We depend on `@tanstack/react-query` and `@tanstack/query-core`; both are confirmed-clean families. The 42 affected packages are router/start/history/*-adapter families that we do not use. | [GHSA-g7cv-rxg3-hmpx](https://github.com/advisories/GHSA-g7cv-rxg3-hmpx) · [postmortem](https://tanstack.com/blog/npm-supply-chain-compromise-postmortem) |
| Axios Sapphire-Sleet RAT (versions `1.14.1`, `0.30.4`) | 2026-03-30 | **None.** `axios` is not in our dependency tree, direct or transitive. | [Trend Micro](https://www.trendmicro.com/en_us/research/26/c/axios-npm-package-compromised.html) · [Snyk](https://snyk.io/blog/axios-npm-package-compromised-supply-chain-attack-delivers-cross-platform/) |
| Shai-Hulud 2.0 worm | 2025-11 | **None.** Affected packages not in tree. | |
| chalk / debug 2FA-bypass phish | 2025-09 | **None.** We resolve `chalk@4.1.2` (pre-attack release line, transitive via eslint) and `debug@4.4.3`. | |
| Build-pipeline compromises (CanisterWorm, LiteLLM) | 2026-03 | **None.** Affected packages not in tree. | |

`npm audit` was last run on the lockfile and shows only well-known moderate Vite/esbuild path-traversal advisories (`GHSA-67mh-4wv8-2f99`, `GHSA-4w7w-66w2-5vf9`) that affect the dev server only and have no production impact.

## Hardening enforced in this repo

### Reproducible installs
- [`frontend/package-lock.json`](frontend/package-lock.json) is committed.
- [`frontend/.npmrc`](frontend/.npmrc) sets `package-lock=true`, `save-exact=true`, `audit-level=high`.
- CI and `make install` use `npm ci` (lockfile-only, no fresh resolution), not `npm install`.

### Lifecycle-script discipline
- The May-2026 TanStack attack ran via build-time code execution in the official pipeline. Two defensive layers:
  1. `.npmrc` declares an explicit `allow-scripts` allowlist (today: `esbuild`, `fsevents`, `es5-ext`). New packages with install scripts must be reviewed and added explicitly.
  2. CI runs `npm audit signatures` before any test step to fail on provenance mismatches.

### Read-only by design (backend)
- No `alpaca.trading` import or `TradingClient` reference. The `make lint` target in [Makefile](Makefile) and [`.github/workflows/ci.yml`](.github/workflows/ci.yml) fail on either string in the codebase.

### Localhost-only bind
- [`backend/app/core/localhost_guard.py`](backend/app/core/localhost_guard.py) raises at startup if `HOST` resolves to anything other than a loopback address.
- CORS allows only `http://127.0.0.1:5173` and `http://localhost:5173`.

### Sandboxed artifacts
- Grok-generated HTML reports render in iframes with `sandbox="allow-scripts"` only — no `allow-same-origin`, no cookies, no parent-frame access.

### Secrets handling
- `.env` is `.gitignore`-d. Only `.env.example` is committed.
- API keys are loaded via `SecretStr` in [`backend/app/core/config.py`](backend/app/core/config.py); never echoed in logs.

## How to re-audit after pulling

```bash
cd frontend
npm ci                              # respects lockfile + allow-scripts
npm audit --audit-level=high        # exits non-zero on high+
npm audit signatures                # verifies provenance
```

## Reporting a vulnerability

Open a private security advisory at https://github.com/alphaonedev/grok-alpaca/security/advisories/new. Do not open a public issue for vulnerabilities.

## Operational guidance for users

This is a research tool you run on your own laptop. The threat model is:
- Localhost network only. Do not expose ports 8000 or 5173 to the internet.
- Use Alpaca paper-trading keys, not live keys. The framework is read-only but defense in depth costs nothing.
- Rotate keys if you suspect any package on your machine has been compromised by a supply-chain attack between installs.
