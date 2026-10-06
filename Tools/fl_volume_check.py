#!/usr/bin/env python3
"""Fashionably Late entry gate — the 50/2 volume-persistence check.

Answers, in the 60 seconds after an FL entry candle closes: does this move have
supply behind it, or was the spike the whole story?

    fl_volume_check.py LGCL                 # live, evaluate the last closed bar
    fl_volume_check.py LGCL --entry 09:53   # live, evaluate a specific entry bar
    fl_volume_check.py LGCL --date 2026-09-01 --entry 09:53   # replay a past session

Three gates, in the order that can disqualify soonest:

  1. REVERSE SPLIT   any split inside 5 sessions -> hard FAIL. These names have no
                     volume base for FL, and their ATR is unusable for sizing.
  2. SPIKE           V0 must be >= 2x the average of the preceding bars.
  3. PERSISTENCE     each of the next two bars must print >= 50 pct of V0.

Live data comes from DAS (fl_shared.fetch_das_bars). Polygon lags ~15 minutes, which
is useless while a position is open, so it is used only for --date replay.

Exit: 0 PASS, 1 FAIL, 2 PENDING (bars not closed yet), 3 no data.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, urllib.request
from zoneinfo import ZoneInfo

try:
    from api_errors import urlopen as api_urlopen  # records 403s for the api-403 issue workflow
except ImportError:  # imported from outside ~/.claude/Tools
    def api_urlopen(url, *, app, provider="auto", **kw):
        return urllib.request.urlopen(url, **kw)

sys.path.insert(0, os.path.expanduser("~/falcon/dashboard"))
ET = ZoneInfo("America/New_York")

SPIKE_MULT   = 2.0   # V0 vs the preceding-bar average
LOOKBACK     = 4     # bars averaged for the spike test
PERSIST_FRAC = 0.50  # each follow bar must hold this fraction of V0
PERSIST_BARS = 2     # how many bars must hold it
SPLIT_WINDOW = 5     # sessions


def _polygon_key() -> str:
    for line in open(os.path.expanduser("~/.claude/.env")):
        if line.startswith("POLYGON_API_KEY"):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("POLYGON_API_KEY not found in ~/.claude/.env")


def recent_split(ticker: str) -> dict | None:
    """A reverse split inside SPLIT_WINDOW sessions disqualifies the setup outright.

    This is checked first and cheaply because it also invalidates the ATR the sizing
    tool would hand back -- LGCL computed an ATR14 of 24.327 on a $4.69 stock the
    morning it split 1-for-125, and sizing_column.py reported that without complaint.
    """
    url = (f"https://api.polygon.io/v3/reference/splits?ticker={ticker}"
           f"&limit=10&apiKey={_polygon_key()}")
    try:
        res = json.load(api_urlopen(url, app="lifeos-tools:fl_volume_check", timeout=15)).get("results", [])
    except Exception as exc:                      # a lookup failure must not read as "clean"
        return {"error": str(exc)}
    today = dt.datetime.now(ET).date()
    for s in res:
        try:
            ex = dt.date.fromisoformat(s["execution_date"])
        except (KeyError, ValueError):
            continue
        # Calendar days, not trading days: deliberately conservative at the boundary.
        if 0 <= (today - ex).days <= SPLIT_WINDOW * 2:
            return s
    return None


def das_bars(sym: str) -> list[dict]:
    """Live 1-minute bars from DAS, reusing fl_shared's MINCHART client.

    fl_shared resolved the host wrongly until 2026-09-01 (default route instead of
    DAS_HOST/loopback, and no inline-comment stripping in _load_env), so every call
    returned [] and read as "no bars" rather than "no connection." Both are fixed in
    fl_shared itself; this deliberately does not re-override HOST, so a future
    regression there surfaces here instead of being papered over.
    """
    from fl_shared import fetch_das_bars
    return fetch_das_bars(sym)


def polygon_bars(sym: str, date: str) -> list[dict]:
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/minute/{date}/{date}"
           f"?adjusted=true&sort=asc&limit=5000&apiKey={_polygon_key()}")
    out = []
    for b in json.load(api_urlopen(url, app="lifeos-tools:fl_volume_check", timeout=25)).get("results", []):
        t = dt.datetime.fromtimestamp(b["t"] / 1000, tz=dt.timezone.utc).astimezone(ET)
        out.append({"ts": t.strftime("%H:%M"), "o": b["o"], "h": b["h"],
                    "l": b["l"], "c": b["c"], "v": float(b["v"])})
    return out


def bar_hhmm(b: dict) -> str:
    """DAS stamps bars as 'YYYY/MM/DD-HH:MM'; Polygon rows are already 'HH:MM'."""
    ts = str(b.get("ts", ""))
    return ts.split("-")[-1][:5] if "-" in ts else ts[:5]


def main() -> int:
    ap = argparse.ArgumentParser(description="FL 50/2 volume-persistence gate")
    ap.add_argument("ticker")
    ap.add_argument("--entry", help="entry bar as HH:MM ET; default = last closed bar")
    ap.add_argument("--date", help="replay a past session (YYYY-MM-DD) via Polygon")
    ap.add_argument("--frac", type=float, default=PERSIST_FRAC,
                    help="fraction of V0 each follow bar must hold (default 0.50)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    sym = a.ticker.upper()

    bars = polygon_bars(sym, a.date) if a.date else das_bars(sym)
    if not bars:
        print(f"{sym}: no bars returned from {'Polygon' if a.date else 'DAS'}")
        return 3

    if a.entry:
        want = a.entry[:5]
        idx = next((i for i, b in enumerate(bars) if bar_hhmm(b) == want), None)
        if idx is None:
            print(f"{sym}: no bar at {want}. Range: {bar_hhmm(bars[0])}-{bar_hhmm(bars[-1])}")
            return 3
    else:
        idx = len(bars) - 1

    entry = bars[idx]
    v0 = entry["v"]
    prior = bars[max(0, idx - LOOKBACK):idx]
    avg = sum(b["v"] for b in prior) / len(prior) if prior else 0.0
    follows = bars[idx + 1: idx + 1 + PERSIST_BARS]
    floor = a.frac * v0

    split = recent_split(sym)
    print(f"\n  FL gate — {sym}  entry bar {bar_hhmm(entry)} ET  "
          f"({'replay ' + a.date if a.date else 'LIVE via DAS'})\n")

    fail = False
    if split and "error" in split:
        print(f"  1. SPLIT       ?  lookup failed ({split['error']}) — verify manually")
    elif split:
        print(f"  1. SPLIT      NO  {split['split_from']}-for-{split['split_to']} on "
              f"{split['execution_date']}  ->  DISQUALIFIED")
        print("                    no volume base for FL, and the ATR is unusable for sizing")
        fail = True
    else:
        print(f"  1. SPLIT      OK  none within {SPLIT_WINDOW} sessions")

    ratio = v0 / avg if avg else 0.0
    spike_ok = ratio >= SPIKE_MULT
    print(f"  2. SPIKE      {'OK' if spike_ok else 'NO'}  V0 {v0:,.0f} vs {LOOKBACK}-bar avg "
          f"{avg:,.0f}  =  {ratio:.2f}x   (need {SPIKE_MULT:.1f}x)")

    pending = persist_fail = False
    print(f"  3. PERSIST        each of next {PERSIST_BARS} bars needs "
          f">= {floor:,.0f}  ({a.frac:.0%} of V0)")
    for n in range(PERSIST_BARS):
        if n < len(follows):
            b = follows[n]
            good = b["v"] >= floor
            pct = b["v"] / v0 if v0 else 0
            print(f"                {'OK' if good else 'NO'}  bar+{n+1} {bar_hhmm(b)}  "
                  f"{b['v']:,.0f}  =  {pct:.0%} of V0")
            if not good:
                persist_fail = True
        else:
            # Not yet closed. This is the whole reason the tool exists at the desk:
            # reporting PASS here would greenlight a trade on evidence that does not
            # exist yet, which is the same error as reading the spike alone.
            print(f"                --  bar+{n+1} has not closed yet")
            pending = True

    # These three failures call for three different actions, so they must not share
    # one message. Telling the desk to "exit now" on a bar that was never a valid entry
    # is as wrong as telling it to hold one that was.
    if fail:                       # split disqualifier
        print(f"\n  ==> DISQUALIFIED. Not an FL candidate at all — wrong instrument.")
        print(f"      Do not size this off sizing_column.py either; the ATR is poisoned.\n")
        rc = 1
    elif not spike_ok:
        print(f"\n  ==> NO SETUP. This bar never met the spike condition, so there is no")
        print(f"      FL entry here to manage. If you are in, you are in on something else.\n")
        rc = 1
    elif persist_fail:
        print(f"\n  ==> FAIL. Supply did not hold. Exit at this bar's close, and do not")
        print(f"      re-enter on the same signal — a re-entry is a fresh setup needing a")
        print(f"      fresh V0 measured from the bar you re-enter on.\n")
        rc = 1
    elif pending:
        print(f"\n  ==> PENDING — {PERSIST_BARS - len(follows)} bar(s) still open. "
              f"Re-run in 60s. Do not treat this as a pass.\n")
        rc = 2
    else:
        print(f"\n  ==> PASS. Supply held for {PERSIST_BARS} bars.\n")
        rc = 0

    if a.json:
        print(json.dumps({"ticker": sym, "entry_bar": bar_hhmm(entry), "v0": v0,
                          "spike_ratio": round(ratio, 2), "floor": floor,
                          "follows": [{"ts": bar_hhmm(b), "v": b["v"]} for b in follows],
                          "split": split, "result": ["PASS", "FAIL", "PENDING"][rc]}))
    return rc


if __name__ == "__main__":
    sys.exit(main())
