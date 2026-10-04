import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/cloudflare-cost-review"
spec = importlib.util.spec_from_file_location("cost_model", SKILL / "scripts/cost_model.py")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class CostModelTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((SKILL / "references/example-input.json").read_text())
        # Isolate the specified usage dimension except in the publisher-operation test.
        self.data["r2_class_b_other_operations"] = 0

    def test_known_2610_million_comparison(self):
        result = model.estimate(self.data)
        self.assertEqual(result["before"]["worker_request_usd"], "780.00")
        self.assertEqual(result["after"]["r2_read_usd"], "6.12")
        self.assertEqual(result["quantities"]["r2_class_b_reads"], 26_100_000)

    def test_cache_failure_can_cost_more(self):
        self.data["origin_fraction"] = "1"
        self.assertEqual(model.estimate(self.data)["after"]["r2_read_usd"], "936.00")

    def test_worker_proxy_still_bills_every_read(self):
        self.data["read_path"] = "worker_proxy"
        self.data["origin_fraction"] = "0.001"
        self.data["publisher_invocations"] = 0
        self.data["account_usage_before_window"]["worker_requests"] = 10_000_000
        self.data["account_usage_before_window"]["r2_class_b"] = 10_000_000
        result = model.estimate(self.data)
        self.assertEqual(result["after"]["worker_request_usd"], "783.00")
        self.assertEqual(result["after"]["r2_read_usd"], "1.08")
        self.assertEqual(result["after"]["modeled_usage_usd"], "784.08")

    def test_ambiguous_read_path_rejected(self):
        self.data["read_path"] = "cdn"
        with self.assertRaises(ValueError):
            model.estimate(self.data)

    def test_high_hit_rate_and_puts_fit_allowance(self):
        self.data["origin_fraction"] = "0.001"
        self.data["r2_class_a_operations"] = 172800
        result = model.estimate(self.data)
        self.assertEqual(result["after"]["modeled_usage_usd"], "0.00")
        self.assertEqual(result["quantities"]["r2_class_a_operations"], 172800)

    def test_r2_free_boundary_one_extra_operation(self):
        self.data["public_reads"] = 10_000_001
        self.data["origin_fraction"] = "1"
        self.assertEqual(model.estimate(self.data)["after"]["r2_read_usd"], "0.36")

    def test_no_shared_allowance_left(self):
        self.data["account_usage_before_window"]["r2_class_b"] = 10_000_000
        self.assertEqual(model.estimate(self.data)["after"]["r2_read_usd"], "9.72")

    def test_account_rounding_is_not_charged_twice(self):
        self.data["public_reads"] = 1
        self.data["origin_fraction"] = "1"
        self.data["account_usage_before_window"]["r2_class_b"] = 10_999_999
        self.assertEqual(model.estimate(self.data)["after"]["r2_read_usd"], "0.00")
        self.data["public_reads"] = 2
        self.assertEqual(model.estimate(self.data)["after"]["r2_read_usd"], "0.36")

    def test_worker_allowance_applied_once_to_combined_paths(self):
        self.data["vote_posts"] = 10_000_000
        result = model.estimate(self.data)
        self.assertEqual(result["before"]["worker_request_usd"], "783.00")
        self.assertEqual(result["after"]["worker_request_usd"], "0.01")

    def test_short_window_does_not_prorate_monthly_allowance(self):
        self.data["window_days"] = 7
        self.data["r2_class_a_operations"] = 10080
        result = model.estimate(self.data)
        self.assertEqual(result["before"]["worker_request_usd"], "780.00")
        self.assertEqual(result["quantities"]["r2_class_a_operations"], 10080)

    def test_r2_operation_amplification_and_publisher_reads(self):
        self.data["origin_fraction"] = "1"
        self.data["r2_operations_per_origin_read"] = 2
        self.data["r2_class_b_other_operations"] = 100
        self.assertEqual(model.estimate(self.data)["quantities"]["r2_class_b_reads"], 5_220_000_100)

    def test_publisher_heads_can_cross_the_free_read_boundary(self):
        self.data["public_reads"] = 10_000_000
        self.data["origin_fraction"] = "1"
        self.data["r2_class_b_other_operations"] = 43200
        self.assertEqual(model.estimate(self.data)["after"]["r2_read_usd"], "0.36")

    def test_cheap_read_path_can_fail_freshness_target(self):
        self.data["freshness"]["target_seconds"] = 20
        result = model.estimate(self.data)
        self.assertEqual(result["freshness"]["healthy_delay_budget_seconds"], "81")
        self.assertFalse(result["freshness"]["within_target_assuming_healthy_services"])

    def test_cpu_is_a_separate_usage_dimension(self):
        self.data["worker_cpu_ms_before"] = 31_000_000
        self.assertEqual(model.estimate(self.data)["before"]["worker_cpu_usd"], "0.02")

    def test_storage_overage_rounds_up(self):
        self.data["r2_storage_gb_month"] = "10.1"
        self.assertEqual(model.estimate(self.data)["after"]["r2_storage_usd"], "0.02")

    def test_invalid_numbers_and_fraction_rejected(self):
        for key, value in [("public_reads", -1), ("public_reads", 1.5), ("public_reads", True),
                           ("origin_fraction", "NaN"), ("origin_fraction", "1.1"),
                           ("window_days", 0), ("window_days", 32), ("r2_operations_per_origin_read", -1)]:
            data = copy.deepcopy(self.data)
            data[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                model.estimate(data)


if __name__ == "__main__":
    unittest.main()
