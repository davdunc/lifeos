// containment-zones.ts — zone inventory (ported from upstream LifeOS hooks/lib/containment-zones.ts).
//
// A zone is a named set of path patterns whose contents are allowed to contain
// personal identity, credentials, or infrastructure IDs. Anything outside every
// zone must stay clean per LifeOS/CONTAINMENT.md.
//
// Consumed by:
//   1. hooks/SystemFileGuard.hook.ts — runtime PreToolUse Write/Edit gate.
//   2. Tools/containment_check.ts — pre-commit gate for the public LifeOS repo.
//
// Local adaptation: this install keeps the system tree under `LifeOS/` (upstream
// uses `LIFEOS/`) and keeps work memory at the root `MEMORY/`. Matching is
// case-SENSITIVE, so patterns use this install's real spelling.
//
// Path patterns are matched relative to CLAUDE_ROOT (~/.claude). `**` means
// "anywhere under this prefix"; a bare path means "this exact file".

export interface ContainmentZone {
  name: string;
  patterns: readonly string[];
  description: string;
}

export const CONTAINMENT_ZONES: readonly ContainmentZone[] = [
  {
    name: "user-data",
    patterns: ["LifeOS/USER/**"],
    description: "Principal identity, TELOS, trading reviews and gameplans, preferences and R-config, skill customizations",
  },
  {
    name: "config-secrets",
    patterns: [
      "settings.json",
      "settings.local.json",
      ".vscode/settings.json",
      ".env",
      ".env.*",
      "LifeOS/.env",
      "LifeOS/.env.*",
    ],
    description: "Shell env with API keys (and editor swap/backup copies of it), allowed command lists, MCP auth",
  },
  {
    name: "runtime-memory",
    patterns: ["MEMORY/**", "LifeOS/MEMORY/**", "projects/**", "History/**"],
    description: "Work sessions (PRDs), learnings, security logs, Claude Code auto-memory and session transcripts",
  },
  {
    name: "private-skills",
    patterns: ["skills/_*/**"],
    description: "Skills with underscore-prefixed names — personal and proprietary",
  },
  {
    name: "install-state",
    patterns: [
      "history.jsonl",
      "Plugins/**",
      "plugins/**",
      "debug/**",
      "debug",
      "file-history/**",
      "paste-cache/**",
      "shell-snapshots/**",
      "session-env/**",
      "sessions/**",
      "telemetry/**",
      "cache/**",
      "state/**",
      "tasks/**",
      "teams/**",
      "jobs/**",
      "todos/**",
      "backups/**",
      "downloads/**",
      "feedback/**",
      "remote-settings.json",
      "stats-cache.json",
      "stats.json",
      "ids.txt",
      "checkpoint-repos.txt",
    ],
    description: "Claude Code runtime state written by the harness: plugin registry, history, session transcripts and snapshots, caches, task state, downloads, backups",
  },
  {
    name: "skill-runtime-data",
    patterns: [
      "skills/*/profile-data/**",
      "skills/*/state/**",
      "skills/*/State/**",
      "skills/*/cache/**",
      "skills/*/Cache/**",
      "skills/*/Logs/**",
      "skills/*/.playwright-cli/**",
      "skills/*/.cache/**",
      "skills/*/node_modules/**",
    ],
    description: "Runtime data accumulated under public-named skills — browser profiles, caches, state, build artifacts",
  },
  {
    name: "local-runtime-data",
    patterns: ["data/**", "VoiceServer/*.log"],
    description: "Local datasets (US-Common-Metrics substrate) and service logs — machine output, never published",
  },
];

// Files outside containment that must still be allowed to embed patterns
// (the checker, the policy doc). Every entry is a standing TODO — keep minimal.
// None of them may contain the deny-list literals themselves: those live only in
// LifeOS/USER/SECURITY/DENY_LIST.txt and are read at runtime.
export const PATTERN_ALLOWLIST_FILES: readonly string[] = [
  "hooks/lib/containment-zones.ts",
  "LifeOS/CONTAINMENT.md",
  "Tools/containment_check.ts",
];

// Component-wise glob match. Handles `*` within a single path segment and
// `**` as a terminal wildcard meaning "any remaining components, including zero".
function componentMatch(component: string, glob: string): boolean {
  if (glob === "*") return true;
  if (!glob.includes("*")) return component === glob;
  const parts = glob.split("*");
  if (!component.startsWith(parts[0])) return false;
  let cursor = parts[0].length;
  for (let i = 1; i < parts.length - 1; i += 1) {
    const idx = component.indexOf(parts[i], cursor);
    if (idx < 0) return false;
    cursor = idx + parts[i].length;
  }
  const tail = parts[parts.length - 1];
  if (tail === "") return true;
  return component.endsWith(tail) && component.length >= cursor + tail.length;
}

function matchesPattern(relPath: string, pattern: string): boolean {
  const patternParts = pattern.split("/");
  const pathParts = relPath === "" ? [] : relPath.split("/");
  let pi = 0;
  let i = 0;
  while (pi < patternParts.length) {
    const pp = patternParts[pi];
    if (pp === "**") return true;
    if (i >= pathParts.length) return false;
    if (!componentMatch(pathParts[i], pp)) return false;
    pi += 1;
    i += 1;
  }
  return i === pathParts.length;
}

// Normalize an absolute path to the path relative to CLAUDE_ROOT. Returns
// the input unchanged if it does not live under CLAUDE_ROOT.
export function relativeToClaudeRoot(absolutePath: string, claudeRoot: string): string {
  if (absolutePath === claudeRoot) return "";
  const prefix = claudeRoot.endsWith("/") ? claudeRoot : claudeRoot + "/";
  return absolutePath.startsWith(prefix) ? absolutePath.slice(prefix.length) : absolutePath;
}

// Predicate: is this path inside any configured containment zone?
export function isContained(absolutePath: string, claudeRoot: string): boolean {
  const rel = relativeToClaudeRoot(absolutePath, claudeRoot);
  for (const zone of CONTAINMENT_ZONES) {
    for (const pattern of zone.patterns) {
      if (matchesPattern(rel, pattern)) return true;
    }
  }
  return false;
}

// Predicate: is this relative path in the pattern-embedding allowlist?
export function isPatternAllowlisted(relativePath: string): boolean {
  return PATTERN_ALLOWLIST_FILES.includes(relativePath);
}
