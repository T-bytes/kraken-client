from datetime import datetime, timezone
from time import time


def bool_from_str(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    value = value.lower()
    if value in ("true", "t", "yes", "y", "on", "1"):
        return True
    elif value in ("false", "f", "no", "n", "off", "0"):
        return False
    raise ValueError(f"Cannot convert '{value}' to boolean")


def get_nonce() -> int:
    return int(time() * 1000.0)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
