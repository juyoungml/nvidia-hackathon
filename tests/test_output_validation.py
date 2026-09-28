"""Check that model outputs do not silently present nonexistent signal names."""

from __future__ import annotations

import unittest

from poc.run import undefined_signal_names


class OutputValidationTests(unittest.TestCase):
    def test_reports_only_unknown_tag_like_names(self) -> None:
        known = {"s_hc1_supply_temperature", "p_net_meter_flow"}
        answer = "Check s_hc1_supply_temperature and p_net_meter_flow, then s_hc1_flow."
        self.assertEqual(undefined_signal_names(answer, known), ["s_hc1_flow"])


if __name__ == "__main__":
    unittest.main()
