"""Kraken REST API Client

This module provides a unified interface to the Kraken REST API supporting both
synchronous and asynchronous operations. Users can freely mix sync and async methods
in their workflow without needing to manage separate client instances.

The client uses httpx for all HTTP operations and provides proper authentication,
error handling, and logging.

Example (Synchronous):
    >>> from kraken.rest import KrakenRESTClient
    >>> client = KrakenRESTClient()
    >>> response = client.request("Time")
    >>> print(response)

Example (Asynchronous):
    >>> from kraken.rest import KrakenRESTClient
    >>> client = KrakenRESTClient()
    >>> response = await client.arequest("Time")
    >>> print(response)

Example (Mixed sync/async):
    >>> client = KrakenRESTClient()
    >>> # Synchronous call
    >>> server_time = client.get("Time")
    >>> # Asynchronous call
    >>> ticker = await client.aget("Ticker", params={"pair": "XBTUSD"})

Example (Context manager):
    >>> # Synchronous context
    >>> with KrakenRESTClient() as client:
    >>>     response = client.request("Time")
    >>>
    >>> # Asynchronous context
    >>> async with KrakenRESTClient() as client:
    >>>     response = await client.arequest("Time")
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from kraken.exceptions import (
    KrakenAPIError,
    KrakenConnectionError,
    KrakenHTTPError,
    KrakenPayloadError,
    KrakenTimeoutError,
)
from kraken.rest.endpoint import KrakenEndpoint

logger = logging.getLogger(__name__)


class KrakenRESTClient:
    """Unified REST client for Kraken API supporting both sync and async operations.

    This client provides a flexible interface to interact with Kraken's REST API,
    allowing users to freely use synchronous or asynchronous methods without managing
    separate client instances. The client handles authentication, request signing,
    and error handling automatically.

    The client uses lazy initialization for underlying HTTP clients, creating them
    only when needed. For best resource management, use the client as a context manager
    or explicitly call close()/aclose() when done.

    Attributes:
        api_key (str): API key for authentication
        api_secret (bytes): Decoded API secret for signing requests
        timeout (int): Request timeout in seconds
        _sync_client (httpx.Client): Synchronous HTTP client (lazy-initialized)
        _async_client (httpx.AsyncClient): Asynchronous HTTP client (lazy-initialized)

    Synchronous Methods:
        request(method, params): Make a request (auto-detects GET/POST)
        get(method, params): Make a GET request
        post(method, params): Make a POST request
        put(method, params): Make a PUT request
        patch(method, params): Make a PATCH request
        delete(method, params): Make a DELETE request

    Asynchronous Methods:
        arequest(method, params): Make an async request (auto-detects GET/POST)
        aget(method, params): Make an async GET request
        apost(method, params): Make an async POST request
        aput(method, params): Make an async PUT request
        apatch(method, params): Make an async PATCH request
        adelete(method, params): Make an async DELETE request

    Example:
        >>> # Without context manager
        >>> client = KrakenRESTClient(api_key="your_key", api_secret="your_secret")
        >>> balance = client.request("Balance")
        >>> ticker = await client.arequest("Ticker", params={"pair": "XBTUSD"})
        >>> client.close()  # or await client.aclose()
        >>>
        >>> # With context manager (recommended)
        >>> with KrakenRESTClient() as client:
        >>>     balance = client.request("Balance")
        >>>
        >>> async with KrakenRESTClient() as client:
        >>>     balance = await client.arequest("Balance")
    """

    API_DOMAIN = "https://api.kraken.com"
    USER_AGENT = "Kraken REST API Client/2.0"

    def __init__(
        self, api_key: Optional[str] = None, api_secret: Optional[str] = None, timeout: int = 30
    ):
        """Initialize the Kraken REST client.

        Args:
            api_key: API key for authentication. If not provided, reads from
                KRAKEN_API_KEY environment variable
            api_secret: API secret for authentication. If not provided, reads from
                KRAKEN_API_SECRET environment variable
            timeout: Request timeout in seconds. Default is 30

        Raises:
            ValueError: If API secret format is invalid
        """
        self.api_key = api_key or os.getenv("KRAKEN_API_KEY")
        secret_str = api_secret or os.getenv("KRAKEN_API_SECRET")

        self.api_secret: Optional[bytes] = None
        if secret_str:
            try:
                self.api_secret = base64.b64decode(secret_str)
            except Exception as e:
                logger.error(f"Failed to decode API secret: {e}")
                raise ValueError(f"Invalid API secret format: {e}") from e

        self.timeout = timeout
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

        logger.info("Kraken REST client initialized")

    def _get_sync_client(self) -> httpx.Client:
        """Get or create the synchronous HTTP client.

        Returns:
            Initialized httpx.Client instance
        """
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                headers={"User-Agent": self.USER_AGENT}, timeout=self.timeout
            )
            logger.debug("Synchronous HTTP client initialized")
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the asynchronous HTTP client.

        Returns:
            Initialized httpx.AsyncClient instance
        """
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                headers={"User-Agent": self.USER_AGENT}, timeout=self.timeout
            )
            logger.debug("Asynchronous HTTP client initialized")
        return self._async_client

    def _get_api_type(self, method: str) -> KrakenEndpoint:
        """Determine the API type for a given method.

        Args:
            method: API method/endpoint name

        Returns:
            The type of API endpoint

        Raises:
            ValueError: If method is not found in any API type
        """
        for api_type in KrakenEndpoint:
            if method in api_type.channels:
                return api_type

        raise ValueError(f"Unknown API method: {method}")

    def _sign_request(self, url_path: str, data: Dict[str, Any], nonce: str) -> str:
        """Generate signature for authenticated requests.

        Args:
            url_path: Full URL path (e.g., "/0/private/Balance")
            data: Request parameters including nonce
            nonce: Unique nonce for this request

        Returns:
            Base64-encoded HMAC-SHA512 signature

        Raises:
            ValueError: If API secret is not configured
        """
        if not self.api_secret:
            raise ValueError("API secret required for private endpoints")

        # Encode the data
        postdata = "&".join([f"{key}={value}" for key, value in data.items()])
        encoded = (nonce + postdata).encode("utf-8")

        # Create SHA256 hash
        message = url_path.encode("utf-8") + hashlib.sha256(encoded).digest()

        # Create HMAC-SHA512 signature
        signature = hmac.new(self.api_secret, message, hashlib.sha512)

        return base64.b64encode(signature.digest()).decode()

    def _request(
        self, method: str, api_type: KrakenEndpoint, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Internal method to make synchronous HTTP requests to Kraken API.

        Args:
            method: API method/endpoint name
            api_type: Type of API endpoint
            params: Request parameters

        Returns:
            Parsed JSON response from the API

        Raises:
            ValueError: If authentication is required but credentials missing
            KrakenTimeoutError: If request times out
            KrakenConnectionError: If connection to API fails
            KrakenHTTPError: If HTTP error occurs (4xx, 5xx)
            KrakenPayloadError: If JSON parsing fails
            KrakenAPIError: If the Kraken API returns an error response
        """
        if params is None:
            params = {}

        url_path = f"{api_type.path}{method}"
        url = f"{self.API_DOMAIN}{url_path}"

        headers = {}
        client = self._get_sync_client()

        try:
            if api_type.is_private():
                # Private endpoint - requires authentication
                if not self.api_key or not self.api_secret:
                    raise ValueError(
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
                response = client.post(url, data=params, headers=headers)
            else:
                # Public endpoint - no authentication required
                logger.debug(f"Making public request to {method}")
                response = client.get(url, params=params, headers=headers)

            # Raise exception for HTTP errors
            response.raise_for_status()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {method}: {e}")
            raise KrakenTimeoutError(f"Request timeout for {method}: {e}") from e
        except httpx.ConnectError as e:
            logger.error(f"Connection error for {method}: {e}")
            raise KrakenConnectionError(f"Connection error for {method}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {method}: {e}")
            raise KrakenHTTPError(f"HTTP error for {method}: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"Request failed for {method}: {e}")
            raise

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise KrakenPayloadError(f"Invalid JSON response: {e}", "", 0) from e

        # Check for API errors
        if "error" in data and data["error"]:
            error_msg = ", ".join(data["error"])
            logger.error(f"API error for {method}: {error_msg}")
            raise KrakenAPIError(f"API error: {error_msg}")

        logger.info(f"Successfully completed request to {method}")
        return data

    async def _arequest(
        self, method: str, api_type: KrakenEndpoint, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Internal method to make asynchronous HTTP requests to Kraken API.

        Args:
            method: API method/endpoint name
            api_type: Type of API endpoint
            params: Request parameters

        Returns:
            Parsed JSON response from the API

        Raises:
            ValueError: If authentication is required but credentials missing
            KrakenTimeoutError: If request times out
            KrakenConnectionError: If connection to API fails
            KrakenHTTPError: If HTTP error occurs (4xx, 5xx)
            KrakenPayloadError: If JSON parsing fails
            KrakenAPIError: If the Kraken API returns an error response
        """
        if params is None:
            params = {}

        url_path = f"{api_type.path}{method}"
        url = f"{self.API_DOMAIN}{url_path}"

        headers = {}
        client = self._get_async_client()

        try:
            if api_type.is_private():
                # Private endpoint - requires authentication
                if not self.api_key or not self.api_secret:
                    raise ValueError(
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

                logger.debug(f"Making authenticated async request to {method}")
                response = await client.post(url, data=params, headers=headers)
            else:
                # Public endpoint - no authentication required
                logger.debug(f"Making public async request to {method}")
                response = await client.get(url, params=params, headers=headers)

            # Raise exception for HTTP errors
            response.raise_for_status()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {method}: {e}")
            raise KrakenTimeoutError(f"Request timeout for {method}: {e}") from e
        except httpx.ConnectError as e:
            logger.error(f"Connection error for {method}: {e}")
            raise KrakenConnectionError(f"Connection error for {method}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {method}: {e}")
            raise KrakenHTTPError(f"HTTP error for {method}: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"Request failed for {method}: {e}")
            raise

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise KrakenPayloadError(f"Invalid JSON response: {e}", "", 0) from e

        # Check for API errors
        if "error" in data and data["error"]:
            error_msg = ", ".join(data["error"])
            logger.error(f"API error for {method}: {error_msg}")
            raise KrakenAPIError(f"API error: {error_msg}")

        logger.info(f"Successfully completed async request to {method}")
        return data

    # Synchronous public methods
    def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a synchronous request to the Kraken API.

        This is the main public method for synchronous interaction with the API.
        It automatically determines the endpoint type and handles authentication.

        Args:
            method: API method/endpoint name (e.g., "Time", "Balance", "AddOrder")
            params: Request parameters

        Returns:
            API response data

        Raises:
            ValueError: If the method is unknown or authentication fails
            KrakenTimeoutError: If request times out
            KrakenConnectionError: If connection to API fails
            KrakenHTTPError: If HTTP error occurs (4xx, 5xx)
            KrakenPayloadError: If JSON parsing fails
            KrakenAPIError: If the API returns an error response

        Example:
            >>> client.request("Time")
            {'error': [], 'result': {'unixtime': 1234567890, 'rfc1123': '...'}}

            >>> client.request("Ticker", params={"pair": "XBTUSD"})
            {'error': [], 'result': {...}}
        """
        api_type = self._get_api_type(method)
        return self._request(method, api_type, params)

    def get(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a synchronous GET request.

        Args:
            method: API method/endpoint name
            params: Query parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    def post(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a synchronous POST request.

        Args:
            method: API method/endpoint name
            params: POST parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    def put(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a synchronous PUT request.

        Args:
            method: API method/endpoint name
            params: PUT parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    def patch(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a synchronous PATCH request.

        Args:
            method: API method/endpoint name
            params: PATCH parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    def delete(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a synchronous DELETE request.

        Args:
            method: API method/endpoint name
            params: DELETE parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    # Asynchronous public methods
    async def arequest(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an asynchronous request to the Kraken API.

        This is the main public method for asynchronous interaction with the API.
        It automatically determines the endpoint type and handles authentication.

        Args:
            method: API method/endpoint name (e.g., "Time", "Balance", "AddOrder")
            params: Request parameters

        Returns:
            API response data

        Raises:
            ValueError: If the method is unknown or authentication fails
            KrakenTimeoutError: If request times out
            KrakenConnectionError: If connection to API fails
            KrakenHTTPError: If HTTP error occurs (4xx, 5xx)
            KrakenPayloadError: If JSON parsing fails
            KrakenAPIError: If the API returns an error response

        Example:
            >>> await client.arequest("Time")
            {'error': [], 'result': {'unixtime': 1234567890, 'rfc1123': '...'}}

            >>> await client.arequest("Ticker", params={"pair": "XBTUSD"})
            {'error': [], 'result': {...}}
        """
        api_type = self._get_api_type(method)
        return await self._arequest(method, api_type, params)

    async def aget(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an asynchronous GET request.

        Args:
            method: API method/endpoint name
            params: Query parameters

        Returns:
            API response data
        """
        return await self.arequest(method, params)

    async def apost(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an asynchronous POST request.

        Args:
            method: API method/endpoint name
            params: POST parameters

        Returns:
            API response data
        """
        return await self.arequest(method, params)

    async def aput(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an asynchronous PUT request.

        Args:
            method: API method/endpoint name
            params: PUT parameters

        Returns:
            API response data
        """
        return await self.arequest(method, params)

    async def apatch(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an asynchronous PATCH request.

        Args:
            method: API method/endpoint name
            params: PATCH parameters

        Returns:
            API response data
        """
        return await self.arequest(method, params)

    async def adelete(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an asynchronous DELETE request.

        Args:
            method: API method/endpoint name
            params: DELETE parameters

        Returns:
            API response data
        """
        return await self.arequest(method, params)

    # Resource management
    def close(self):
        """Close the synchronous HTTP client and cleanup resources."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        logger.info("Kraken REST client (sync) closed")

    async def aclose(self):
        """Close the asynchronous HTTP client and cleanup resources."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
        logger.info("Kraken REST client (async) closed")

    # Context manager support - Synchronous
    def __enter__(self):
        """Synchronous context manager entry."""
        # Pre-initialize sync client for context manager usage
        self._get_sync_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit."""
        self.close()
        return False

    # Context manager support - Asynchronous
    async def __aenter__(self):
        """Asynchronous context manager entry."""
        # Pre-initialize async client for context manager usage
        self._get_async_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit."""
        await self.aclose()
        return False


# Backward compatibility aliases
KrakenClientREST = KrakenRESTClient
KrakenClientAsyncREST = KrakenRESTClient
