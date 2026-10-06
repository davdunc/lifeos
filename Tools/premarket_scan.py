#!/usr/bin/env python3
"""Premarket inefficiency scan — ranks candidates by EXPECTED RANGE, not direction.

Built 2026-07-28 from a study of 66,071 ticker-days across 23 sessions
(2026-06-24 .. 2026-07-27), same filters as below.

What the study found:

  |gap|      names/day   range>5%   range>10%   avg range
  0-1%          1780        18%         3%         3.3%
  2-4%           324        49%        14%         6.2%
  4-8%           112        75%        34%        10.8%
  8-15%           27        95%        69%        15.8%
  15%+            13        97%        87%        33.3%

  gap>=8% + prior-day range>=8%   ->  86% deliver >10% range
  gap>=8% + prior-day range<8%    ->  50%
  gap 4-8% + prior-day range>=8%  ->  63%
  gap <4%  + prior-day range>=15% ->  71%

What it did NOT find: any directional edge. Every gap bucket came in at
44-55% continuation. Gap magnitude tells you HOW MUCH a name will move.
It tells you NOTHING about which way. Use this to pick where to look;
use intraday structure to pick a side.

Usage:
    premarket_scan.py                 # top candidates
    premarket_scan.py --min-gap 4     # widen the net
    premarket_scan.py --json

Polygon data is delayed ~15 min on this plan — fine for building a candidate
list an hour before the open, NOT for timing an entry. Confirm the shortlist
on live DAS with das_quote.py before committing to a level.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    from api_errors import urlopen as api_urlopen  # records 403s for the api-403 issue workflow
except ImportError:  # imported from outside ~/.claude/Tools
    def api_urlopen(url, *, app, provider="auto", **kw):
        return urllib.request.urlopen(url, **kw)

ENV_FILE = Path.home() / ".claude" / ".env"
SNAPSHOT = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip().removeprefix("export "),
                              v.split("  #")[0].strip().strip("'\""))


def account_band(price: float) -> str:
    if price < 3:
        return "below"
    if price <= 50:
        return "sweet"
    if price <= 400:
        return "A+only"
    return "EXCLUDED"


def tier(gap: float, prev_rng: float) -> tuple[str, int, str]:
    """(label, expected % delivering >10% range, sort key)"""
    a = abs(gap)
    if a >= 8 and prev_rng >= 8:
        return ("A", 86, "gap>=8 + prior>=8")
    if a >= 8:
        return ("B", 50, "gap>=8, prior<8")
    if a >= 4 and prev_rng >= 8:
        return ("C", 63, "gap 4-8 + prior>=8")
    if a < 4 and prev_rng >= 15:
        return ("D", 71, "quiet gap, wild prior day")
    return ("-", 0, "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-gap", type=float, default=4.0,
                    help="minimum |gap| %% to consider (default 4)")
    ap.add_argument("--min-prev-vol", type=float, default=500_000)
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    load_env()
    key = os.environ.get("POLYGON_API_KEY")
    if not key:
        print("POLYGON_API_KEY missing from ~/.claude/.env", file=sys.stderr)
        return 1

    try:
        d = json.loads(api_urlopen(f"{SNAPSHOT}?apiKey={key}", app="lifeos-tools:premarket_scan",
                                              timeout=120).read())
    except Exception as exc:
        print(f"Polygon snapshot failed ({type(exc).__name__})", file=sys.stderr)
        return 1

    rows = []
    for t in d.get("tickers", []):
        prev = t.get("prevDay") or {}
        pc, pv = prev.get("c", 0), prev.get("v", 0)
        ph, pl, po = prev.get("h", 0), prev.get("l", 0), prev.get("o", 0)
        last = (t.get("lastTrade") or {}).get("p") or (t.get("min") or {}).get("c") or 0
        if not pc or not last or pv < args.min_prev_vol or not po:
            continue
        if not (3 <= last <= 400):
            continue
        gap = (last / pc - 1) * 100
        prev_rng = (ph - pl) / po * 100 if po else 0
        lbl, expect, why = tier(gap, prev_rng)
        if lbl == "-" or abs(gap) < args.min_gap:
            continue
        rows.append(dict(sym=t.get("ticker"), last=last, gap=gap, prev_close=pc,
                         prev_high=ph, prev_low=pl, prev_rng=prev_rng,
                         prev_vol=pv, pm_vol=(t.get("min") or {}).get("v", 0),
                         tier=lbl, expect=expect, why=why,
                         band=account_band(last)))

    order = {"A": 0, "C": 1, "D": 2, "B": 3}
    rows.sort(key=lambda r: (order.get(r["tier"], 9), -abs(r["gap"])))
    rows = rows[:args.limit]

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    if not rows:
        print("No candidates cleared the filters. Market may be quiet, or it is "
              "too early for premarket prints to have populated.")
        return 0

    print("══ PREMARKET INEFFICIENCY SCAN ═══════════════════════════════════════")
    print("   Ranked by EXPECTED RANGE. Direction is a coin flip — see below.\n")
    print(f"{'sym':<7}{'tier':>5}{'last':>9}{'gap':>9}{'prior rng':>11}"
          f"{'>10% odds':>11}{'band':>10}   levels (prior H/L)")
    for r in rows:
        flag = "  <-- excluded by size" if r["band"] == "EXCLUDED" else ""
        print(f"{r['sym']:<7}{r['tier']:>5}{r['last']:>9.2f}{r['gap']:>+8.1f}%"
              f"{r['prev_rng']:>10.1f}%{r['expect']:>10}%{r['band']:>10}   "
              f"{r['prev_high']:.2f} / {r['prev_low']:.2f}{flag}")

    print("\n── tiers ──────────────────────────────────────────────────────────")
    print("  A  gap>=8% + prior-day range>=8%   86% deliver a >10% range")
    print("  D  quiet gap but wild prior day    71%")
    print("  C  gap 4-8% + prior range>=8%      63%")
    print("  B  gap>=8% but calm prior day      50%")
    print("\n⚠️  DIRECTION IS NOT PREDICTED. Across 23 sessions every gap bucket")
    print("   came in at 44-55% continuation. This tells you WHERE the volatility")
    print("   will be, not which way it breaks. Take the level, let the tape pick")
    print("   the side. Confirm the shortlist on live DAS — Polygon lags ~15 min.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
