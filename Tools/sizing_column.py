#!/usr/bin/env python3
"""Compute the gameplan watchlist's `Max sh @1R` column.

Answers, before the open, the question that otherwise gets answered badly at 08:31:
how many shares can I hold and still place a stop that survives this instrument's noise?

    max_shares = R_VALUE / (MIN_STOP_ATR * premarket ATR14)

Both constants come from the PREFERENCES R-CONFIG. A name yielding under MIN_SHARES
at the LIVE risk unit is not a watchlist candidate at all -- it is flagged UNTRADEABLE
so it never reaches the board, rather than being demoted after a chart looks good.

Usage:
    sizing_column.py MRVL NOW CRM PLTR            # markdown rows for the plan
    sizing_column.py --table MRVL NOW             # full diagnostic table
    sizing_column.py --date 2026-08-28 --cutoff 09:15 MRVL   # replay a past session

Exit: 0 all names viable, 1 at least one UNTRADEABLE or lacking data.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from api_errors import urlopen as api_urlopen  # records 403s for the api-403 issue workflow
except ImportError:  # imported from outside ~/.claude/Tools
    def api_urlopen(url, *, app, provider="auto", **kw):
        return urllib.request.urlopen(url, **kw)

PREFS = Path.home() / ".claude/LifeOS/USER/SKILLCUSTOMIZATIONS/Trading/PREFERENCES.md"
ENV = Path.home() / ".claude/.env"
ET = ZoneInfo("America/New_York")
MIN_SHARES = 10  # below this at LIVE R, the risk unit cannot express the trade


def env(key: str) -> str | None:
    if key in os.environ:
        return os.environ[key]
    if not ENV.exists():
        return None
    for line in ENV.read_text().splitlines():
        line = line.strip().removeprefix("export ")
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].split("  #")[0].strip().strip("'\"")
    return None


def config() -> tuple[dict[str, float], float]:
    """R per account and MIN_STOP_ATR, parsed from PREFERENCES. Never duplicated here."""
    if not PREFS.exists():
        sys.exit(f"ERROR: PREFERENCES not found at {PREFS}")
    text = PREFS.read_text()
    r: dict[str, float] = {}
    for line in text.splitlines():
        if not line.startswith("|") or "**" not in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        m = re.search(r"\((\w+)\)", cells[0])
        if not m:
            continue
        label = "LIVE" if "LIVE" in cells[0] else "SIM" if "SIM" in cells[0] else None
        if not label:
            continue
        try:
            r[label] = float(cells[1].replace("*", "").replace("$", "").replace(",", ""))
        except (IndexError, ValueError):
            continue
    m = re.search(r"`MIN_STOP_ATR`\s*\|\s*\*\*([\d.]+)\*\*", text)
    if not r or not m:
        sys.exit("ERROR: could not parse R_VALUE / MIN_STOP_ATR from PREFERENCES")
    return r, float(m.group(1))


def premarket_atr(sym: str, date: str, cutoff: str, key: str, n: int = 14) -> tuple[float | None, int]:
    """ATR over 5-minute bars up to `cutoff` ET. Returns (atr, bars_used)."""
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/5/minute/{date}/{date}"
           f"?adjusted=true&sort=asc&limit=5000&apiKey={key}")
    try:
        with api_urlopen(url, app="lifeos-tools:sizing_column", timeout=30) as fh:
            rs = json.load(fh).get("results", [])
    except Exception:
        return None, 0
    rs = [r for r in rs
          if datetime.fromtimestamp(r["t"] / 1000, ET).strftime("%H:%M") <= cutoff]
    if len(rs) < n + 1:
        return None, len(rs)
    w = rs[-(n + 1):]
    trs = [max(w[i]["h"] - w[i]["l"], abs(w[i]["h"] - w[i - 1]["c"]), abs(w[i]["l"] - w[i - 1]["c"]))
           for i in range(1, len(w))]
    return sum(trs) / len(trs), len(rs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--date", default=datetime.now(ET).strftime("%Y-%m-%d"))
    ap.add_argument("--cutoff", default=datetime.now(ET).strftime("%H:%M"),
                    help="ET clock time to measure up to (default: now)")
    ap.add_argument("--table", action="store_true", help="diagnostic table instead of plan rows")
    args = ap.parse_args()

    key = env("POLYGON_API_KEY")
    if not key:
        sys.exit("ERROR: POLYGON_API_KEY not set. Without ATR there is no honest size.")
    r_values, min_atr = config()
    live_r, sim_r = r_values.get("LIVE", 0.0), r_values.get("SIM", 0.0)

    rows, bad = [], False
    for sym in [t.upper() for t in args.tickers]:
        atr, bars = premarket_atr(sym, args.date, args.cutoff, key)
        if not atr:
            rows.append({"sym": sym, "atr": None, "bars": bars})
            bad = True
            continue
        stop = min_atr * atr
        live, sim = int(live_r // stop), int(sim_r // stop)
        if live < MIN_SHARES:
            bad = True
        rows.append({"sym": sym, "atr": atr, "stop": stop, "live": live, "sim": sim,
                     "verdict": "UNTRADEABLE" if live < MIN_SHARES else
                                ("thin" if live < 15 else "ok")})

    if args.table:
        print(f"  ATR from 5-min bars to {args.cutoff} ET on {args.date} · "
              f"stop = {min_atr}×ATR · LIVE 1R ${live_r:.0f} · SIM 1R ${sim_r:.0f}\n")
        print(f"  {'Ticker':8}{'ATR':>8}{'stop':>8}{'LIVE sh':>9}{'SIM sh':>8}   verdict")
        for r in rows:
            if r["atr"] is None:
                print(f"  {r['sym']:8}{'—':>8}{'—':>8}{'—':>9}{'—':>8}   NO DATA ({r['bars']} bars)")
            else:
                print(f"  {r['sym']:8}{r['atr']:>8.3f}{r['stop']:>8.2f}"
                      f"{r['live']:>9}{r['sim']:>8}   {r['verdict']}")
        if bad:
            print(f"\n  UNTRADEABLE / NO DATA names do not go on the board. At LIVE 1R the risk")
            print(f"  unit cannot express them, however clean the setup looks.")
    else:
        # Markdown fragment, ready to paste into the watchlist table.
        for r in rows:
            if r["atr"] is None:
                print(f"| **{r['sym']}** | — | — | — | **NO PREMARKET DATA — off the board** | — |")
            elif r["verdict"] == "UNTRADEABLE":
                print(f"| **{r['sym']}** | — | — | **{r['live']}** | "
                      f"**UNTRADEABLE at 1R — off the board** | — |")
            else:
                print(f"| **{r['sym']}** |  |  | **{r['live']}** (SIM {r['sim']}) |  |  |")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
