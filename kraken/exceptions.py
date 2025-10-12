class KrakenAPIError(Exception):
    """Base exception for Kraken API errors"""

    pass


class KrakenAuthenticationError(KrakenAPIError):
    """Raised when authentication fails"""

    pass


class KrakenRequestError(KrakenAPIError):
    """Raised when a client-side request error occurs"""

    pass


class KrakenResponseError(KrakenAPIError):
    """Raised when the API returns an error response"""

    pass
