# ADR 0006 — Setup changes stay in this repo; upstream gets only real bug fixes

**Status:** accepted · **Date:** 2026-10-14

## Context

The USMetrics `.env` loader (ADR 0003) works around how this install supplies keys. When asked whether to PR it
to upstream LifeOS, the operator said: "It's not appropriate to change the way it works upstream." The earlier
upstream contribution (PR #2253) fixed a real defect in USMetrics trend windows, and upstream applied it.

## Decision

Changes that adapt LifeOS to this install (key loading, paths, layout, local conventions, containment
adaptations) ship only in this repo. Upstream contributions are limited to defects upstream would agree are
bugs, and only to repositories on the operator's PR whitelist.

## Consequences

- This repo will keep diverging from upstream in setup and convention. ADRs are where that divergence is
  explained.
- When pulling ideas from upstream (as with containment, ADR 0004), we adapt them locally rather than proposing
  our adaptations back.
