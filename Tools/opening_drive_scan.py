#!/usr/bin/env python3
"""
Opening-drive scan — the 10:00 ET refresh the premarket scan cannot do.

Why this exists: on 2026-08-31 the premarket scan surfaced 8 A-tier names and only
ONE (WETO) appeared in the day's actual top-8 by intraday range. The names that ran
were not gapping at 08:00; they were made by the opening auction. Ranking by
premarket gap answers "what gapped", not "what is being repriced right now".

Ranks by first-30-minute volume against PRIOR FULL DAY volume. On 08-31 that ratio
put RDHL at 522x, MOVE at 29x and MOBX at 10x — all three delivered 19-43% of range
AFTER 10:00 ET, i.e. still tradeable when the scan runs.

Usage:
  opening_drive_scan.py                 # today, ranks the 09:30-10:00 drive
  opening_drive_scan.py --date 2026-08-31 --min-ratio 3
"""
import argparse, datetime as dt, os, sys
from zoneinfo import ZoneInfo
import requests

try:
    from api_errors import check_response  # records 403s for the api-403 issue workflow
except ImportError:  # imported from outside ~/.claude/Tools
    def check_response(resp, *, app, provider="auto"):
        return resp

ET = ZoneInfo("America/New_York")

def api_key() -> str:
    for line in open(os.path.expanduser("~/.claude/.env")):
        if line.startswith("POLYGON_API_KEY="):
            return line.strip().split("=", 1)[1]
    sys.exit("POLYGON_API_KEY not in ~/.claude/.env")

def prev_session(k: str, day: dt.date) -> dt.date:
    d = day - dt.timedelta(days=1)
    while d.weekday() > 4:
        d -= dt.timedelta(days=1)
    return d

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.datetime.now(ET).date().isoformat())
    ap.add_argument("--min-ratio", type=float, default=2.0,
                    help="first-30-min volume / prior full-day volume")
    ap.add_argument("--min-vol", type=float, default=200_000,
                    help="minimum first-30-min shares; below this it is not tradeable")
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--min-prior-vol", type=float, default=20_000,
                    help="prior-session volume floor. Without this, SPACs and new "
                         "listings with ~0 prior volume produce infinite RVOL and "
                         "crowd out the real movers — they are illiquid, not moving.")
    ap.add_argument("--min-range", type=float, default=8.0,
                    help="minimum intraday range pct. Volume without range is a "
                         "block print, not a tradeable move.")
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    k = api_key()
    day = dt.date.fromisoformat(a.date)
    prev = prev_session(k, day)

    g = check_response(requests.get(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{prev}"
                     f"?adjusted=true&apiKey={k}", timeout=60), app="lifeos-tools:opening_drive_scan").json().get("results", [])
    prior = {b["T"]: b.get("v", 0) for b in g}

    today = check_response(requests.get(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{day}"
                         f"?adjusted=true&apiKey={k}", timeout=60), app="lifeos-tools:opening_drive_scan").json().get("results", [])
    if not today:
        print(f"No grouped bars for {day} yet — the scan needs the session to be open.")
        return 1

    rows = []
    for b in today:
        t, o, c, v = b["T"], b.get("o"), b.get("c"), b.get("v", 0)
        if not o or o < a.min_price or v < a.min_vol:
            continue
        pv = prior.get(t, 0)
        if pv < a.min_prior_vol:
            continue
        rng = (b["h"] - b["l"]) / o * 100
        if rng < a.min_range:
            continue
        ratio = v / pv
        if ratio < a.min_ratio:
            continue
        rows.append((t, o, c, v, pv, ratio, rng))
    rows.sort(key=lambda r: -r[5])

    print(f"\n══ OPENING-DRIVE SCAN — {day} ══")
    print(f"   volume vs prior session, min ratio {a.min_ratio}x, min {a.min_vol:,.0f} shares\n")
    print(f"{'SYM':<8}{'PRICE':>9}{'RANGE%':>8}{'VOL':>13}{'PRIOR VOL':>13}{'RVOL':>9}")
    for t, o, c, v, pv, ratio, rng in rows[:a.limit]:
        r = f"{ratio:.1f}x"
        print(f"{t:<8}{c:>9.2f}{rng:>8.1f}{v:>13,.0f}{pv:>13,.0f}{r:>9}")
    print(f"\n   {len(rows)} names cleared the filter.")
    print("   Confirm on live DAS before acting — Polygon lags ~15 min.")
    print("   These are NOT premarket gappers; they are names the auction is repricing now.\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
