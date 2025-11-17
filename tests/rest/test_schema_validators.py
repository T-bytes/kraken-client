"""Unit tests for Kraken REST API Schema Validators"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from kraken.constants import LATENCY_TOLERANCE
from kraken.rest.schema import validators

# ============================================================================
# Simple Normalization Validators
# ============================================================================


class TestValidateOrdertype:
    """Tests for validate_ordertype function"""

    def test_validate_ordertype_uppercase_to_lowercase(self):
        """Test ordertype conversion from uppercase to lowercase"""
        result = validators.validate_ordertype("MARKET")
        assert result == "market"

    def test_validate_ordertype_mixed_case(self):
        """Test ordertype conversion from mixed case to lowercase"""
        result = validators.validate_ordertype("LiMiT")
        assert result == "limit"

    def test_validate_ordertype_already_lowercase(self):
        """Test ordertype that is already lowercase"""
        result = validators.validate_ordertype("stop-loss")
        assert result == "stop-loss"

    def test_validate_ordertype_strips_whitespace(self):
        """Test ordertype strips leading and trailing whitespace"""
        result = validators.validate_ordertype("  limit  ")
        assert result == "limit"

    def test_validate_ordertype_strips_and_lowers(self):
        """Test ordertype strips whitespace and converts to lowercase"""
        result = validators.validate_ordertype("  MARKET  ")
        assert result == "market"

    def test_validate_ordertype_single_character(self):
        """Test ordertype with single character"""
        result = validators.validate_ordertype("M")
        assert result == "m"


class TestValidateVolume:
    """Tests for validate_volume function"""

    def test_validate_volume_from_integer(self):
        """Test volume conversion from integer"""
        result = validators.validate_volume(100)
        assert result == "100"

    def test_validate_volume_from_float(self):
        """Test volume conversion from float"""
        result = validators.validate_volume(1.5)
        assert result == "1.5"

    def test_validate_volume_from_string(self):
        """Test volume conversion from string"""
        result = validators.validate_volume("2.5")
        assert result == "2.5"

    def test_validate_volume_zero_integer(self):
        """Test volume conversion from zero integer"""
        result = validators.validate_volume(0)
        assert result == "0"

    def test_validate_volume_zero_float(self):
        """Test volume conversion from zero float"""
        result = validators.validate_volume(0.0)
        assert result == "0.0"

    def test_validate_volume_small_decimal(self):
        """Test volume conversion from small decimal"""
        result = validators.validate_volume(0.0001)
        assert result == "0.0001"

    def test_validate_volume_large_number(self):
        """Test volume conversion from large number"""
        result = validators.validate_volume(1000000)
        assert result == "1000000"

    def test_validate_volume_scientific_notation(self):
        """Test volume conversion from scientific notation"""
        result = validators.validate_volume(1e-8)
        assert result == "1e-08"


class TestValidateLeverage:
    """Tests for validate_leverage function"""

    def test_validate_leverage_none(self):
        """Test leverage validation with None"""
        result = validators.validate_leverage(None)
        assert result is None

    def test_validate_leverage_from_integer(self):
        """Test leverage conversion from integer"""
        result = validators.validate_leverage(5)
        assert result == "5"

    def test_validate_leverage_from_string(self):
        """Test leverage conversion from string"""
        result = validators.validate_leverage("10")
        assert result == "10"

    def test_validate_leverage_low_value(self):
        """Test leverage with low value"""
        result = validators.validate_leverage(2)
        assert result == "2"


class TestValidateTimeInForce:
    """Tests for validate_time_in_force function"""

    def test_validate_time_in_force_lowercase_to_uppercase(self):
        """Test time in force conversion from lowercase to uppercase"""
        result = validators.validate_time_in_force("gtc")
        assert result == "GTC"

    def test_validate_time_in_force_mixed_case(self):
        """Test time in force conversion from mixed case to uppercase"""
        result = validators.validate_time_in_force("IoC")
        assert result == "IOC"

    def test_validate_time_in_force_already_uppercase(self):
        """Test time in force that is already uppercase"""
        result = validators.validate_time_in_force("FOK")
        assert result == "FOK"

    def test_validate_time_in_force_strips_whitespace(self):
        """Test time in force strips leading and trailing whitespace"""
        result = validators.validate_time_in_force("  GTC  ")
        assert result == "GTC"

    def test_validate_time_in_force_strips_and_uppers(self):
        """Test time in force strips whitespace and converts to uppercase"""
        result = validators.validate_time_in_force("  ioc  ")
        assert result == "IOC"


class TestNormalizeTxid:
    """Tests for normalize_txid function"""

    def test_normalize_txid_none(self):
        """Test txid normalization with None"""
        result = validators.normalize_txid(None)
        assert result is None

    def test_normalize_txid_integer(self):
        """Test txid normalization with integer"""
        result = validators.normalize_txid(12345)
        assert result == 12345

    def test_normalize_txid_numeric_string(self):
        """Test txid normalization with numeric string"""
        result = validators.normalize_txid("67890")
        assert result == 67890

    def test_normalize_txid_alphanumeric_string(self):
        """Test txid normalization with alphanumeric string"""
        result = validators.normalize_txid("ABC123-DEF45-GHI678")
        assert result == "ABC123-DEF45-GHI678"

    def test_normalize_txid_string_with_whitespace(self):
        """Test txid normalization with string containing whitespace"""
        result = validators.normalize_txid("  TXN-12345  ")
        assert result == "TXN-12345"

    def test_normalize_txid_numeric_string_with_leading_zeros(self):
        """Test txid normalization with numeric string containing leading zeros"""
        result = validators.normalize_txid("00123")
        assert result == 123

    def test_normalize_txid_zero(self):
        """Test txid normalization with zero"""
        result = validators.normalize_txid(0)
        assert result == 0

    def test_normalize_txid_zero_string(self):
        """Test txid normalization with zero string"""
        result = validators.normalize_txid("0")
        assert result == 0


# ============================================================================
# Complex Validators
# ============================================================================


class TestValidateDisplayVolume:
    """Tests for validate_display_volume function"""

    def test_validate_display_volume_none(self):
        """Test display volume validation with None"""
        result = validators.validate_display_volume(None, 100.0)
        assert result is None

    def test_validate_display_volume_within_range(self):
        """Test display volume within valid range"""
        result = validators.validate_display_volume(10.0, 100.0)
        assert result == "10.0"

    def test_validate_display_volume_at_floor(self):
        """Test display volume exactly at floor (order_volume / 15)"""
        order_volume = 150.0
        floor = order_volume / 15.0  # 10.0
        result = validators.validate_display_volume(floor, order_volume)
        assert result == "10.0"

    def test_validate_display_volume_at_ceiling(self):
        """Test display volume exactly at ceiling (order_volume)"""
        order_volume = 100.0
        result = validators.validate_display_volume(order_volume, order_volume)
        assert result == "100.0"

    def test_validate_display_volume_below_floor(self):
        """Test display volume below floor, should return floor"""
        order_volume = 150.0
        floor = order_volume / 15.0  # 10.0
        result = validators.validate_display_volume(5.0, order_volume)
        assert result == str(floor)

    def test_validate_display_volume_above_ceiling(self):
        """Test display volume above ceiling, should return ceiling"""
        order_volume = 100.0
        result = validators.validate_display_volume(200.0, order_volume)
        assert result == "100.0"

    def test_validate_display_volume_from_string(self):
        """Test display volume from string input"""
        result = validators.validate_display_volume("50.0", 100.0)
        assert result == "50.0"

    def test_validate_display_volume_from_integer(self):
        """Test display volume from integer input"""
        result = validators.validate_display_volume(50, 100.0)
        assert result == "50"

    def test_validate_display_volume_small_order(self):
        """Test display volume with small order volume"""
        order_volume = 15.0
        floor = order_volume / 15.0  # 1.0
        result = validators.validate_display_volume(0.5, order_volume)
        assert result == str(floor)


class TestValidateOrderFlags:
    """Tests for validate_order_flags function"""

    def test_validate_order_flags_none(self):
        """Test order flags validation with None"""
        result = validators.validate_order_flags(None)
        assert result is None

    def test_validate_order_flags_single_valid_string(self):
        """Test order flags with single valid flag as string"""
        result = validators.validate_order_flags("post")
        assert result == "post"

    def test_validate_order_flags_comma_separated_valid(self):
        """Test order flags with comma-separated valid flags"""
        result = validators.validate_order_flags("post,fcib")
        assert set(result.split(",")) == {"post", "fcib"}

    def test_validate_order_flags_list_valid(self):
        """Test order flags with list of valid flags"""
        result = validators.validate_order_flags(["post", "fciq"])
        assert set(result.split(",")) == {"post", "fciq"}

    def test_validate_order_flags_set_valid(self):
        """Test order flags with set of valid flags"""
        result = validators.validate_order_flags({"fcib", "viqc"})
        assert set(result.split(",")) == {"fcib", "viqc"}

    def test_validate_order_flags_invalid_flag(self):
        """Test order flags with invalid flag, should return None"""
        result = validators.validate_order_flags("invalid")
        assert result is None

    def test_validate_order_flags_mixed_valid_invalid(self):
        """Test order flags with mix of valid and invalid flags"""
        result = validators.validate_order_flags(["post", "invalid", "fcib"])
        assert set(result.split(",")) == {"post", "fcib"}

    def test_validate_order_flags_all_valid_flags(self):
        """Test order flags with all valid flags"""
        result = validators.validate_order_flags(["post", "fcib", "fciq", "viqc"])
        assert set(result.split(",")) == {"post", "fcib", "fciq", "viqc"}

    def test_validate_order_flags_empty_string(self):
        """Test order flags with empty string"""
        result = validators.validate_order_flags("")
        assert result is None

    def test_validate_order_flags_empty_list(self):
        """Test order flags with empty list"""
        result = validators.validate_order_flags([])
        assert result is None

    def test_validate_order_flags_empty_set(self):
        """Test order flags with empty set"""
        result = validators.validate_order_flags(set())
        assert result is None

    def test_validate_order_flags_duplicate_in_list(self):
        """Test order flags with duplicate flags in list"""
        result = validators.validate_order_flags(["post", "fcib", "post"])
        assert set(result.split(",")) == {"post", "fcib"}


class TestNormalizeCommaSeparatedList:
    """Tests for normalize_comma_separated_list function"""

    def test_normalize_comma_separated_list_none(self):
        """Test comma-separated list normalization with None"""
        result = validators.normalize_comma_separated_list(None)
        assert result is None

    def test_normalize_comma_separated_list_single_string(self):
        """Test comma-separated list with single item string"""
        result = validators.normalize_comma_separated_list("BTC")
        assert result == "BTC"

    def test_normalize_comma_separated_list_comma_separated(self):
        """Test comma-separated list with comma-separated string"""
        result = validators.normalize_comma_separated_list("BTC,ETH")
        assert result == "BTC,ETH"

    def test_normalize_comma_separated_list_single_item_list(self):
        """Test comma-separated list with single item list"""
        result = validators.normalize_comma_separated_list(["BTC"])
        assert result == "BTC"

    def test_normalize_comma_separated_list_multiple_items(self):
        """Test comma-separated list with multiple items"""
        result = validators.normalize_comma_separated_list(["BTC", "ETH", "USD"])
        assert result == "BTC,ETH,USD"

    def test_normalize_comma_separated_list_duplicates_removed(self):
        """Test comma-separated list removes duplicates while preserving order"""
        result = validators.normalize_comma_separated_list(["BTC", "ETH", "BTC"])
        assert result == "BTC,ETH"

    def test_normalize_comma_separated_list_whitespace_stripped(self):
        """Test comma-separated list strips whitespace from string"""
        result = validators.normalize_comma_separated_list("  BTC  ")
        assert result == "BTC"

    def test_normalize_comma_separated_list_list_items_stripped(self):
        """Test comma-separated list strips whitespace from list items"""
        result = validators.normalize_comma_separated_list(["  BTC  ", "  ETH  "])
        assert result == "BTC,ETH"

    def test_normalize_comma_separated_list_empty_string_raises(self):
        """Test comma-separated list raises ValueError for empty string"""
        with pytest.raises(ValueError, match="String cannot be empty or whitespace"):
            validators.normalize_comma_separated_list("")

    def test_normalize_comma_separated_list_whitespace_string_raises(self):
        """Test comma-separated list raises ValueError for whitespace-only string"""
        with pytest.raises(ValueError, match="String cannot be empty or whitespace"):
            validators.normalize_comma_separated_list("   ")

    def test_normalize_comma_separated_list_empty_list_raises(self):
        """Test comma-separated list raises ValueError for empty list"""
        with pytest.raises(ValueError, match="List cannot be empty"):
            validators.normalize_comma_separated_list([])

    def test_normalize_comma_separated_list_list_with_empty_string_raises(self):
        """Test comma-separated list raises ValueError for list with empty string"""
        with pytest.raises(
            ValueError, match="List cannot contain empty or whitespace-only strings"
        ):
            validators.normalize_comma_separated_list(["BTC", "", "ETH"])

    def test_normalize_comma_separated_list_list_with_whitespace_raises(self):
        """Test comma-separated list raises ValueError for list with whitespace-only string"""
        with pytest.raises(
            ValueError, match="List cannot contain empty or whitespace-only strings"
        ):
            validators.normalize_comma_separated_list(["BTC", "   ", "ETH"])

    def test_normalize_comma_separated_list_non_string_item_raises(self):
        """Test comma-separated list raises ValueError for non-string list item"""
        with pytest.raises(ValueError, match="All list items must be strings"):
            validators.normalize_comma_separated_list(["BTC", 123])

    def test_normalize_comma_separated_list_invalid_type_raises(self):
        """Test comma-separated list raises ValueError for invalid type"""
        with pytest.raises(ValueError, match="Must be a string, list, or None"):
            validators.normalize_comma_separated_list({"BTC": "ETH"})


# ============================================================================
# Time-based Validators (require mocking)
# ============================================================================


class TestValidateDeadline:
    """Tests for validate_deadline function"""

    def test_validate_deadline_none(self):
        """Test deadline validation with None"""
        result = validators.validate_deadline(None)
        assert result is None

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_valid_within_range(self, mock_utc_now):
        """Test deadline validation with valid deadline within 2-60 second range"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        # 30 seconds from now
        deadline = (fixed_time + timedelta(seconds=30)).isoformat()
        result = validators.validate_deadline(deadline)
        assert result == deadline

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_below_minimum_bounded_to_2_seconds(self, mock_utc_now):
        """Test deadline below 2 seconds is bounded to minimum"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        # 1 second from now (below minimum)
        deadline = (fixed_time + timedelta(seconds=1)).isoformat()
        result = validators.validate_deadline(deadline)

        expected = (fixed_time + timedelta(seconds=2)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_above_maximum_bounded_to_60_seconds(self, mock_utc_now):
        """Test deadline above 60 seconds is bounded to maximum"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        # 120 seconds from now (above maximum)
        deadline = (fixed_time + timedelta(seconds=120)).isoformat()
        result = validators.validate_deadline(deadline)

        expected = (fixed_time + timedelta(seconds=60)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_exactly_2_seconds(self, mock_utc_now):
        """Test deadline exactly at 2 second boundary"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        deadline = (fixed_time + timedelta(seconds=2)).isoformat()
        result = validators.validate_deadline(deadline)
        assert result == deadline

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_exactly_60_seconds(self, mock_utc_now):
        """Test deadline exactly at 60 second boundary"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        deadline = (fixed_time + timedelta(seconds=60)).isoformat()
        result = validators.validate_deadline(deadline)
        assert result == deadline

    def test_validate_deadline_missing_timezone_raises(self):
        """Test deadline without timezone raises ValueError"""
        deadline = "2025-01-15T12:00:00"  # No timezone
        with pytest.raises(ValueError, match="Deadline must include timezone information"):
            validators.validate_deadline(deadline)

    def test_validate_deadline_invalid_format_raises(self):
        """Test deadline with invalid format raises ValueError"""
        with pytest.raises(ValueError, match="Invalid deadline format"):
            validators.validate_deadline("not-a-datetime")

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_with_z_timezone(self, mock_utc_now):
        """Test deadline with Z timezone indicator"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        # 30 seconds from now with Z timezone
        deadline_dt = fixed_time + timedelta(seconds=30)
        deadline = deadline_dt.isoformat().replace("+00:00", "Z")
        result = validators.validate_deadline(deadline)

        # Result should be in ISO format with +00:00
        assert result is not None

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_different_timezone(self, mock_utc_now):
        """Test deadline with non-UTC timezone is converted correctly"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        # Create deadline with +05:00 timezone offset
        other_tz = timezone(timedelta(hours=5))
        deadline_dt = (fixed_time + timedelta(seconds=30)).astimezone(other_tz)
        deadline = deadline_dt.isoformat()

        result = validators.validate_deadline(deadline)
        assert result is not None

    @patch("kraken.rest.schema.validators.utc_now")
    def test_validate_deadline_in_past_bounded_to_minimum(self, mock_utc_now):
        """Test deadline in past is bounded to minimum (2 seconds)"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        # Past deadline
        deadline = (fixed_time - timedelta(seconds=10)).isoformat()
        result = validators.validate_deadline(deadline)

        expected = (fixed_time + timedelta(seconds=2)).isoformat()
        assert result == expected


class TestComputeDeadline:
    """Tests for compute_deadline function"""

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_default_latency(self, mock_utc_now):
        """Test compute deadline with default latency tolerance"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline()

        # Default LATENCY_TOLERANCE is likely 5 seconds
        expected = (fixed_time + timedelta(seconds=LATENCY_TOLERANCE)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_custom_latency_within_range(self, mock_utc_now):
        """Test compute deadline with custom latency within valid range"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline(latency_tolerance=30)

        expected = (fixed_time + timedelta(seconds=30)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_latency_below_minimum(self, mock_utc_now):
        """Test compute deadline with latency below minimum (bounded to 2 seconds)"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline(latency_tolerance=1)

        expected = (fixed_time + timedelta(seconds=2)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_latency_above_maximum(self, mock_utc_now):
        """Test compute deadline with latency above maximum (bounded to 60 seconds)"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline(latency_tolerance=100)

        expected = (fixed_time + timedelta(seconds=60)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_latency_exactly_2_seconds(self, mock_utc_now):
        """Test compute deadline with latency exactly at 2 second boundary"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline(latency_tolerance=2)

        expected = (fixed_time + timedelta(seconds=2)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_latency_exactly_60_seconds(self, mock_utc_now):
        """Test compute deadline with latency exactly at 60 second boundary"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline(latency_tolerance=60)

        expected = (fixed_time + timedelta(seconds=60)).isoformat()
        assert result == expected

    @patch("kraken.rest.schema.validators.utc_now")
    def test_compute_deadline_returns_rfc3339_format(self, mock_utc_now):
        """Test compute deadline returns RFC3339 formatted string"""
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_utc_now.return_value = fixed_time

        result = validators.compute_deadline(latency_tolerance=10)

        # Verify it can be parsed back
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None


# ============================================================================
# Range Validators
# ============================================================================


class TestValidateTimeout:
    """Tests for validate_timeout function"""

    def test_validate_timeout_zero(self):
        """Test timeout validation with zero (minimum valid)"""
        result = validators.validate_timeout(0)
        assert result == 0

    def test_validate_timeout_maximum(self):
        """Test timeout validation with 86400 (maximum valid)"""
        result = validators.validate_timeout(86400)
        assert result == 86400

    def test_validate_timeout_mid_range(self):
        """Test timeout validation with mid-range value"""
        result = validators.validate_timeout(3600)
        assert result == 3600

    def test_validate_timeout_from_string(self):
        """Test timeout validation from string"""
        result = validators.validate_timeout("7200")
        assert result == 7200

    def test_validate_timeout_negative_raises(self):
        """Test timeout validation with negative value raises ValueError"""
        with pytest.raises(ValueError, match="Timeout must be between 0 and 86400"):
            validators.validate_timeout(-1)

    def test_validate_timeout_above_maximum_raises(self):
        """Test timeout validation above maximum raises ValueError"""
        with pytest.raises(ValueError, match="Timeout must be between 0 and 86400"):
            validators.validate_timeout(86401)

    def test_validate_timeout_far_above_maximum_raises(self):
        """Test timeout validation far above maximum raises ValueError"""
        with pytest.raises(ValueError, match="Timeout must be between 0 and 86400"):
            validators.validate_timeout(100000)


class TestValidateOhlcInterval:
    """Tests for validate_ohlc_interval function"""

    def test_validate_ohlc_interval_none(self):
        """Test OHLC interval validation with None"""
        result = validators.validate_ohlc_interval(None)
        assert result is None

    def test_validate_ohlc_interval_1_minute(self):
        """Test OHLC interval validation with 1 minute"""
        result = validators.validate_ohlc_interval(1)
        assert result == 1

    def test_validate_ohlc_interval_5_minutes(self):
        """Test OHLC interval validation with 5 minutes"""
        result = validators.validate_ohlc_interval(5)
        assert result == 5

    def test_validate_ohlc_interval_15_minutes(self):
        """Test OHLC interval validation with 15 minutes"""
        result = validators.validate_ohlc_interval(15)
        assert result == 15

    def test_validate_ohlc_interval_30_minutes(self):
        """Test OHLC interval validation with 30 minutes"""
        result = validators.validate_ohlc_interval(30)
        assert result == 30

    def test_validate_ohlc_interval_60_minutes(self):
        """Test OHLC interval validation with 60 minutes"""
        result = validators.validate_ohlc_interval(60)
        assert result == 60

    def test_validate_ohlc_interval_240_minutes(self):
        """Test OHLC interval validation with 240 minutes"""
        result = validators.validate_ohlc_interval(240)
        assert result == 240

    def test_validate_ohlc_interval_1440_minutes(self):
        """Test OHLC interval validation with 1440 minutes (1 day)"""
        result = validators.validate_ohlc_interval(1440)
        assert result == 1440

    def test_validate_ohlc_interval_10080_minutes(self):
        """Test OHLC interval validation with 10080 minutes (1 week)"""
        result = validators.validate_ohlc_interval(10080)
        assert result == 10080

    def test_validate_ohlc_interval_21600_minutes(self):
        """Test OHLC interval validation with 21600 minutes (15 days)"""
        result = validators.validate_ohlc_interval(21600)
        assert result == 21600

    def test_validate_ohlc_interval_invalid_2_raises(self):
        """Test OHLC interval validation with invalid value 2 raises ValueError"""
        with pytest.raises(ValueError, match="Interval must be one of"):
            validators.validate_ohlc_interval(2)

    def test_validate_ohlc_interval_invalid_10_raises(self):
        """Test OHLC interval validation with invalid value 10 raises ValueError"""
        with pytest.raises(ValueError, match="Interval must be one of"):
            validators.validate_ohlc_interval(10)

    def test_validate_ohlc_interval_invalid_100_raises(self):
        """Test OHLC interval validation with invalid value 100 raises ValueError"""
        with pytest.raises(ValueError, match="Interval must be one of"):
            validators.validate_ohlc_interval(100)

    def test_validate_ohlc_interval_zero_raises(self):
        """Test OHLC interval validation with zero raises ValueError"""
        with pytest.raises(ValueError, match="Interval must be one of"):
            validators.validate_ohlc_interval(0)

    def test_validate_ohlc_interval_negative_raises(self):
        """Test OHLC interval validation with negative value raises ValueError"""
        with pytest.raises(ValueError, match="Interval must be one of"):
            validators.validate_ohlc_interval(-1)


class TestValidateOrderBookCount:
    """Tests for validate_order_book_count function"""

    def test_validate_order_book_count_none(self):
        """Test order book count validation with None"""
        result = validators.validate_order_book_count(None)
        assert result is None

    def test_validate_order_book_count_minimum(self):
        """Test order book count validation with minimum value (1)"""
        result = validators.validate_order_book_count(1)
        assert result == 1

    def test_validate_order_book_count_maximum(self):
        """Test order book count validation with maximum value (500)"""
        result = validators.validate_order_book_count(500)
        assert result == 500

    def test_validate_order_book_count_mid_range(self):
        """Test order book count validation with mid-range value"""
        result = validators.validate_order_book_count(100)
        assert result == 100

    def test_validate_order_book_count_zero_raises(self):
        """Test order book count validation with zero raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 500"):
            validators.validate_order_book_count(0)

    def test_validate_order_book_count_negative_raises(self):
        """Test order book count validation with negative value raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 500"):
            validators.validate_order_book_count(-1)

    def test_validate_order_book_count_above_maximum_raises(self):
        """Test order book count validation above maximum raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 500"):
            validators.validate_order_book_count(501)

    def test_validate_order_book_count_far_above_maximum_raises(self):
        """Test order book count validation far above maximum raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 500"):
            validators.validate_order_book_count(1000)


class TestValidateRecentTradesCount:
    """Tests for validate_recent_trades_count function"""

    def test_validate_recent_trades_count_none(self):
        """Test recent trades count validation with None"""
        result = validators.validate_recent_trades_count(None)
        assert result is None

    def test_validate_recent_trades_count_minimum(self):
        """Test recent trades count validation with minimum value (1)"""
        result = validators.validate_recent_trades_count(1)
        assert result == 1

    def test_validate_recent_trades_count_maximum(self):
        """Test recent trades count validation with maximum value (1000)"""
        result = validators.validate_recent_trades_count(1000)
        assert result == 1000

    def test_validate_recent_trades_count_mid_range(self):
        """Test recent trades count validation with mid-range value"""
        result = validators.validate_recent_trades_count(500)
        assert result == 500

    def test_validate_recent_trades_count_zero_raises(self):
        """Test recent trades count validation with zero raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 1000"):
            validators.validate_recent_trades_count(0)

    def test_validate_recent_trades_count_negative_raises(self):
        """Test recent trades count validation with negative value raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 1000"):
            validators.validate_recent_trades_count(-1)

    def test_validate_recent_trades_count_above_maximum_raises(self):
        """Test recent trades count validation above maximum raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 1000"):
            validators.validate_recent_trades_count(1001)

    def test_validate_recent_trades_count_far_above_maximum_raises(self):
        """Test recent trades count validation far above maximum raises ValueError"""
        with pytest.raises(ValueError, match="Count must be between 1 and 1000"):
            validators.validate_recent_trades_count(10000)
