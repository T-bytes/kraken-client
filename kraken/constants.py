import os

RETRY_TIME_LIMIT = int(os.getenv("KRAKEN_RETRY_TIME", "60"))  # seconds
