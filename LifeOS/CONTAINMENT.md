# LifeOS Containment Policy (local)

> Adapted from upstream LifeOS `LIFEOS/DOCUMENTATION/Tools/Containment.md` (v1.2.3). The OS ships; the life never does.

## The policy in one sentence

**Anything under `~/.claude` that is not inside a containment zone must be clean of personal identity, credentials, and infrastructure IDs.**

## Zones

The authoritative list is `hooks/lib/containment-zones.ts`. Matching is case-sensitive and relative to `~/.claude`.

| Zone | Patterns | What lives here |
|---|---|---|
| `user-data` | `LifeOS/USER/**` | TELOS, trading reviews and gameplans, preferences, R-config, the deny list |
| `config-secrets` | `.env`, `.env.*`, `settings.json`, `settings.local.json` | API keys and any editor or backup copy of them |
| `runtime-memory` | `MEMORY/**`, `LifeOS/MEMORY/**`, `projects/**`, `History/**` | Work sessions, security logs, Claude Code memory and transcripts |
| `private-skills` | `skills/_*/**` | Personal skills; the `_` prefix is the contract |
| `install-state` | harness runtime dirs (`sessions/`, `file-history/`, `shell-snapshots/`, `cache/`, …) | Written by Claude Code, never published |
| `skill-runtime-data` | `skills/*/State/**`, `skills/*/cache/**`, … | Caches and state that accumulate under public skills |
| `local-runtime-data` | `data/**`, `VoiceServer/*.log` | Local datasets and service logs |

Everything else (`skills/<Public>/`, `Tools/`, `hooks/`, `LifeOS/*.md`) is the **system tree**. It is what gets pushed to the public `davdunc/lifeos` repo.

## Enforcement

1. **Write time — `hooks/SystemFileGuard.hook.ts`** (PreToolUse on Write and Edit). If the target is in the system tree and the new text matches the deny list, the write is blocked (exit 2). Writes into a zone are never blocked. Any internal error fails open, so a guard bug can never stop work. Blocks are logged to `MEMORY/SECURITY/system-file-guard.jsonl`.
2. **Publish time — `Tools/containment_check.ts --staged`**, run as the `pre-commit` hook of `~/src/lifeos`. It fails the commit on a deny-list hit in any staged file (G2) or a staged `.env*` file (G5).
3. **Audit — `Tools/containment_check.ts --audit`**. It lists system-tree files that already contain deny-list identifiers. It only reports; it changes nothing.

## The deny list

`LifeOS/USER/SECURITY/DENY_LIST.txt` holds one regex per line, matched case-insensitively. It lives in the user-data zone, so the identifiers never appear in a public file. Not even the checker embeds them.

Current scope (operator choice, 2026-10-14): broker account IDs and the Windows user-profile path.

## Handling common situations

- **A tool needs a secret:** read `process.env.X` first, then fall back to `~/.claude/.env`, parsed in the tool itself with no shared helper. If it's still missing, warn once on stderr.
- **A tool needs a machine-specific path or ID:** read it from `.env` (`TRADE_REVIEW_PATH`, `DAS_ROOT`, `DAS_ACCOUNT`) instead of writing the literal.
- **Pushing a file that contains an identifier:** redact it in the pushed copy (`<LIVE_ACCOUNT>`, `<SIM_ACCOUNT>`). Never edit the local file to redact it.
- **Adding a private directory:** add its pattern to `CONTAINMENT_ZONES` first.
- **A file must embed a pattern to detect it:** add it to `PATTERN_ALLOWLIST_FILES` with a reason. Every entry is a standing TODO.

## Not adopted yet

- **Salted-hash filter** (upstream `DeriveDenyHashes`). It catches novel private tokens without listing them in the clear. It needs a `DENYLIST_SALT` in `.env` and a derivation tool.
- **Upstream release gates G3–G25.** These belong to Daniel's ShadowRelease pipeline, which has no local equivalent. Only G2 and G5 are mirrored here.
