import json

import httpx
import requests.exceptions as reqex
import websockets.exceptions as socketex


class KrakenAPIError(RuntimeError):
    pass


class KrakenPayloadError(KrakenAPIError, json.JSONDecodeError):
    pass


class KrakenWebsocketError(KrakenAPIError, socketex.WebSocketException):
    pass


class KrakenTimeoutError(KrakenAPIError, reqex.Timeout, httpx.TimeoutException):
    pass


class KrakenConnectionError(KrakenAPIError, reqex.ConnectionError, httpx.ConnectError):
    pass


class KrakenHTTPError(KrakenAPIError, reqex.HTTPError, httpx.HTTPError):
    pass
