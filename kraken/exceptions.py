import json

import httpx
import websockets.exceptions


class KrakenAPIError(RuntimeError):
    """Base exception for all Kraken API errors.

    Kraken API errors follow the format: <severity>:<category>:<description>

    Attributes:
        message: The full error message from the API
        severity: Error severity (E for error, W for warning)
        category: Error category (General, Order, Service, Auth, Account, etc.)
        description: Detailed error description
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
        self.severity, self.category, self.description = self._parse_error(message)

    @staticmethod
    def _parse_error(message: str) -> tuple[str, str, str]:
        """Parse Kraken error message format: <severity>:<category>:<description>"""
        parts = message.split(":", 2)
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        return "E", "General", message


class KrakenPayloadError(KrakenAPIError, json.JSONDecodeError):
    """Exception raised when response payload cannot be parsed."""

    def __init__(self, msg: str, doc: str, pos: int):
        """Initialize KrakenPayloadError with both parent class requirements.

        Args:
            msg: Error message describing the issue
            doc: The JSON document being parsed
            pos: Position in document where error occurred
        """
        json.JSONDecodeError.__init__(self, msg, doc, pos)
        KrakenAPIError.__init__(self, msg)


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


class KrakenInvalidArgumentsError(KrakenAPIError):
    """Exception raised when request payload is malformed, incorrect or ambiguous.

    Corresponds to:
        - EGeneral:Invalid arguments
    """

    pass


class KrakenRateLimitError(KrakenAPIError):
    """Exception raised when API rate limit is exceeded.

    Rate limits are tier-based with a counter that increments per request
    and decays over time. When exceeded, requests are rejected until the
    counter decays below the threshold.

    Corresponds to:
        - EAPI:Rate limit exceeded
        - EOrder:Rate limit exceeded
    """

    pass


class KrakenTemporaryLockoutError(KrakenAPIError):
    """Exception raised when too many sequential invalid key errors occur.

    Corresponds to:
        - EGeneral:Temporary lockout
    """

    pass


class KrakenServiceUnavailableError(KrakenAPIError):
    """Exception raised when the matching engine or API is offline.

    Corresponds to:
        - EService:Unavailable
        - EService:Market in cancel_only mode
        - EService:Market in post_only mode
    """

    pass


class KrakenPermissionDeniedError(KrakenAPIError):
    """Exception raised when API key lacks permission for the request.

    Corresponds to:
        - EGeneral:Permission denied
    """

    pass


class KrakenInvalidKeyError(KrakenAPIError):
    """Exception raised when authentication fails.

    Corresponds to:
        - EAPI:Invalid key
        - EAPI:Invalid signature
        - EAPI:Invalid nonce
    """

    pass


class KrakenOrderError(KrakenAPIError):
    """Base exception for order-related errors."""

    pass


class KrakenInsufficientFundsError(KrakenOrderError):
    """Exception raised when client lacks sufficient funds.

    Corresponds to:
        - EOrder:Insufficient funds
        - EOrder:Insufficient margin
    """

    pass


class KrakenInvalidPriceError(KrakenOrderError):
    """Exception raised when order price is invalid.

    Corresponds to:
        - EOrder:Invalid price
    """

    pass


class KrakenMarginTradingError(KrakenOrderError):
    """Exception raised for margin trading violations.

    Corresponds to:
        - EOrder:Cannot open opposing position
        - EOrder:Margin allowance exceeded
        - EOrder:Margin level too low
        - EOrder:Margin position size exceeded
    """

    pass


class KrakenOrderLimitsError(KrakenOrderError):
    """Exception raised when order violates limits.

    Corresponds to:
        - EOrder:Orders limit exceeded
        - EOrder:Positions limit exceeded
        - EOrder:Rate limit exceeded
        - EOrder:Order minimum not met
        - EOrder:Cost minimum not met
        - EOrder:Tick size check failed
    """

    pass


class KrakenAccountError(KrakenAPIError):
    """Exception raised for account-related issues.

    Corresponds to:
        - EAccount:Invalid permissions
        - EAuth:Account temporary disabled
        - EAuth:Account unconfirmed
        - EAuth:Rate limit exceeded
        - EAuth:Too many requests
    """

    pass


class KrakenFundingError(KrakenAPIError):
    """Exception raised for funding/withdrawal issues.

    Corresponds to: EFunding:Max fee exceeded
    """

    pass


def classify_error(error_msg: str) -> KrakenAPIError:
    """Classify an error message and return the appropriate exception class.

    Args:
        error_msg: Error message from Kraken API (format: <severity>:<category>:<description>)

    Returns:
        The most specific exception class for this error type
    """
    error_lower = error_msg.lower()

    # Rate limiting errors
    if "rate limit exceeded" in error_lower:
        return KrakenRateLimitError

    # Authentication errors
    if any(x in error_lower for x in ["invalid key", "invalid signature", "invalid nonce"]):
        return KrakenInvalidKeyError

    # Permission and access errors
    if "permission denied" in error_lower:
        return KrakenPermissionDeniedError
    if "temporary lockout" in error_lower:
        return KrakenTemporaryLockoutError

    # Service availability errors
    if any(x in error_lower for x in ["unavailable", "cancel_only mode", "post_only mode"]):
        return KrakenServiceUnavailableError

    # General errors
    if "invalid arguments" in error_lower:
        return KrakenInvalidArgumentsError

    # Order-specific errors
    if any(x in error_lower for x in ["insufficient funds", "insufficient margin"]):
        return KrakenInsufficientFundsError
    if "invalid price" in error_lower:
        return KrakenInvalidPriceError
    if any(
        x in error_lower
        for x in [
            "cannot open opposing position",
            "margin allowance exceeded",
            "margin level too low",
            "margin position size exceeded",
        ]
    ):
        return KrakenMarginTradingError
    if any(
        x in error_lower
        for x in [
            "orders limit exceeded",
            "positions limit exceeded",
            "order minimum not met",
            "cost minimum not met",
            "tick size check failed",
        ]
    ):
        return KrakenOrderLimitsError

    # Account errors
    if any(
        x in error_lower
        for x in [
            "invalid permissions",
            "account temporary disabled",
            "account unconfirmed",
            "too many requests",
        ]
    ):
        return KrakenAccountError

    # Funding errors
    if "max fee exceeded" in error_lower:
        return KrakenFundingError

    # Default to base error class
    return KrakenAPIError
