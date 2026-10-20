---
description: Five-check slow-day protocol for quiet sessions and mid-session resets — prioritize instead of forcing setups
---

# SlowDayChecklist Workflow

Run when the session is quiet and the normal news-driven checklist has nothing to say:
muted volatility, almost no fresh news, a gap into the middle of the prior session's range,
the big idea not playing out — or mid-session, when the published thesis has gone quiet and
the process needs a restart. Source: Roberto's slow-day checklist, inspired by
*The Checklist Manifesto*.

**A slow day is NOT automatically a no-trade day.** The checklist is a prioritization pass;
its output can still be a full seven-section game plan. Collapse sections 3–5 into POSTURE
only when the qualification process itself warrants it (see the no-trade-days rule in
`Workflows/MorningGamePlan.md`).

## The five checks — run in order

Run them slowly and in order at first; with repetition, all five in seconds.

### 1. Big Picture

- [ ] Where is the market relative to its most important support and resistance? Always
  start here — it is the context every later check is read against.
- [ ] Locate the gap versus the prior session's range (a middle-of-range gap into a quiet
  tape is the slow-day signature).
- [ ] State whether the original thesis is still playing out: INTACT / NOT PLAYING OUT /
  UNCLEAR.

Evidence: `tradekit regime --json` (completed-session dimensions — pre-session context, not
a live read) plus the §2 index sub-table pivots.

### 2. Sector ETFs

- [ ] Which sector ETFs are gapping into levels that matter, and which are just drifting?
  Gaps into support or resistance show where other participants will need to act faster.
- [ ] For each ETF, state explicitly: INTO A LEVEL (name the level) or DRIFTING.

Evidence: `tradekit groups` ranks sector/industry rotation with RVol — it does NOT give ETF
price levels. Levels come from the operator's charts (DAS). A level not actually pulled is
written UNAVAILABLE with its reason, never guessed.

### 3. Catalysts

- [ ] Fresh news, upgrades or rating changes, scheduled events — per name and per sector.
- [ ] Note which candidates have a fresh catalyst and which do not. Absence of a catalyst
  does not disqualify a slow-day name; the other checks carry the ranking.
- [ ] The video intel layer is still mandatory context: automated newsfeeds returning zero
  items is absence of coverage, not absence of news (see the MorningGamePlan video-intel
  hard rule).

### 4. Elevated premarket volume

- [ ] Premarket dollar volume = premarket VWAP × premarket shares traded, per candidate.
- [ ] Compare to prior days and to other names, then prioritize what is really moving.

tradekit does not compute premarket VWAP — pull VWAP and shares from the platform (DAS),
compute the product, and write UNAVAILABLE with the reason where premarket data is missing.
Never fabricate or extrapolate the figure.

### 5. Relative strength / weakness

- [ ] At the open, switch from execution mindset to scanning mindset.
- [ ] Names holding bid while others roll over are telling you they are In Play. Let the
  market show you.
- [ ] Premarket relative strength is a PENDING observation until the open confirms it —
  the check produces candidates to watch, not a completed read.

## Risk rules (Roberto's guidance — attributed, not validated gates)

- **C-size risk** on these ideas. C-size comes from the approved R-CONFIG definition in
  PREFERENCES.md; do not invent a fraction. If absent, write C-size UNDEFINED and derive no
  risk or share count. A C-risk trade can still become an A outcome (AMZN 4:1 review example).
- **RVOL target 1.5+**; most traders lose the most money at 0.8 or less. The note does not
  define the RVOL calculation — compute it on the platform and name the lookback used.

## Output — re-scopes the game plan skeleton, never adds sections

The seven-section skeleton and fixed watchlist columns are unchanged. The checklist's
results land inside the existing sections:

| Section | What the slow-day run puts there |
|---|---|
| **2 MACRO** | An ordered five-check summary — one line per check, each with its verdict/evidence — under the regime block |
| **3 THESIS TRADE** | `WAIT — scanning for relative strength/weakness` is a valid entry; do not manufacture a premarket thesis |
| **4 WATCHLIST** | Candidates surfaced by checks 2–5, same fixed columns, same gates — R-viability first, then the movement gate |
| **6 RULES** | The C-size + RVOL guidance fits inside the existing 3-bullet cap — it does not add bullets |

## Mid-session reset

When the thesis is not playing out, restart from check 1 — the note's example time is
11:30 AM, an illustration, not a schedule. A reset:

- never resurrects expired triggers — Kill Times stand;
- never bypasses the R-viability or playbook gates;
- produces an updated board, not a reversal authorization.
