#!/usr/bin/env python3
"""lifeos_release.py — versioned releases of the davdunc/lifeos repo, per-node install stamps,
and drift checks, so every node can say which release it runs and whether its files match.

Run it from a checkout of davdunc/lifeos (default ~/src/lifeos), or pass --repo.

  version                 print the repo release (VERSION + commit)
  manifest                maintainer: regenerate MANIFEST.sha256 for every tracked file
  install <component>     copy a component's files into ~/.claude, wire it up, and stamp the node
  status                  compare ~/.claude against the release manifest and print the node stamp
  precommit               git pre-commit gate: any staged change must bump VERSION, add a
                          CHANGELOG entry for it, and carry a fresh MANIFEST.sha256

Node stamp: ~/.claude/LifeOS/LOCAL_RELEASE.json
  {"release": "1.0.0", "commit": "...", "node": "...", "components": {...}, "installed_at": "..."}

Status verdicts per manifest file:
  MATCH     installed copy is byte-identical to the release
  DIFFERS   installed copy has drifted (edited locally, or the node is on another release)
  MISSING   file is in the release but not installed on this node
  REDACTED  the files differ AND the release copy carries redaction placeholders, so it is a
            public copy of a private-valued file and cannot be compared byte-for-byte
  REPO-ONLY used by the checkout itself (githooks/); nothing to install
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

CLAUDE = Path(os.environ.get("HOME", str(Path.home()))) / ".claude"
STAMP = CLAUDE / "LifeOS" / "LOCAL_RELEASE.json"
META_FILES = {"VERSION", "CHANGELOG.md", "MANIFEST.sha256", "README.md", ".gitignore", "CLAUDE.md"}
REDACTION_MARKERS = (b"<LIVE_ACCOUNT>", b"<SIM_ACCOUNT>", b"<REDACTED")
REPO_ONLY_PREFIXES = ("githooks/",)                      # used by the checkout, never installed
INSTALL_ROOTS = {"systemd/user/": Path.home() / ".config" / "systemd" / "user"}  # repo prefix -> node dir


def installed_path(rel: str) -> Path | None:
    """Where a release file lives on the node; None for repo-only files."""
    if rel.startswith(REPO_ONLY_PREFIXES):
        return None
    for prefix, root in INSTALL_ROOTS.items():
        if rel.startswith(prefix):
            return root / rel[len(prefix):]
    return CLAUDE / rel

# Components a node can install from the release. Files are ~/.claude-relative.
COMPONENTS = {
    "containment": {
        "files": [
            "hooks/SystemFileGuard.hook.ts",
            "hooks/lib/containment-zones.ts",
            "hooks/lib/system-file-guard-core.ts",
            "hooks/lib/hook-input.ts",
            "Tools/containment_check.ts",
            "Tools/lifeos_release.py",
            "LifeOS/CONTAINMENT.md",
        ],
        "executable": ["hooks/SystemFileGuard.hook.ts", "Tools/containment_check.ts", "Tools/lifeos_release.py"],
        "hook": {"event": "PreToolUse", "matchers": ["Write", "Edit"],
                 "command": "${LIFEOS_DIR}/hooks/SystemFileGuard.hook.ts"},
        "requires": ["LifeOS/USER/SECURITY/DENY_LIST.txt"],
    },
}


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_of(repo: Path) -> dict:
    version = (repo / "VERSION").read_text().strip()
    commit = git(repo, "rev-parse", "--short", "HEAD")
    dirty = bool(git(repo, "status", "--porcelain", "--untracked-files=no"))
    return {"release": version, "commit": commit + ("-dirty" if dirty else "")}


def cmd_version(repo: Path) -> int:
    r = release_of(repo)
    print(f"lifeos {r['release']} ({r['commit']})")
    return 0


def cmd_manifest(repo: Path) -> int:
    lines = []
    for rel in sorted(git(repo, "ls-files").splitlines()):
        if rel in META_FILES:
            continue
        lines.append(f"{sha256(repo / rel)}  {rel}")
    (repo / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    print(f"MANIFEST.sha256: {len(lines)} files")
    return 0


def read_manifest(repo: Path) -> list[tuple[str, str]]:
    out = []
    for line in (repo / "MANIFEST.sha256").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        out.append((digest, rel))
    return out


def register_hook(spec: dict) -> bool:
    settings = CLAUDE / "settings.json"
    data = json.loads(settings.read_text())
    changed = False
    for entry in data.setdefault("hooks", {}).setdefault(spec["event"], []):
        if entry.get("matcher") in spec["matchers"]:
            hooks = entry.setdefault("hooks", [])
            if not any(h.get("command") == spec["command"] for h in hooks):
                hooks.append({"type": "command", "command": spec["command"]})
                changed = True
    present = {e.get("matcher") for e in data["hooks"][spec["event"]]}
    for matcher in spec["matchers"]:
        if matcher not in present:
            data["hooks"][spec["event"]].append(
                {"matcher": matcher, "hooks": [{"type": "command", "command": spec["command"]}]})
            changed = True
    if changed:
        shutil.copy2(settings, settings.with_name("settings.json.pre-release-install"))
        # ensure_ascii=False keeps the file's existing unicode instead of escaping it.
        settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return changed


def cmd_install(repo: Path, component: str) -> int:
    if component not in COMPONENTS:
        print(f"unknown component {component!r}; known: {', '.join(COMPONENTS)}", file=sys.stderr)
        return 2
    spec = COMPONENTS[component]
    rel_info = release_of(repo)
    if rel_info["commit"].endswith("-dirty"):
        print("refusing to install from a dirty checkout; commit or stash first", file=sys.stderr)
        return 2
    manifest = dict((rel, d) for d, rel in read_manifest(repo))
    for rel in spec["files"]:
        src, dst = repo / rel, CLAUDE / rel
        if manifest.get(rel) != sha256(src):
            print(f"{rel}: checkout does not match MANIFEST.sha256 — run `manifest` and commit", file=sys.stderr)
            return 2
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha256(dst) != sha256(src):
            shutil.copy2(dst, dst.with_name(dst.name + ".pre-release-install"))
        shutil.copy2(src, dst)
        if rel in spec.get("executable", []):
            dst.chmod(0o754)
        print(f"installed {rel}")
    if spec.get("hook") and register_hook(spec["hook"]):
        print("registered hook in settings.json (backup: settings.json.pre-release-install)")
    for req in spec.get("requires", []):
        if not (CLAUDE / req).exists():
            print(f"WARNING: {req} is missing — this node must create it (private, never in the repo)")
    stamp = json.loads(STAMP.read_text()) if STAMP.exists() else {"components": {}}
    stamp.update(rel_info)
    stamp["node"] = os.environ.get("LIFEOS_MACHINE_ID") or socket.gethostname()
    stamp["installed_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    stamp.setdefault("components", {})[component] = rel_info["release"]
    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(json.dumps(stamp, indent=2) + "\n")
    print(f"stamped {STAMP}: lifeos {rel_info['release']} ({rel_info['commit']}) on {stamp['node']}")
    return 0


def cmd_status(repo: Path) -> int:
    rel_info = release_of(repo)
    stamp = json.loads(STAMP.read_text()) if STAMP.exists() else None
    print(f"repo release : lifeos {rel_info['release']} ({rel_info['commit']})")
    if stamp:
        print(f"node stamp   : lifeos {stamp['release']} ({stamp['commit']}) on {stamp['node']} "
              f"at {stamp['installed_at']} components={stamp.get('components')}")
    else:
        print("node stamp   : NONE (no release installed via lifeos_release.py)")
    counts: dict[str, int] = {}
    for digest, rel in read_manifest(repo):
        dst = installed_path(rel)
        if dst is None:
            verdict = "REPO-ONLY"
        elif not dst.exists():
            verdict = "MISSING"
        elif sha256(dst) == digest:
            verdict = "MATCH"
        elif any(m in (repo / rel).read_bytes() for m in REDACTION_MARKERS):
            verdict = "REDACTED"
        else:
            verdict = "DIFFERS"
        counts[verdict] = counts.get(verdict, 0) + 1
        if verdict not in ("MATCH", "REPO-ONLY"):
            print(f"  {verdict:9} {rel}")
    print("summary      : " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    installed = {f for c in (stamp or {}).get("components", {}) for f in COMPONENTS.get(c, {}).get("files", [])}
    drift = [rel for d, rel in read_manifest(repo)
             if rel in installed and (not (CLAUDE / rel).exists() or sha256(CLAUDE / rel) != d)]
    if drift:
        print("component drift: " + ", ".join(drift))
        return 1
    return 0


def cmd_precommit(repo: Path) -> int:
    staged = [f for f in git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMRD").splitlines() if f]
    if not [f for f in staged if f not in META_FILES]:
        return 0
    problems = []
    if "VERSION" not in staged:
        problems.append("VERSION was not bumped")
    version = git(repo, "show", ":VERSION").strip()
    previous = subprocess.run(["git", "-C", str(repo), "show", "HEAD:VERSION"], capture_output=True, text=True).stdout.strip()
    if previous and version == previous:
        problems.append(f"VERSION is still {version}")
    if f"## [{version}]" not in git(repo, "show", ":CHANGELOG.md"):
        problems.append(f"CHANGELOG.md has no '## [{version}]' entry")
    expected = []
    for rel in sorted(git(repo, "ls-files", "--cached").splitlines()):
        if rel in META_FILES:
            continue
        blob = subprocess.check_output(["git", "-C", str(repo), "show", f":{rel}"])
        expected.append(f"{hashlib.sha256(blob).hexdigest()}  {rel}")
    staged_manifest = subprocess.run(["git", "-C", str(repo), "show", ":MANIFEST.sha256"],
                                     capture_output=True, text=True).stdout
    if staged_manifest != "\n".join(expected) + "\n":
        problems.append("MANIFEST.sha256 is stale — run `lifeos_release.py manifest` and stage it")
    for p in problems:
        print(f"release gate: {p}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=str(Path.home() / "src" / "lifeos"))
    ap.add_argument("command", choices=["version", "manifest", "install", "status", "precommit"])
    ap.add_argument("component", nargs="?")
    a = ap.parse_args()
    repo = Path(a.repo)
    if a.command == "version":
        return cmd_version(repo)
    if a.command == "manifest":
        return cmd_manifest(repo)
    if a.command == "install":
        if not a.component:
            ap.error("install needs a component")
        return cmd_install(repo, a.component)
    if a.command == "precommit":
        return cmd_precommit(repo)
    return cmd_status(repo)


if __name__ == "__main__":
    sys.exit(main())
