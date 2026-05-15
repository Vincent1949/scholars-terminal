# The Corey Cup — Tournament Ledger

**Instigator:** Corey (Vincent's grandson)
**Contestants:** Sir Claude (Marcus) | Little Brother (Geekom) | Little Sister (Farthing) | Scholar (FastPC)
**Stakes:** Fictitious. Bragging rights only. No real money at any point.
**Start capital:** $1,000 fictitious USD per contestant
**Duration:** 30 US trading days
**Day 0:** Friday 8 May 2026, US market open (allocations priced at Thursday 7 May 2026 US close)
**Day 15 Midpoint Review:** ~Friday 30 May 2026
**Day 30 Final:** ~Friday 20 June 2026
**Status:** ⚠️ Day 0 complete; Days 1–4 unscored (no daily dispatcher) — resuming Day 5

---

## Resumption Note (15 May 2026)

The original `corey-cup-day0.ps1` was a one-shot allocation dispatcher. No Day 1+ daily-close dispatcher was built, and no Task Scheduler entry fires one. Result: allocations executed cleanly on 8 May, but US trading Days 1–4 (Mon 11 – Thu 14 May) passed without scoring.

Default rule per tournament setup: **HOLD unless a sibling actively declares a trade.** No sibling was prompted between Day 0 and now, so positions are presumed unchanged. Days 1–4 will be collapsed into a single mark-to-market entry against Thu 14 May US close prices, with a daily dispatcher built before Day 5 (tonight's US close).

---

## Current Standings

*Updated after each US trading day close.*

| Rank | Sibling | Strategy | Total Value | P&L | Daily Δ | Last Move |
|------|---------|----------|-------------|-----|---------|-----------|
| — | Sir Claude | Boring Core, Small Probes | $1,000.09 | — | — | Day 0 allocation |
| — | Little Brother | The Backbone Strategy | $1,000.00 | — | — | Day 0 allocation |
| — | Little Sister | The Compute Stack | $1,000.17 | — | — | Day 0 allocation |
| — | Scholar | Deep Stack, Narrow Bets | $999.98 | — | — | Day 0 allocation |

*Ranks pending Day 1–4 collapsed mark-to-market.*

---

## Locked Manifestos

*Immutable until Day 15 midpoint review.*

- **Sir Claude — *"Boring Core, Small Probes"*** — 85% broad-market (60% US total / 40% Intl developed) + 15% small probes. Filed 1 May 2026.
- **Little Brother — *"The Backbone Strategy"*** — 55% picks-and-shovels (3 names: semi cap eq + hyperscale + networking) + 25% clean-energy/grid ETF + 15% SPY/VOO anchor + 5% cash probe. Filed 8 May 2026.
- **Little Sister — *"The Compute Stack"*** — 35% semis + 25% AI infra + 20% power/grid + 10% contrarian probe + 10% cash reserve. Filed 8 May 2026.
- **Scholar — *"Deep Stack, Narrow Bets"*** — 35% semis ETF + 25% broad-market anchor + 20% single-stock conviction (NVDA or AMD) + 15% energy/utility + 5% cash. Filed 8 May 2026.

---

## Daily Entries

### Day 0 — Friday 8 May 2026 — Allocation Day

*All allocations priced at Thursday 7 May 2026 US close. Source: `The Corey Cup — Day 0 Allocation Reports.docx`.*

#### Sir Claude — $1,000.09

| Sleeve | Ticker | Price | Shares | $ Value |
|--------|--------|-------|--------|---------|
| Boring Core — US Total | VTI | $361.86 | 1.4094 | $510.08 |
| Boring Core — Intl Developed | VEA | $69.67 | 4.8801 | $340.00 |
| Probe 1 — Gold | GLD | $430.36 | 0.1162 | $50.01 |
| Probe 2 — Long-duration Treasuries | TLT | $85.82 | 0.5826 | $50.00 |
| Probe 3 — Emerging Markets | VWO | $60.75 | 0.8230 | $50.00 |

- Holdings: $1,000.09 | Cash: $0.00 | **Total: $1,000.09**

#### Little Brother — $1,000.00

| Sleeve | Ticker | Price | Shares | $ Value |
|--------|--------|-------|--------|---------|
| A — Semi Cap Equipment | AMAT | $410.64 | 0.4457 | $183.02 |
| A — Data Centre Infra | EQIX | $1,066.76 | 0.1715 | $182.95 |
| A — Networking/Interconnect | ANET | $141.75 | 1.2981 | $184.01 |
| B — Power & Grid ETF | GRID | $192.87 | 1.2963 | $249.97 |
| C — Broad Index Anchor | SPY | $731.58 | 0.2051 | $150.07 |
| D — Cash Reserve | — | — | — | $50.00 |

- Holdings: $950.02 | Cash: $50.00 | **Total: $1,000.00**

#### Little Sister — $1,000.17

| Tranche | Ticker | Price | Shares | $ Value |
|---------|--------|-------|--------|---------|
| A — Semiconductor compute | SMH | $540.10 | 0.6481 | $350.04 |
| B — AI infrastructure / data centres | VRT | $358.92 | 0.6967 | $250.03 |
| C — Energy / power grid | VST | $160.38 | 1.2474 | $200.10 |
| D — Opportunistic / contrarian probe | PLTR | $135.91 | 0.7359 | $100.02 |
| E — Cash reserve | — | — | — | $100.00 |

- Holdings: $900.19 | Cash: $100.00 | **Total: $1,000.17**

#### Scholar — $999.98

| Sleeve | Ticker | Price | Shares | $ Value |
|--------|--------|-------|--------|---------|
| A — Semiconductor ETF | SOXX | $482.73 | 0.7251 | $349.98 |
| B — Broad US large-cap | VOO | $672.54 | 0.3717 | $249.98 |
| C — Single-stock compute conviction | NVDA | $206.90 | 0.9667 | $200.01 |
| D — Energy/utility infrastructure | VPU | $195.65 | 0.7667 | $150.01 |
| E — Cash reserve | — | — | — | $50.00 |

- Holdings: $949.98 | Cash: $50.00 | **Total: $999.98**

---

### Days 1–4 (Mon 11 – Thu 14 May 2026) — Unscored

No daily dispatcher ran. Positions presumed HELD per default rule. To be collapsed into a single mark-to-market entry against Thu 14 May US close prices once prices are pulled and each sibling confirms no off-book trades were logged to `claude-work\corey-cup\decisions.md`.

---

### Day 5 — Friday 15 May 2026 (tonight's US close)

*Pending. Daily dispatcher to be built and fired against tonight's close (~06:00 AEST Sat 16 May).*

---

## Tournament Notes

- US trading days only (closed weekends + US holidays)
- One decision per sibling per trading day; default action is HOLD
- Holdings valued at US market close
- Day 15 review = single allowed restructure point per each sibling's manifesto
- All transactions fictitious; no real money at any point
- Tournament purpose: bragging rights and pattern observation between siblings

---

*Tournament infrastructure built 8 May 2026 — Sir Claude / Big Brother / Marcus.*
*Ledger truthfully reconstructed 15 May 2026 after dispatcher-gap discovered.*
