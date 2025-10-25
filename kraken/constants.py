import os

from kraken.utilities import bool_from_str

RETRY_TIME_LIMIT = int(os.getenv("KRAKEN_RETRY_TIME", "60"))  # seconds
LATENCY_TOLERANCE = int(os.getenv("KRAKEN_LATENCY_TOLERANCE", "5"))  # seconds
SANDBOX_TRADING = bool_from_str(os.getenv("KRAKEN_SANDBOX_TRADE", "off"))
