#!/usr/bin/env python3
"""Record HTTP 403s from paid data APIs, and file them as bugs in each app's GitHub repo.

Operator rule, 2026-10-06: a 403 from Massive/Polygon or Finviz is a bug in the app that hit it
(throttling we caused, an entitlement we don't have, or an expired key). Each one gets logged and
reported to that app's issue tracker, without risking access to the paid feeds.

Two halves:

1. **record** — every app appends one JSON line per 403 to a shared log
   (``$API_ERROR_LOG``, default ``~/.local/state/api-errors/events.jsonl``). tradekit writes the
   same schema from ``tradekit.data.api_errors``. In ~/.claude/Tools use the wrappers::

       from api_errors import urlopen, check_response
       urlopen(url, app="lifeos-tools:sizing_column", timeout=30)        # urllib callers
       check_response(requests.get(url), app="lifeos-tools:opening_drive_scan")  # requests callers

   The wrappers record and then re-raise or return exactly what they would have. They never retry
   and never make an extra request ([[protect-paid-data-access]]).

2. **report** — ``api_errors.py report [--dry-run]`` reads the events since the last run, groups them
   by (app, provider, endpoint), and per group either comments on the open ``api-403`` issue whose
   body carries the same fingerprint, or opens a new issue labelled ``bug`` + ``api-403``.
   A daily systemd timer runs it on daslaptop (``api-403-report.timer``).

Both target repos are public. Events keep the URL **path only**, with ticker and date segments
normalized, so no key, query string, account or market data can reach an issue.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

# app prefix -> GitHub repo. Longest matching prefix wins.
REPO_MAP = {
    "tradekit": "davdunc/tradekit",
    "lifeos-tools": "davdunc/lifeos",
    "falcon-core": "TradingAsBuddies/falcon-core",
    "falcon-stats": "davdunc/falcon-stats",
    "falcon": "davdunc/falcon",
}
LABEL = "api-403"
REPORT_STATUSES = {403}
PROVIDER_NAMES = {"massive": "Massive/Polygon", "finviz": "Finviz", "fred": "FRED"}


def log_path() -> Path:
    env = os.environ.get("API_ERROR_LOG")
    if env:
        return Path(env)
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return base / "api-errors" / "events.jsonl"


def _node() -> str:
    try:
        return Path("/etc/hostname").read_text().strip() or socket.gethostname()
    except OSError:
        return socket.gethostname()


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TICKER_PARENTS = {"ticker", "tickers"}


def normalize(url: str) -> tuple[str, str]:
    """Return (host, path) with the query dropped and ticker/date segments replaced by placeholders."""
    parts = urllib.parse.urlsplit(url)
    segs = parts.path.split("/")
    out = []
    for i, s in enumerate(segs):
        if _DATE.match(s):
            out.append("{date}")
        elif i > 0 and segs[i - 1].lower() in _TICKER_PARENTS and s:
            out.append("{ticker}")
        else:
            out.append(s)
    return parts.hostname or "", "/".join(out) or "/"


def record(app: str, provider: str, url: str, status: int, detail: str = "", method: str = "GET") -> None:
    """Append one redacted event. Never raises: logging must not break the caller."""
    try:
        host, path = normalize(url)
        ev = {
            "ts": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "node": _node(),
            "app": app,
            "provider": provider,
            "status": int(status),
            "method": method,
            "host": host,
            "path": path,
            "detail": str(detail)[:200],
        }
        p = log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev) + "\n")
    except Exception:  # noqa: BLE001 - best effort by design
        pass


def provider_for(host: str) -> str:
    h = host.lower()
    if "polygon" in h or "massive" in h:
        return "massive"
    if "finviz" in h:
        return "finviz"
    if "stlouisfed" in h:
        return "fred"
    return h or "unknown"


def urlopen(url, *, app: str, provider: str = "auto", **kwargs):
    """``urllib.request.urlopen`` that records a 403 and re-raises the same HTTPError."""
    try:
        return urllib.request.urlopen(url, **kwargs)
    except urllib.error.HTTPError as e:
        if e.code in REPORT_STATUSES:
            full = url.get_full_url() if isinstance(url, urllib.request.Request) else str(url)
            prov = provider_for(urllib.parse.urlsplit(full).hostname or "") if provider == "auto" else provider
            record(app, prov, full, e.code, detail="HTTPError")
        raise


def check_response(resp, *, app: str, provider: str = "auto"):
    """Record a 403 from a ``requests`` response and return the response unchanged."""
    if getattr(resp, "status_code", None) in REPORT_STATUSES:
        prov = provider_for(urllib.parse.urlsplit(resp.url).hostname or "") if provider == "auto" else provider
        record(app, prov, resp.url, resp.status_code, detail=(resp.reason or ""))
    return resp


# ----- reporter -----


def repo_for(app: str) -> str | None:
    best = None
    for prefix, repo in REPO_MAP.items():
        if (app == prefix or app.startswith(prefix + ":")) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, repo)
    return best[1] if best else None


def fingerprint(repo: str, app: str, provider: str, host: str, path: str, status: int) -> str:
    return hashlib.sha1(f"{repo}|{app}|{provider}|{host}|{path}|{status}".encode()).hexdigest()[:12]


def _cursor_path() -> Path:
    return log_path().with_name("report.cursor")


def read_new_events() -> tuple[list[dict], int]:
    p = log_path()
    if not p.exists():
        return [], 0
    try:
        start = int(_cursor_path().read_text().strip())
    except (OSError, ValueError):
        start = 0
    size = p.stat().st_size
    if start > size:  # log rotated/truncated
        start = 0
    events = []
    with open(p, "rb") as fh:
        fh.seek(start)
        data = fh.read()
    end = start
    for line in data.splitlines(keepends=True):
        if not line.endswith(b"\n"):
            break  # partial line being written; take it next run
        end += len(line)
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events, end


def group(events: list[dict]) -> tuple[dict, list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    unmapped = []
    for ev in events:
        if ev.get("status") not in REPORT_STATUSES:
            continue
        repo = repo_for(ev.get("app", ""))
        if not repo:
            unmapped.append(ev)
            continue
        key = (repo, ev["app"], ev["provider"], ev["host"], ev["path"], ev["status"])
        groups[key].append(ev)
    return groups, unmapped


def summarize(evs: list[dict]) -> str:
    ts = sorted(e["ts"] for e in evs)
    nodes = sorted({e["node"] for e in evs})
    details = sorted({e["detail"] for e in evs if e.get("detail")})
    by_day = defaultdict(int)
    for e in evs:
        by_day[e["ts"][:10]] += 1
    days = ", ".join(f"{d}: {n}" for d, n in sorted(by_day.items()))
    return (
        f"- **Occurrences:** {len(evs)} ({days})\n"
        f"- **First / last (UTC):** {ts[0]} / {ts[-1]}\n"
        f"- **Nodes:** {', '.join(nodes)}\n"
        + (f"- **Detail:** {'; '.join(details)}\n" if details else "")
    )


def issue_body(fp: str, key: tuple, evs: list[dict]) -> str:
    repo, app, provider, host, path, status = key
    pname = PROVIDER_NAMES.get(provider, provider)
    return f"""<!-- {LABEL}:{fp} -->
`{app}` received **HTTP {status}** from **{pname}** (`{host}{path}`).

{summarize(evs)}
A 403 from a paid data feed is treated as a bug: either we exceeded the provider's budget (Finviz:
10 requests per 5 s plus an hourly cap, shared by every node), we called an endpoint the plan is not
entitled to (Massive options), or a credential expired.

**Triage**
- [ ] Throttling? Check for concurrent callers and bunched schedules; the fix is spacing, caching or bulk endpoints, not more retries.
- [ ] Entitlement? Stop calling the endpoint, or gate it behind a plan check.
- [ ] Credential? Rotate it per machine; never copy keys between machines.

Fingerprint `{fp}`. New occurrences are added here as comments by `api_errors.py report`.
URLs are logged path-only (query strings, keys and tickers removed).
"""


def _gh(args: list[str], dry: bool, stdin: str | None = None) -> str:
    if dry:
        print("  [dry-run] gh " + " ".join(args))
        return ""
    r = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {r.stderr.strip()[:300]}")
    return r.stdout


def ensure_labels(repo: str, dry: bool) -> None:
    have = set() if dry else set(_gh(["label", "list", "-R", repo, "-L", "200", "--json", "name", "-q", ".[].name"], dry).split())
    for name, color, desc in (("bug", "d73a4a", "Something isn't working"), (LABEL, "b60205", "HTTP 403 from a paid data API")):
        if name not in have:
            _gh(["label", "create", name, "-R", repo, "--color", color, "--description", desc], dry)


def open_issues_by_fp(repo: str, dry: bool) -> dict[str, int]:
    if dry:
        return {}
    out = _gh(["issue", "list", "-R", repo, "--state", "open", "--label", LABEL, "-L", "200", "--json", "number,body"], dry)
    found = {}
    for it in json.loads(out or "[]"):
        m = re.search(rf"<!-- {LABEL}:([0-9a-f]{{12}}) -->", it.get("body") or "")
        if m:
            found[m.group(1)] = it["number"]
    return found


def report(dry: bool = False) -> int:
    events, end = read_new_events()
    groups, unmapped = group(events)
    print(f"{len(events)} new event(s); {len(groups)} 403 group(s); {len(unmapped)} unmapped")
    for ev in unmapped:
        print(f"  unmapped app {ev.get('app')!r} — add it to REPO_MAP: {ev.get('provider')} {ev.get('host')}{ev.get('path')}")
    failures = 0
    by_repo: dict[str, list] = defaultdict(list)
    for key, evs in groups.items():
        by_repo[key[0]].append((key, evs))
    for repo, items in by_repo.items():
        try:
            ensure_labels(repo, dry)
            existing = open_issues_by_fp(repo, dry)
        except RuntimeError as e:
            print(f"  {repo}: {e}")
            failures += 1
            continue
        for key, evs in items:
            fp = fingerprint(*key)
            _, app, provider, host, path, status = key
            try:
                if fp in existing:
                    n = existing[fp]
                    _gh(["issue", "comment", str(n), "-R", repo, "--body-file", "-"], dry,
                        stdin=f"New occurrences since the last report:\n\n{summarize(evs)}")
                    print(f"  {repo}#{n}: +{len(evs)} occurrence(s) [{fp}]")
                else:
                    title = f"{PROVIDER_NAMES.get(provider, provider)} returned {status} on {path} ({app})"
                    url = _gh(["issue", "create", "-R", repo, "--title", title, "--label", "bug", "--label", LABEL,
                               "--body-file", "-"], dry, stdin=issue_body(fp, key, evs))
                    print(f"  {repo}: opened {url.strip() or title} [{fp}]")
            except RuntimeError as e:
                print(f"  {repo}: {e}")
                failures += 1
    if not dry and failures == 0:
        _cursor_path().parent.mkdir(parents=True, exist_ok=True)
        _cursor_path().write_text(str(end))
    elif failures:
        print(f"{failures} failure(s); cursor not advanced, events will be retried next run")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="file grouped 403s as GitHub issues")
    r.add_argument("--dry-run", action="store_true", help="print gh actions; touch nothing, keep the cursor")
    sub.add_parser("tail", help="print unreported events")
    a = ap.parse_args()
    if a.cmd == "report":
        return report(dry=a.dry_run)
    events, _ = read_new_events()
    for ev in events:
        print(json.dumps(ev))
    return 0


if __name__ == "__main__":
    sys.exit(main())
