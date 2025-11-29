"""Unit tests for RateLimiter"""

import asyncio
import time
from unittest.mock import patch

import pytest

from kraken.limiter import RateLimiter


class TestRateLimiterInitialization:
    """Tests for RateLimiter initialization"""

    def test_init_starter_tier(self):
        """Test initialization with starter tier"""
        limiter = RateLimiter(tier="starter")
        assert limiter.tier == "starter"
        assert limiter.max_counter == 15
        assert limiter.decay_rate == -0.33
        assert limiter.counter == 0.0

    def test_init_intermediate_tier(self):
        """Test initialization with intermediate tier"""
        limiter = RateLimiter(tier="intermediate")
        assert limiter.tier == "intermediate"
        assert limiter.max_counter == 20
        assert limiter.decay_rate == -0.5

    def test_init_pro_tier(self):
        """Test initialization with pro tier"""
        limiter = RateLimiter(tier="pro")
        assert limiter.tier == "pro"
        assert limiter.max_counter == 20
        assert limiter.decay_rate == -1.0

    def test_init_unknown_tier_defaults_to_starter(self):
        """Test initialization with unknown tier defaults to starter"""
        limiter = RateLimiter(tier="unknown")
        assert limiter.tier == "starter"
        assert limiter.max_counter == 15
        assert limiter.decay_rate == -0.33


class TestRateLimiterCounterDecay:
    """Tests for counter decay logic"""

    def test_counter_decay_over_time(self):
        """Test that counter decays over time"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 10.0
        initial_time = time.time()
        limiter.last_update = initial_time

        # Simulate 1 second passing
        with patch("time.time", return_value=initial_time + 1.0):
            limiter._update_counter()

        # Counter should decrease by decay_rate (starter: -0.33/sec)
        # 10.0 + (-0.33 * 1.0) = 9.67
        assert limiter.counter == pytest.approx(9.67, rel=0.01)

    def test_counter_does_not_go_negative(self):
        """Test that counter never goes below zero"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 1.0
        initial_time = time.time()
        limiter.last_update = initial_time

        # Simulate 10 seconds passing (enough to go negative)
        with patch("time.time", return_value=initial_time + 10.0):
            limiter._update_counter()

        # Counter should be clamped at 0
        assert limiter.counter == 0.0

    def test_counter_decay_pro_tier(self):
        """Test counter decay with pro tier (faster decay)"""
        limiter = RateLimiter(tier="pro")
        limiter.counter = 10.0
        initial_time = time.time()
        limiter.last_update = initial_time

        # Simulate 1 second passing
        with patch("time.time", return_value=initial_time + 1.0):
            limiter._update_counter()

        # Counter should decrease by -1.0/sec
        # 10.0 + (-1.0 * 1.0) = 9.0
        assert limiter.counter == pytest.approx(9.0, rel=0.01)


class TestRateLimiterCheckAndIncrement:
    """Tests for check_and_increment logic"""

    def test_check_and_increment_success(self):
        """Test successful check and increment when under limit"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 5.0

        can_proceed, wait_time = limiter.check_and_increment(increment=2.0)

        assert can_proceed is True
        assert wait_time == 0.0
        assert limiter.counter == pytest.approx(7.0, abs=0.001)

    def test_check_and_increment_at_limit(self):
        """Test check and increment when at exactly the limit"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 14.0

        can_proceed, wait_time = limiter.check_and_increment(increment=1.0)

        assert can_proceed is True
        assert wait_time == 0.0
        assert limiter.counter == pytest.approx(15.0, abs=0.001)

    def test_check_and_increment_exceeds_limit(self):
        """Test check and increment when would exceed limit"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 14.0

        can_proceed, wait_time = limiter.check_and_increment(increment=3.0)

        assert can_proceed is False
        # Excess: (14 + 3) - 15 = 2
        # Wait time: 2 / 0.33 ≈ 6.06 seconds
        assert wait_time == pytest.approx(6.06, rel=0.01)
        # Counter should not be incremented when limit exceeded
        assert limiter.counter == pytest.approx(14.0, abs=0.001)

    def test_check_and_increment_default_increment(self):
        """Test check and increment with default increment of 1.0"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 5.0

        can_proceed, wait_time = limiter.check_and_increment()

        assert can_proceed is True
        assert wait_time == 0.0
        assert limiter.counter == pytest.approx(6.0, abs=0.001)

    def test_check_and_increment_applies_decay(self):
        """Test that check_and_increment applies decay before checking"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 10.0
        initial_time = time.time()
        limiter.last_update = initial_time

        # Simulate 1 second passing
        with patch("time.time", return_value=initial_time + 1.0):
            can_proceed, wait_time = limiter.check_and_increment(increment=1.0)

        assert can_proceed is True
        # Counter after decay: 10.0 + (-0.33 * 1.0) = 9.67
        # Counter after increment: 9.67 + 1.0 = 10.67
        assert limiter.counter == pytest.approx(10.67, rel=0.01)


class TestRateLimiterSyncWaitIfNeeded:
    """Tests for synchronous wait_if_needed method"""

    def test_wait_if_needed_no_wait(self):
        """Test wait_if_needed when no wait is needed"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 5.0

        start_time = time.time()
        limiter.wait_if_needed(increment=2.0)
        elapsed = time.time() - start_time

        # Should complete almost immediately (< 0.1 seconds)
        assert elapsed < 0.1
        assert limiter.counter == pytest.approx(7.0, abs=0.001)

    def test_wait_if_needed_with_wait(self):
        """Test wait_if_needed when wait is required"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 14.0

        start_time = time.time()
        limiter.wait_if_needed(increment=3.0)
        elapsed = time.time() - start_time

        # Should wait approximately 6.06 seconds
        # Excess: (14 + 3) - 15 = 2
        # Wait time: 2 / 0.33 ≈ 6.06 seconds
        assert elapsed >= 6.0
        assert limiter.counter == 15.0  # Set to max_counter after wait

    @patch("time.sleep")
    def test_wait_if_needed_calls_sleep(self, mock_sleep):
        """Test that wait_if_needed calls time.sleep with correct duration"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 14.0

        limiter.wait_if_needed(increment=3.0)

        mock_sleep.assert_called_once()
        call_args = mock_sleep.call_args[0][0]
        assert call_args == pytest.approx(6.06, rel=0.01)

    @patch("time.sleep")
    def test_wait_if_needed_does_not_call_sleep_when_not_needed(self, mock_sleep):
        """Test that wait_if_needed doesn't call sleep when under limit"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 5.0

        limiter.wait_if_needed(increment=2.0)

        mock_sleep.assert_not_called()


class TestRateLimiterAsyncAwaitIfNeeded:
    """Tests for asynchronous await_if_needed method"""

    @pytest.mark.asyncio
    async def test_await_if_needed_no_wait(self):
        """Test await_if_needed when no wait is needed"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 5.0

        start_time = time.time()
        await limiter.await_if_needed(increment=2.0)
        elapsed = time.time() - start_time

        # Should complete almost immediately (< 0.1 seconds)
        assert elapsed < 0.1
        assert limiter.counter == pytest.approx(7.0, abs=0.001)

    @pytest.mark.asyncio
    async def test_await_if_needed_with_wait(self):
        """Test await_if_needed when wait is required"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 14.0

        start_time = time.time()
        await limiter.await_if_needed(increment=3.0)
        elapsed = time.time() - start_time

        # Should wait approximately 6.06 seconds
        assert elapsed >= 6.0
        assert limiter.counter == 15.0  # Set to max_counter after wait

    @pytest.mark.asyncio
    async def test_await_if_needed_uses_asyncio_sleep(self):
        """Test that await_if_needed uses asyncio.sleep, not time.sleep"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 14.0

        with patch("asyncio.sleep", return_value=asyncio.sleep(0)) as mock_async_sleep:
            with patch("time.sleep") as mock_time_sleep:
                await limiter.await_if_needed(increment=3.0)

                # Should call asyncio.sleep, not time.sleep
                mock_async_sleep.assert_called_once()
                mock_time_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_await_if_needed_does_not_block_event_loop(self):
        """Test that await_if_needed doesn't block the event loop"""
        limiter = RateLimiter(tier="pro")  # Use pro for faster test (faster decay)
        limiter.counter = 19.0

        # Track if concurrent task was able to run
        concurrent_task_ran = False

        async def concurrent_task():
            nonlocal concurrent_task_ran
            await asyncio.sleep(0.1)
            concurrent_task_ran = True

        # Start both tasks concurrently
        await asyncio.gather(
            limiter.await_if_needed(increment=3.0),  # Will need to wait ~2 seconds
            concurrent_task(),
        )

        # If await_if_needed blocked the event loop, concurrent_task wouldn't run
        assert concurrent_task_ran is True

    @pytest.mark.asyncio
    async def test_await_if_needed_does_not_call_asyncio_sleep_when_not_needed(self):
        """Test that await_if_needed doesn't call sleep when under limit"""
        limiter = RateLimiter(tier="starter")
        limiter.counter = 5.0

        with patch("asyncio.sleep") as mock_async_sleep:
            await limiter.await_if_needed(increment=2.0)
            mock_async_sleep.assert_not_called()


class TestRateLimiterMultipleRequests:
    """Tests for multiple sequential requests"""

    def test_multiple_requests_within_limit(self):
        """Test multiple requests that stay within limit"""
        limiter = RateLimiter(tier="starter")

        for _ in range(10):
            can_proceed, wait_time = limiter.check_and_increment(increment=1.0)
            assert can_proceed is True
            assert wait_time == 0.0

        assert limiter.counter == pytest.approx(10.0, abs=0.001)

    def test_multiple_requests_exceed_limit(self):
        """Test that exceeding limit requires waiting"""
        limiter = RateLimiter(tier="starter")

        # Fill up to limit
        for _ in range(15):
            limiter.check_and_increment(increment=1.0)

        # Next request should require wait
        can_proceed, wait_time = limiter.check_and_increment(increment=1.0)
        assert can_proceed is False
        assert wait_time > 0

    @pytest.mark.asyncio
    async def test_async_multiple_requests_within_limit(self):
        """Test multiple async requests that stay within limit"""
        limiter = RateLimiter(tier="starter")

        for _ in range(10):
            await limiter.await_if_needed(increment=1.0)

        assert limiter.counter == pytest.approx(10.0, abs=0.001)

    @pytest.mark.asyncio
    async def test_async_multiple_requests_with_natural_decay(self):
        """Test that requests naturally decay over time"""
        limiter = RateLimiter(tier="pro")  # Use pro for faster decay

        # Make 15 requests quickly
        for _ in range(15):
            await limiter.await_if_needed(increment=1.0)

        assert limiter.counter == pytest.approx(15.0, abs=0.001)

        # Wait for some decay (1 second = -1.0 decay for pro tier)
        await asyncio.sleep(1.1)

        # Check that counter has decayed
        can_proceed, _ = limiter.check_and_increment(increment=0.0)
        assert can_proceed is True
        # After 1 second: 15.0 + (-1.0 * 1.0) ≈ 14.0
        assert limiter.counter < 15.0
