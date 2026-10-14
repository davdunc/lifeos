# Architecture Decision Records

One file per decision that shapes how this LifeOS install works: why it is the way it is, and what we gave up.
The format matches `tradekit/docs/adr/`.

- **File:** `NNNN-kebab-title.md`, numbered in order, never renumbered.
- **Header:** `# ADR NNNN — <decision as a sentence>`, then `**Status:** proposed | accepted | superseded by NNNN · **Date:** YYYY-MM-DD`.
- **Sections:** Context, Decision, Consequences. Alternatives go in Context when they were seriously weighed.
- **Changing a decision:** write a new ADR and mark the old one `superseded by NNNN`. Don't rewrite history.
- **Shipping:** an ADR ships like any other change, as a release (ADR 0005). It must pass the containment gate (ADR 0004): no account IDs, keys, or personal paths.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | accepted |
| [0002](0002-secrets-stay-in-dotenv.md) | Secrets stay in `~/.claude/.env` for now; no vault | accepted |
| [0003](0003-tools-load-keys-from-dotenv.md) | Tools load their keys from `.env` themselves | accepted |
| [0004](0004-adopt-lifeos-containment.md) | Adopt upstream LifeOS containment, adapted to this layout | accepted |
| [0005](0005-versioned-releases-and-node-stamps.md) | Every change ships as a versioned release, and nodes stamp what they run | accepted |
| [0006](0006-fork-only-for-setup-changes.md) | Setup changes stay in this repo; upstream gets only real bug fixes | accepted |
