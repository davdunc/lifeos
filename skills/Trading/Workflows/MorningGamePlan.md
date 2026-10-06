---
description: Build the daily morning game plan with market data, intelligence, and Notion integration
---

# MorningGamePlan Workflow

## ⛔ HARD RULE: Video Intel Layer Is a Prerequisite, Not a Nice-to-Have

**Before Phase 1, pull the prior session's evening videos. If they are missing, say so in the published plan — do not proceed silently.**

```bash
python3 ~/.claude/Tools/video_intel.py                    # prior session, all channels
python3 ~/.claude/Tools/video_intel.py --date 2026-07-27  # explicit date
```

Channels come from `AnalystSources.md` (`**Channel ID:**` lines). Registering a channel there is the only step needed to add it. Transcripts cache to `Intelligence/transcripts/`.

**Why this is a hard rule and not advice:** on 2026-07-27 this workflow ran *without* the evening review, in direct violation of `[[evening-review-before-gameplan]]`. The published thesis was semis-long. Overnight, a Chinese memory maker (CXMT) had debuted +465% in Shanghai and China had begun mass-producing domestic lithography machines — the story that drove a two-day semiconductor unwind. **The Polygon newsfeed returned ZERO items** for every watchlist small cap and zero items market-wide after 08:00 ET on both days. The tape decay was measured correctly and could not be explained, because the only source carrying the catalyst was the video layer.

Automated newsfeeds do not cover this. Treat their silence as absence of coverage, never as absence of news.

The videos also supply **pre-specified levels** worth more than the narrative — e.g. Blue Cloud's Ichimoku triggers (XLF >56.94, XLV >165.60) and StockedUp's breakpoints (TSM <388) all resolved exactly as stated.

**Gotcha:** evening hosts record after the close ET, so a "07/27" recap can carry a UTC published stamp of 07-28. `video_intel.py` handles the rollover; a naive date filter will silently miss the most important video of the day.

## ⛔ HARD RULE: Weekly Readiness Is the Foundation, Not a Parallel Process

**Before Phase 1, check Notion (David Duncan Daily Game Plan database) for a "Weekly Readiness — Week of [Date]" page whose date falls within the current Mon-Fri week.** If found, pull its watchlist, market regime, and discipline commitment into this run's context — the daily plan builds on the week's thesis, it doesn't re-derive it from scratch. If missing, **say so explicitly in the published plan** ("no weekly readiness review found for this week") rather than silently proceeding as if the week had no strategic frame.

Weekly readiness itself is produced by a separate, portable repo — `~/Projects/weekly-readiness`
(https://github.com/davdunc/weekly-readiness) — run manually by David, typically Saturday ~4PM ET.
It is not scheduled and not guaranteed to exist every week; this check exists so a missing one is a
visible gap, not a silent one. See `[[project-weekly-readiness-review]]`.

## ⛔ HARD RULE: Publish is Deterministic

Once Phase 6 (synthesis) completes, **immediately fire Phase 7 (Slack) + Phase 7b (Discord) + Phase 8 (DAS Market Viewer) + Notion Game Plan DB entry in parallel.** Do NOT prompt the user with AskUserQuestion for publish-yes-or-no, channel selection, or send-confirmation. The default IS all four channels. Linked memory: `[[publish-is-deterministic]]`.

**Failures are isolated.** Each channel publishes independently; a Discord webhook error, a Slack timeout, or a Notion 5xx must NOT block the others. Report per-channel status and move on — a partial publish that is *reported as partial* is fine, a publish blocked because one channel was down is not.

Adjustments to gameplan CONTENT (thesis pick, watchlist edits, ticker additions) ARE valid AskUserQuestion topics — those are content decisions. But the act of publishing the FINAL synthesis is part of the workflow contract, not an option.

Failure mode this prevents: 2026-06-03 — drafted clean gameplan, then asked "publish y/n + channel selection + thesis edits" → operator rejected the publish question as friction.

## ⛔ HARD RULE: R-Units Required

**All trade plans, stops, targets, and recap numbers use R-units.** Read the R-CONFIG block at the top of `~/.claude/LifeOS/USER/SKILLCUSTOMIZATIONS/Trading/PREFERENCES.md → Trading Preferences → Risk Parameters` at the start of every run. Express stops as both price + per-share R, targets as R-multiples, daily limits as ±NR, position sizing as fraction-of-R-exposure. Always include the derived dollar in parentheses for readability (e.g., "1R ($28)" for LIVE, "1R ($75)" for SIM). Linked memory: `[[r-units-default]]`.

**Anti-pattern:** Hard-coding dollar amounts ("max $280 risk", "target $30.50") in workflow output. R-units are the lingua franca; dollars derive from PREFERENCES.

## ⛔ HARD RULE: Canonical Reporting Schema

**Setup grades, R-units, discipline scoring, and every comparison table follow
`Reference/ReportingSchema.md`** — the same contract DailyReview and WeeklyReview render
against, so the morning plan and the evening recap line up on one grade ladder and one R
axis.

Rule 0 of that schema applies here: **a rule with no live enforcer is ASPIRATIONAL and must
not be used to score anything.** `tradekit cards *` does not exist as of 2026-08-05 — do not
call it or promise its output.

## ⛔ HARD RULE: Game Plan Skeleton (local artifact)

**`Reviews/YYYY-MM-DD-gameplan.md` MUST contain these seven sections, in this order, every
session.**

| # | Section | Must contain |
|---|---|---|
| 1 | **HEADER** | date · build time · intel-layer source + transcript count · R basis (LIVE/SIM) · daily max · max LIVE tickers · flat-check time |
| 2 | **MACRO** | **Regime (dimensional) table from `tradekit regime --json`, or UNAVAILABLE with the reason** · GEX snapshot **or the literal word UNAVAILABLE with the reason** · **Volatility sub-table (IV30 / IVR / IV%ile / HV20 / IV/HV) for SPY + ACTIVE names, or UNAVAILABLE with the reason** · **Index sub-table (operator-requested 2026-10-01, see below)** · today's calendar |
| 3 | **THESIS TRADE** | exactly **ONE** named `TICKER SIDE` · trigger · stop · target in R · one-sentence edge · setup tag. **`WAIT — no premarket thesis` is a valid entry**; do not manufacture one |
| 4 | **WATCHLIST** | three labelled groups — **ACTIVE**, **DORMANT**, **WATCH-ONLY** — each a table with fixed columns `Ticker \| Bias \| Trigger \| Max sh @1R \| Status \| Kill (CT)`. Admission gated per the rule below |
| 5 | **VALIDITY GATE** | which names pass, which fail, and **why** — named, not implied |
| 6 | **RULES** | **exactly 3 bullets.** Not two, not five |
| 7 | **FOOTER** | privacy class + channel manifest (which channels got which version) |

### Index sub-table — fixed columns (operator request, 2026-10-01)

Section 2 carries this table every session, in this column order, one row each for **SPY, QQQ,
IWM, DIA, VIX, WTI, TLT**, plus any ETF carrying the day's sector read (SOXL, XLE, SLV, GLD):

| | Prior close | Prior chg | Pivot | Premarket | PM vol | Read |
|---|---:|---:|---:|---:|---:|---|

- **Pivot** = classic daily pivot `(H + L + C) / 3` from the prior session's bar, or the operator's
  own number when he supplies one (DIA 512 on 10-01 was operator-supplied; say so in the cell).
  The Read column states where premarket sits relative to the pivot.
- **PM vol** is stated beside every premarket price; a price on under ~50K shares is labelled thin.
- **Read** is one clause: what the row means for today's board, not a description of the number.
- Missing feeds are written UNAVAILABLE in the cell, never dropped (the 10-01 QQQ/IWM pivots were
  UNAVAILABLE at build because only closes had been pulled).

### Watchlist admission — the R-VIABILITY gate runs FIRST

**Before the movement gate, before the chart, before anything: can 1R buy a position in this
name?** This is not a rule to remember — it is a column, computed at build time:

```bash
python3 ~/.claude/Tools/sizing_column.py --table MRVL NOW CRM PLTR SLV INTC GLD MU
python3 ~/.claude/Tools/sizing_column.py MRVL NOW CRM     # markdown rows for the board
```

`max_shares = R_VALUE / (MIN_STOP_ATR × premarket ATR14)`, both constants read from the
PREFERENCES R-CONFIG. Exit 1 means at least one name is UNTRADEABLE or has no premarket data.

**Under ~10 shares at LIVE R = not a watchlist candidate.** The tool prints `UNTRADEABLE` and
the name never reaches the board — it is not demoted later after a chart looks good. It goes on a
"right idea, wrong instrument" line and never enters ACTIVE, DORMANT or the thesis slot.

At LIVE 1R = $28 this excludes most of the megacap tape. Worked example from 2026-08-28:

Real output for 2026-08-28, measured to 09:15 ET:

```
Ticker       ATR    stop  LIVE sh  SIM sh   verdict
DRAM       0.103    0.15      181     485   ok
SLV        0.171    0.26      109     293   ok
INTC       0.177    0.27      105     282   ok
PLTR       0.298    0.45       62     167   ok
NOW        0.355    0.53       52     140   ok
GLD        0.412    0.62       45     121   ok
NVDA       0.418    0.63       44     119   ok
CRM        0.630    0.94       29      79   ok
MRVL       1.173    1.76       15      42   ok (thin)
MU         2.296    3.44        8      21   UNTRADEABLE
```

Note MRVL: viable at 15 shares, but thin — which is the honest read on a name whose
premarket range was $4.98. MU excludes itself without anyone having to decide.

**Why this rule exists.** On 2026-08-28 the screen ran in the opposite order: it ranked by
premarket movement and volume, promoted MRVL (9 shares) to thesis, left MU (3 shares) in ACTIVE
all morning, and checked R-viability only on the winner — then used it to kill the trade. The
six names that actually delivered 3R+ that session (NOW, SLV, CRM, PLTR, GLD, INTC) were **all**
labelled DORMANT, WATCH-ONLY or "not the trade." NOW and CRM triggered within two minutes of the
open. The operator was left with a board where every tradeable name was pre-labelled do-not-trade
and the published expectation was zero trades, so he sourced ideas elsewhere.

**A plan that produces nothing actionable has not produced a WAIT — it has produced a vacuum,
and the vacuum gets filled.** `WAIT` is legitimate only when the R-viable candidates were
screened and genuinely none qualified. State how many were screened.

**Corollary — never publish a conditional you predict will fail.** If the R math says a name is
untradeable, the output is *the R-viable alternatives*, not a gate built to die. The 08-28 plan
wrote "opening ranges on gap-down earnings names are usually wider than the premarket range" and
then set the condition at $1.90 against a $4.98 premarket range. That is not a plan, it is a
prediction of no-trade dressed as one.

**Corollary — a failing thesis is a signal, not a deletion.** SLV was downgraded from LONG to
watch-only at 07:15 CT because the long was breaking. It then fell 6%. The analysis was right and
stopped one step short: when a directional thesis fails on real evidence, evaluate the other side
before dropping the name.

### Watchlist admission — the premarket movement gate

**If a name is not MOVING premarket, it comes OFF the active list.** In-play means
premarket movement, RVOL, or a live catalyst. **Dead-flat premarket = DORMANT, not listed.**
A dormant name returns only if it **wakes at the open** — reclaims its trigger, **and** its
group confirms, **and** real volume shows up. Operator rule, called live 2026-08-11.
Linked memory: `[[feedback-watchlist-premarket-movement-gate]]`.

Build the watchlist **after** the premarket read. Movement is an **admission test**, not a
column. Group the board explicitly:

| Group | Meaning |
|---|---|
| **ACTIVE** | moving, or has a live catalyst. These are tradeable today |
| **DORMANT** | trigger exists but the name is flat. **Revisit only if it wakes at the open** |
| **WATCH-ONLY** | earnings movers, off-thesis. **Open-only, no premarket entries** |

**Thin prints are not movement.** A quote on 311 shares is noise, not a signal — state the
premarket volume beside any premarket price, and if it is not credible say so.

**Worked example (2026-08-11):** XOM sat at 159.2 under its 160.40 trigger with XLE/OXY/USO
all flat — the whole energy thesis was pulled premarket and the active list fell to two
names, SPY (WAIT) and GLD (runner). **Counter-example (2026-08-10):** the plan carried 16
names including V at −0.09% on **311 shares** and DKNG at 0.00% on 8.7K. Under this rule
that board was about four names.

**Why:** a long list of untriggered, unmoving names is not preparation — it is a menu, and
a menu invites substitution when the real setup does not fire. See
`[[feedback-activity-over-patience]]`.

**Constraints:**
- **Sections never reorder, and are never renamed.** "Rules in force" ≠ "RULES"; use the
  heading above. A renamed section is a new section and breaks week-over-week comparison.
- **Never add ad-hoc top-level sections.** Anything extra is a subsection under one of the
  seven. If it fits nowhere, it does not belong in the game plan.
- **No-trade days:** sections 3–5 collapse into a single **POSTURE** section stating the
  stance and the re-entry condition. Sections 1, 2, 6, 7 still render.
- **A missing input is written as UNAVAILABLE with its reason, never silently dropped.**
  An absent section reads as "nothing to report"; that is how a broken data source becomes
  invisible.

### Mapping to the Notion body — deliberately NOT identical

The two structures share a spine but are not the same list, because the Notion page keeps
growing after the plan is written and the local artifact does not.

| Local section | Notion counterpart |
|---|---|
| 1 HEADER · 2 MACRO · 3 THESIS TRADE · 4 WATCHLIST | same, same order |
| 6 RULES | Notion §5 RULES — **same content, different position** |
| 5 VALIDITY GATE · 7 FOOTER | **local only** — build-time reasoning + channel manifest |
| — | **Notion only:** INTRA-DAY UPDATES, EOD REVIEW — appended during and after the session, so they cannot exist at build time |

Do not "fix" this into a 1:1 mapping. Sections 1–4 must match exactly so the two renderings
can be diffed; the rest differ for a stated reason.

**Why this exists:** across five shipped plans (06-05, 06-08, 08-05, 08-06, 08-10) **not one
section heading appeared in all five**, and the only surviving concept — "rules" — drifted
from `Rules for Today (3 rules max)` to `Rules in force`, silently dropping the 3-rule cap.
Structure was mandated for the Notion page only, so the artifact read at 06:00 every morning
was ungoverned and reinvented per session.

### Other naming conventions that have drifted — hold these too

- **Private Drive file:** `GAMEPLAN-YYYY-MM-DD.md`. On 2026-08-10 it was written as
  `2026-08-10 Game Plan (PRIVATE) — GLD LONG`, which does not sort with its siblings.
- **Local artifact:** `Reviews/YYYY-MM-DD-gameplan.md`, lowercase, ISO date first
  (ReportingSchema Rule 7). The `-PRIVATE` / `-PUBLIC` suffixes used in June are deprecated.

## ⛔ HARD RULE: Channel Topology + Notion Protocol

**Notion + Slack #general + Discord = PUBLIC channels. Google Drive Game_Plan folder = PRIVATE channel.** Public-channel content is sanitized per `[[channel-topology]]` + `[[public-share-minimal]]` (strip broker accounts, FL internals, banned-ticker rationale, behavioral contracts verbatim, $ R-values).

Discord carries the **same sanitized payload as Slack #general** — one PUBLIC body is built once and posted to both. Never build a Discord-specific variant from the private Drive version; that is how unsanitized content reaches a server whose membership you do not control.

**Notion structure follows the protocol:** `~/.claude/LifeOS/USER/SKILLCUSTOMIZATIONS/Trading/NOTION_PROTOCOL.md`. Linked memory: `[[notion-gameplan-protocol]]`. Specifically:

- **Main page title:** `YYYY-MM-DD — TICKER SIDE` (e.g., `2026-06-04 — HPE SHORT`)
- **Main page properties:** Status (DRAFT→PUBLISHED→UPDATED→REVIEWED), Thesis Ticker, Thesis Side, Thesis Outcome, Combined R, Discipline Score, Private Drive Link
- **7-section fixed body structure:** HEADER callout → MACRO CONTEXT → THESIS TRADE → WATCHLIST table → RULES → INTRA-DAY UPDATES (appended) → EOD REVIEW (appended)
- **Per-ticker sub-DB entries** created in `Fresh News` (collection://4fa7df7d-a224-40e1-918e-46ccec5088e7) for new same-day catalysts, and `Second Day Plays` (collection://3d16085b-bfa0-4cfb-a67c-ea119b6b90d3) for continuations/technical. Each entry has: Ticker, Bias (Long/Short/Neutral), Setup (multi-select per DB's options — note: Fresh News has "Earnings" option, Second Day Plays does NOT), Support, Resistance, Inflexion, Trading Plan, Notes, Date=today, Triggered (initially false), Outcome (TBD)
- **Private Drive write:** save FULL version to `Game_Plan` folder (id `1krsep2YWSLe6-V72j-evU32lXj4Vcuym`) as `GAMEPLAN-YYYY-MM-DD.md`; cross-link from Notion page property

## ⛔ HARD RULE: DAS Market Viewer Path — `GamePlan\` Subfolder Only

**The one canonical DAS watchlist path on every node is:**

```
C:\Cobra Trading_x64-Beta\GamePlan\GamePlan-Today.txt
```

Plus the dated sibling `GamePlan\GamePlan-YYYY-MM-DD.txt`. Nothing else is a game plan file.

**Never write, read, or load `C:\Cobra Trading_x64-Beta\GamePlan-Today.txt` (the install root).**
The DAS install root holds DLLs and `Config.cfg`; plan files stay out of it. Any root-level
`GamePlan*.txt` is a **legacy decoy** — it is not maintained, it will be stale, and loading it
puts an old board in front of the operator that looks current.

**Operator setup:** point Market Viewer at the `GamePlan\` subfolder once. Right-click the
Market Viewer tab → Load → `C:\Cobra Trading_x64-Beta\GamePlan\GamePlan-Today.txt`. DAS remembers
the last directory, so this is a one-time action per node.

**Why this rule exists:** on 2026-08-18 daslaptop's subfolder copy was 18 days stale after a
cluster handoff, while a *differently* stale root-level copy sat beside it — two files, two
dates, neither correct, no way to tell from inside DAS which one the Viewer had loaded. One
path removes the ambiguity.

### Node-local artifacts do not survive a cluster handoff

Slack, Notion, Drive and Discord are shared surfaces — publishing them once covers every node.
**The DAS file is the only deliverable that is node-local.** A `DAS Viewer ✅` from the
publishing node is evidence about *that node's* C: drive and nothing more.

**After any handoff, the receiving node re-runs Phase 8 before the open** and verifies by
`mtime`, never by the publisher's report:

```bash
python3 ~/falcon/dashboard/das_market_viewer.py <tickers> --file-only
```

`--file-only` skips the CMD API probe — use it whenever DAS is not up.

**⛔ Never hardcode the CMD API port.** Read `DAS_PORT` from `~/.claude/.env` (this node: **3192**,
also at `C:\Cobra Trading_x64-Beta\Config.cfg` → `CMDAPI:PORT`). On 2026-08-28 this workflow's own
prose said `9910`; probing that port returned a refusal, which was published as "DAS is DOWN"
while DAS was serving quotes on 3192. The whole plan was then built on 15-min-lagged Polygon
data and broadcast to five channels. Verify with:
```bash
python3 ~/.claude/Tools/das_quote.py SPY --seconds 6   # reads DAS_PORT from .env
```
The write itself does not require DAS to be running. Linked memory:
`[[reference-node-local-artifacts-dont-survive-handoff]]`.

## ⛔ HARD RULE: Falcon-Cluster Bus

**Every MorningGamePlan run MUST post a session-start beacon AND a publish notification to Slack #falcon-cluster (C0B8RHBLDAS)** so LifeOS agents on other machines (ddd-laptop, home-pda) can detect this session's state without polling S3 or guessing.

Use one of:
- CLI from terminal: `~/.claude/Tools/falcon-cluster-handoff.sh start` (requires `SLACK_BOT_TOKEN` + `LIFEOS_MACHINE_ID` in `~/.claude/.env`)
- Slack MCP from within the session: `slack_send_message` to `C0B8RHBLDAS` with the start beacon + publish summary

Post twice per MorningGamePlan run:
1. **Start beacon** (before OBSERVE/synthesis): `:satellite: [MACHINE] MorningGamePlan START · ISO_TS`
2. **Publish notification** (after Phase 7-8 publish completes): include Notion main page ID, Drive file ID, Slack #general message ts, and any sub-DB entry count

Linked memory: `[[falcon-cluster-agent-sync]]`, `[[channel-topology]]`.

**Why:** Without this, other machines' agents have no real-time way to know this machine has published a gameplan, leading to duplicate work and state drift. The S3 backup is point-in-time; #falcon-cluster is the real-time delta stream.

## ⛔ HARD RULE: Dilution Catalyst Scan (R/S + ATM combo detection)

**Every MorningGamePlan run MUST scan the overnight news for the R/S + ATM dilution combo and flag any matches as Day-2/Day-3 short watch — NOT Day-1 short candidates.**

Run as part of the news-pull step:
```bash
~/falcon/dashboard/.venv-gameplan/bin/python ~/falcon/dashboard/dilution_scan.py
```

The script pulls Polygon news (last 24h) and flags any ticker whose recent news matches keywords across two categories:

**Category A — Reverse Stock Split:**
- "reverse stock split"
- "ratio of 1-for"
- "1-for-N reverse split" (any N)

**Category B — Dilution Vehicle:**
- "at-the-market offering" / "ATM offering" / "ATM facility"
- "S-3 shelf" / "S-3 registration"
- "$NN million equity offering" / "common stock offering"
- "private placement" (lower-priority, but still flag)

**A match in BOTH categories on the same ticker = R/S + ATM combo** = highest-conviction Day-2/Day-3 short setup in the playbook taxonomy.

### Setup rules (do NOT violate Day-1)

| Day | Action |
|-----|--------|
| **Day 1** (announcement day, halt-runner) | **WATCH ONLY** — build the level map from L2; locate desk closed; squeeze can extend further than rationality |
| **Day 2** | Locate availability opens; ATM mechanical selling visible at bid; first lower high = short signal |
| **Day 3+** | Dilution overwhelms; gap-downs on filings; sustained fade |

**Entry:** confirmed lower high with stop above prior high  
**Target:** 50%+ retrace of the spike (70-80% typical on heavy ATM cases)  
**Edge:** ATM mechanism guarantees seller persistence; locate desk loosens by Day 2  
**Anti-rule:** NEVER short Day 1 of the halt-runner. INHD 2026-06-08 = textbook violation example.

### Top Playbook tag (current schema)

Closest existing Top Playbook tag: **Short Overextension Fade**. A future Notion schema update may add a dedicated **"R/S + ATM Combo Fade"** option to distinguish dilution-mechanism fades from generic overextension fades. Until then, tag as Short Overextension Fade with a Notes field flagging "R/S + ATM combo."

Linked memory: `[[rs-atm-combo-setup]]`.

## ⛔ HARD RULE: SPY GEX Snapshot in Macro Block

**Every MorningGamePlan run MUST include the SPY Gamma Exposure (GEX) snapshot in the Macro Context section** to anchor the regime read (mean-reversion vs trend-extension).

Run before Phase 6 synthesis (data: **CBOE public delayed-quotes feed** — free, no API key, real open interest + IV; gamma via Black-Scholes-Merton. yfinance's `openInterest` returned 0 and was retired 2026-08-11):
```bash
tradekit gex --max-dte 14
```

**⛔ There is no longer a loose `spy_gex_compute.py` on any node — do not resurrect one.**
The tool lives in `tradekit` (`analysis/gex.py`, `tradekit gex`), installed with
`uv tool install ~/src/tradekit`. It was packaged on 2026-09-08 because trader-desk and
daslaptop had drifted onto different copies at different paths: a fix shipped into
`~/falcon/dashboard/spy_gex_compute.py` never reached the node where that path held a
retired yfinance version, and nothing in either output could tell the two apart.
If `tradekit gex` is missing, install it — do not copy a script back in.

Verify the version before trusting a reading, and put it in the cluster beacon:
```bash
tradekit gex --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['asof'], d['regime'])"
```

Paste the markdown output into the macro section. The regime label + tape-read implication determines how to grade today's setups:

| GEX Regime | Setup Bias |
|------------|------------|
| **Positive (strong)** | Mean-reversion + fade setups preferred; breakouts fail more often; pinning at magnet strikes |
| **Positive (moderate)** | Mild dampening; ranges hold; lower-conviction trend trades |
| **Negative (moderate)** | Mild amplification; trends extend; breakouts more reliable |
| **Negative (strong)** | Chase breakouts; fade fades only at multi-TF confirm; momentum extends |

Zero-gamma flip level: if within $5 of spot, the day will likely revolve around that level (magnet/repellent behavior). If no flip in ±15% band, the regime is stable.

**Top magnet strikes** are intraday targets — price tends to gravitate toward them on options-driven hedging flow. Use them as both:
- **Targets** when trading toward them
- **Trigger levels** when price breaks through (acceleration through a magnet often signals dealer-hedge unwind)

Linked memory: `[[ema9-sma34-cross-research]]` (flow tools), `[[imbalance-papers]]` (broader theoretical context), `[[falcon-cluster-agent-sync]]` (other-machine agents read the same output).

## ⛔ HARD RULE: Volatility Context (IV Rank) in the Macro Block and on every ACTIVE name

**Every MorningGamePlan run MUST include a Volatility sub-table under §2 MACRO** for SPY, the
thesis ticker, and every ACTIVE watchlist name — IV30, IV Rank, IV percentile, HV20, IV/HV — from:

```bash
~/src/tradekit/.venv/bin/python ~/.claude/Tools/iv_rank.py SPY <active tickers>
```

Same CBOE delayed feed as `tradekit gex`; the tool appends today's IV30 to
`Intelligence/iv_history.csv`, which is the only source of the rank. **IVR is `n/a` until ≥20
sessions of local history exist for a ticker** — print it as `n/a (N sess)` and lean on IV/HV.
Do not paste a rank from a broker screen without naming the screen and its lookback.

Operator rule 2026-09-24, citing Bob Sosnoff (Tastytrade, later Lossdog.com): ignoring volatility as
a factor of any trade is a mistake that may make it impossible to be profitable. Linked memory:
`[[iv-rank-in-reviews]]`.

**How it changes the plan, not just decorates it:**

| Reading | Plan consequence |
|---|---|
| IVR ≥ 50 or IV/HV ≥ 1.3 | market is braced: expect wider ranges; stops off 1.5×ATR are the floor, not the target; breakout targets extend, entries wait for the closed bar |
| IVR ≤ 20 or IV/HV ≤ 0.8 | complacent: expansion risk both ways; breakouts need volume confirmation; fades are lower-conviction |
| SPY IVR high + name IVR low | idiosyncratic setup in a nervous tape — size down, kill earlier |

The fixed §4 watchlist columns do not change; the vol read lives in §2 and, for ACTIVE names, as a
clause inside the Trigger cell.

## ⛔ HARD RULE: Trigger Kill Time

**Every thesis trade and watchlist entry MUST specify a "Trigger Kill Time" — an explicit clock time after which the setup is dead for the session, regardless of price action.**

Format on the gameplan: `Trigger: <condition> | Kill: HH:MM CT`

Defaults (override per setup):
- **Thesis trades:** Kill = open + 30 min (e.g., 9:00 CT for a standard 8:30 CT open, 10:00 CT for NFP days where open delays)
- **ORB / first-15-min-range-break setups:** Kill = open + 45 min (the range needs time to form, then break)
- **Day-2 continuation / Day-3 continuation:** Kill = open + 60 min (require trend confirmation, not first-bar entry)
- **Bounce-Fade / Failed-Breakdown-Reclaim:** Kill = open + 90 min (require failure of the prior move first)

If the trigger has not fired by Kill Time, **the thesis is dead for the day.** No "I'll keep watching it" — that's the open-ended chop where substitute setups creep in.

**Why this rule exists:** 2026-06-04 HPE thesis missed + 2026-06-05 LULU thesis missed = 2 consecutive sessions of "the published thesis didn't trigger cleanly so I drifted to off-plan/banned names instead." The open-ended wait IS the substitution vector. Linked memory: `[[trigger-kill-time]]`, `[[activity-over-patience]]`.

**Anti-pattern this prevents:** Operator stares at the published thesis ticker for 90 min waiting for the "perfect" entry; chop feels like a knife; substitute setups (often banned-LIVE names with intraday momentum) start looking like the only available trade; operator clicks substitutes. The Kill Time converts open-ended wait into a defined go/no-go window.

**How to apply during synthesis:** Add `Kill: HH:MM CT` to every Thesis Trade block and every Watchlist row's Trigger column. Use defaults above unless the setup has a specific reason to extend (e.g., earnings-reaction trades may need to wait for the first analyst note that drives direction).

## Steps

### Phase 1: Market Context (6:00-6:20 CT)

1. **Check futures/ETFs:**
   - `MarketData.ts quote SPY QQQ IWM /CL GLD`
   - Assess overnight direction and gap

2. **Economic calendar:**
   - Check for FOMC, CPI, jobs, GDP, or other scheduled releases
   - Flag any events that could cause volatility

3. **USMetrics Macro Context:**
   Read `~/.claude/data/Substrate/US-Common-Metrics/us-metrics-current.csv` and extract the six key trading signals:

   | Signal | Metric | Threshold | Regime Label |
   |--------|--------|-----------|--------------|
   | Volatility | VIX (VIXCLS) | <15 tight / 15-20 calm / 20-30 elevated / >30 spike | CALM / ELEVATED / SPIKE |
   | Yield curve | 10Y-2Y Spread (T10Y2Y) | >0 = normal / <0 = inverted | NORMAL / INVERTED |
   | Consumer stress | UMich Sentiment (UMCSENT) | >75 ok / 60-75 cautious / <60 stress | OK / CAUTIOUS / STRESS |
   | Energy | WTI Crude (DCOILWTICO) | <80 low / 80-100 moderate / >100 elevated | LOW / MODERATE / ELEVATED |
   | Systemic risk | Financial Stress Index (STLFSI4) | <0 = low / 0-1 = moderate / >1 = high | LOW / MODERATE / HIGH |
   | Dollar | USD Index (DTWEXBGS) | directional note only | UP / DOWN / FLAT |

   Output the compact macro bias block:
   ```
   ══ MACRO CONTEXT ══════════════════════════════════
   VIX:          [value]  → [CALM/ELEVATED/SPIKE]  — [one-line implication for today]
   Yield Curve:  [value]  → [NORMAL/INVERTED]  — [one-line implication]
   Consumer:     [value]  → [OK/CAUTIOUS/STRESS]  — [sector bias note]
   Oil:          $[value] → [LOW/MODERATE/ELEVATED]  — [inflation/energy note]
   Stress Index: [value]  → [LOW/MODERATE/HIGH]  — [systemic risk note]
   ══ REGIME BIAS ════════════════════════════════════
   [2-sentence synthesis: what this macro backdrop means for today's setups]
   ═══════════════════════════════════════════════════
   ```

   **VIX → Setup filter:**
   - CALM (15-20): FL Long bias, trending setups preferred, good breakout follow-through
   - ELEVATED (20-30): Both directions viable, wider stops needed, reduce size
   - SPIKE (>30): Reversal/fade setups only, no momentum longs, sim-first

   **Consumer stress → Sector filter:**
   - STRESS (<60): Caution on retail/discretionary longs (AMZN, WMT, AZO, etc.)
   - OK/CAUTIOUS: No sector filter applied

   Note: If Substrate data is more than 7 days old, flag it and run `bun ~/.claude/skills/USMetrics/Tools/UpdateSubstrateMetrics.ts` before proceeding.

4. **Market regime comes from tradekit, per dimension. Never hand-label it** (operator rule 2026-10-06; tradekit ADR 0002):
   ```bash
   tradekit regime --json --event "fed:Williams 08:05 CT" --event "corp:MRVL investor day 08:00 CT"   # events from step 2
   ```
   - Render §2's **Regime (dimensional)** table straight from `state` + `evidence`: direction, structure,
     volatility, participation, liquidity, events, data_quality. Show `conflicts` (e.g. QQQ vs SPY) and the
     `configuration_status`. While it is `experimental`, label the read **provisional**.
   - Copy the `playbooks` decisions into the validity gate. A `blocked` playbook does not reach ACTIVE;
     `conditional` carries its reason into the Trigger cell. The regime **gates setups. It is never a trade
     signal** and never sets direction for a name on its own.
   - Notion: `Regime` (text) = the one-line dimension summary from the JSON. The legacy `Market Regime`
     multi-select gets **exactly one** value, mapped from the JSON: structure `range` → Ranging; `trend` + `up`
     → Melting Higher; `trend` + `down` → Trending Down; `transition` → Choppy; anything `unknown` → leave empty.
     Never copy the weekly page's labels into the daily field.
   - If tradekit exits 2 (no approved `~/.config/tradekit/regime.yaml`) or 3 (Massive unavailable), write
     **Regime: UNAVAILABLE — <reason>** and continue. Do not substitute a hand-picked label.
   - There is no verified public SMB regime list. Do not cite one.
   - Query intelligence for the dimensions that bind today (e.g. `Intelligence/MarketRegimes/` notes on
     range days or narrow participation) for how to trade them.

### Phase 2: Scanning & Watchlist (6:15-6:45 CT)

1. **Run Finviz screener:**
   - Pre-market gappers > 3% with volume > 500K
   - Unusual volume movers
   - Earnings/catalyst plays

2. **For each candidate ticker:**
   - `MarketData.ts quote TICKER` — fundamentals snapshot
   - `MarketData.ts ohlcv TICKER --period daily --range 5d` — calculate Camarilla pivots
   - `EdgarLookup.ts filings TICKER --days 14` — recent SEC filings
   - Extract catalyst keywords from filings

3. **Statistical Covariance Analysis (for each candidate ticker):**
   - Pull 90 days of daily OHLCV from Polygon REST API (`api.polygon.io/v2/aggs/ticker/TICKER/range/1/day/`)
   - Calculate: 20-day mean, 20-day std dev, z-score (current price vs 20-day mean)
   - Calculate: weekly high/low, range position (%), annualized volatility
   - Classify: NORMAL (|z| < 2), EXTENDED (2-3), EXTREME (>3)
   - **Setup signal rule:** NORMAL stocks → Fashionably Late long candidates. EXTREME stocks → Offsides short candidates.
   - Filter: must deliver $1 intraday move (check avg daily range)
   - Filter: account size ($3-50 sweet spot, $50-400 A+ only, >$400 excluded)

4. **Grade each ticker** (per PlaybookSetups.md grading criteria + covariance status)

5. **Separate into two categories:**
   - **Fresh News:** New catalysts today (earnings, filings, breaking news)
   - **Second Day Plays / Technical Setups:** Day 2 continuations, HTF setups, range breaks

### Phase 3: Query Intelligence Base (6:45-7:00 CT)

For each ticker on the watchlist:

1. **Match to playbook setup:**
   - Search `Intelligence/Setups/` for matching patterns
   - Pull relevant analyst insights for this setup type

2. **Check analyst commentary:**
   - Search `Intelligence/Analysts/` for any recent mentions of ticker or sector

3. **Load relevant psychology reminders:**
   - Based on recent review patterns (e.g., "exiting winners too early")
   - Pull from `Intelligence/Psychology/`

### Phase 4: Build the Game Plan (7:00-7:15 CT)

1. **Create Notion entry** in David Duncan Daily Game Plan database:
   - Date, Monthly Goal, Weekly Goal
   - Market Regime
   - 1% Change (behavioral focus from recent lessons)

2. **Populate Fresh News sub-database:**
   - Ticker, Support (Camarilla S3/S4), Resistance (Camarilla R3/R4)
   - Inflexion point, Bias, Setup type, Trading Plan, Notes

3. **Populate Second Day Plays sub-database:**
   - Same fields, focused on continuation and technical patterns

4. **Each Trading Plan field should include:**
   - Entry trigger (specific price action confirmation)
   - Stop loss (ATR-based or level-based)
   - Profit targets (R:R ratio)
   - Intelligence note (what analysts/intel says about this setup)

### Phase 5: Identify the Thesis Trade (7:15-7:30 CT)

> "Trade the thesis, not the ticker that's moving the most on your screen."

1. **Which ticker has the highest conviction?**
   - Strongest catalyst + cleanest chart + best setup grade
   - Intelligence base confirms edge in this setup type

2. **Mark as PRIMARY TRADE:**
   - This gets live capital
   - Define exact entry, stop, targets
   - Plan to size into conviction (not 5-share lots)

3. **Prepare both directions:**
   - Long scenario AND short scenario for the primary ticker

### Phase 6: Output Summary

Present the complete game plan:
```
═══ MORNING GAME PLAN — [Date] ═══

Market Regime: [tradekit regime dimensions, e.g. neutral · range · normal vol · mixed participation]
1% Change: [behavioral focus]
Thesis Trade: [TICKER] — [setup type] — [direction]

MACRO CONTEXT:
VIX [value] → [CALM/ELEVATED/SPIKE] | Consumer [value] → [OK/CAUTIOUS/STRESS] | Oil $[value] → [LOW/MODERATE/ELEVATED]
Regime bias: [one-sentence synthesis for today's setups]

STATISTICAL COVARIANCE:
[table: Ticker | Price | Z-Score | Status | Range Pos | Ann Vol | Setup Signal]
Rule: NORMAL → FL long. EXTREME → Offsides short.

FRESH NEWS:
[table of tickers with levels, bias, plan — filtered by account size + covariance]

SECOND DAY PLAYS:
[table of tickers with levels, bias, plan]

INTELLIGENCE NOTES:
[relevant analyst insights for today's setups]

RULES REMINDER:
[top 3 rules from RulesOfEngagement.md based on recent patterns]
```

### Phase 7: Post to #general — Discipline Workshop Format

Post the trading plan to Slack channel **#general** (ID: `C0B5U2DHB0U`) using the discipline workshop format below. This is a focused, accountability-first summary — not the full game plan dump.

```
*GAME PLAN — [Date]* | Regime: [regime]

*1% Change:* [behavioral focus from recent review]
*Yesterday's Discipline:* [X/10 — one-line pattern note]

*THESIS TRADE:* [TICKER] — [setup] — [LONG/SHORT]
• Entry: [specific trigger]
• Stop: [level] ([ATR-based or level])
• Target: [level] ([R:R])
• Edge: [one-line intel note]

*WATCHLIST:*
[TICKER] | [bias] | [z-score status] | [key level]
[TICKER] | [bias] | [z-score status] | [key level]
...

*RULES FOR TODAY:*
1. [rule 1 — most relevant to recent pattern]
2. [rule 2]
3. [rule 3]
```

**Guidelines:**
- Keep it under 40 lines — this is for focus, not reference
- Lead with the behavioral commitment (1% Change) — discipline first
- Thesis trade must have all four fields (entry, stop, target, edge) or don't post it
- Watchlist: max 6 tickers, z-score status only (NORMAL / EXTENDED / EXTREME)
- Rules: pull the 3 most relevant from RulesOfEngagement.md based on recent review patterns

### Phase 7b: Post to Discord (auto, parallel with Phase 7)

Posts the **same sanitized body built for Slack #general** — build the PUBLIC payload once, send it
to both. Discord is a PUBLIC channel per the topology rule above.

```bash
python3 ~/.claude/Tools/discord_post.py --file <sanitized-plan.md> --title "Morning Game Plan — YYYY-MM-DD"
```

The tool handles the three Slack/Discord incompatibilities automatically — do not hand-convert:

| Slack | Discord | Handled by |
|---|---|---|
| `*bold*` | `**bold**` | `slack_to_discord()` |
| `<url\|label>` | `[label](url)` | `slack_to_discord()` |
| markdown tables | **unsupported** → fenced code block | `tables_to_code()` |
| 40k char limit | **2000 char limit** | `chunk()`, fence-balanced across seams |

Webhook URL comes from `DISCORD_GAMEPLAN_WEBHOOK` in `~/.claude/.env`. It is never passed as an
argument — it is a bearer credential and would land in shell history.

Verify with `--dry-run` first whenever the plan format changes.

**Failure handling:** a non-zero exit reports which chunks failed. Log it and continue — Discord
never blocks Slack, Notion, Drive, or Phase 8.

### Phase 8: DAS Market Viewer (auto)

After presenting the game plan, automatically populate DAS Trader Market Viewer:

1. **Collect all plan tickers** — thesis trade + fresh news + second day plays (deduplicated)
   - Include context tickers if they appear as active setups (SPY, QQQ for regime reads)
   - Order: thesis trade first, then fresh news, then second day plays

2. **Run das_market_viewer.py:**
   ```bash
   python3 ~/falcon/dashboard/das_market_viewer.py TICKER1 TICKER2 TICKER3 ...
   ```
   - Always writes `C:\Cobra Trading_x64-Beta\GamePlan\GamePlan-Today.txt` (1-right-click load fallback), creating the folder if absent
   - The `GamePlan\` subfolder is the **only** sanctioned path — see HARD RULE: DAS Market Viewer Path. Never write the install root
   - Pass `--file-only` when DAS is not listening on `$DAS_HOST:$DAS_PORT`; the file write does not need DAS running
   - If DAS is running: probes CMD API SCRIPT commands to auto-populate Market Viewer
   - Reports to stderr whether auto-load succeeded or file-only

3. **Output to user:**
   ```
   ══ DAS MARKET VIEWER ══════════════════════
   Tickers written → C:\Cobra Trading_x64-Beta\GamePlan\GamePlan-Today.txt
   [If DAS running]: Auto-load attempted via CMD API — check Market Viewer
   [If DAS not open]: Right-click Market Viewer tab → Load → GamePlan-Today.txt
   ═══════════════════════════════════════════
   ```
