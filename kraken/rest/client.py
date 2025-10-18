"""Kraken REST API Client

This module provides both synchronous and asynchronous interfaces to the Kraken REST API.
It supports both public and private endpoints with proper authentication,
error handling, and logging.

Example (Sync):
    >>> from kraken.rest import KrakenClientREST
    >>> client = KrakenClientREST()
    >>> response = client.request("Time")
    >>> print(response)

Example (Async):
    >>> from kraken.rest import KrakenClientAsyncREST
    >>> async with KrakenClientAsyncREST() as client:
    >>>     response = await client.request("Time")
    >>>     print(response)
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict, Optional

import httpx
import requests

from kraken.exceptions import KrakenAPIError
from kraken.rest.endpoint import KrakenEndpoint

logger = logging.getLogger(__name__)


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
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

        logger.info("Kraken REST client initialized")

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
        """Internal method to make HTTP requests to Kraken API.

        Args:
            method: API method/endpoint name
            api_type: Type of API endpoint
            params: Request parameters

        Returns:
            Parsed JSON response from the API

        Raises:
            ValueError: If authentication is required but credentials missing, or JSON parsing fails
            requests.exceptions.*: If HTTP request fails
            KrakenAPIError: If the Kraken API returns an error response
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
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {method}: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {method}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method}: {e}")
            raise

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}") from e

        # Check for API errors
        if "error" in data and data["error"]:
            error_msg = ", ".join(data["error"])
            logger.error(f"API error for {method}: {error_msg}")
            raise KrakenAPIError(f"API error: {error_msg}")

        logger.info(f"Successfully completed request to {method}")
        return data

    def request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Kraken API.

        This is the main public method for interacting with the API.
        It automatically determines the endpoint type and handles authentication.

        Args:
            method: API method/endpoint name (e.g., "Time", "Balance", "AddOrder")
            params: Request parameters

        Returns:
            API response data

        Raises:
            ValueError: If the method is unknown or authentication fails
            requests.exceptions.*: If HTTP request fails
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
        """Convenience method for GET requests (typically public endpoints).

        Args:
            method: API method/endpoint name
            params: Query parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    def post(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience method for POST requests (typically private endpoints).

        Args:
            method: API method/endpoint name
            params: POST parameters

        Returns:
            API response data
        """
        return self.request(method, params)

    def close(self):
        """Close the HTTP session and cleanup resources."""
        self.session.close()
        logger.info("Kraken REST client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class KrakenClientAsyncREST:
    """Asynchronous REST client for Kraken API

    This client provides an async interface to interact with Kraken's REST API,
    handling authentication, request signing, and error handling automatically.
    Perfect for concurrent API calls and integration with async frameworks.

    Attributes:
        api_key (str): API key for authentication
        api_secret (bytes): Decoded API secret for signing requests
        client (httpx.AsyncClient): Async HTTP client for connection pooling
        api_domain (str): Base URL for API requests

    Example:
        >>> async with KrakenClientAsyncREST(api_key="your_key", api_secret="your_secret") as client:
        >>>     balance = await client.request("Balance")
        >>>     ticker = await client.request("Ticker", params={"pair": "XBTUSD"})

        >>> # Concurrent requests
        >>> async with KrakenClientAsyncREST() as client:
        >>>     results = await asyncio.gather(
        >>>         client.request("Time"),
        >>>         client.request("Ticker", params={"pair": "XBTUSD"}),
        >>>         client.request("Ticker", params={"pair": "ETHUSD"})
        >>>     )
    """

    API_DOMAIN = "https://api.kraken.com"
    USER_AGENT = "Kraken REST API Client/1.0 (Async)"

    def __init__(
        self, api_key: Optional[str] = None, api_secret: Optional[str] = None, timeout: int = 30
    ):
        """Initialize the async Kraken REST client.

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
        self.client: Optional[httpx.AsyncClient] = None

        logger.info("Kraken async REST client initialized")

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

    async def _request(
        self, method: str, api_type: KrakenEndpoint, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Internal method to make async HTTP requests to Kraken API.

        Args:
            method: API method/endpoint name
            api_type: Type of API endpoint
            params: Request parameters

        Returns:
            Parsed JSON response from the API

        Raises:
            RuntimeError: If client is not initialized
            ValueError: If authentication is required but credentials missing, or JSON parsing fails
            httpx.*: If HTTP request fails
            KrakenAPIError: If the Kraken API returns an error response
        """
        if self.client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        if params is None:
            params = {}

        url_path = f"{api_type.path}{method}"
        url = f"{self.API_DOMAIN}{url_path}"

        headers = {}

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
                response = await self.client.post(
                    url, data=params, headers=headers, timeout=self.timeout
                )
            else:
                # Public endpoint - no authentication required
                logger.debug(f"Making public async request to {method}")
                response = await self.client.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )

            # Raise exception for HTTP errors
            response.raise_for_status()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout for {method}: {e}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Connection error for {method}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {method}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request failed for {method}: {e}")
            raise

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response: {e}") from e

        # Check for API errors
        if "error" in data and data["error"]:
            error_msg = ", ".join(data["error"])
            logger.error(f"API error for {method}: {error_msg}")
            raise KrakenAPIError(f"API error: {error_msg}")

        logger.info(f"Successfully completed async request to {method}")
        return data

    async def request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async request to the Kraken API.

        This is the main public method for interacting with the API.
        It automatically determines the endpoint type and handles authentication.

        Args:
            method: API method/endpoint name (e.g., "Time", "Balance", "AddOrder")
            params: Request parameters

        Returns:
            API response data

        Raises:
            ValueError: If the method is unknown or authentication fails
            httpx.*: If HTTP request fails
            KrakenAPIError: If the API returns an error response

        Example:
            >>> await client.request("Time")
            {'error': [], 'result': {'unixtime': 1234567890, 'rfc1123': '...'}}

            >>> await client.request("Ticker", params={"pair": "XBTUSD"})
            {'error': [], 'result': {...}}
        """
        api_type = self._get_api_type(method)
        return await self._request(method, api_type, params)

    async def get(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience method for GET requests (typically public endpoints).

        Args:
            method: API method/endpoint name
            params: Query parameters

        Returns:
            API response data
        """
        return await self.request(method, params)

    async def post(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convenience method for POST requests (typically private endpoints).

        Args:
            method: API method/endpoint name
            params: POST parameters

        Returns:
            API response data
        """
        return await self.request(method, params)

    async def close(self):
        """Close the HTTP client and cleanup resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
        logger.info("Kraken async REST client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(headers={"User-Agent": self.USER_AGENT})
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
