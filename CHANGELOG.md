# Changelog

Every change to this repo ships as a numbered release, so each node can report exactly what it runs
(`Tools/lifeos_release.py status`) and drift is visible. The `githooks/pre-commit` gate enforces it:
a commit that changes any file must bump `VERSION`, add an entry here, and carry a fresh `MANIFEST.sha256`.

**Versioning (semver):**
- **MAJOR:** a change a node must act on manually (new private file, settings layout, removed component).
- **MINOR:** a new component, tool, or workflow behavior.
- **PATCH:** fixes and wording.

**Tags:** `vX.Y.Z` on the release commit. **Node stamp:** `~/.claude/LifeOS/LOCAL_RELEASE.json`, written by
`lifeos_release.py install <component>`.

## [1.1.0] — 2026-10-14
### Added
- **Architecture Decision Records** in `docs/adr/` (tradekit format), with an index:
  - 0001: record architecture decisions
  - 0002: secrets stay in `.env`; no vault yet (options priced)
  - 0003: tools load keys from `.env` (notes the open divergence from upstream's no-shared-helper rule)
  - 0004: containment adoption
  - 0005: versioned releases and node stamps
  - 0006: setup changes are fork-only

### Changed
- `lifeos_release.py status`: `docs/` is REPO-ONLY.
- `lifeos_release.py manifest`: also covers new, not-yet-staged files (outside `.gitignore`). Before this, running `manifest` before `git add` left new files out, and the pre-commit gate rejected the commit.

## [1.0.1] — 2026-10-14
### Fixed
- `lifeos_release.py status`: a file is REDACTED only when it differs from the node copy **and** carries a placeholder. Files that merely mention `<LIVE_ACCOUNT>` (the policy doc, the checker, this tool) now report MATCH.
- `lifeos_release.py status`: `githooks/` is REPO-ONLY, and `systemd/user/*` is compared against `~/.config/systemd/user/` instead of being reported MISSING under `~/.claude`.

## [1.0.0] — 2026-10-14
First versioned release. Everything before this commit is the unversioned history below.

### Added
- **Containment** (component `containment`): a port of upstream LifeOS containment to this install's layout.
  - `hooks/lib/containment-zones.ts`: the zone inventory.
  - `hooks/SystemFileGuard.hook.ts` + `hooks/lib/system-file-guard-core.ts` + `hooks/lib/hook-input.ts`: a PreToolUse Write/Edit guard.
  - `Tools/containment_check.ts`: the publish gate (`--staged`) and tree audit (`--audit`).
  - `LifeOS/CONTAINMENT.md`: the policy.
  - **Each node must create its own `LifeOS/USER/SECURITY/DENY_LIST.txt`.** It's private and never in this repo.
- **Release tooling:** `Tools/lifeos_release.py` (`version`, `manifest`, `install`, `status`, `precommit`); `VERSION`; `MANIFEST.sha256`; a versioned `githooks/pre-commit` (enable it with `git config core.hooksPath githooks`).

### Changed
- `.gitignore`: ignores `LifeOS/USER/`, `LifeOS/MEMORY/`, and `.env.*` (keeps `.env.example`).

### Unversioned history (before 1.0.0)
- `cf33526` SystemFileGuard: local deny-message wording
- `0083adb` Containment adoption (first cut)
- `4ccccd0` USMetrics: tools load FRED/EIA keys from the LifeOS `.env`
- `eeacde7`, `1ce40a7` MorningGamePlan: the regime comes from `tradekit regime --json`, and its section leads with the glance
- `29ba1f0` api-403 issue workflow, Massive-first source order, wired Massive tools
- Earlier: repo rename (PAI → LifeOS), gib-page-refresh and usmetrics-notion-refresh Lambdas, the initial scrubbed framework
