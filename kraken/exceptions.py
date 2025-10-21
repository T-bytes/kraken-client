import json

import httpx
import websockets.exceptions as socketex


class KrakenAPIError(RuntimeError):
    """Base exception for all Kraken API errors."""

    pass


class KrakenPayloadError(KrakenAPIError, json.JSONDecodeError):
    """Exception raised when response payload cannot be parsed."""

    pass


class KrakenWebsocketError(KrakenAPIError, socketex.WebSocketException):
    """Exception raised for WebSocket-related errors."""

    pass


class KrakenTimeoutError(KrakenAPIError, httpx.TimeoutException):
    """Exception raised when a request times out."""

    pass


class KrakenConnectionError(KrakenAPIError, httpx.ConnectError):
    """Exception raised when connection to API fails."""

    pass


class KrakenHTTPError(KrakenAPIError, httpx.HTTPError):
    """Exception raised for HTTP-level errors (4xx, 5xx)."""

    pass
