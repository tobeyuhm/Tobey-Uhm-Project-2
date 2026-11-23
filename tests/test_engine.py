"""Validation tests. Run from the repository root:  python -m unittest discover -s tests -v"""

import copy
import hashlib
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from p2 import mandate as M                                   # noqa: E402
from p2 import pipeline as P                                  # noqa: E402
from p2.data import DATA, Prices, TreasuryCurve, load_config  # noqa: E402
from p2.estimates import estimate, from_inputs, portfolio_stats  # noqa: E402
from p2.optimizer import optimize                             # noqa: E402

CFG = load_config()
PRICES = Prices.load(assets=CFG["assets"])
CURVE = TreasuryCurve.load()

# ---- Lab 13 common case, typed from the lab handout (known answer) ----
LAB13_ASSETS = {
    "Cash": dict(issuer="none", issuer_exempt=True, days_to_redeem=0, reserve_eligible=True, trade_cost_bps=0),
    "Treasury bills": dict(issuer="U.S. Treasury", issuer_exempt=True, days_to_redeem=1, reserve_eligible=True, trade_cost_bps=0),
    "Treasury 10-year note": dict(issuer="U.S. Treasury", issuer_exempt=True, days_to_redeem=1, reserve_eligible=True, trade_cost_bps=0),
    "Global equity index fund": dict(issuer="diversified fund", issuer_exempt=True, days_to_redeem=2, reserve_eligible=False, trade_cost_bps=0),
    "Investment-grade bond fund": dict(issuer="diversified fund", issuer_exempt=True, days_to_redeem=3, reserve_eligible=False, trade_cost_bps=0),
    "Private real estate fund": dict(issuer="diversified fund", issuer_exempt=True, days_to_redeem=90, reserve_eligible=False, trade_cost_bps=0),
    "Acme Corp bonds": dict(issuer="Acme Corp", issuer_exempt=False, days_to_redeem=4, reserve_eligible=False, trade_cost_bps=0),
    "Acme Corp stock": dict(issuer="Acme Corp", issuer_exempt=False, days_to_redeem=1, reserve_eligible=False, trade_cost_bps=0),
}
LAB13_CFG = {"assets": LAB13_ASSETS, "reserve_usd_m": 100, "quarterly_distribution_usd_m": 0.75,
             "quarters_to_cover": 4,
             "limits": {"liquidity_window_days": 5, "min_liquid_share": 0.90, "issuer_limit": 0.08}}
ORDER13 = list(LAB13_ASSETS)
CANDIDATES = {"A": [2, 2, 10, 60, 26, 0, 0, 0], "B": [1, 0, 0, 55, 20, 15, 5, 4], "C": [1, 1, 0, 70, 20, 0, 0, 8]}


def lab13(weights_pct):
    return {n: w / 100 for n, w in zip(ORDER13, weights_pct)}


class KnownAnswerLab13(unittest.TestCase):
    """The mandate checker reproduces the Lab 13 answer key."""

    def test_reserve_minimum(self):
        self.assertAlmostEqual(M.reserve_minimum(LAB13_CFG), 0.03)

    def measured(self, cand):
        rules = M.check(lab13(CANDIDATES[cand]), LAB13_CFG)
        return {r["id"]: (round(r["measured"] * 100, 1), r["passed"]) for r in rules}

    def test_candidate_a_passes(self):
        self.assertEqual(self.measured("A"), {"M1": (100.0, True), "M2": (0.0, True), "M3": (14.0, True),
                                              "M4": (100.0, True), "M5": (0.0, True)})

    def test_candidate_b_fails_three(self):
        self.assertEqual(self.measured("B"), {"M1": (100.0, True), "M2": (0.0, True), "M3": (1.0, False),
                                              "M4": (85.0, False), "M5": (9.0, False)})

    def test_candidate_c_fails_one(self):
        self.assertEqual(self.measured("C"), {"M1": (100.0, True), "M2": (0.0, True), "M3": (2.0, False),
                                              "M4": (100.0, True), "M5": (8.0, True)})

    def test_long_only_probe(self):
        probe = list(CANDIDATES["A"])
        probe[0], probe[3] = -2, 64
        rules = {r["id"]: r for r in M.check(lab13(probe), LAB13_CFG)}
        self.assertFalse(rules["M2"]["passed"])
        self.assertAlmostEqual(rules["M3"]["measured"], 0.10)
        self.assertEqual([k for k, r in rules.items() if not r["passed"]], ["M2"])


class KnownAnswerLab15(unittest.TestCase):
    """The optimizer reproduces the Lab 15 Meridian training answers (5-point grid)."""

    MU = {"Treasury bills": 0.035, "Treasury 10-year note": 0.043, "Investment-grade bond fund": 0.050,
          "Global equity index fund": 0.080}
    VOL = {"Treasury bills": 0.005, "Treasury 10-year note": 0.070, "Investment-grade bond fund": 0.060,
           "Global equity index fund": 0.160}
    CORR = {"Treasury bills": {"Treasury bills": 1.00, "Treasury 10-year note": 0.10, "Investment-grade bond fund": 0.05, "Global equity index fund": 0.00},
            "Treasury 10-year note": {"Treasury bills": 0.10, "Treasury 10-year note": 1.00, "Investment-grade bond fund": 0.80, "Global equity index fund": -0.10},
            "Investment-grade bond fund": {"Treasury bills": 0.05, "Treasury 10-year note": 0.80, "Investment-grade bond fund": 1.00, "Global equity index fund": 0.25},
            "Global equity index fund": {"Treasury bills": 0.00, "Treasury 10-year note": -0.10, "Investment-grade bond fund": 0.25, "Global equity index fund": 1.00}}

    def run_lab15(self, equity_mu=0.08):
        mu = dict(self.MU, **{"Global equity index fund": equity_mu})
        est = from_inputs(mu, self.VOL, self.CORR)
        res, _ = optimize(est, min_return=0.065, reserve_eligible={"Treasury bills", "Treasury 10-year note"},
                          reserve_min=0.03)
        return [round(res["weights"][n] * 100) for n in mu], round(res["expected_return"] * 100, 2), round(res["volatility"] * 100, 2)

    def test_as_loaded(self):
        self.assertEqual(self.run_lab15(), ([0, 20, 25, 55], 6.51, 9.44))

    def test_equity_seven_percent(self):
        self.assertEqual(self.run_lab15(0.07), ([0, 10, 10, 80], 6.53, 12.94))


class Estimates(unittest.TestCase):
    def test_hand_computed(self):
        est = estimate({"X": [0.01, 0.03, 0.02], "Y": [0.00, 0.02, 0.04]})
        self.assertAlmostEqual(est["mu"]["X"], 0.24)
        self.assertAlmostEqual(est["vol"]["X"], 0.01 * 12 ** 0.5)
        self.assertAlmostEqual(est["corr"]["X"]["Y"], 0.5)

    def test_portfolio_loss_95(self):
        est = from_inputs({"A": 0.10}, {"A": 0.20}, {"A": {"A": 1.0}})
        self.assertAlmostEqual(portfolio_stats({"A": 1.0}, est)["loss_95"], -(0.10 - 1.645 * 0.20))


class PointInTime(unittest.TestCase):
    def test_curve_uses_only_prior_day(self):
        r = CURVE.value_known_on("2026-10-30")
        self.assertEqual(r["observation_date"], "2026-10-29")
        self.assertAlmostEqual(r["spread_pct"], 0.80)
        for d in ("2022-12-30", "2015-06-01", "2026-01-02"):
            self.assertLess(CURVE.value_known_on(d)["observation_date"], d)

    def test_treasury_matches_lab17_dgs10(self):
        """Known answer: Lab 17's FRED DGS10 three-value check (5.24, 5.26, 5.29)."""
        rows = {d.isoformat(): y10 for d, _, y10 in CURVE.rows}
        self.assertEqual([rows["2026-09-28"], rows["2026-09-29"], rows["2026-09-30"]], [5.24, 5.26, 5.29])
        self.assertEqual(CURVE.value_known_on("2026-09-30")["y10_pct"], 5.26)   # Lab 17: last known on 9/30

    def test_joby_spac_prices_excluded(self):
        joby = PRICES.series["JOBY"]
        for month, value in zip(PRICES.months, joby):
            if month < "2021-08":
                self.assertIsNone(value)
        self.assertNotIn("2021-08", PRICES.returns("JOBY"))   # first return is Aug -> Sep
        self.assertIn("2021-09", PRICES.returns("JOBY"))

    def test_window_ends_at_decision_month(self):
        months, _ = PRICES.window(["BIL"], "2026-10", 36)
        self.assertEqual((months[0], months[-1], len(months)), ("2023-11", "2026-10", 36))

    def test_no_look_ahead_in_walk_forward_decision(self):
        """A rebalance computed with the full file equals one computed with later data deleted."""
        for month in ("2016-12", "2019-12", "2024-12"):
            cut = PRICES.months.index(month) + 1
            truncated = Prices(PRICES.months[:cut], {t: v[:cut] for t, v in PRICES.series.items()})
            curve_cut = TreasuryCurve([row for row in CURVE.rows if row[0] <= date(int(month[:4]), 12, 31)])
            full = P.run_decision(CFG, PRICES, CURVE, {"end_month": month})
            part = P.run_decision(CFG, truncated, curve_cut, {"end_month": month})
            self.assertEqual(full["feasible"], part["feasible"], month)
            if full["feasible"]:
                self.assertEqual(full["portfolios"]["constrained"]["weights"],
                                 part["portfolios"]["constrained"]["weights"], month)
            self.assertEqual(full["signal_reading"], part["signal_reading"], month)

    def test_data_snapshot_hashes(self):
        snap = json.loads((DATA / "data_snapshot.json").read_text(encoding="utf-8"))
        for name, meta in snap["files"].items():
            self.assertEqual(hashlib.sha256((DATA / name).read_bytes()).hexdigest(), meta["sha256"], name)


class MandateAndOptimizer(unittest.TestCase):
    def setUp(self):
        self.run = P.run_decision(CFG, PRICES, CURVE)

    def test_baseline_verdicts_name_the_rule(self):
        pf = self.run["portfolios"]
        self.assertIn("M5", pf["equal_weight"]["verdict"]["failed_rules"])   # JOBY 16.7% > 8%
        self.assertIn("O1", pf["inverse_vol"]["verdict"]["failed_rules"])    # misses CPI + 4%
        self.assertIn("M3", pf["benchmark"]["verdict"]["failed_rules"])      # no payout reserve

    def test_constrained_passes_every_hard_rule(self):
        p = self.run["portfolios"]["constrained"]
        self.assertTrue(p["verdict"]["passed"])
        self.assertLessEqual(p["weights"]["JOBY"], CFG["limits"]["issuer_limit"] + 1e-9)

    def test_issuer_cap_binds_when_return_needs_joby(self):
        est = from_inputs({"A": 0.02, "J": 0.50}, {"A": 0.01, "J": 0.80},
                          {"A": {"A": 1, "J": 0}, "J": {"A": 0, "J": 1}})
        res, _ = optimize(est, min_return=0.04, caps={"J": 0.08})
        self.assertAlmostEqual(res["weights"]["J"], 0.05)          # largest 5-point step under 8%
        capped, _ = optimize(est, min_return=0.05, caps={"J": 0.08})
        uncapped, _ = optimize(est, min_return=0.05)
        self.assertIsNone(capped)                                   # the cap, not the return, binds
        self.assertGreater(uncapped["weights"]["J"], 0.08)

    def test_infeasible_is_reported_not_crashed(self):
        r = P.run_decision(CFG, PRICES, CURVE, {"cpi_pct": 40.0})
        self.assertFalse(r["feasible"])
        self.assertNotIn("constrained", r["portfolios"])

    def test_turnover_and_cost(self):
        new, old = {"A": 0.6, "B": 0.4}, {"A": 0.4, "B": 0.6}
        self.assertAlmostEqual(M.one_way_turnover(new, old), 0.2)
        assets = {"A": {"trade_cost_bps": 10}, "B": {"trade_cost_bps": 30}}
        self.assertAlmostEqual(M.trading_cost(new, old, assets), 0.2 * 10e-4 + 0.2 * 30e-4)


class Signal(unittest.TestCase):
    def test_inverted_moves_ief_to_bil(self):
        w, action = P.apply_signal({"BIL": 0.1, "IEF": 0.3, "ACWI": 0.6}, {"spread_pct": -0.5}, True)
        self.assertEqual(w, {"BIL": 0.4, "IEF": 0.0, "ACWI": 0.6})
        self.assertIn("inverted", action)

    def test_positive_keeps_ief(self):
        w, _ = P.apply_signal({"BIL": 0.1, "IEF": 0.3}, {"spread_pct": 0.5}, True)
        self.assertEqual(w, {"BIL": 0.1, "IEF": 0.3})


class FrozenOutput(unittest.TestCase):
    """The visible output on GitHub is what the engine produces from the frozen data today."""

    def test_visible_output_matches_engine(self):
        frozen = json.loads((ROOT / "output" / "visible_output.json").read_text(encoding="utf-8"))
        fresh = P.run_decision(CFG, PRICES, CURVE)
        self.assertEqual(frozen["decision"]["portfolios"]["constrained"]["weights"],
                         fresh["portfolios"]["constrained"]["weights"])
        self.assertEqual(frozen["recommendation"]["action"], "REJECT")
        self.assertTrue(frozen["stop_status"]["stop"])


if __name__ == "__main__":
    unittest.main()
