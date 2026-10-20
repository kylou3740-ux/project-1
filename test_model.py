import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import model

class ModelTests(unittest.TestCase):
    def test_balance_sheet_articulates(self):
        a, rows = model.build_model()
        self.assertTrue(all(abs(rows[y]["balance_gap"]) < 1e-5 for y in model.YEARS))
    def test_cash_flow_ties_to_cash(self):
        a, rows = model.build_model()
        self.assertTrue(all(abs(rows[y]["cash_tie"]) < 1e-6 for y in model.YEARS))
    def test_wacc_above_growth_required(self):
        with self.assertRaises(ValueError):
            model.build_model({"wacc": 0.025, "terminal_growth": 0.03})
    def test_dcf_directionality(self):
        a, rows = model.build_model()
        base = model.dcf_value(rows, a)["value_per_share"]
        high_wacc = model.dcf_value(rows, a, wacc=0.11)["value_per_share"]
        high_g = model.dcf_value(rows, a, terminal_growth=0.03)["value_per_share"]
        self.assertLess(high_wacc, base)
        self.assertGreater(high_g, base)
    def test_revenue_growth_directionality(self):
        base = model.run_report()["dcf"]["value_per_share"]
        high = model.run_report({"revenue_growth": 0.05})["dcf"]["value_per_share"]
        self.assertGreater(high, base)

if __name__ == "__main__":
    unittest.main()
