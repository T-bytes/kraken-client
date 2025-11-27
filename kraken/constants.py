import os

from kraken.utilities import bool_from_str

RETRY_TIME_LIMIT = int(os.getenv("KRAKEN_RETRY_TIME", "60"))
LATENCY_TOLERANCE = int(os.getenv("KRAKEN_LATENCY_TOLERANCE", "5"))
SANDBOX_TRADING = bool_from_str(os.getenv("KRAKEN_SANDBOX_TRADE", "off"))

RATE_LIMIT_TIER = os.getenv("KRAKEN_RATE_LIMIT_TIER", "starter").lower()

RATE_LIMIT_CONFIG = {
    "starter": {"max_counter": 15, "decay_rate": -0.33},
    "intermediate": {"max_counter": 20, "decay_rate": -0.5},
    "pro": {"max_counter": 20, "decay_rate": -1.0},
}
