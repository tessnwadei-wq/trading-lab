# Pre-registered spec: `ts_momentum` (time-series momentum, 4 assets, portfolio with risk rules)

**Status: FROZEN.** Written and committed on its own on 2026-09-28 (session 5), **before any code was written for
this idea and before anyone looked at its 2018+ (test-period) results.** No backtest of this idea, on any data, had
been run when this file was committed. Every `ts_momentum` report shows the commit ID of this file.

Changing anything below after the first test-period look makes it a **new idea** (a new name, a new spec, a new
look), never a fix to this one.

**What had been seen before this spec (for honesty):** results of the lab's earlier ideas (ma_trend, overfit_demo,
portfolio_ma_trend, vol_target) on SPY, XIU.TO and GLD, and, when IEF was added to the data earlier in session 5,
IEF's plain yearly returns in the "How the markets differ" table (e.g. its worst year was 2022). No momentum signal,
backtest or benchmark comparison for this idea has been computed on any real data.

Source of the idea: Tessy's session-5 brief (item 3).

## 1. The question

Does a simple **trend signal** ("hold an asset only while its past 12 months beat cash") add anything over **just
holding the same four assets all the time**? The fair control (section 6) holds exactly the same assets at the same
20% each, always. If momentum can't beat that control, and the equal-risk mix, after costs, the signal adds nothing.

## 2. Published sources

- Moskowitz, Ooi & Pedersen, "Time Series Momentum", *Journal of Financial Economics* 104(2), 2012. For 58 futures
  markets, an asset's own **past 12-month excess return** (return above the T-bill rate) predicts its next month's
  return. Their strategy goes long when that excess return is positive and **short** when it's negative, holds for one
  month, and scales each position to the same ex-ante volatility (with leverage).
- Counterpoints: Kim, Tse & Wald, "Time series momentum and volatility scaling", *Journal of Financial Markets* 30,
  2016 (much of the published profit comes from the volatility scaling, not the signal); Huang, Li, Wang & Zhou,
  "Time-series momentum: Is it there?", *Journal of Financial Economics* 135(3), 2020 (weak evidence of predictability
  asset by asset). Our test checks whether the plain signal alone helps.

**How our version differs from the paper (on purpose, and decided now):**
1. **Long-only.** When the signal is negative we hold **cash** for that slot, never a short (lab rule).
2. **No volatility scaling and no leverage.** Each asset gets at most 20% of the account (the lab's 20% risk rule),
   sized by the lab's risk rules (section 4). This removes the part of the published mechanism that Kim et al. say did
   most of the work, so we expect a weaker effect.
3. **Four ETFs** (US stocks, Canadian stocks, gold, US Treasury bonds), not 58 futures.
4. **Every CLAUDE.md risk rule applies** (stops, 1% risk, 20% cap, 5 positions, circuit breaker), through the lab's
   portfolio engine (`lab/portfolio.py`).

## 3. The exact rule

For each of the four assets separately, on that asset's own trading calendar:

1. **When:** at the close of the **last trading day of each calendar month**. Same implementation as `vol_target`: a
   day counts as the month's last trading day if the next weekday (Mon-Fri) is in a new month; if that weekday turns out
   to be a holiday, the decision is made at the first trading day of the new month instead (one day late, never using
   future prices).
2. **Asset's 12-month total return:** `R = close(today) / close(the decision day 12 months earlier) − 1`, where "the
   decision day 12 months earlier" is the 12th previous monthly decision day on the same asset's calendar. Closes are
   dividend-adjusted (`data/csv/`), so this is a total return.
3. **Cash's 12-month return over the same days:** `C = product of (1 + daily T-bill return)` over every trading day
   after that earlier decision day up to and including today, `− 1`, using the lab's cash rate (`lab/cash.py`, the
   13-week US T-bill, `^IRX`; the US rate is used for XIU.TO too, as everywhere in the lab). If the cash data is
   missing, cash earns 0% (and the report says so).
4. **Signal:** **hold** the asset if `R > C`, otherwise **cash** for that slot (a tie counts as cash).
5. **Warm-up:** an asset has no signal until it has a decision day 12 months back (so the first decision is about
   January 2006). The portfolio's results are measured from the first day **every** asset has a signal.

## 4. Sizing, rebalancing and the risk rules

Run through the portfolio engine as **one account** starting in cash, with all CLAUDE.md risk rules enforced:

- **Timing:** every decision is made at a close and **filled at the next close** of that asset's market
  (`config.EXECUTION = "next_close"`). Costs 0.10% + 0.05% on every buy and sell, on the amount traded (double in the
  double-cost check).
- **Size of each holding (target):** the smaller of the 1% risk rule and the 20% cap, exactly as the engine already
  sizes entries: stop = 3 × the asset's 20-day average daily move below the fill price, sized as if 2 more average
  moves away (the one-day buffer) plus buying and selling costs, so a normal stop-out loses no more than 1% of the
  account; and never more than 20%. The rest of the account is in cash earning the T-bill rate.
- **Monthly rebalancing (every month-end decision day):**
  - signal turns to **hold** and the asset isn't held → buy the target size at the next close;
  - signal turns to **cash** and the asset is held → sell it all at the next close;
  - signal stays **hold** and the asset is held → **resize** it to a freshly computed target at the next close (buy or
    sell only the difference, costs on that difference) and **reset its stop** to 3 × the average daily move below
    that fill price. This is what "monthly rebalancing" means here: it mirrors the control (section 6), which is traded
    back to 20% each month, so the difference between them is the signal and the risk rules, not drift.
- **Between month-ends:** positions drift with prices. The 20% rule still applies every day: anything above 20% at a
  close is trimmed to 18% at the next close; a 22% alert is logged.
- **Stops:** checked at every close, sale at the next close (the engine's rule). **After a stop-out**, the asset is
  bought again at the **next month-end decision** if its signal is still **hold** then (not only after the signal
  switches off and on, which is the rule for daily-signal strategies like `ma_trend`; for a monthly rule that could
  keep an asset in cash for years).
- **Max 5 open positions:** always satisfied (4 assets).
- **Circuit breaker:** the engine's rule (after a 10% fall from the peak, no new trades for the assumed 21-trading-day
  review in a backtest; 20% hard floor = no new trades for good). While it is on: no new positions **and no top-ups**;
  sales, stop-outs, trims and resizes that *reduce* a position still happen.
- **Currency:** XIU.TO's returns are added as if in the same currency (the lab's usual simplification).

## 5. Parameters (no search was done)

| Parameter | Value | Why |
|---|---|---|
| `lookback_months` | **12** | Moskowitz, Ooi & Pedersen (2012), their headline setting. |
| `skip_months` | **0** | The paper's rule uses the most recent 12 months, skipping nothing. |
| Hurdle | **the T-bill return over the same 12 months** | The paper uses the *excess* return (above T-bills). |
| Rebalance | **monthly** (month-end decision, next-close fill) | The paper (one-month holding period); Tessy's brief. |
| Max per asset | **20%** | Lab risk rule. |

**No parameter search was done, and none will be.** The over-search counter (`journal/trials.csv`) records
**1 configuration** for the portfolio, "pre-registered values (spec strategies/specs/ts_momentum.md), no search".

**Sensitivity grid (Skeptic check 4, training data only, fixed now):** `lookback_months` ∈ {6, 9, 12, 15, 18} ×
`skip_months` ∈ {0, 1} (`skip_months = 1` measures the 12 months ending one month ago, a common variant). It only checks
the frozen choice; it is never used to pick a different one. The check's usual rule applies: the chosen setting's
neighbours must have a median training Sharpe of at least 70% of its own, and none may lose money.

## 6. Assets and benchmarks

- **Assets:** SPY, XIU.TO, GLD and IEF, as one portfolio.
- **Fair control benchmark (new for this idea):** the same four assets at **20% each, always held** (80% invested,
  20% cash earning the T-bill rate), rebalanced back to 20% each at the start of every month, with the same costs and
  next-close timing (the lab's `fixed_mix`). It isolates whether the momentum signal adds anything. **Compared on
  Sharpe ratio** (return above cash per unit of risk), because it is always 80% invested while the strategy is often
  less invested, so their risk levels differ; the equal-risk mix (below) does the same-risk comparison on return.
- **Also compared (Skeptic check 3, test period 2018+, after costs, next-close execution, normal AND double costs):**
  - equal-weight buy-and-hold of the four assets (25% each, rebalanced monthly), on Sharpe;
  - the broad index (SPY buy-and-hold), on Sharpe;
  - the same-risk mix (the equal-weight basket + cash, sized to the strategy's volatility on 2005-2017 only), on CAGR;
  - the equal-risk mix (the same mix rescaled to the strategy's 2018+ volatility, session 5 item 1), on CAGR.
  Check 3 PASSES only if the strategy beats **all five** (these four + the control) at normal **and** double costs.
- **Data split:** training 2005-2017 (development and debugging only, plus demo data), test 2018 onward (touched
  **once**, with `python run_lab.py --reason "ts_momentum pre-registered test"`).

## 7. Sample-size rule (agreed now, before any results)

Round-trip trades would be muddied by monthly resizes and stops, so **for `ts_momentum` check 5 is:**

- **PASS** if **both**:
  1. at least **30 signal changes** in total across the four assets over the whole measured period (a signal change =
     a month-end decision that flips an asset from hold to cash or from cash to hold; the first decision is not a
     change), **and**
  2. the test period covers at least **5 years** of data.
- Otherwise **NEEDS MORE DATA**. The report also shows how many signal changes fell in the test period.

## 8. What would prove it wrong (decided now)

`ts_momentum` **FAILS** if, in the 2018+ test period, **after costs and with next-close execution**, it fails to beat
**the fair control benchmark** (on Sharpe) **or the equal-risk mix** (on CAGR), at normal costs **or** at double costs.

On top of that, every other Skeptic Checklist item applies as usual (look-ahead, out-of-sample, beating equal-weight
buy-and-hold, SPY and the same-risk mix, sensitivity, sample size as above, drawdown vs equal-weight buy-and-hold,
regimes 2008/2020/2022, consistency as a warning), and a FAIL on any of them fails the idea.

## 9. If it fails

No tweaks. A different lookback, skip, hurdle, sizing, volatility scaling, shorting, asset list, stop rule or
rebalancing rule would be a **new idea** with a new spec, a new trials row and a new test-period look, and the journal
must say so.
