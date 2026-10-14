#!/usr/bin/env bun
/**
 * containment_check.ts — release gate for the public LifeOS repo, plus a tree audit.
 *
 * Local stand-in for upstream LifeOS's ShadowRelease containment gates (see
 * LifeOS/CONTAINMENT.md). Two modes:
 *
 *   --staged [repo]   Pre-commit gate. Scans the STAGED content of every added or
 *                     modified file in <repo> (default: cwd). Fails on:
 *                       G2  a deny-list hit (LifeOS/USER/SECURITY/DENY_LIST.txt)
 *                       G5  a staged .env or .env.* file (except .env.example)
 *   --audit           Walks ~/.claude and reports deny-list hits in files OUTSIDE
 *                     every containment zone (hooks/lib/containment-zones.ts).
 *                     Report only; changes nothing.
 *
 * Exit: 0 clean · 1 violations found · 2 usage/config error.
 * The deny-list literals are never embedded here; they are read at runtime.
 */
import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { isContained, isPatternAllowlisted, relativeToClaudeRoot } from "../hooks/lib/containment-zones";
import { loadPatterns, scanForFirstHit } from "../hooks/lib/system-file-guard-core";

const CLAUDE_ROOT = join(process.env.HOME ?? homedir(), ".claude");
const MAX_BYTES = 2_000_000;
const SKIP_DIRS = new Set([".git", "node_modules", ".venv", "venv", "__pycache__"]);

const patterns = loadPatterns();
if (patterns.length === 0) {
  console.error("containment_check: deny-list is empty or missing — refusing to report clean");
  process.exit(2);
}

function isEnvStray(path: string): boolean {
  const base = path.split("/").pop() ?? "";
  return (base === ".env" || base.startsWith(".env.")) && base !== ".env.example";
}

function looksBinary(buf: Buffer): boolean {
  return buf.subarray(0, 8000).includes(0);
}

function staged(repo: string): number {
  const git = (...args: string[]) => execFileSync("git", ["-C", repo, ...args], { maxBuffer: 64 * 1024 * 1024 });
  const files = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").toString().split("\0").filter(Boolean);
  let violations = 0;
  for (const f of files) {
    if (isEnvStray(f)) {
      console.error(`G5 .env stray staged: ${f}`);
      violations++;
      continue;
    }
    const buf = git("show", `:${f}`);
    if (buf.length > MAX_BYTES || looksBinary(buf)) continue;
    const hit = scanForFirstHit(buf.toString("utf-8"), patterns);
    if (hit) {
      const line = buf.toString("utf-8").slice(0, hit.index).split("\n").length;
      console.error(`G2 deny-list hit: ${f}:${line}  (pattern ${hit.pattern})`);
      violations++;
    }
  }
  if (violations) {
    console.error(`\ncontainment_check: ${violations} violation(s). Redact in this copy (e.g. <LIVE_ACCOUNT>), unstage, or move the content into a zone.`);
  } else {
    console.log(`containment_check: ${files.length} staged file(s) clean`);
  }
  return violations;
}

function audit(): number {
  let violations = 0;
  const walk = (dir: string) => {
    for (const name of readdirSync(dir)) {
      if (SKIP_DIRS.has(name)) continue;
      const abs = join(dir, name);
      let st;
      try { st = statSync(abs); } catch { continue; }
      if (isContained(abs, CLAUDE_ROOT)) continue;
      if (st.isDirectory()) { walk(abs); continue; }
      const rel = relativeToClaudeRoot(abs, CLAUDE_ROOT);
      if (isPatternAllowlisted(rel) || st.size > MAX_BYTES) continue;
      const buf = readFileSync(abs);
      if (looksBinary(buf)) continue;
      const hit = scanForFirstHit(buf.toString("utf-8"), patterns);
      if (hit) {
        console.log(`${rel}  (pattern ${hit.pattern})`);
        violations++;
      }
    }
  };
  walk(CLAUDE_ROOT);
  console.log(`\ncontainment_check --audit: ${violations} SYSTEM-tree file(s) contain deny-list identifiers`);
  return violations;
}

const [mode, arg] = process.argv.slice(2);
if (mode === "--staged") process.exit(staged(arg ?? process.cwd()) ? 1 : 0);
if (mode === "--audit") process.exit(audit() ? 1 : 0);
console.error("usage: containment_check.ts --staged [repo] | --audit");
process.exit(2);
