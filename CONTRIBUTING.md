# Contributing (for busy collaborators)

Thanks for helping! This is Tessy's learning lab for testing trading rules on **past data only**.
Your role is light and optional: read, comment, and suggest ideas whenever you have time. Five minutes is plenty.

## Where the reports live
- Every tested strategy has a report at `reports/<strategy-name>/report.md`
  (e.g. [reports/ma_trend/report.md](reports/ma_trend/report.md)). GitHub shows it with charts.
- Start with the **Skeptic Checklist** table near the top of each asset section: it shows the verdict
  (PASS / FAIL / NEEDS MORE DATA) and why.
- The experiment log is in [`journal/`](journal/). New words are explained in [LEARNING.md](LEARNING.md).

## How to comment on a pull request
A pull request (PR) is a proposed change waiting to be accepted.
1. Open the repo on GitHub → **Pull requests** tab → click the PR.
2. To comment generally, scroll to the bottom and type in the box → **Comment**.
3. To comment on a specific line, go to **Files changed**, hover over the line, click the blue **+**, write, then **Add single comment**.
4. Questions like "why this rule?" or "have you tried X?" are very welcome. You can't break anything by commenting.

## How to submit an idea
1. **Issues** tab → **New issue** → **Strategy idea** → **Get started**.
2. Fill in the short form (it works on a phone). Rough is fine; the researcher will turn it into exact rules.
3. The most useful field is **"What would prove this wrong?"** Decide it *before* seeing results.

## Ground rules
- **Paper only.** No live trading, no real money, no broker connections. This is research and learning.
- **The Skeptic decides.** Every idea, including yours and Tessy's, must pass the full Skeptic Checklist.
  Past experience and a good story aren't evidence; the out-of-sample test is. Most ideas fail. That's normal.
- **No shared money.** Nothing here is investment advice, and no money is pooled or managed for anyone.
- **Tessy makes the decisions.** Suggestions are welcome; there's no obligation to reply quickly or at all.
- **Never paste passwords or API keys** into issues, comments or code.
