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

## [1.2.0] — 2026-10-20
### Added
- **SlowDayChecklist workflow** (`skills/Trading/Workflows/SlowDayChecklist.md`): Roberto's
  five-check prioritization protocol for quiet sessions — Big Picture → Sector ETFs →
  Catalysts → Elevated premarket volume → Relative strength/weakness — usable premarket and
  as a mid-session reset. A slow day is not automatically a no-trade day; the checklist
  re-scopes the existing seven-section game plan (five-check summary under MACRO,
  candidates under WATCHLIST, C-size/RVOL guidance inside the 3-bullet RULES cap) and never
  adds sections. C-size risk comes from the approved R-CONFIG definition; RVOL 1.5+ /
  ≤0.8 caution is Roberto's attributed guidance, not a validated automated gate.
- **MorningGamePlan: Slow Day Protocol hard rule** — phase hooks in Phase 2 (slow-day
  discovery route when the gapper/catalyst screen comes up empty), Phase 5 (`WAIT —
  scanning for relative strength/weakness` is a valid thesis entry), and Phase 6 (ordered
  five-check summary in the output). Also corrected the stale claim that `tradekit cards *`
  does not exist: the reporting layer shipped with PR #12 (`tradekit cards gameplan
  --format dw` renders the stored GAMEPLAN record).

## [1.1.1] — 2026-10-14
### Changed
- **USMetrics key loading now follows upstream's secrets rule** (ADR 0007, superseding 0003):
  - each tool reads `process.env`, then falls back to `~/.claude/.env` with its own small parser;
  - `skills/USMetrics/Tools/loadEnv.ts` is removed, along with its extra paths and comment stripping.

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
