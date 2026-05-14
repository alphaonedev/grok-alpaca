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

`npm audit` shows only well-known **moderate** Vite/esbuild dev-server path-traversal advisories (`GHSA-67mh-4wv8-2f99`, `GHSA-4w7w-66w2-5vf9`) that affect the dev server only and have no production impact. No high or critical. No supply-chain advisories.

## Hardening enforced in this repo

The TanStack attack succeeded because it executed code through the **trusted official build pipeline** and shipped with valid OIDC signatures. Lockfile pinning and audit-signatures alone would not have stopped it on May 11. The defenses below assume a future compromise of a transitive dependency is **likely** and aim to make it survivable.

### 1. Block all install-time code execution

The most consequential change. The May-2026 TanStack and March-2026 Axios attacks both ran code via lifecycle scripts (`preinstall`, `install`, `postinstall`, `prepare`). We block all of them at the registry layer:

- [`frontend/.npmrc`](frontend/.npmrc) sets `ignore-scripts = true`.
- [`@lavamoat/allow-scripts`](https://github.com/LavaMoat/LavaMoat/tree/main/packages/allow-scripts) (MetaMask's tool) is the only way scripts can run, and only for packages in the [`lavamoat.allowScripts`](frontend/package.json) allowlist.
- A compromised dependency cannot execute code on `npm ci`. Adding a new dep with install scripts requires a manual allowlist entry — a deliberate, reviewable act.
- [`@lavamoat/preinstall-always-fail`](https://github.com/LavaMoat/LavaMoat/tree/main/packages/preinstall-always-fail) is installed as a **tripwire**: if `ignore-scripts` is ever accidentally disabled, its preinstall fires and the install fails loudly.

### 2. Lockfile is the only source of truth

- [`frontend/package-lock.json`](frontend/package-lock.json) is committed. Every entry has an SRI integrity hash.
- All direct deps in [`frontend/package.json`](frontend/package.json) are **exact-pinned** (no `^` or `~`). The `save-exact = true` config preserves this on future installs.
- CI and `make install` use `npm ci` — refuses to install if the lockfile doesn't match `package.json`, refuses to mutate the lockfile.
- The registry is pinned via `.npmrc`: `registry = https://registry.npmjs.org/`. A hijacked global npm config cannot silently redirect installs.

### 3. Pin the toolchain too

- `package.json` declares `packageManager: "npm@11.11.1"` and `engines` for Node + npm.
- CI runs the Node 20 + 22 LTS matrix; engine mismatches surface in PR checks.

### 4. Audit on every install

- `audit = true` and `audit-level = high` in `.npmrc`.
- CI runs `npm audit --audit-level=high` (build-failing) and `npm audit signatures` (informational; doesn't block because the TanStack attack shipped *valid* signatures and we don't want a false sense of security from it).

### 5. Restrict CI runner egress

- Every job uses `step-security/harden-runner@v2` with `egress-policy: audit`. The first audit run will surface every external host the build talks to; we can promote to `egress-policy: block` once the allowlist is known and stable.
- Default `permissions: {}` on the workflow; each job opts in to the minimum scope (`contents: read`).
- `actions/checkout` uses `persist-credentials: false` so the `GITHUB_TOKEN` is not sitting in `.git/config` on the runner.

### 6. Automated security updates

- [`.github/dependabot.yml`](.github/dependabot.yml) runs daily for `npm`, `pip`, and weekly for GitHub Actions. PRs are grouped by patch/minor to limit noise during supply-chain crises.

### 7. CDN integrity for generated artifacts

- Grok-generated HTML reports load Plotly from `cdn.plot.ly` with a pinned [Subresource Integrity (SRI) hash](backend/app/services/reports/html_artifact.py) (`sha384-…`). If the CDN is ever compromised, the browser refuses to execute the script.
- Reports render in `<iframe sandbox="allow-scripts">` — no `allow-same-origin`, no cookies, no parent-frame access.

### 8. Read-only domain by design

- No `alpaca.trading` import or `TradingClient` reference anywhere in the codebase. `make lint` and CI both `grep`-fail the build if either string ever appears.

### 9. Localhost-only bind

- [`backend/app/core/localhost_guard.py`](backend/app/core/localhost_guard.py) raises at startup if `HOST` resolves to anything other than a loopback address.
- CORS allows only `http://127.0.0.1:5173` and `http://localhost:5173`.

### 10. Secrets handling

- `.env` is `.gitignore`d. Only `.env.example` is committed.
- API keys are loaded via `SecretStr` in [`backend/app/core/config.py`](backend/app/core/config.py); never echoed in logs.

## How to re-audit after pulling

```bash
cd frontend
npm ci                                # respects lockfile + ignore-scripts
npx allow-scripts                     # runs ONLY allowlisted lifecycle scripts
npm audit --audit-level=high          # exits non-zero on high+
npm audit signatures                  # verifies provenance attestations
```

Or in one command from the repo root:

```bash
make audit
```

## What does NOT save you

For honesty, the following defenses are **not sufficient on their own** against an attack like Mini Shai-Hulud:

- **`npm audit signatures` alone.** The TanStack attack shipped through OIDC trusted publishing with valid SLSA provenance. Signatures only catch the lower-grade attacks.
- **A floating version range that "should" pull a clean version.** The TanStack publish window was 6 minutes wide; any install in that window pulled poison.
- **Trusting the @scope namespace.** The whole point of namespace compromise is that the namespace is legitimate.
- **Vendor pinning to "old, stable" versions.** A compromised maintainer can backport.

The defense-in-depth approach above assumes any single layer can fail and aims to make a compromise survivable.

## Reporting a vulnerability

Open a private security advisory at https://github.com/alphaonedev/grok-alpaca/security/advisories/new. Do not open a public issue for vulnerabilities.

## Operational guidance for users

This is a research tool you run on your own laptop. The threat model:

- Localhost network only. Do not expose ports 8000 or 5173 to the internet.
- Use Alpaca paper-trading keys, not live keys. The framework is read-only but defense in depth costs nothing.
- Rotate keys if you suspect any package on your machine has been compromised by a supply-chain attack between installs. Watchpoints: AWS, GCP, Kubernetes, GitHub PAT, Vault, SSH keys, `.npmrc` auth tokens.
- Run `make audit` before each `make dev` if you're at all concerned about a recent install.
