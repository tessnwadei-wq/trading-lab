# Pre-registered spec: `vol_target` (volatility targeting)

**Status: FROZEN.** Written and committed on its own on 2026-09-26 (session 4), **before any code was written for
this idea and before anyone looked at its 2018+ (test-period) results.** No backtest of this idea, on any data, had
been run when this file was committed. Every `vol_target` report shows the commit ID of this file.

Changing anything below after the first test-period look makes it a **new idea** (a new name, a new spec, a new
look), never a fix to this one.

Source of the idea: [issue #4](https://github.com/tessnwadei-wq/trading-lab/issues/4) (proposed by the researcher
agent in session 3; "no 2018+ data was looked at").

## 1. The question

Is "holding less stock when markets are jumpy" better than **simply owning less stock all the time** (the same-risk
mix)? Volatility targeting only changes *how much* of the asset we hold. If it can't beat a constant "X% asset + rest in
cash" mix that is equally bumpy, it adds nothing.

## 2. Published sources

- Moreira & Muir, "Volatility-Managed Portfolios", *Journal of Finance* 72(4), 2017. Scale the market exposure by the
  inverse of the **previous month's realised variance of daily returns**, rebalanced **monthly**.
- Harvey, Hoyle, Korgaonkar, Rattray, Sargaison & Van Hemert, "The Impact of Volatility Targeting", *Journal of
  Portfolio Management* 45(1), 2018. Target a fixed volatility (they use **10%** a year), estimated from the
  **standard deviation of daily returns**; exposure = target ÷ estimated volatility. They find higher Sharpe ratios for
  equities and fewer extreme returns.
- Counterpoint: Cederburg, O'Doherty, Wang & Yan, "On the performance of volatility-managed portfolios", *Journal of
  Financial Economics* 138(1), 2020. Most of the benefit disappears out of sample. This is what our test checks.

**How our version differs from the papers (on purpose, and decided now):**
1. **No borrowing.** Both papers let exposure go above 100% (leverage) when markets are calm. The lab forbids leverage,
   so our weight is capped at 100%. That removes half of the published mechanism (buying *more* in calm times), so we
   expect a weaker effect than the papers report.
2. **Target ÷ volatility** (Harvey et al.), not target ÷ variance (Moreira & Muir). It's gentler and easier to explain.
3. **A plain 21-day standard deviation**, not an exponentially weighted one. Simplest version first.

## 3. The exact rule

Applied to one asset at a time (a 100% research account, like the lab's other single-asset reports).

1. **When:** at the close of the **last trading day of each calendar month**, on the asset's own trading calendar.
2. **Measure volatility:** `vol` = standard deviation (pandas default, `ddof=1`) of the last `vol_days` **daily
   returns** (close-to-close % changes), ending with that day's close, × √252 (to turn it into a yearly number).
   Uses only prices up to and including that close.
3. **Target weight:** `w = min(1, target_vol / vol)`. Never above 100% (no borrowing), never below 0% (no shorting).
   The rest of the account (`1 − w`) is in cash earning the T-bill rate, like every lab strategy.
4. **Trade:** the lab's standard timing: decided at that close, **traded at the next close** (the first trading day of
   the new month). Between month-ends there are no trades, so the actual weight **drifts** with prices.
5. **Warm-up:** until the first month-end with at least `vol_days` daily returns, the strategy holds cash (like every
   lab strategy's warm-up) and results are measured from the first day it can act.

Examples: vol 8% → w = 100%. vol 16% → w = 75%. vol 40% → w = 30%.

## 4. Rebalancing and costs

- **Monthly, at month-end, no drift band.** At each month-end the weight is set to the new `w`. (The issue says
  "rebalanced once a month"; the papers rebalance monthly. A drift band was considered and **not** added: it would be a
  third parameter.)
- If the new target is exactly the old target (in practice only when both are 100%), nothing is traded. A 100%
  position doesn't drift, so there is nothing to fix.
- **Costs on every weight change:** each rebalance trades `|w_new − w_actual|` of the account, where `w_actual` is the
  drifted weight just before the trade, and pays the lab's standard 0.10% + 0.05% = **0.15%** on that amount
  (0.30% in the double-cost check). Buying the first position counts too.

## 5. Parameters (no search was done)

| Parameter | Value | Why |
|---|---|---|
| `target_vol` | **12% a year** | Set in issue #4 before any results. Harvey et al. use 10% *with* borrowing; with our 100% cap a slightly higher target keeps the strategy fully invested in calm markets (US and Canadian stock ETFs typically move ~15-20% a year) and cuts back only in stormy ones. Common sense, not fitted. |
| `vol_days` | **21 trading days** | About one month: Moreira & Muir use the previous month's daily returns. |
| Rebalance | **monthly** (last trading day, traded next close) | Both papers; issue #4. |
| Cap | **100%** | Lab rule: no borrowing. |

**No parameter search was done, and none will be.** Neither value was chosen by looking at any backtest, on training or
test data. The over-search counter (`journal/trials.csv`) records **1 configuration per asset**, "pre-registered values
(spec strategies/specs/vol_target.md), no search".

**Sensitivity grid (Skeptic check 4, training data only, fixed now):** `target_vol` ∈ {8%, 10%, 12%, 14%, 16%} ×
`vol_days` ∈ {10, 21, 42, 63}. It only checks the frozen choice; it is never used to pick a different one.

## 6. Assets and benchmarks

- **Assets:** SPY and XIU.TO, each on its own. (GLD later, as a new idea.)
- **Benchmarks (test period 2018+, after costs, next-close execution, normal AND double costs):**
  buy-and-hold of the same asset, the broad index (SPY), and **the same-risk mix**: `X%` of the asset + the rest in cash,
  rebalanced monthly, where `X` = the strategy's volatility ÷ the asset's volatility **measured on 2005-2017 only**,
  capped at 100%, then frozen. This is the lab's standard Skeptic check 3.
- **Data split:** training 2005-2017 (development and debugging only), test 2018 onward (touched **once**, with
  `python run_lab.py --reason "vol_target pre-registered test"`).

## 7. Sample-size rule (agreed now, before any results)

Check 5 normally counts round-trip trades (at least 30). This strategy is almost never fully out of the market, so it
would show about 1 "trade". Instead, **for `vol_target` check 5 is:**

- **PASS** if **both**:
  1. at least **30 "active rebalances"** over the full period, where an active rebalance is a month-end trade that
     changes the weight by **at least 5 percentage points** (smaller changes barely differ from a constant mix), **and**
  2. the test period covers at least **5 years** (60 months) of data.
- Otherwise **NEEDS MORE DATA**.

Why: each active rebalance is one independent decision the rule made differently from the constant mix, like a trade
is for an in/out rule. 30 matches the lab's usual bar. The report also shows how many active rebalances fell in the
test period.

## 8. What would prove it wrong (decided now)

`vol_target` **FAILS** if, in the 2018+ test period, **after costs and with next-close execution**, it does **not earn a
higher yearly return (CAGR) than the same-risk mix**, at normal costs **or** at double costs, on **either** asset.

That is the key test for Tessy's question. On top of it, every other Skeptic Checklist item applies as usual (look-ahead,
out-of-sample, beating buy-and-hold and SPY on Sharpe, sensitivity, sample size as above, drawdown, regimes,
consistency), and a FAIL on any of them fails the idea. The issue's other two "wrong if" points are covered by:
- "only one `target_vol` / `vol_days` pair works" → check 4 (sensitivity grid above);
- "lags badly after crashes (e.g. 2020)" → check 7 (regime table, 2020 row), reported in words in the journal.

## 9. If it fails

No tweaks. A different target, window, band, asset, variance scaling or leverage would be a **new idea** with a new
spec, a new trials row and a new test-period look, and the journal must say so.
