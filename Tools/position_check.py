#!/usr/bin/env python3
"""Flag positions too large for a 1R-compliant stop to survive the instrument's noise.

RISK IS NOT NOTIONAL. Notional (shares x price) is the cost of the position and says
nothing about risk. Risk is shares x stop_distance, and the stop distance is set by the
instrument's volatility, not by its price.

    max_shares = R_VALUE / (MIN_STOP_ATR * ATR14_at_trade_time)

MIN_STOP_ATR is the tightest stop worth placing, in ATR units. Below roughly 1.5 ATR a
stop is taken out by ordinary noise rather than by the thesis being wrong.

Supersedes notional_check.py (2026-08-28), which used a notional band and was wrong: price
and ATR only correlate on megacaps. On a $5 name with a 0.30 ATR, a $7,500 notional band
permits 1,500 shares = 9.0R in a single position -- three times the daily max, in exactly
the low-priced high-volatility setups the playbook targets.

R_VALUE and MIN_STOP_ATR are read from the PREFERENCES R-CONFIG, never hard-coded here.

Usage:
    position_check.py <trades.csv> [--date YYYY-MM-DD] [--json]

Exit: 0 all sized so a 1.5-ATR stop costs <=1R, 1 marginal (<=1.25x), 2 oversized.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
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


def load_env(key: str) -> str | None:
    if key in os.environ:
        return os.environ[key]
    if not ENV.exists():
        return None
    for line in ENV.read_text().splitlines():
        line = line.strip().removeprefix("export ")
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].split("  #")[0].strip().strip("'\"")
    return None


def load_rconfig() -> tuple[dict[str, float], float]:
    """R per account, plus MIN_STOP_ATR. Parsed from PREFERENCES -- never duplicated here."""
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
        try:
            r[m.group(1)] = float(cells[1].replace("*", "").replace("$", "").replace(",", ""))
        except (IndexError, ValueError):
            continue
    m = re.search(r"`MIN_STOP_ATR`\s*\|\s*\*\*([\d.]+)\*\*", text)
    if not r:
        sys.exit("ERROR: could not parse R_VALUE from the R-CONFIG table")
    if not m:
        sys.exit("ERROR: MIN_STOP_ATR not found in PREFERENCES -- add it to the shared table")
    return r, float(m.group(1))


def atr_at(sym: str, date: str, end: datetime, key: str, n: int = 14) -> float | None:
    """ATR over the n 1-minute bars ending at the position's own timestamp.

    Measured at trade time, never end-of-day: a chart opened in the evening reports ATR
    from the last bar in its dataset (often post-market), which is far quieter than the
    open. That mismatch is a reporting artifact, not a bad indicator.
    """
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/minute/{date}/{date}"
           f"?adjusted=true&sort=asc&limit=50000&apiKey={key}")
    try:
        with api_urlopen(url, app="lifeos-tools:position_check", timeout=30) as fh:
            rs = json.load(fh).get("results", [])
    except Exception:
        return None
    rs = [r for r in rs if datetime.fromtimestamp(r["t"] / 1000, ET) <= end]
    if len(rs) < n + 1:
        return None
    w = rs[-(n + 1):]
    trs = [max(w[i]["h"] - w[i]["l"], abs(w[i]["h"] - w[i - 1]["c"]), abs(w[i]["l"] - w[i - 1]["c"]))
           for i in range(1, len(w))]
    return sum(trs) / len(trs)


def peaks(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open()))
    for r in rows:
        r["qty"] = int(r["qty"])
        r["price"] = float(r["price"])
        r["t"] = datetime.strptime(r["time"].strip(), "%m/%d/%y %H:%M:%S").replace(tzinfo=ET)
    rows.sort(key=lambda r: r["t"])
    held: dict[tuple[str, str], int] = defaultdict(int)
    peak: dict[tuple[str, str], dict] = {}
    for r in rows:
        k = (r["Account"], r["symb"])
        held[k] += r["qty"] if r["B/S"] == "B" else -r["qty"]
        if abs(held[k]) > peak.get(k, {}).get("shares", 0):
            peak[k] = {"account": r["Account"], "symbol": r["symb"],
                       "shares": abs(held[k]), "price": r["price"], "at": r["t"]}
    return sorted(peak.values(), key=lambda d: -d["shares"] * d["price"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trades", type=Path)
    ap.add_argument("--date", help="YYYY-MM-DD (default: inferred from the fills)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.trades.exists():
        sys.exit(f"ERROR: {args.trades} not found")

    key = load_env("POLYGON_API_KEY")
    if not key:
        sys.exit("ERROR: POLYGON_API_KEY not set -- ATR cannot be measured, so the check "
                 "cannot run. It is not safe to fall back to a notional proxy.")
    rcfg, min_atr = load_rconfig()

    findings, worst = [], 0
    for p in peaks(args.trades):
        R = rcfg.get(p["account"])
        if not R:
            continue
        date = args.date or p["at"].strftime("%Y-%m-%d")
        atr = atr_at(p["symbol"], date, p["at"], key)
        if not atr:
            findings.append({**p, "at": p["at"].strftime("%H:%M:%S"), "band": "no-data"})
            continue
        stop = min_atr * atr
        max_sh = R / stop
        ratio = p["shares"] / max_sh
        risk_R = p["shares"] * stop / R
        band = "OVERSIZED" if ratio > 1.25 else "marginal" if ratio > 1.0 else "ok"
        worst = max(worst, {"ok": 0, "marginal": 1, "OVERSIZED": 2}[band])
        findings.append({**p, "at": p["at"].strftime("%H:%M:%S"), "atr": atr, "stop": stop,
                         "max_shares": max_sh, "ratio": ratio, "risk_R": risk_R, "band": band})

    if args.json:
        print(json.dumps({"worst": worst, "min_stop_atr": min_atr, "findings": findings},
                         indent=2, default=str))
        return worst

    print(f"══ POSITION CHECK ── {args.trades.parent.name} ══════════════════")
    print(f"   max_shares = 1R / ({min_atr} x ATR at trade time).  Risk, not notional.\n")
    print(f"{'':3}{'acct':10}{'sym':7}{'held':>6}{'ATR':>8}{'stop':>8}{'max sh':>8}{'over':>7}{'risk':>8}   band")
    for f in findings:
        if f["band"] == "no-data":
            print(f"   {f['account']:10}{f['symbol']:7}{f['shares']:>6}{'':>39}   no bars")
            continue
        mark = {"ok": "   ", "marginal": " ! ", "OVERSIZED": "!! "}[f["band"]]
        print(f"{mark}{f['account']:10}{f['symbol']:7}{f['shares']:>6}{f['atr']:>8.3f}"
              f"{f['stop']:>8.2f}{f['max_shares']:>8.0f}{f['ratio']:>6.1f}x{f['risk_R']:>7.1f}R   {f['band']}")
    if worst == 2:
        print("\n  OVERSIZED: a 1R-compliant stop would sit inside the noise band, so the")
        print("  per-symbol cap cannot be honored at this size. Reduce shares -- telling the")
        print("  operator to 'honor stops' does not fix an arithmetic problem.")
    elif worst == 1:
        print("\n  Marginal: at or just over the ATR-implied limit. Review.")
    else:
        print("\n  All positions sized so a placeable stop costs <= 1R.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
