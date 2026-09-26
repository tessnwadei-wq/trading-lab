# overfit_demo, real data, lab v2 (2026-09-26)

- **Idea:** Deliberately bad process: fast/slow moving-average crossover with a band and a minimum holding period,
  all four knobs chosen by brute force (1,920 combinations per asset) on 2005-2017. A teaching example, not a trading idea.
- **Data:** real (Yahoo Finance, `data/csv/`); SPY and XIU.TO, 2005 – 25 Sep 2026; cash earns the T-bill rate.
- **Parameters:** chosen by the search (now scored on Sharpe above cash): SPY `fast=10, slow=150, band=0.02, min_hold=10`;
  XIU.TO `fast=50, slow=80, band=0.0, min_hold=40`. Same winners as the lab-v1 run.
- **Result:**

  | | SPY | XIU.TO |
  |---|---|---|
  | Sharpe, train → test | 0.87 → 0.68 | 0.83 → 0.45 |
  | Test Sharpe vs buy-and-hold / SPY | 0.675 vs 0.677 / 0.677 | 0.45 vs 0.67 / 0.68 |
  | Test CAGR vs same-risk mix | 10.3% vs 8.9% | 8.0% vs 9.2% |
  | Luck bar for best-of-1,920 (training) | 0.98 → rough chance it's real **36%** | 0.97 → **32%** |
  | Trades (total / test) | 31 / 13 | 30 / 13 |

- **Verdict:** **FAIL** (both assets). SPY: "...fell short of buy-and-hold at normal costs (Sharpe 0.675 vs 0.677, short by 0.002)...";
  XIU.TO: "...fell short of buy-and-hold at normal costs (Sharpe 0.45 vs 0.67, short by 0.21)..." (full sentences in the report).
- **Lesson:** The new over-search counter says it plainly: after 1,920 tries, a training Sharpe of ~0.85 is *below*
  what the luckiest useless rule would be expected to show (~0.98). The SPY winner lost to buy-and-hold by only 0.002,
  which shows why the skeptic now prints three decimals for near-ties. Also note: 13 test-period trades is thin evidence.
- **Report:** [reports/overfit_demo/report.md](../reports/overfit_demo/report.md)
