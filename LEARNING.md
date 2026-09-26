# Learning notes (glossary)

Plain-English explanations of every concept used in the lab. Add to it whenever something new comes up.

## Basics

**Backtest**: Replaying history to see what *would* have happened if you'd followed a rule. Useful, but
it's easy to fool yourself, which is why the lab has a Skeptic.

**Rules-based strategy**: A strategy written as exact rules a computer can follow ("buy when X, sell when Y"),
with no gut feel. That makes it testable.

**Long-only**: You can only own an asset or hold cash. You can't bet on prices falling ("shorting").

**Buy-and-hold**: Buy on day one and never sell. The simplest possible strategy, and surprisingly hard to beat.
Every strategy must be compared with it.

**Broad index**: A basket representing a whole market, like the S&P 500 (the 500 biggest US companies).
We use SPY (an ETF tracking the S&P 500) as our broad index. If a clever strategy can't beat just owning
the index, there's no reason to use it.

**ETF (Exchange-Traded Fund)**: A fund you buy like a single stock that holds a whole basket. SPY holds the
S&P 500; XIU.TO holds the 60 biggest Canadian companies; GLD holds gold.

**Daily bar**: One day of price data (open, high, low, close). The lab uses the closing price.

**Adjusted close**: The closing price adjusted for dividends and share splits, so that "price went from A to B"
reflects what an investor actually earned.

## Costs

**Commission**: The fee (or bid/ask spread) paid each time you trade. Lab default: 0.10% per trade.

**Slippage**: The gap between the price you expected and the price you actually got. Lab default: 0.05%.
Together that's 0.15% every time we buy *and* every time we sell. Strategies that trade a lot get hit hardest.

## Scorecard numbers

**CAGR (Compound Annual Growth Rate)**: The steady yearly growth rate that would turn your starting money into
your ending money. "8% CAGR" ≈ the account grew as if it earned 8% every year.

**Volatility**: How bumpy the ride is (how much daily returns swing), expressed per year. Higher = scarier.

**Sharpe ratio**: *Excess* return divided by volatility: "how much reward, above what cash pays, per unit of
bumpiness". Lets you compare a calm strategy with a wild one fairly. Rough guide: <0.5 weak, ~1 good, >2 in a
backtest = be suspicious. The lab uses Sharpe as its main "does it beat buy-and-hold?" measure, because a strategy
that sits in cash half the time *should* earn less, but it should be less bumpy too.
*Changed in session 2:* Sharpe used to be return ÷ volatility, as if cash paid 0%. It is now calculated on
**excess return** (see below), which is the standard way. That lowers everyone's Sharpe a bit (by about the cash
rate ÷ volatility), and lowers calm things more than bumpy ones, so the numbers in older reports aren't directly
comparable with new ones.

**Risk-free rate (cash rate)**: What you can earn with (almost) no risk, by lending to the US government for a few
months through **Treasury bills (T-bills)**. The lab uses the 13-week T-bill yield (Yahoo ticker `^IRX`, file
`data/csv/IRX.csv`). It has ranged from ~0% (2009-2015, 2020-21) to ~5% (2007, 2023-24). Money a strategy keeps in
cash now earns this rate every day, which is what would happen in a real brokerage or savings account.
Simplification: the US rate is used for Canadian XIU.TO too.

**Excess return**: Return *minus* what cash would have paid over the same time. If a strategy made 7% in a year when
T-bills paid 5%, its excess return was only 2%: that 2% is all it earned for taking risk. A strategy only deserves
credit for its excess return.

**Average share invested**: On an average day, what share of the account was in the market (the rest in cash).
For an all-in-or-all-out rule, this is the same as "time in market".

**Drawdown**: How far the account is below its previous high. **Max drawdown** is the worst peak-to-trough fall.
A -50% drawdown needs a +100% gain to recover, which is why drawdowns matter so much.

**Recovery time**: How long it took to climb back to the old high after the worst fall.

**Win rate**: The share of trades that made money. Trend-following strategies often have low win rates
(many small losses, a few big wins), so a low win rate isn't automatically bad.

**Time in market**: The share of days the strategy was invested rather than in cash.

**Trade (round trip)**: One buy plus the matching sell.

## The Skeptic's concepts

**Look-ahead bias**: Accidentally using information you wouldn't have had at the time, e.g. deciding on
Monday using Tuesday's price. It makes backtests look amazing and is the #1 beginner mistake. The lab prevents it
by acting one day *after* each decision, and tests for it with a **truncation test**: hide the future and check that
no past decision changes.

**In-sample / training period**: The data you're allowed to study and tune on (here, 2005–2017).

**Out-of-sample / test period**: Data kept aside and used **once**, after all choices are frozen (here, 2018 onward).
It's the closest thing to "the future" a backtest has. If you peek and re-tune, it stops being a fair test.

**Overfitting (curve fitting)**: Tuning a rule so precisely to past data that it captures random noise rather than a
real pattern. It looks brilliant in training and disappoints on new data. See `strategies/overfit_demo.py`.

**Multiple testing / data snooping**: If you try enough rules, some will look great by pure luck. Trying 1,920
combinations and keeping the best is almost guaranteed to find a "lucky" one. That's why the journal records
*every* experiment, including failures.

**Parameter**: A number inside a rule, like the "200" in "200-day moving average".

**Parameter sensitivity**: Checking whether nearby parameter values (190, 210…) also work. A real effect is usually a
smooth "hill"; a fluke is a lone spike (a "magic number").

**Sample size**: How many trades the result is based on. With fewer than ~30 trades, luck can easily explain the
result. Like judging a coin after 5 flips.

**Same-risk mix (same-risk benchmark)**: A fairer yardstick for a strategy that is often in cash. It is simply
"X% in the asset, the rest in cash earning interest", rebalanced monthly, where X is picked so the mix is exactly
as bumpy (volatile) as the strategy. Example: the 200-day rule on SPY was about 57% as bumpy as SPY in 2005-2017,
so its same-risk mix is 57% SPY + 43% cash. If the strategy can't earn more than that, all it did was own less of
the asset, and you could do that with no rules at all. X is set on **training data only** (2005-2017) and then
frozen, so the benchmark never peeks at the test period. At equal risk the fair comparison is plain return
(CAGR), not Sharpe. Mixing an asset with cash leaves its Sharpe almost unchanged, so a Sharpe comparison would just
repeat the buy-and-hold one.

**Rebalancing**: Trading back to your target percentages after prices have moved them (e.g. once a month). It
costs a little each time.

**Regime**: A period with a distinct market "mood": a crash (2008, 2020), a slow bear market (2022), a calm bull
market. Good strategies shouldn't fall apart in one regime.

**PASS / WARN / FAIL**: Each Skeptic check gets one. **FAIL** means the strategy fails, full stop. **WARN**
means "you should know this": it's shown in the report and the verdict sentence, but doesn't fail the
strategy on its own. **NEEDS MORE DATA** means we can't tell yet (e.g. under 30 trades).

**Consistency (check 8)**: Does the strategy behave about the same in training (2005-2017) and testing (2018+)?
A Sharpe ratio measured over ~10 years has a margin of error of roughly ±0.3, so the lab WARNs if the two differ by
more than 0.4 *in either direction*. A big jump up is not good news. It usually means the test period happened to
suit the rule (XIU.TO: 0.16 → 0.68), not that the rule suddenly got better. Either way the period, not a steady
edge, drove the result.

**Over-search (multiple testing) counter and luck bar**: `journal/trials.csv` counts every parameter combination the
lab has ever tested on real data. The more you try, the higher the Sharpe the *luckiest useless* rule will show by
chance: over ~12 years of data, the best of 1 useless rule scores about 0, the best of 100 about 0.7, the best of
2,000 about 1.0. That expected-best-by-luck number is the **luck bar**; a result needs to clear it. The report's
"rough chance it's real" compares the result with the bar. This is a simplified version of the **deflated Sharpe
ratio** (Bailey & López de Prado, 2014). Example: overfit_demo's best-of-1,920 training Sharpe of 0.87 sits *below*
its luck bar of 0.98, so pure luck explains it.

**Synthetic (demo) data**: Made-up prices generated by a computer to *resemble* real markets. Useful for testing
that code works; useless for judging a strategy. A strategy tested only on synthetic data can never be approved.

**Whipsaw**: When a trend rule sells after a drop and then has to buy back higher after a quick rebound, losing a
little each time. The 2020 crash-and-rebound is a classic whipsaw period for trend filters.

## Strategies

**Moving average (MA)**: The average closing price over the last N days, recalculated daily. It smooths out noise.
The **200-day MA** is a widely watched "long-term trend" line.

**Trend filter**: A rule that's invested only when the trend is up (e.g. price above its 200-day MA) and in cash
otherwise. It aims to sidestep big crashes, at the cost of some whipsaws.

**Moving-average crossover**: Invested when a fast (short) MA is above a slow (long) MA.

**Band (buffer)**: Requiring the price to move a few % past a line before switching, to reduce whipsaws.

## Other markets (coming later)

**Commodity**: A raw material like gold, oil or wheat. Gold (GLD) doesn't pay dividends or earnings; its price is
driven by fear, interest rates and the US dollar.

**Forex (FX)**: Trading one currency against another. **USD/CAD** (Yahoo ticker `CAD=X`) is how many Canadian dollars
one US dollar buys. When it goes up, the CAD got weaker.

**Correlation**: How much two things move together, from -1 (opposite) through 0 (unrelated) to +1 (in lockstep).
Combining assets with low correlation smooths a portfolio.

**Leverage**: Trading with borrowed money so gains *and losses* are multiplied. Common in forex; not allowed in this lab.

## Risk (enforced in code from phase 2: `lab/portfolio.py`)

**Portfolio backtest**: Running one strategy on several assets at once as a single account (here SPY, XIU.TO and
GLD), so the risk rules can limit how the money is shared out.

**Position size**: How much money goes into one trade.

**Stop (protective stop, exit point)**: A price decided in advance at which you sell to cap a loss. Without one,
"how much am I risking?" has no answer.

**Risk per trade**: How much you'd lose if the trade hits its stop, as a share of the account. It is NOT the
position size: a 20% position with a stop 3% below entry risks 20% × 3% = 0.6% of the account. The lab's rule: max 1%.

**Volatility-based position sizing**: Choosing the size so every trade risks the same 1%, whatever the asset.
The stop is placed a distance below entry that depends on how much the asset normally moves: here 3 × its
**average daily move** over the last 20 days (a closing-price version of the **ATR, Average True Range**).
Then *size = 1% ÷ stop distance*. A calm asset (small moves, close stop) gets a bigger position; a jumpy one (big
moves, far stop) a smaller one. Why not a fixed 5% stop? It would be knocked out by normal wiggles in a jumpy
market and be needlessly loose in a calm one. In practice, for SPY/XIU.TO/GLD the stop is usually only 2-4% away,
so the 1% rule would allow 25-50% positions and the 20% cap below does the limiting instead.

**Gap**: When a price jumps between one close and the next, skipping over the stop. The loss can then be bigger than
planned. The lab only checks stops at the close, so the report shows the worst real loss per trade.

**Max position size / max open positions**: No more than 20% of the account in one position and no more than 5
positions at once. A position that grows past 20% is **trimmed** (partly sold) back to 18%. The small buffer
avoids selling a sliver every day.

**Drawdown circuit breaker**: An automatic "stop and think" switch. If the account falls 10% from its peak, the
lab opens no new trades, logs it, and flags it for review in the report. In a backtest nobody can do the review,
so the lab simulates it as a ~1-month (21 trading-day) pause, after which trading resumes and the current value
counts as the new peak. Existing positions keep their normal exits.

**Currency-hedged**: Ignoring exchange-rate moves when adding up assets priced in different currencies. The
portfolio treats XIU.TO (Canadian dollars) this way, which is a simplification.
