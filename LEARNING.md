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
Monday using Tuesday's price. It makes backtests look amazing and is the #1 beginner mistake. It can hide in two
places: in the *rule* (a signal that reads future prices) and in the *engine* (trading at a price you only knew after
deciding, see **Execution timing** below). The lab tests both. The **truncation test** hides the future and checks
that no past decision changes. The **trade-timing test** (added in session 3) changes one day's closing price and
checks that what was held right after that close doesn't change, which proves the trade happened at a *later* close
than the decision.

**Execution timing (same close vs next close)**: *When* a trade happens relative to the decision. The lab only has
one price per day, the close. A rule like "buy when the price closes above its 200-day average" can only be checked
once that close is known, and by then the market has shut. So the lab now decides at day t's close and trades at
**day t+1's close** ("next close"); gains or losses start the day after that. In real life you'd do this with a
**market-on-close order** (an order to buy or sell at whatever the closing price turns out to be).
Until session 3 the lab traded at the *same* close it decided on ("same close"). That setting is kept only for the
*Timing cost* table in each report.

**Why same-close is optimistic**: Trading at the very price you used to decide is like betting on a race after
seeing the finish photo: you always get in right at the turning point. With next-close timing you get the price one
day later, which is usually a bit worse, because trend rules switch exactly when the price has just moved. For the
200-day rule this cost about 0.5-0.7 percentage points a year, and it wiped out the rule's small lead over the
same-risk mix. Rule of thumb: the gap between the two timings shows how much a strategy relies on perfect timing.
If a strategy only works with same-close timing, it doesn't work.

**Test-period looks**: Every time anyone sees an idea's 2018+ results during development, that's a "look" at the
test period. The rule is *one look per idea*, because if you look, change something, and look again, the test data
starts to become training data without anyone noticing. The lab logs every look (date and reason) in
`journal/test_period_looks.csv`, and every report shows the count. `python run_lab.py --reason "..."` logs a look
automatically; re-running with nothing changed shows identical numbers and isn't counted again. More than one look
doesn't fail a strategy, but it's a warning that the test isn't completely fresh any more. A strategy *changed
because of* a look must be treated as a brand-new idea.

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

**Equal-risk mix (session 5)**: A second, stricter version of the same-risk mix. Because the same-risk mix is sized
on 2005-2017, a strategy can drift to being *bumpier* than it in 2018+, and then "beat" it simply because it took more
risk: more risk usually earns more in a rising market. That's what happened with `vol_target` (12.9% volatility vs the
mix's 11.8% on SPY). The equal-risk mix removes that loophole: take the same mix and rescale it so that **in 2018+ it
was exactly as bumpy as the strategy was in 2018+**. Mixing an asset with cash scales bumpiness in proportion, so if
the strategy was 9% bumpier than a 63% mix, the equal-risk mix holds 63% × 1.09 ≈ 69%. Then the fair question
"at the same risk, who earned more?" has a clean answer. If the strategy loses to it (at normal or double costs),
check 3 FAILs. It is capped at 100% (the lab never borrows).
*Why is it allowed to use test-period data?* The rule "never tune on the test period" is about **strategy decisions**:
anything that changes what the strategy does. The equal-risk mix changes nothing about the strategy; it is a
**yardstick for judging** the result after the fact, like measuring both runners' times on the same day's track. It
can only make a strategy's test harder to pass, never easier. (The same-risk mix keeps its training-only sizing, so a
strategy still has to beat both.)

**Rebalancing**: Trading back to your target percentages after prices have moved them (e.g. once a month). It
costs a little each time.

**Fractional position**: Holding part of the account in an asset and the rest in cash, e.g. 45% SPY + 55% cash,
instead of all-in or all-out. Added to the engine in session 4 (`lab/backtest.py`).

**Drift**: A fractional position doesn't stay put. If you hold 60% stock and stocks rise 10% while cash earns almost
nothing, the stock is now about 62% of the account. The lab lets the weight drift between rebalances, and only trades
when the strategy asks for a new weight.

**Turnover and costs on weight changes**: With fractional positions, costs are charged on how much of the account
changes hands: going from a drifted 62% to a new target of 50% trades 12% of the account, which costs 12% × 0.15% =
0.018% of the account. **Turnover** is the total traded over a year; `vol_target` traded about 1.3-1.5 times its
account a year, costing roughly 0.2% a year (double that at double costs).

**Pre-registration (freezing the rules first)**: Writing down *exactly* what you will test, and what result would count
as failure, **before** you look at the results, and making that record impossible to change quietly. The lab does it
by writing a spec (`strategies/specs/<idea>.md`) and committing it on its own; git gives that commit an ID and a time,
and pushing it to GitHub makes it public. Every report shows the ID. *Why:* after you've seen results it's very easy,
without meaning to, to pick the version that looked best ("let's use 10% instead of 12%", "let's count this differently")
and then believe it. If the rules and the pass/fail line were fixed beforehand, the result can't be argued away in
either direction. Medicine does this for clinical trials for the same reason. Rule: if a pre-registered idea fails, any
change is a *new* idea with its own spec and its own look. First used for `vol_target` in session 4.

**Sample size for always-invested strategies**: The usual "30 trades" rule counts round trips (all in → all out). A
strategy that is always partly invested almost never does a round trip, so it would show "1 trade". Instead, its spec
agrees another count in advance: for `vol_target`, at least 30 **active rebalances** (weight changes of 5 percentage
points or more, each one a separate decision that made it behave differently from a constant mix) and at least 5
years of test period.

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

**Volatility targeting (volatility-managed exposure)**: Instead of deciding *whether* to own an asset, decide *how
much*, based on how jumpy it has been lately. Once a month, measure the last 21 days' bumpiness (volatility) and hold
`12% ÷ volatility` of the account in the asset (never more than 100%, since the lab doesn't borrow), the rest in cash.
Calm market (volatility 8%): 100% invested. Stormy market (40%): 30% invested. The idea behind it: storms tend to
follow storms, but stormy periods haven't paid proportionally more, so stepping back during them might improve
return per unit of risk (Moreira & Muir 2017; Harvey et al. 2018). The catch: later studies found most of the benefit
disappears out of sample (Cederburg et al. 2020), and after a crash it stays cautious while prices bounce back.
Lab result (session 4, `vol_target`): **FAIL**. It edged out the same-risk mix after costs in 2018+ (by 0.1-0.6 points a
year) but was bumpier than it, lost to buy-and-hold and SPY per unit of risk, and missed most of the 2020 rebound.

**Time-series momentum (trend following on a 12-month view)**: For each asset on its own, ask once a month: "over
the last 12 months, did this asset earn more than cash?" If yes, hold it; if no, hold cash instead. It's called
*time-series* momentum because each asset is compared with **its own past**, not with other assets (comparing assets
with each other and buying the winners is *cross-sectional* momentum, a different idea). The belief behind it: news
sinks in slowly and people follow the crowd, so trends tend to carry on for months. Source: Moskowitz, Ooi & Pedersen
(2012), who found it across 58 futures markets, but their version could also bet on falls (shorting) and used
**volatility scaling** and leverage; later studies (Kim, Tse & Wald 2016; Huang et al. 2020) say much of the profit came
from that scaling rather than the signal. Lab result (session 5, `ts_momentum`, pre-registered): **FAIL**. On SPY,
XIU.TO, GLD and IEF with every risk rule, it scored a Sharpe of 0.47 in 2018+ vs 0.81 for simply holding the same four
assets at 20% each. The lab's tight stops, reset every month, stopped positions out on ordinary dips, so it was only
36% invested on average.

**Fair control benchmark**: A benchmark built to differ from the strategy in *one* way only. For `ts_momentum` it holds
exactly the same four assets at the same 20% each, all the time. So if the strategy loses to it, the signal (the only
difference) didn't help. It's like a drug trial's placebo group. Because it's always more invested than the strategy,
it's compared on Sharpe (reward per unit of risk), and the equal-risk mix handles the "same risk, more return?" question.

**Signal changes (sample size for monthly signal strategies)**: For `ts_momentum` the spec counts how many month-end
decisions flipped an asset between "hold" and "cash", across all four assets (at least 30, plus at least 5 years of
test period). Round trips would be muddied by the monthly resizes and stop-outs. It found 96 (45 in the test period).

**Stop reset (a lesson from session 5)**: A stop sits a fixed distance below a price you choose. In `portfolio_ma_trend`
the stop stays where it was set when you bought, so as the price rises the stop is left further and further behind. In
`ts_momentum` every monthly resize moved the stop up to just below the *current* price (about 1-2% below), so a normal
wobble in the next few weeks triggered it. Same rule, very different effect: how a risk rule interacts with a
strategy has to be thought through before the test.

## Other markets (coming later)

**Commodity**: A raw material like gold, oil or wheat. Gold (GLD) doesn't pay dividends or earnings; its price is
driven by fear, interest rates and the US dollar.

**Bond**: A loan you can buy and sell. The US government borrows by selling **Treasury bonds**; the 7-10 year ETF
**IEF** (added in session 5) holds ones that are repaid in 7-10 years and pays their interest. Two things make bonds
behave differently from stocks:
1. **Their price moves opposite to interest rates.** A bond paying 2% becomes less attractive when new bonds pay 4%,
   so its price falls until its yield matches; when rates fall, older bonds are worth more. The longer until repayment,
   the bigger this effect (**duration**: IEF's is about 7, so a 1-point rise in rates knocks roughly 7% off its price).
2. **They're often a "safe haven".** In most stock crashes (2008: IEF +17.9% while SPY fell 36.8%) investors rush to government
   bonds and central banks cut rates, so bonds rise while stocks fall (2020: IEF +10.0%). Over 2005-2026 IEF's daily moves had a correlation
   of about -0.28 with SPY. **But not always:** when inflation forces rates up fast, stocks *and* bonds fall together.
   2022 was IEF's worst year (-15.2%) at the same time as a stock bear market.
Bonds are much calmer than stocks, and a bond ETF's long-run return is roughly the interest it pays (IEF averaged about
3% a year).

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

**One-day buffer (session 4)**: The lab only sees a stop being hit at a close, and the sale fills at the *next* close,
so the price can keep falling for a day. To keep a normal stop-out within 1%, positions are now sized as if the stop
were **2 more average daily moves** further away than it really is (`STOP_FILL_BUFFER_MOVES` in `lab/config.py`). Why 2:
on training data (2005-2017), 81% of the portfolio's stop-sales filled within 2 average moves past the stop, and a
one-day fall bigger than 2 average moves happens on only ~7% of days. Effect on real data: stop-outs over 1% went from 1
to 0 (worst 0.99%), trades over 1% of any kind from 4 to 1. The one left was a sale on a -4% day in June 2020: a buffer
covers normal days, not every gap.

**Volatility-based position sizing**: Choosing the size so every trade risks the same 1%, whatever the asset.
The stop is placed a distance below entry that depends on how much the asset normally moves: here 3 × its
**average daily move** over the last 20 days (a closing-price version of the **ATR, Average True Range**).
Then *size = 1% ÷ stop distance*. A calm asset (small moves, close stop) gets a bigger position; a jumpy one (big
moves, far stop) a smaller one. Why not a fixed 5% stop? It would be knocked out by normal wiggles in a jumpy
market and be needlessly loose in a calm one. In practice, for SPY/XIU.TO/GLD the stop is usually only 2-4% away,
so the 1% rule would allow 25-50% positions and the 20% cap below does the limiting instead.

**Gap**: When a price jumps between one close and the next, skipping over the stop. The loss can then be bigger than
planned. The lab only checks stops at the close, and (with next-close timing) sells at the *following* close, so a
price that keeps falling for that extra day also adds to the loss. The report shows the worst real loss per trade.

**Order / fill**: An *order* is an instruction to buy or sell; it is *filled* when the trade actually happens. In the
lab every decision at a close becomes an order that fills at the next close. That's why a position can sit slightly
above the 20% cap for one day: it's found above 20% at one close and trimmed at the next.

**Max position size / max open positions**: No more than 5 positions at once, and the 20% rule, worded (session 4)
exactly as enforced: *"No buy that would take a position above 20%. Anything above 20% at a close is trimmed to 18% at
the next close."* **Trimmed** means partly sold. Trimming to 18% rather than 20% avoids selling a sliver every day.
Because the trim waits a day, a position can sit a little above 20% for one close; that's expected.

**Position alert (22%)**: If a position *ends a day* above 22%, something unusual happened (a big one-day jump, or the
rest of the account fell while that asset's market was shut). The lab logs it, prints it and lists it in the report.

**Drawdown circuit breaker**: An automatic "stop and think" switch. If the account falls 10% from its peak, the
lab opens no new trades, logs it, and flags it for review in the report. Existing positions keep their normal exits.
A **hard floor** also stops new trades if the account is ever 20% below its all-time high, so several 10% falls in a
row can't quietly add up.

**Circuit breaker manual reset**: In paper trading (a later phase) the breaker **never restarts by itself**. After
it trips, no new trades are opened until a person has reviewed what happened and runs
`python reset_circuit_breaker.py --who Tessy --reason "what I checked"` and **types `RESET`** when asked. For the 20%
hard floor there's an extra step: type `HARD FLOOR` and your name again. The reset is refused without all of that, and
refuses to run at all from a script. Every reset is written to `journal/circuit_breaker_resets.csv` (when, who, why, and
what tripped it). This matters because an automatic restart means nobody ever actually looks. **Human-only rule
(CLAUDE.md):** agents must never run, script or suggest automating the reset. Only Tessy resets it.

**Append-only log and fingerprints (hashes)**: An append-only log can be added to but never edited or shortened. A
**hash** (here SHA-256) is a fingerprint of a file: change a single character and the fingerprint is completely
different. Each row of the reset log stores the fingerprint of everything above it (a "hash chain"), so editing an
old row breaks the chain; and the breaker remembers how many rows the log had and its fingerprint, so deleting rows is
caught too. Either way, resets are refused until the log is restored (e.g. from git). It catches accidents and casual
edits; someone determined could rewrite both files, which is why the files also live in git. A backtest can't wait for a person, so
there the lab makes an explicit **modelling assumption**: the review takes 21 trading days (about a month,
`CIRCUIT_BREAKER_REVIEW_DAYS` in `lab/config.py`, picked by common sense, not by looking at results), then trading
resumes and the current value counts as the new peak. Each portfolio report prints this assumption.

**Modelling assumption**: Something a simulation has to assume because it can't happen in a simulation (like a
person pressing "reset"). Good practice: write it down, choose it before seeing results, and show it in the report.

**Currency-hedged**: Ignoring exchange-rate moves when adding up assets priced in different currencies. The
portfolio treats XIU.TO (Canadian dollars) this way, which is a simplification.

## Paper trading (session 5: the plumbing)

**Paper trading (paper account)**: Following your rules with **pretend money** and **real, live prices**, day by day,
going forward. `python paper_trade.py` runs the lab's paper account on your PC: $10,000 of pretend money, orders
decided at one close and filled at the next, costs charged, every risk rule and the circuit breaker enforced, and every
order, fill and balance written down in `journal/paper/`.

**What a paper account proves:** that the *machinery* works in real time: prices arrive, orders are placed and filled at
the right close, costs are charged, the 20% rule and stops fire, the circuit breaker blocks trading and only a person can
restart it, and the records can't be quietly changed. It also shows real-life frictions a backtest hides: a price file
that's a day late, a holiday, forgetting to run it, and how it *feels* to watch a position fall.

**What it doesn't prove:** that a strategy works. A few months of results are far too short to judge (a Sharpe ratio
needs years; remember the ±0.3 margin of error over ~10 years), and pretend money has no **real fills**: a real broker's
price can be worse than the closing price, orders can fail, and real money changes how people behave. Right now it only
runs `buy_and_hold` of the control mix, *because no strategy has passed the Skeptic yet*, so this run tests the plumbing,
not an idea. Passing paper trading is a necessary step, never a sufficient one, before any thought of real money
(and real-money trading is not allowed in this lab at all).

**Checksum / tamper checks in the paper account**: The account file carries a fingerprint of its own contents, and it
remembers a fingerprint of the `journal/paper` logs, so a hand edit (even one that's committed to git) is caught. It
also refuses to run if its files don't match the last git commit, so every change, including a circuit-breaker reset,
has to be on the record first. This catches accidents and casual edits. Someone determined could still rewrite
everything *and* git history, which is why the files are also pushed to GitHub.

