# overfit_demo (2026-09-26)

- **Idea:** Deliberately bad process, run as a teaching example. Fast/slow moving-average crossover with a band and a minimum
  holding period; all 4 parameters picked by brute force (1,920 combinations) on 2005-2017 data.
  Source: teaching example; see Bailey et al., "Pseudo-Mathematics and Financial Charlatanism" (2014).
- **Data:** ⚠️ **SYNTHETIC demo data**. SPY and XIU.TO, 2005 – Sept 2026.
- **Parameters chosen by the search (training data only):**
  - SPY: fast 25, slow 210, band 2%, min hold 40 days (best of 1,920; median combination scored 0.07)
  - XIU.TO: fast 5, slow 80, band 5%, min hold 1 day (best of 1,920; median combination scored 0.42)
- **Result (demo data):**

  | | SPY-like | XIU.TO-like |
  |---|---|---|
  | Sharpe, train → test | 0.48 → 0.59 | **0.78 → 0.35** |
  | Test Sharpe vs buy-and-hold / SPY | 0.59 vs 0.68 / 0.68 | 0.35 vs 0.33 / 0.68 |
  | Sensitivity (neighbours' median vs chosen) | **0.29 vs 0.48** | 0.64 vs 0.78 |
  | Trades (total / test) | **19** / 8 | 46 / 25 |

- **Verdict:** **FAIL**.
  - SPY: "It failed 2 of 7 checks. Main problem (costs): after costs it does not beat simply buying and holding, so it isn't earning its complexity." (also failed parameter sensitivity; too few trades)
  - XIU.TO: "It failed 2 of 7 checks. Main problem (out-of-sample): performance collapsed on data it had never seen, a classic sign of luck or overfitting."
- **Lesson:** The skeptic caught the over-tuned strategy in two different ways. On XIU.TO the training Sharpe of 0.78 (double
  buy-and-hold's!) more than halved on unseen data. The textbook overfitting pattern. On SPY the chosen setting was a
  lone bright spot on the sensitivity heatmap, with neighbours scoring far worse, and it rested on only 19 trades. Takeaway:
  **the best result from a big search is mostly a measure of how hard you searched**, not of a real edge.
- **Report:** [reports/overfit_demo/report.md](../reports/overfit_demo/report.md)
