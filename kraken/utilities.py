import re
from datetime import datetime, timezone
from time import time
from uuid import uuid4


def bool_from_str(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    value = value.lower().strip()
    if value in ("true", "t", "yes", "y", "on", "1"):
        return True
    elif value in ("false", "f", "no", "n", "off", "0"):
        return False
    raise ValueError(f"Cannot convert '{value}' to boolean")


def get_nonce() -> int:
    return int(time() * 1000.0)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def rand_uuid() -> str:
    return str(uuid4())


def is_uuid(i: str) -> bool:
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(pattern, i, re.IGNORECASE))


def is_txid(i: str) -> bool:
    pattern = r"^[A-Z0-9]{6}-[A-Z0-9]{5}-[A-Z0-9]{6}$"
    return bool(re.match(pattern, i, re.IGNORECASE))
