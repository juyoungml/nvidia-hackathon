"""Pace NVIDIA API requests below the account's 40 requests/minute limit."""

from __future__ import annotations

import time
from collections.abc import Callable

ACCOUNT_LIMIT_RPM = 40
POC_TARGET_RPM = 36  # Leave room for clock jitter and occasional manual requests.


class RequestPacer:
    def __init__(
        self,
        rpm: int = POC_TARGET_RPM,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rpm <= 0 or rpm > ACCOUNT_LIMIT_RPM:
            raise ValueError(f"rpm must be between 1 and {ACCOUNT_LIMIT_RPM}")
        self.interval_seconds = 60 / rpm
        self.clock = clock
        self.sleep = sleep
        self.last_request_at: float | None = None

    def wait(self) -> None:
        now = self.clock()
        if self.last_request_at is not None:
            remaining = self.interval_seconds - (now - self.last_request_at)
            if remaining > 0:
                self.sleep(remaining)
        self.last_request_at = self.clock()


def retry_delay_seconds(header: str | None, attempt: int) -> float:
    """Use a numeric Retry-After header or a bounded fallback for HTTP 429."""
    if header:
        try:
            return max(float(header), 0.0)
        except ValueError:
            pass
    return min(5 * (2**attempt), 30)
