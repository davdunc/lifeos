# ADR 0005 — Every change ships as a versioned release, and nodes stamp what they run

**Status:** accepted · **Date:** 2026-10-14

## Context

Several nodes pull this repo, but nothing recorded which commit each one had applied. Changes were copied into
`~/.claude` by hand, so drift between nodes, and between what the assistant said it changed and what was
actually installed, was invisible. The operator asked for "a release version on any changes that is
identifiable and useful for tracking your consistency."

## Decision

- **Semver** in `VERSION`:
  - MAJOR: a node must act manually.
  - MINOR: a new component, tool, workflow, or process.
  - PATCH: fixes, wording, docs.
- Every release gets a dated `CHANGELOG.md` entry, a fresh `MANIFEST.sha256` (sha256 per file), and an
  annotated tag `vX.Y.Z`.
- The versioned `githooks/pre-commit` (enabled with `core.hooksPath githooks`) **rejects** any commit that
  changes files without all of these, after the containment gate.
- `Tools/lifeos_release.py install <component>` copies only that component's files, wires its hooks, and stamps
  `~/.claude/LifeOS/LOCAL_RELEASE.json` (release, commit, node, components, time). It never bulk-overwrites
  `~/.claude`, because some repo files are redacted public copies.
- `lifeos_release.py status` reports each file as MATCH, DIFFERS, MISSING, REDACTED, or REPO-ONLY.
- Nodes include `lifeos <version>` in #falcon-cluster beacons. A release handoff is confirmed by the marker
  `LIFEOS-RELEASE-OK vX.Y.Z <node>`.

## Consequences

- Release history so far: v1.0.0 (first versioned release: containment plus tooling) and v1.0.1 (status
  verdict fixes found by running status on daslaptop).
- Committing to this repo now requires the containment component on that node.
- Files that don't install into `~/.claude` (`githooks/`) are REPO-ONLY. `systemd/user/*` is compared against
  `~/.config/systemd/user/`.
