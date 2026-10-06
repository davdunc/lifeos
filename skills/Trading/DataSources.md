# Data Sources

## Source Priority (operator rule, 2026-10-06)

**Collect from Massive (Polygon) first, wherever Massive has the data.** TradingView and Finviz are
fallbacks for what Massive lacks. When a fallback is used, say so in the output and give the reason.

| Need | First | Then |
|---|---|---|
| Prior-session OHLCV, pivots, ATR / z-score history | Massive REST aggs, or flat files for history | — |
| Market-wide movers (prior day) | Massive grouped daily aggs (one call, ~12K tickers) | Finviz universe export |
| Delayed snapshot / gainers / losers | Massive `/v2/snapshot/...` (**~15 min delayed**; drop rights/warrants/units) | TradingView screener |
| News / catalysts | Massive news | video layer, then Finviz |
| **Live** premarket / intraday quotes, triggers, sizing at entry | **DAS** (real-time) | TradingView only if DAS is down |
| Float, short float, RVOL, group performance | Finviz Elite (universe cache) | — |
| Options IV / GEX | CBOE (Massive options = 403 on this plan) | — |
| Economic calendar | TradingView | — |

Massive is **not real-time on this plan**: snapshots lag about 15 minutes and carry no last trade or quote.
Never use them for a trigger. Budget: stocks are unlimited, but self-cap at **10 req/s** and never
load-test (2026-10-06 operator rule: do not jeopardize access).

## Finviz Elite Export API

- **Purpose:** Pre-market gap screener, ticker discovery, fundamentals + technicals snapshot
- **Base endpoint:** `https://elite.finviz.com/export`
- **Auth:** Append `&auth=FINVIZ_API_KEY` (never log the token)
- **Response format:** CSV with header row; parse with `csv.DictReader`
- **API key env var:** `FINVIZ_API_KEY` (from `~/.claude/.env`)

### URL Construction

```
https://elite.finviz.com/export?v=111&f={filters}&ft=4&c={columns}&auth={FINVIZ_API_KEY}
```

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `v` | View preset (111 = overview) | `v=111` |
| `f` | Comma-separated filter codes | `f=geo_usa,sh_price_o3,ta_gap_u3` |
| `ft` | Filter type (4 = strict) | `ft=4` |
| `c` | Comma-separated column IDs | `c=1,65,61,67` |
| `auth` | API token | `auth=KEY` |

### Common Filter Codes

| Filter | Code | Notes |
|--------|------|-------|
| US stocks only | `geo_usa` | Always include |
| Price over $3 | `sh_price_o3` | Sweet-spot floor |
| Price under $50 | `sh_price_u50` | Sweet-spot ceiling |
| Avg volume > 500K | `sh_avgvol_o500` | Liquidity floor |
| Gap up > 3% | `ta_gap_u3` | Pre-market gapper |
| Gap up > 5% | `ta_gap_u5` | Strong gapper |

### Key Column IDs (trading-relevant)

| ID | Column | Category |
|----|--------|----------|
| 1 | Ticker | identity |
| 2 | Company | identity |
| 49 | Average True Range | technical |
| 61 | Gap | price-volume |
| 63 | Average Volume | price-volume |
| 64 | Relative Volume | price-volume |
| 65 | Price | price-volume |
| 66 | Change | price-volume |
| 67 | Volume | price-volume |
| 68 | Earnings Date | events |
| 71 | After-Hours Close | price-volume |
| 72 | After-Hours Change | price-volume |
| 81 | Prev Close | price-volume |
| 86 | Open | price-volume |
| 87 | High | price-volume |
| 88 | Low | price-volume |

### Phase 2 Screener Profile (sweet-spot gap-ups)

```
f=geo_usa,sh_price_o3,sh_price_u50,sh_avgvol_o500,ta_gap_u3
c=1,65,61,63,64,66,67
```

Returns: Ticker, Price, Gap, Avg Volume, Relative Volume, Change, Volume

### Column Schema

Full validated column ID range: 0–150. See JSON schema at:
`~/.claude/skills/Trading/Config/FinvizColumnSchema.json`

## Massive.com API
- **Purpose:** OHLCV historical candle data
- **Key endpoints:**
  - Daily candles: for Camarilla pivot calculation, support/resistance
  - Intraday candles (1min, 5min): for pattern analysis
- **Key fields:** Open, High, Low, Close, Volume per period
- **Used for:** Camarilla pivot calculation, ATR computation, trend identification
- **API key location:** `~/.claude/LifeOS/USER/SKILLCUSTOMIZATIONS/Trading/PREFERENCES.md`

## SEC EDGAR
- **Purpose:** Company filings for catalyst identification
- **Base URL:** `https://efts.sec.gov/LATEST/`
- **No API key required** (rate limit: 10 req/sec with User-Agent header)
- **Key filing types:**
  - 8-K: Material events (earnings, acquisitions, leadership changes, offerings)
  - 10-Q: Quarterly financials
  - 10-K: Annual financials
  - S-1: IPO registration
  - SC 13D/G: Institutional ownership changes
  - 4: Insider transactions
- **Catalyst keywords:** acquisition, merger, partnership, offering, FDA, approval, contract, restructuring, bankruptcy, investigation

## DAS Trader Exports
- **Path:** `/mnt/c/Users/davdunc/OneDrive/Desktop/Trade_Review/YYYY/MM/YYYY-MM-DD/`
- **Files:**
  - `Trades.csv` — Individual executions (TradeID, Account, B/S, Symbol, Qty, Price, Time)
  - `Orders.csv` — Order history
  - `Tickets.csv` — Ticket data
  - `pnl-by-position-*.csv` — P&L summary by position
  - `pnl-by-position-*.jpg` — P&L screenshot
  - `positions-*.csv` — Position details
  - `*.jpg` — Chart screenshots per ticker
- **Accounts:** `<LIVE_ACCOUNT>` (live/Cobra), `<SIM_ACCOUNT>` (sim) — real IDs live only in the local PREFERENCES.md
