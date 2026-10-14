# ADR 0001 — Record architecture decisions

**Status:** accepted · **Date:** 2026-10-14

## Context

On 2026-10-14 a single session produced several decisions that shape this install: where secrets live, how
tools find them, containment, release versioning, and what goes upstream. The reasoning existed only in a chat
transcript and in the assistant's private memory files. Neither is visible to the other nodes (trader-desk and
the rest), and neither is a durable record the operator can review. tradekit already keeps ADRs in
`docs/adr/`, and they have worked well for its regime and config decisions.

## Decision

Keep ADRs in `docs/adr/` of this repo, in the tradekit format: one numbered file per decision, with Context,
Decision, and Consequences. Write an ADR when a choice changes how nodes behave, what gets published, or where
data or secrets live. The assistant drafts each one at the time of the decision, and the operator's choice is
recorded as the decision.

## Consequences

- Each node gets the reasoning with the code, through the same release (ADR 0005).
- Superseding is explicit: a new ADR, with the old one marked `superseded by`.
- The assistant's private memory keeps pointers to ADRs, not duplicates of them.
