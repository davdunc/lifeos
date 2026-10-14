# ADR 0003 — Tools load their keys from `.env` themselves

**Status:** superseded by 0007 · **Date:** 2026-10-14

## Context

The USMetrics tools read `FRED_API_KEY` only from the process environment. Upstream documents
`export FRED_API_KEY=...` as the setup. A run from a fresh shell failed with "FRED_API_KEY environment variable
not set". Sourcing `.env` wholesale isn't reliable either: one unquoted value with a space breaks the shell parse.

Upstream's secrets rule (`Containment.md`) says:
1. Read `process.env` first.
2. Fall back to reading `~/.claude/.env` directly, with `fs.readFileSync` and a small parser in each tool.
3. Use no shared helper ("no central env helper exists by design").
4. Never compute the path as `$LIFEOS_CONFIG_DIR/.env`.

## Decision

USMetrics tools fill missing keys from `.env` at startup, and the real environment always wins. Shipped in
4ccccd0 as one shared `skills/USMetrics/Tools/loadEnv.ts`, which checks `$LIFEOS_CONFIG_DIR/.env`,
`~/.config/LifeOS/.env`, then `~/.claude/.env`, parses line by line, and strips trailing comments on unquoted
values.

## Consequences

- Unattended runs (timers, other agents) get their keys without manual exports.
- **Known divergence from upstream's rule:** the loader is a shared helper, and it checks
  `$LIFEOS_CONFIG_DIR/.env` first. That's harmless here, because that file doesn't exist on our nodes, but it's
  the pattern upstream warns against. Aligning it (a per-tool `~/.claude/.env` fallback) was proposed and not
  yet chosen. If adopted, it supersedes this ADR.
- Fork-only change (ADR 0006).
