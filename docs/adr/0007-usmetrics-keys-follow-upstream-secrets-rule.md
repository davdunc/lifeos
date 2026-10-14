# ADR 0007 — USMetrics reads keys the way upstream's secrets rule says, with no local improvements

**Status:** accepted · **Date:** 2026-10-14 · **Supersedes:** 0003

## Context

ADR 0003 shipped a shared `loadEnv.ts` that checked three `.env` locations, including the
`$LIFEOS_CONFIG_DIR/.env` path upstream warns against, and stripped inline comments. It worked, but it diverged
from upstream's documented secrets rule (`Containment.md`): read `process.env` first, then fall back to
`~/.claude/.env` read directly, using a small parser in each tool, with no shared helper. Two options were
weighed:
- **Align with upstream:** a few duplicated lines per tool, no divergence.
- **Keep the helper:** one place to change parsing, but a standing divergence.

## Decision

Align with upstream exactly. The operator said: "throw away our changes that were meant to be an improvement."
- `UpdateSubstrateMetrics.ts`, `FetchFredSeries.ts`, and `GenerateAnalysis.ts` each carry their own `readDotEnv()`:
  - read only `~/.claude/.env`;
  - use upstream's line parser (`^([^#=]+)=(.*)$`, trim, strip surrounding quotes);
  - apply only when `process.env` doesn't already have the key.
- `loadEnv.ts` is deleted, along with its extras: the multi-path search, the `$LIFEOS_CONFIG_DIR` lookup, the
  `export` prefix handling, and inline-comment stripping.
- The existing "key not set" errors remain the single warning when a key is missing everywhere.

## Consequences

- Behavior for the keys these tools use is unchanged: the FRED and EIA lines in `.env` carry no inline
  comments, and a key set in the shell still wins.
- An inline `# comment` after a key in `.env` would now become part of the value, as it would upstream. Keep key
  lines comment-free.
- Future upstream changes to these tools should merge with fewer conflicts.
- Still fork-only (ADR 0006).
