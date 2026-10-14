# ADR 0002 — Secrets stay in `~/.claude/.env` for now; no vault

**Status:** accepted · **Date:** 2026-10-14

## Context

All API keys, tokens, and webhooks live in a plaintext `~/.claude/.env` on each node (28 secrets, plus 15
non-secret config values). Stray copies had accumulated beside it (an old `.env.bak.*` and an editor swap file).
Vault options were priced for 28 secrets, and for 140 if each of five nodes keeps its own keys:

| Option | Cost |
|---|---|
| AWS SSM Parameter Store, standard tier | $0 (fits the per-node IAM users already in place) |
| AWS Secrets Manager | $11.20/mo per-secret, or about $2/mo bundled one secret per node |
| Bitwarden Secrets Manager | Free for 3 machine accounts; Teams $72/yr covers all nodes |
| 1Password service accounts | about $36–$96/yr, depending on plan support |
| sops + age | $0, with manual key rotation |

## Decision

Keep `.env` as the source of truth on each node for now. The operator accepts that this is less secure than a
vault. Contain it instead: `.env` and `.env.*` are in the `config-secrets` zone (ADR 0004), stray copies get
deleted, and keys never appear in published files.

## Consequences

- Secrets sit in plaintext on disk; disk-level protection and node hygiene are the controls.
- If a vault is adopted later, the leading option is SSM standard tier with a generated `.env`. Tools would keep
  reading `.env` (ADR 0003), so only how the file is produced changes. That would be a new ADR superseding this one.
