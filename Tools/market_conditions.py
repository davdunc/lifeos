#!/usr/bin/env python3
"""Reconstruct market conditions for any past date — for use when studying a chart.

Answers "what was the tape like that day?" from durable sources rather than
from whatever happened to be journaled: daily bars from Polygon, macro series
from FRED as-of the date, plus any local gameplan/review artifacts for that day.

Usage:
    market_conditions.py 2026-07-24 [EXTRA ...] [--json]
    market_conditions.py 2026-07-24 WOLF MXL      # add tickers you're charting

Keys from ~/.claude/.env: POLYGON_API_KEY, FRED_API_KEY.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from api_errors import urlopen as api_urlopen  # records 403s for the api-403 issue workflow
except ImportError:  # imported from outside ~/.claude/Tools
    def api_urlopen(url, *, app, provider="auto", **kw):
        return urllib.request.urlopen(url, **kw)

ENV_FILE = Path.home() / ".claude" / ".env"
TRADING_DIR = Path.home() / ".claude" / "LifeOS" / "USER" / "TRADING"

INDEXES = ["SPY", "QQQ", "IWM"]

# FRED series -> (label, threshold fn returning a regime word)
MACRO = {
    "VIXCLS": ("VIX", lambda v: "TIGHT" if v < 15 else "CALM" if v < 20
               else "ELEVATED" if v < 30 else "SPIKE"),
    "DGS10": ("10Y Treasury", None),
    "DGS2": ("2Y Treasury", None),
    "T10Y2Y": ("10Y-2Y Spread", lambda v: "NORMAL" if v > 0 else "INVERTED"),
    "DGS30": ("30Y Treasury", None),
    "FEDFUNDS": ("Fed Funds (eff)", None),
    "DCOILWTICO": ("WTI Crude", lambda v: "LOW" if v < 80 else "MODERATE" if v <= 100
                   else "ELEVATED"),
    "UMCSENT": ("UMich Sentiment", lambda v: "OK" if v > 75 else "CAUTIOUS" if v >= 60
                else "STRESS"),
    "STLFSI4": ("Financial Stress", lambda v: "LOW" if v < 0 else "MODERATE" if v <= 1
                else "HIGH"),
    "MORTGAGE30US": ("30Y Mortgage", None),
}


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


def get_json(url: str, timeout: int = 30) -> dict:
    return json.loads(api_urlopen(url, app="lifeos-tools:market_conditions", timeout=timeout).read())


def daily_bar(ticker: str, day: str, key: str) -> dict | None:
    """Polygon daily agg for one ticker/date. Returns None on holiday/weekend."""
    url = (f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
           f"{day}/{day}?adjusted=true&apiKey={key}")
    try:
        d = get_json(url)
    except urllib.error.HTTPError as exc:
        print(f"  {ticker}: Polygon HTTP {exc.code}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  {ticker}: {type(exc).__name__}", file=sys.stderr)
        return None
    res = d.get("results") or []
    return res[0] if res else None


def prev_close(ticker: str, day: str, key: str) -> float | None:
    """Walk back up to 6 calendar days to find the prior session's close."""
    d0 = datetime.strptime(day, "%Y-%m-%d").date()
    for back in range(1, 7):
        prev = (d0 - timedelta(days=back)).isoformat()
        bar = daily_bar(ticker, prev, key)
        if bar:
            return bar["c"]
    return None


def fred_asof(series_id: str, day: str, key: str) -> tuple[float, str] | str:
    """Latest observation on or before `day` — i.e. what was known that day.

    Returns (value, as_of) or an error string. Never returns None: a silently
    dropped macro row is indistinguishable from one that doesn't apply.
    """
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}"
           f"&api_key={key}&file_type=json&observation_end={day}"
           f"&sort_order=desc&limit=8")
    last = "unknown"
    for attempt in range(3):
        try:
            d = get_json(url)
        except Exception as exc:
            last = f"{type(exc).__name__}{getattr(exc, 'code', '')}"
            time.sleep(0.4 * (attempt + 1))
            continue
        for o in d.get("observations", []):
            if o["value"] != ".":
                return float(o["value"]), o["date"]
        return "no observation on or before that date"
    return f"FETCH FAILED ({last})"


def local_artifacts(day: str) -> list[str]:
    hits = []
    for pat in (f"GAMEPLAN-{day}.md", f"Reviews/{day}-review.md",
                f"Reviews/{day}-blotter.html"):
        p = TRADING_DIR / pat
        if p.exists():
            hits.append(str(p))
    bl = TRADING_DIR / "Reviews" / f"{day}-blotter"
    if bl.is_dir():
        hits.append(f"{bl}/ ({len(list(bl.glob('*.png')))} charts)")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("day", help="YYYY-MM-DD")
    ap.add_argument("tickers", nargs="*", help="extra tickers you're charting")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        d0 = datetime.strptime(args.day, "%Y-%m-%d").date()
    except ValueError:
        print("date must be YYYY-MM-DD", file=sys.stderr)
        return 2
    if d0 > date.today():
        print("that date is in the future", file=sys.stderr)
        return 2

    load_env()
    pkey = os.environ.get("POLYGON_API_KEY")
    fkey = os.environ.get("FRED_API_KEY")
    if not pkey or not fkey:
        print("POLYGON_API_KEY / FRED_API_KEY missing from ~/.claude/.env",
              file=sys.stderr)
        return 1

    out: dict = {"date": args.day, "weekday": d0.strftime("%A"),
                 "bars": {}, "macro": {}, "artifacts": local_artifacts(args.day)}

    for t in INDEXES + [t.upper() for t in args.tickers]:
        bar = daily_bar(t, args.day, pkey)
        if not bar:
            continue
        pc = prev_close(t, args.day, pkey)
        rng = bar["h"] - bar["l"]
        out["bars"][t] = {
            "open": bar["o"], "high": bar["h"], "low": bar["l"], "close": bar["c"],
            "volume": bar.get("v"), "prev_close": pc,
            "chg_pct": (bar["c"] / pc - 1) * 100 if pc else None,
            "range": rng,
            # where the close sat in the day's range: 1.0 = on the high
            "close_in_range": (bar["c"] - bar["l"]) / rng if rng else None,
        }

    for sid, (label, regime) in MACRO.items():
        got = fred_asof(sid, args.day, fkey)
        if isinstance(got, str):
            out["macro"][label] = {"error": got}
            continue
        val, asof = got
        out["macro"][label] = {"value": val, "as_of": asof,
                               "regime": regime(val) if regime else None}

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    if not out["bars"]:
        print(f"No index bars for {args.day} ({out['weekday']}) — "
              "market holiday or weekend?")
        return 0

    print(f"══ MARKET CONDITIONS — {args.day} ({out['weekday']}) "
          + "═" * 20)
    print(f"{'':<7}{'open':>10}{'high':>10}{'low':>10}{'close':>10}"
          f"{'chg%':>9}{'range':>9}{'cls-in-rng':>12}")
    for t, b in out["bars"].items():
        chg = f"{b['chg_pct']:+.2f}%" if b["chg_pct"] is not None else "n/a"
        cir = f"{b['close_in_range']:.0%}" if b["close_in_range"] is not None else "n/a"
        print(f"{t:<7}{b['open']:>10.2f}{b['high']:>10.2f}{b['low']:>10.2f}"
              f"{b['close']:>10.2f}{chg:>9}{b['range']:>9.2f}{cir:>12}")
    print("\n── Macro as known that day " + "─" * 33)
    for label, m in out["macro"].items():
        if "error" in m:
            print(f"  {label:<18}{'—':>10}   ⚠️  {m['error']}")
            continue
        reg = f"  → {m['regime']}" if m["regime"] else ""
        stale = "" if m["as_of"] == args.day else f"   (as of {m['as_of']})"
        print(f"  {label:<18}{m['value']:>10.3f}{reg}{stale}")
    if out["artifacts"]:
        print("\n── Your artifacts from that day " + "─" * 28)
        for a in out["artifacts"]:
            print(f"  {a}")
    else:
        print("\n  (no local gameplan or review on file for that date)")
    print("\n  close-in-range: 100% = closed on the high, 0% = on the low")
    return 0


if __name__ == "__main__":
    sys.exit(main())
