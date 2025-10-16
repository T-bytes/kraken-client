class KrakenAPIError(Exception):
    """Base exception for Kraken API errors.

    This exception is used specifically for errors returned by the Kraken API
    in response bodies (e.g., invalid parameters, rate limits, etc.).

    For other error types, the library uses standard exceptions:
    - ValueError: Authentication/configuration errors
    - requests.exceptions.*: HTTP client errors (sync)
    - httpx.*: HTTP client errors (async)
    - websockets.exceptions.*: WebSocket errors
    - json.JSONDecodeError: Response parsing errors
    """

    pass
