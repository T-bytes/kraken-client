"""Kraken REST API Client

This module provides an object-oriented interface to the Kraken REST API.
It supports both public and private endpoints with proper authentication,
error handling, and logging.

Example:
    >>> from kraken.rest import KrakenClientREST
    >>> client = KrakenClientREST()
    >>> response = client.request("Time")
    >>> print(response)
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from enum import Enum
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class APIType(Enum):
    """Enumeration of Kraken API endpoint types

    Each type corresponds to a different category of API endpoints
    and has an associated set of available channels.
    """

    PUBLIC = "public"
    PRIVATE = "private"
    TRADING = "trading"
    FUNDING = "funding"
    STAKING = "staking"

    @property
    def channels(self) -> set:
        """Get the set of available channels for this API type

        Returns:
            set: Set of channel/endpoint names available for this API type
        """
        _channels = {
            APIType.PUBLIC: {
                "Time",
                "Assets",
                "AssetPairs",
                "Ticker",
                "OHLC",
                "Depth",
                "Trades",
                "Spread",
                "SystemStatus",
            },
            APIType.PRIVATE: {
                "Balance",
                "BalanceEx",
                "TradeBalance",
                "OpenOrders",
                "ClosedOrders",
                "QueryOrders",
                "TradesHistory",
                "QueryTrades",
                "OpenPositions",
                "Ledgers",
                "QueryLedgers",
                "TradeVolume",
                "AddExport",
                "ExportStatus",
                "RetrieveExport",
                "RemoveExport",
                "GetWebSocketsToken",
                "CreateSubaccount",
                "AccountTransfer",
            },
            APIType.TRADING: {
                "AddOrder",
                "AddOrderBatch",
                "EditOrder",
                "CancelOrder",
                "CancelOrderBatch",
                "CancelAll",
                "CancelAllOrdersAfter",
            },
            APIType.FUNDING: {
                "DepositMethods",
                "DepositAddresses",
                "DepositStatus",
                "WithdrawInfo",
                "Withdraw",
                "WithdrawStatus",
                "WithdrawCancel",
                "WalletTransfer",
            },
            APIType.STAKING: {
                "Earn/Strategies",
                "Earn/Allocations",
                "Earn/Allocate",
                "Earn/Deallocate",
                "Earn/AllocateStatus",
                "Earn/DeallocateStatus",
                "Staking/Assets",
                "Staking/Balance",
                "Stake",
                "Unstake",
                "Staking/Pending",
                "Staking/Transactions",
            },
        }
        return _channels[self]

    @property
    def path(self) -> str:
        """Get the API path prefix for this type

        Returns:
            str: API path prefix (i.e., "/0/public/" or "/0/private/")
        """
        if self == APIType.PUBLIC:
            return "/0/public/"
        return "/0/private/"

    def is_private(self) -> bool:
        """Check if this API type requires authentication

        Returns:
            bool: True if authentication is required, False otherwise
        """
        return self != APIType.PUBLIC


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


class KrakenClientREST:
    """Synchronous REST client for Kraken API

    This client provides a clean interface to interact with Kraken's REST API,
    handling authentication, request signing, and error handling automatically.

    Attributes:
        api_key (str): API key for authentication
        api_secret (bytes): Decoded API secret for signing requests
        session (requests.Session): HTTP session for connection pooling
        api_domain (str): Base URL for API requests

    Example:
        >>> client = KrakenClientREST(api_key="your_key", api_secret="your_secret")
        >>> balance = client.request("Balance")
        >>> ticker = client.request("Ticker", params={"pair": "XBTUSD"})
    """

    API_DOMAIN = "https://api.kraken.com"
    USER_AGENT = "Kraken REST API Client/1.0"

    def __init__(
        self, api_key: Optional[str] = None, api_secret: Optional[str] = None, timeout: int = 30
    ):
        """Initialize the Kraken REST client

        Parameters:
            api_key (str, optional): API key for authentication.
                If not provided, reads from KRAKEN_API_KEY environment variable
            api_secret (str, optional): API secret for authentication.
                If not provided, reads from KRAKEN_API_SECRET environment variable
            timeout (int, optional): Request timeout in seconds. Default is 30

        Raises:
            KrakenAuthenticationError: If credentials are required but not provided
        """
        self.api_key = api_key or os.getenv("KRAKEN_API_KEY")
        secret_str = api_secret or os.getenv("KRAKEN_API_SECRET")

        self.api_secret: Optional[bytes] = None
        if secret_str:
            try:
                self.api_secret = base64.b64decode(secret_str)
            except Exception as e:
                logger.error(f"Failed to decode API secret: {e}")
                raise KrakenAuthenticationError(f"Invalid API secret format: {e}")

        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

        logger.info("Kraken REST client initialized")

    def _get_api_type(self, method: str) -> APIType:
        """Determine the API type for a given method

        Parameters:
            method (str): API method/endpoint name

        Returns:
            APIType: The type of API endpoint

        Raises:
            KrakenRequestError: If method is not found in any API type
        """
        for api_type in APIType:
            if method in api_type.channels:
                return api_type

        raise KrakenRequestError(f"Unknown API method: {method}")

    def _sign_request(self, url_path: str, data: Dict[str, Any], nonce: str) -> str:
        """Generate signature for authenticated requests

        Parameters:
            url_path (str): Full URL path (e.g., "/0/private/Balance")
            data (Dict[str, Any]): Request parameters including nonce
            nonce (str): Unique nonce for this request

        Returns:
            str: Base64-encoded HMAC-SHA512 signature

        Raises:
            KrakenAuthenticationError: If API secret is not configured
        """
        if not self.api_secret:
            raise KrakenAuthenticationError("API secret required for private endpoints")

        # Encode the data
        postdata = "&".join([f"{key}={value}" for key, value in data.items()])
        encoded = (nonce + postdata).encode("utf-8")

        # Create SHA256 hash
        message = url_path.encode("utf-8") + hashlib.sha256(encoded).digest()

        # Create HMAC-SHA512 signature
        signature = hmac.new(self.api_secret, message, hashlib.sha512)

        return base64.b64encode(signature.digest()).decode()

    def _request(
        self, method: str, api_type: APIType, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Internal method to make HTTP requests to Kraken API

        Parameters:
            method (str): API method/endpoint name
            api_type (APIType): Type of API endpoint
            params (Dict[str, Any], optional): Request parameters

        Returns:
            Dict[str, Any]: Parsed JSON response from the API

        Raises:
            KrakenAuthenticationError: If authentication is required but credentials missing
            KrakenRequestError: If the request fails due to client-side issues
            KrakenResponseError: If the API returns an error
        """
        if params is None:
            params = {}

        url_path = f"{api_type.path}{method}"
        url = f"{self.API_DOMAIN}{url_path}"

        headers = {}

        try:
            if api_type.is_private():
                # Private endpoint - requires authentication
                if not self.api_key or not self.api_secret:
                    raise KrakenAuthenticationError(
                        "API key and secret required for private endpoints. "
                        "Set KRAKEN_API_KEY and KRAKEN_API_SECRET environment variables."
                    )

                # Add nonce to parameters
                nonce = str(int(time.time() * 1000))
                params["nonce"] = nonce

                # Generate signature
                signature = self._sign_request(url_path, params, nonce)

                # Add authentication headers
                headers["API-Key"] = self.api_key
                headers["API-Sign"] = signature

                logger.debug(f"Making authenticated request to {method}")
                response = self.session.post(
                    url, data=params, headers=headers, timeout=self.timeout
                )
            else:
                # Public endpoint - no authentication required
                logger.debug(f"Making public request to {method}")
                response = self.session.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )

            # Raise exception for HTTP errors
            response.raise_for_status()

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout for {method}: {e}")
            raise KrakenRequestError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {method}: {e}")
            raise KrakenRequestError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {method}: {e}")
            raise KrakenRequestError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method}: {e}")
            raise KrakenRequestError(f"Request failed: {e}")

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise KrakenResponseError(f"Invalid JSON response: {e}")

        # Check for API errors
        if "error" in data and data["error"]:
            error_msg = ", ".join(data["error"])
            logger.error(f"API error for {method}: {error_msg}")
            raise KrakenResponseError(f"API error: {error_msg}")

        logger.info(f"Successfully completed request to {method}")
        return data

    def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Kraken API

        This is the main public method for interacting with the API.
        It automatically determines the endpoint type and handles authentication.

        Parameters:
            method (str): API method/endpoint name (e.g., "Time", "Balance", "AddOrder")
            params (Dict[str, Any], optional): Request parameters

        Returns:
            Dict[str, Any]: API response data

        Raises:
            KrakenRequestError: If the method is unknown or request fails
            KrakenAuthenticationError: If authentication fails
            KrakenResponseError: If the API returns an error

        Example:
            >>> client.request("Time")
            {'error': [], 'result': {'unixtime': 1234567890, 'rfc1123': '...'}}

            >>> client.request("Ticker", params={"pair": "XBTUSD"})
            {'error': [], 'result': {...}}
        """
        api_type = self._get_api_type(method)
        return self._request(method, api_type, params)

    def get(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience method for GET requests (typically public endpoints)

        Parameters:
            method (str): API method/endpoint name
            params (Dict[str, Any], optional): Query parameters

        Returns:
            Dict[str, Any]: API response data
        """
        return self.request(method, params)

    def post(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience method for POST requests (typically private endpoints)

        Parameters:
            method (str): API method/endpoint name
            params (Dict[str, Any], optional): POST parameters

        Returns:
            Dict[str, Any]: API response data
        """
        return self.request(method, params)

    def close(self):
        """Close the HTTP session and cleanup resources"""
        self.session.close()
        logger.info("Kraken REST client closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
