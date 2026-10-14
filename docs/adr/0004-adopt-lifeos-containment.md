# ADR 0004 — Adopt upstream LifeOS containment, adapted to this layout

**Status:** accepted · **Date:** 2026-10-14

## Context

This repo is public, and the only thing keeping personal identifiers out of it was a manual grep before each
push. The live tree already had broker account IDs and a Windows user-profile path in 11 shared files
(`Tools/das_*`, `skills/Trading/*`). Upstream LifeOS has a containment policy for exactly this:
- private **zones** that may hold identity;
- a runtime write guard (`SystemFileGuard`);
- release-time gates.

Our install predates it, and it differs from upstream: it uses `LifeOS/` rather than `LIFEOS/`, keeps memory at
the root `MEMORY/`, and runs on Linux, where path matching is case-sensitive.

## Decision

Port containment with local zone spellings:
- **Zones:** `LifeOS/USER/**`, `.env` and `.env.*`, `settings*.json`, `MEMORY/**`, `LifeOS/MEMORY/**`,
  `projects/**`, `skills/_*/**`, harness runtime directories, `data/**`.
- **Runtime guard:** a PreToolUse Write/Edit hook that blocks deny-list hits in files outside the zones and
  fails open on its own errors.
- **Deny list:** `LifeOS/USER/SECURITY/DENY_LIST.txt`, private to each node. Its scope is broker account IDs
  plus the Windows user path (operator choice).
- **Publish gate:** `Tools/containment_check.ts --staged` runs in this repo's pre-commit hook. It mirrors
  upstream gates G2 (identity) and G5 (`.env` strays). `--audit` reports existing leaks.

## Consequences

- New identifiers can't be written into shared files, and the guard says where they belong instead
  (`.env`, `LifeOS/USER`).
- The 11 existing files still contain identifiers. They're redacted in pushed copies but not yet refactored to
  read `.env`.
- Each node needs its own deny list. Deferred: upstream's salted-hash filter and gates G3–G25.
- Ships as component `containment` (ADR 0005).
