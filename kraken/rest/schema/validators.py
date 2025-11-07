"""Reusable field validators for trading schemas.

This module contains validator functions that can be used with Pydantic's
@field_validator decorator to ensure consistent validation across schemas.
"""

from datetime import datetime, timedelta
from typing import Any

from pydantic_core import PydanticCustomError

from kraken.constants import LATENCY_TOLERANCE
from kraken.utilities import utc_now

# Order flag validation set
ORDER_FLAG_SET = {"post", "fcib", "fciq", "viqc"}


def validate_ordertype(value: str) -> str:
    """Convert order type to lowercase and strip whitespace.

    Args:
        value: The order type string

    Returns:
        Lowercase, stripped order type
    """
    return value.lower().strip()


def validate_volume(value: str | float | int) -> str:
    """Convert volume to string representation.

    Args:
        value: Volume as string, float, or int

    Returns:
        String representation of volume
    """
    return str(value)


def validate_display_volume(value: str | float | int | None, order_volume: float) -> str | None:
    """Validate and floor display volume to acceptable range.

    For iceberg orders, display volume must be between 1/15 of order volume
    and the full order volume.

    Args:
        value: Display volume to validate
        order_volume: Total order volume for floor/ceiling calculation

    Returns:
        Validated display volume as string, or None if input is None
    """
    if value is None:
        return None

    floor_volume = order_volume / 15.0
    display_val = float(value)

    if display_val > order_volume:
        return str(order_volume)
    elif display_val < floor_volume:
        return str(floor_volume)
    else:
        return str(value)


def validate_leverage(value: str | int | None) -> str | None:
    """Convert leverage to string representation.

    Args:
        value: Leverage as string, int, or None

    Returns:
        String representation of leverage, or None if input is None
    """
    if value is None:
        return None
    return str(value)


def validate_order_flags(value: str | list[str] | set[str] | None) -> str | None:
    """Normalize and validate order flags.

    Accepts comma-separated string, list, or set of flags. Filters to only
    valid flags and returns as comma-separated string.

    Args:
        value: Order flags in various formats

    Returns:
        Comma-separated string of valid flags, or None if no valid flags
    """
    if value is None:
        return None

    if isinstance(value, str):
        splits = value.split(",")
        value = set(splits) if len(splits) > 1 else {value}
    elif isinstance(value, list):
        value = set(value)

    # Filter to only valid flags
    valid_flags = ORDER_FLAG_SET.intersection(value)
    return ",".join(valid_flags) if valid_flags else None


def validate_time_in_force(value: str) -> str:
    """Convert time in force to uppercase and strip whitespace.

    Args:
        value: Time in force string

    Returns:
        Uppercase, stripped time in force
    """
    return value.upper().strip()


def validate_deadline(value: str | None) -> str | None:
    """Validate deadline format and bound to acceptable range.

    Ensures deadline:
    - Includes timezone information (RFC3339 format)
    - Is between 2-60 seconds from current time

    Args:
        value: RFC3339 timestamp string or None

    Returns:
        Validated and bounded deadline timestamp, or None if input is None

    Raises:
        ValueError: If deadline missing timezone or invalid format
    """
    if value is None:
        return None

    try:
        deadline = datetime.fromisoformat(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid deadline format: {e}") from e

    if deadline.tzinfo is None:
        raise ValueError(
            "Deadline must include timezone information (RFC3339 format). "
            "Example: '2025-01-15T12:00:00+00:00' or use 'Z' for UTC."
        )

    # Bound deadline between 2-60 seconds from now
    now = utc_now()
    min_t, max_t = now + timedelta(seconds=2), now + timedelta(seconds=60)
    deadline_utc = deadline.astimezone(now.tzinfo)

    if deadline_utc < min_t:
        deadline_utc = min_t
    elif deadline_utc > max_t:
        deadline_utc = max_t

    return deadline_utc.isoformat()


def normalize_txid(value: str | int | None) -> str | int | None:
    """Normalize transaction ID - convert string integers to int.

    Args:
        value: Transaction ID as string, int, or None

    Returns:
        Integer if value is numeric string or int, original string otherwise
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return value.strip()
    return value


def compute_deadline(latency_tolerance: int = LATENCY_TOLERANCE) -> str:
    """Compute a deadline timestamp for request submission.

    This utility should be called by the REST client at request signing time,
    not during order instantiation, to ensure accurate timing for async operations.

    Args:
        latency_tolerance: Seconds to add to current time for deadline (default from config)

    Returns:
        RFC3339 formatted deadline string bounded to 2-60 seconds from now
    """
    now = utc_now()
    deadline = now + timedelta(seconds=latency_tolerance)
    min_t, max_t = now + timedelta(seconds=2), now + timedelta(seconds=60)

    if deadline < min_t:
        deadline = min_t
    elif deadline > max_t:
        deadline = max_t

    return deadline.isoformat()


def validate_timeout(value: int | str) -> int:
    """Validate timeout is within allowed range (0-86400 seconds).

    Args:
        value: Timeout value in seconds

    Returns:
        Validated timeout as integer

    Raises:
        ValueError: If timeout is outside allowed range
    """
    timeout = int(value)
    if timeout < 0 or timeout > 86400:
        raise ValueError(f"Timeout must be between 0 and 86400 seconds (24 hours), got {timeout}")
    return timeout


def normalize_comma_separated_list(value: str | list[str] | None) -> str | None:
    """Normalize input to comma-separated string format.

    Accepts a string (returned as-is after stripping), a list of strings
    (converted to comma-separated format), or None. Validates that list
    items are non-empty strings and removes duplicates while preserving order.

    Args:
        value: Either a comma-delimited string, a list of strings, or None

    Returns:
        Comma-delimited string or None

    Raises:
        ValueError: If input is invalid (empty, wrong type, contains empty strings, etc.)

    Examples:
        >>> normalize_comma_separated_list("BTC")
        'BTC'
        >>> normalize_comma_separated_list("BTC,ETH")
        'BTC,ETH'
        >>> normalize_comma_separated_list(["BTC", "ETH"])
        'BTC,ETH'
        >>> normalize_comma_separated_list(None)
        None
        >>> normalize_comma_separated_list(["BTC", "ETH", "BTC"])
        'BTC,ETH'
    """
    if value is None:
        return None

    if isinstance(value, str):
        if not value.strip():
            raise ValueError("String cannot be empty or whitespace")
        return value.strip()

    if isinstance(value, list):
        if not value:
            raise ValueError("List cannot be empty")

        validated_items = []
        seen = set()

        for item in value:
            if not isinstance(item, str):
                raise ValueError(f"All list items must be strings, got {type(item).__name__}")

            stripped = item.strip()
            if not stripped:
                raise ValueError("List cannot contain empty or whitespace-only strings")

            # Remove duplicates while preserving order
            if stripped not in seen:
                validated_items.append(stripped)
                seen.add(stripped)

        return ",".join(validated_items)

    raise ValueError(f"Must be a string, list, or None, got {type(value).__name__}")
