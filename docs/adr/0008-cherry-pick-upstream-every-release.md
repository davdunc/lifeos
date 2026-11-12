# ADR 0008 — Cherry-pick upstream LifeOS corrections on every upstream release

**Status:** accepted · **Date:** 2026-11-12

## Context

Upstream (`danielmiessler/LifeOS`) shipped 8.761.0 on 2026-10-27. It renamed USMetrics to **USStats** and
restructured it: new `UsStatsConfig.ts`, a dependency on `LIFEOS/TOOLS/Paths.ts`, `Intents/` instead of
`Workflows/`, and a new data directory. It also carried real corrections that this fork lacked: display
scaling for FRED series reported in a smaller unit than they print (ICSA, CCSA, RSAFS, TOTALSL, BOPG*,
GFDEBTN, POPTHM), the ICSA "189.0M" label, unit metadata in `FetchFredSeries`, and fetch-failure
reporting. Nobody noticed until a report printed claims as 189 million.

We can't adopt the release wholesale. This install has no `LIFEOS/TOOLS/Paths.ts`, it keeps keys in
`~/.claude/.env` (ADR 0007), and its dataset lives under `~/.claude/data/Substrate/`.

## Decision

The operator said: "we should cherry-pick all of the lifeos updates every release."

- **When upstream tags a release:** diff every skill this fork carries against the upstream copy. Upstream
  may have renamed the skill, so map by content, not only by path.
- **Cherry-pick corrections:** bug fixes, unit and format fixes, data-source fixes, and guards.
- **Don't cherry-pick structural changes** that would break this layout (paths, config loaders, renames)
  unless the operator asks for a migration. Record each one that was skipped in the CHANGELOG entry.
- Prefer upstream's form of a fix over our own (for example, `scale` as a divisor), so later diffs stay
  small.
- Each cherry-pick ships as its own versioned release (ADR 0005). Its CHANGELOG entry names the upstream
  tag and commit it came from.
- Local fixes that upstream lacks stay fork-only (ADR 0006), unless they're a clear upstream bug.

## Consequences

- The fork stays within one upstream release of the corrections, with no forced restructuring.
- Every upstream release costs a diff pass. Trigger it from the upstream release feed.
- Skipped structural changes pile up as known drift. Revisit them if a migration becomes worth it.
