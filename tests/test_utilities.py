from datetime import datetime, timezone
from time import sleep, time

import pytest

from kraken.utilities import bool_from_str, get_nonce, utc_now


class TestBoolFromStr:
    """Test cases for bool_from_str function."""

    def test_bool_input_true(self):
        """Test that True boolean input returns True."""
        assert bool_from_str(True) is True

    def test_bool_input_false(self):
        """Test that False boolean input returns False."""
        assert bool_from_str(False) is False

    def test_true_string_variations(self):
        """Test all string variations that should return True."""
        true_values = ["true", "True", "TRUE", "t", "T", "yes", "Yes", "YES", "y", "Y", "on", "On", "ON", "1"]
        for value in true_values:
            assert bool_from_str(value) is True, f"Failed for value: {value}"

    def test_false_string_variations(self):
        """Test all string variations that should return False."""
        false_values = ["false", "False", "FALSE", "f", "F", "no", "No", "NO", "n", "N", "off", "Off", "OFF", "0"]
        for value in false_values:
            assert bool_from_str(value) is False, f"Failed for value: {value}"

    def test_invalid_string_raises_error(self):
        """Test that invalid strings raise ValueError."""
        invalid_values = ["invalid", "maybe", "2", "", "truee", "yep"]
        for value in invalid_values:
            with pytest.raises(ValueError, match=f"Cannot convert '{value}' to boolean"):
                bool_from_str(value)


class TestGetNonce:
    """Test cases for get_nonce function."""

    def test_returns_integer(self):
        """Test that get_nonce returns an integer."""
        nonce = get_nonce()
        assert isinstance(nonce, int)

    def test_returns_positive_value(self):
        """Test that get_nonce returns a positive value."""
        nonce = get_nonce()
        assert nonce > 0

    def test_is_millisecond_timestamp(self):
        """Test that nonce is approximately current time in milliseconds."""
        nonce = get_nonce()
        current_time_ms = int(time() * 1000.0)
        # Allow 1 second difference for test execution time
        assert abs(nonce - current_time_ms) < 1000

    def test_nonce_increases_over_time(self):
        """Test that nonce values increase over time."""
        nonce1 = get_nonce()
        sleep(0.001)  # Sleep for 1 millisecond
        nonce2 = get_nonce()
        assert nonce2 > nonce1

    def test_nonce_uniqueness(self):
        """Test that calls within same millisecond return same value, different milliseconds return different values."""
        # Rapid successive calls within same millisecond should return same value
        nonces = [get_nonce() for _ in range(10)]
        # Since all calls happen within ~same millisecond, they should be identical or very similar
        assert len(set(nonces)) <= 3  # Allow for at most a few different values

        # Calls separated by sleep should return different values
        nonce1 = get_nonce()
        sleep(0.002)  # Sleep 2 milliseconds
        nonce2 = get_nonce()
        assert nonce2 > nonce1


class TestUtcNow:
    """Test cases for utc_now function."""

    def test_returns_datetime(self):
        """Test that utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)

    def test_has_utc_timezone(self):
        """Test that returned datetime has UTC timezone."""
        result = utc_now()
        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self):
        """Test that utc_now returns approximately the current time."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        assert before <= result <= after

    def test_multiple_calls_increase(self):
        """Test that successive calls return increasing times."""
        time1 = utc_now()
        sleep(0.001)  # Sleep for 1 millisecond
        time2 = utc_now()
        assert time2 > time1