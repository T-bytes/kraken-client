import json

import httpx
import websockets.exceptions


class KrakenAPIError(RuntimeError):
    """Base exception for all Kraken API errors."""

    pass


class KrakenPayloadError(KrakenAPIError, json.JSONDecodeError):
    """Exception raised when response payload cannot be parsed."""

    pass


class KrakenWebsocketError(KrakenAPIError, websockets.exceptions.WebSocketException):
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
