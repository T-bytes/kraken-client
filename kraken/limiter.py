import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter implementing Kraken's tier-based rate limiting with decay.

    Rate limits are tier-based with a counter that:
    - Increments on each request (different amounts for different endpoints)
    - Decays over time based on the tier's decay rate

    When the counter exceeds the maximum, requests should be delayed until
    the counter decays below the threshold.
    """

    def __init__(self, tier: str = "starter"):
        """Initialize rate limiter for a specific tier.

        Args:
            tier: Rate limit tier (starter, intermediate, pro)
        """
        from kraken.constants import RATE_LIMIT_CONFIG

        if tier not in RATE_LIMIT_CONFIG:
            logger.warning(f"Unknown tier '{tier}', defaulting to 'starter'")
            tier = "starter"

        self.tier = tier
        config = RATE_LIMIT_CONFIG[tier]
        self.max_counter = config["max_counter"]
        self.decay_rate = config["decay_rate"]
        self.counter = 0.0
        self.last_update = time.time()
        logger.info(
            f"Rate limiter initialized for tier '{tier}' (max: {self.max_counter}, decay: {self.decay_rate}/sec)"
        )

    def _update_counter(self) -> None:
        """Update counter based on time decay."""
        now = time.time()
        elapsed = now - self.last_update
        self.counter = max(0.0, self.counter + (self.decay_rate * elapsed))
        self.last_update = now

    def check_and_increment(self, increment: float = 1.0) -> tuple[bool, float]:
        """Check if request can proceed and increment counter.

        Args:
            increment: Amount to increment counter (default 1.0 for most requests)

        Returns:
            Tuple of (can_proceed, wait_time_seconds)
            - can_proceed: True if request can proceed immediately
            - wait_time_seconds: Seconds to wait if can_proceed is False
        """
        self._update_counter()

        # Check if we would exceed the limit
        new_counter = self.counter + increment
        if new_counter > self.max_counter:
            excess = new_counter - self.max_counter
            wait_time = excess / abs(self.decay_rate)
            logger.warning(
                f"Rate limit would be exceeded (counter: {self.counter:.2f} + {increment} > {self.max_counter}), "
                f"need to wait {wait_time:.2f}s"
            )
            return False, wait_time

        # Increment and allow
        self.counter = new_counter
        logger.debug(f"Rate limit check passed (counter: {self.counter:.2f}/{self.max_counter})")
        return True, 0.0

    def wait_if_needed(self, increment: float = 1.0) -> None:
        """Wait if necessary before making a request (synchronous).

        Args:
            increment: Amount to increment counter
        """
        can_proceed, wait_time = self.check_and_increment(increment)
        if not can_proceed:
            logger.info(f"Rate limiting: sleeping for {wait_time:.2f}s")
            time.sleep(wait_time)
            self.counter = self.max_counter

    async def await_if_needed(self, increment: float = 1.0) -> None:
        """Wait if necessary before making a request (asynchronous).

        Uses asyncio.sleep() to avoid blocking the event loop.

        Args:
            increment: Amount to increment counter
        """
        can_proceed, wait_time = self.check_and_increment(increment)
        if not can_proceed:
            logger.info(f"Rate limiting: sleeping for {wait_time:.2f}s (async)")
            await asyncio.sleep(wait_time)
            self.counter = self.max_counter
