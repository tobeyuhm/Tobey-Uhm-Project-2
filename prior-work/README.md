# Prior work (copied unchanged)

These files are copied byte-for-byte from my lab repositories so the lineage of this project is visible in one place. They are not run by the app.

| Folder | Lab | Original location | What Project 2 reuses |
|---|---|---|---|
| `lab13/` | Lab 13, Portfolio Mandate Defense (Oct. 15, 2026) | github.com/tobeyuhm/Lab-13- | S1-S10 typing, the mandate checker logic (now `p2/mandate.py`, Lab 13 answer key in the tests), the question for the CIO |
| `lab15/` | Lab 15, Portfolio Stability (Oct. 22, 2026) | same repository | Estimation conventions, the grid search (now `p2/optimizer.py`, Lab 15 answer key in the tests), the window-instability finding |
| `lab17/` | Lab 17, Rates as of a Date (Oct. 29, 2026) | Lab 17 repository | The one-business-day lag and no-revision evidence for Treasury yields (`docs/data-card.md`, Lab 17 values in the tests) |

Lab 15's optimizer had no single-company constraint. Its all-months answer (BIL 80% / JOBY 20%) breaks Lab 13's 8% issuer rule. Project 2 adds the rule (see `docs/validation-and-ai-use.md`, AI-output check A).
