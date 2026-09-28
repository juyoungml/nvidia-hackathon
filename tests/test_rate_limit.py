"""Exercise the account-limit pacing without making network requests."""

from __future__ import annotations

import unittest

from poc.rate_limit import POC_TARGET_RPM, RequestPacer, retry_delay_seconds


class RequestPacerTests(unittest.TestCase):
    def test_sequential_requests_are_spaced_below_account_limit(self) -> None:
        elapsed = [0.0]
        sleeps = []

        def clock() -> float:
            return elapsed[0]

        def sleep(seconds: float) -> None:
            sleeps.append(seconds)
            elapsed[0] += seconds

        pacer = RequestPacer(clock=clock, sleep=sleep)
        pacer.wait()
        pacer.wait()
        self.assertEqual(len(sleeps), 1)
        self.assertAlmostEqual(sleeps[0], 60 / POC_TARGET_RPM)

    def test_retries_use_server_delay_or_backoff(self) -> None:
        self.assertEqual(retry_delay_seconds("12", 0), 12)
        self.assertEqual(retry_delay_seconds(None, 1), 10)
        self.assertEqual(retry_delay_seconds("invalid", 2), 20)


if __name__ == "__main__":
    unittest.main()
