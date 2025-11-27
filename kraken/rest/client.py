"""Kraken REST API Client

This module provides a unified interface to the Kraken REST API supporting both
synchronous and asynchronous operations. Sync and async methods can be mixed
within the same client instance.

The client uses httpx for HTTP operations and provides authentication,
error handling, and logging.

Example (Synchronous):
    >>> from kraken.rest import KrakenRESTClient
    >>> client = KrakenRESTClient()
    >>> # Public endpoint (GET)
    >>> response = client.get("Time")
    >>> print(response)
    >>> # Private endpoint (POST)
    >>> balance = client.post("Balance")
    >>> print(balance)

Example (Asynchronous):
    >>> from kraken.rest import KrakenRESTClient
    >>> client = KrakenRESTClient()
    >>> # Public endpoint (GET)
    >>> response = await client.aget("Time")
    >>> print(response)
    >>> # Private endpoint (POST)
    >>> balance = await client.apost("Balance")
    >>> print(balance)

Example (Mixed sync/async):
    >>> client = KrakenRESTClient()
    >>> # Synchronous GET call
    >>> server_time = client.get("Time")
    >>> # Asynchronous GET call with parameters
    >>> ticker = await client.aget("Ticker", params={"pair": "XBTUSD"})
    >>> # Asynchronous POST call
    >>> balance = await client.apost("Balance")

Example (Context manager):
    >>> # Synchronous context
    >>> with KrakenRESTClient() as client:
    >>>     response = client.get("Time")
    >>>
    >>> # Asynchronous context
    >>> async with KrakenRESTClient() as client:
    >>>     response = await client.aget("Time")
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from typing import Any, Dict, Optional, TypeVar, overload

import httpx

from kraken.exceptions import (
    KrakenAPIError,
    KrakenConnectionError,
    KrakenHTTPError,
    KrakenPayloadError,
    KrakenTimeoutError,
)
from kraken.rest.channels import KrakenChannel
from kraken.rest.schema import *
from kraken.rest.schema import get_endpoint_info
from kraken.utilities import get_nonce

# Type variable for generic schema-based requests
TRequest = TypeVar("TRequest", bound=BaseRequestSchema)
TResponse = TypeVar("TResponse", bound=BaseResponseWrapper)

logger = logging.getLogger(__name__)


class KrakenRESTClient:
    """Unified REST client for Kraken API supporting both sync and async operations.

    This client provides an interface to interact with Kraken's REST API,
    supporting both synchronous and asynchronous methods within a single instance.
    The client handles authentication, request signing, and error handling.

    The client uses lazy initialization for underlying HTTP clients, creating them
    only when needed. For resource management, use the client as a context manager
    or explicitly call close()/aclose() when done.

    Attributes:
        api_key (str): API key for authentication
        api_secret (bytes): Decoded API secret for signing requests
        timeout (int): Request timeout in seconds
        _sync_client (httpx.Client): Synchronous HTTP client (lazy-initialized)
        _async_client (httpx.AsyncClient): Asynchronous HTTP client (lazy-initialized)

    Synchronous Methods:
        request(endpoint, **kwargs): Make a request (auto-detects GET/POST based on endpoint type)
        get(endpoint, **kwargs): Make a GET request
        post(endpoint, **kwargs): Make a POST request

    Asynchronous Methods:
        arequest(endpoint, **kwargs): Make an async request (auto-detects GET/POST)
        aget(endpoint, **kwargs): Make an async GET request
        apost(endpoint, **kwargs): Make an async POST request

    Example:
        >>> # Without context manager
        >>> client = KrakenRESTClient(api_key="your_key", api_secret="your_secret")
        >>> # Auto-detect endpoint type
        >>> balance = client.request("Balance")
        >>> # Convenience methods
        >>> server_time = client.get("Time")
        >>> ticker = await client.aget("Ticker", params={"pair": "XBTUSD"})
        >>> client.close()  # or await client.aclose()
        >>>
        >>> # With context manager (recommended)
        >>> with KrakenRESTClient() as client:
        >>>     balance = client.post("Balance")
        >>>
        >>> async with KrakenRESTClient() as client:
        >>>     balance = await client.apost("Balance")
    """

    API_DOMAIN = "https://api.kraken.com"
    USER_AGENT = "Kraken REST API Client/2.0"

    def __init__(
        self, api_key: str | None = None, api_secret: str | None = None, timeout: int = 30
    ):
        """Initialize the Kraken REST client.

        Args:
            api_key: API key for authentication. If not provided, reads from
                KRAKEN_API_KEY environment variable.
            api_secret: API secret for authentication. If not provided, reads from
                KRAKEN_API_SECRET environment variable.
            timeout: Request timeout in seconds. Default is 30.

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

    def __enter__(self):
        """Synchronous context manager entry."""
        self._get_sync_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit."""
        self.close()
        return False

    async def __aenter__(self):
        """Asynchronous context manager entry."""
        self._get_async_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit."""
        await self.aclose()

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

    def _get_api_type(self, method: str) -> KrakenChannel:
        """Determine the API type for a given method.

        Args:
            method: API method/endpoint name

        Returns:
            The type of API endpoint

        Raises:
            ValueError: If method is not found in any API type
        """
        for api_type in KrakenChannel:
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
        postdata = "&".join([f"{key}={value}" for key, value in data.items()])
        encoded = (nonce + postdata).encode("utf-8")
        message = url_path.encode("utf-8") + hashlib.sha256(encoded).digest()
        signature = hmac.new(self.api_secret, message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def _prepare_order_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare order data by adding deadline at request time if needed.

        This method handles time-sensitive fields that must be computed at
        request signing time rather than order instantiation time to prevent
        stale timestamps in async/queued scenarios.

        Args:
            endpoint: The API endpoint name
            data: Request data dictionary

        Returns:
            Modified data dictionary with deadline added if applicable
        """
        try:
            match endpoint:
                case "AddOrder":
                    data["deadline"] = AddOrderRequest.compute_deadline()
                    logger.debug(f"Generated deadline at request time: {data['deadline']}")
                case _:
                    raise NotImplementedError(f"Endpoint '{endpoint}' is not supported")
        except NotImplementedError as e:
            logger.warning(str(e))
        except Exception as e:
            logger.error(f"Unable to prepare order: {str(e)}")
        return data

    # Overloaded signatures for type safety
    @overload
    def request(self, schema: TRequest, headers: Optional[Dict[str, str]] = None) -> TResponse:
        """Make a schema-based request (returns typed response)."""
        ...

    @overload
    def request(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a string-based request (returns dict)."""
        ...

    def request(
        self, endpoint_or_schema: str | TRequest, headers: Dict[str, str] | None = None, **kwargs
    ) -> Dict[str, Any] | TResponse:
        """Make a synchronous request to the Kraken API.

        This method supports two calling patterns:
        1. Schema-based (recommended): Pass a BaseRequestSchema instance for type-safe requests
        2. String-based (legacy): Pass an endpoint name string with kwargs

        Args:
            endpoint_or_schema: Either a BaseRequestSchema instance or endpoint name string
            headers: Optional headers dict (for schema-based calls)
            **kwargs: Additional request parameters (for string-based calls):
                - params: Query parameters for GET requests
                - data: Body parameters for POST requests
                - headers: Additional headers

        Returns:
            For schema-based calls: Typed BaseResponseWrapper subclass
            For string-based calls: Dict with API response data

        Raises:
            ValueError: If the endpoint is unknown or authentication fails
            KrakenTimeoutError: If request times out
            KrakenConnectionError: If connection to API fails
            KrakenHTTPError: If HTTP error occurs (4xx, 5xx)
            KrakenPayloadError: If JSON parsing fails
            KrakenAPIError: If the API returns an error response

        Example (schema-based):
            >>> from kraken.rest.schema.market import GetAssetInfoRequest
            >>> request = GetAssetInfoRequest(asset=["XBT", "ETH"])
            >>> response = client.request(request)
            >>> if response.is_success:
            >>>     print(response.success.assets)

        Example (string-based):
            >>> client.request("Time")
            {'error': [], 'result': {'unixtime': 1234567890, 'rfc1123': '...'}}
        """
        # Create request
        if isinstance(endpoint_or_schema, BaseRequestSchema):
            schema = endpoint_or_schema
            endpoint, response_class = get_endpoint_info(schema)
            data = schema.to_api_dict()
            raw_response = {}
            try:
                raw_response = self.request(endpoint, data=data, headers=headers or {})
            except Exception as e:
                raw_response["error"] = [str(e)]
            return response_class.from_response(raw_response)
        else:
            endpoint = endpoint_or_schema
            api_type = self._get_api_type(endpoint)
            url_path = f"{api_type.path}{endpoint}"
            url = f"{self.API_DOMAIN}{url_path}"
            if headers is None:
                headers = kwargs.pop("headers", {})
            client = self._get_sync_client()
            try:
                if api_type.is_private():  # Private endpoint - requires auth and always uses POST
                    if not self.api_key or not self.api_secret:
                        raise ValueError(
                            "API key and secret required for private endpoints. Set `KRAKEN_API_KEY` and `KRAKEN_API_SECRET` environment variables."
                        )
                    data = kwargs.pop("data", kwargs.pop("params", {}))
                    data = self._prepare_order_data(endpoint, data)
                    nonce = str(get_nonce())
                    data["nonce"] = nonce
                    signature = self._sign_request(url_path, data, nonce)
                    headers["API-Key"] = self.api_key
                    headers["API-Sign"] = signature
                    logger.debug(f"Making authenticated POST request to {endpoint}")
                    response = client.post(url, data=data, headers=headers, **kwargs)
                else:  # Public endpoint - always uses GET
                    logger.debug(f"Making public GET request to {endpoint}")
                    response = client.get(url, headers=headers, **kwargs)
                response.raise_for_status()
            except httpx.TimeoutException as e:
                logger.error(f"Request timeout for {endpoint}: {e}")
                raise KrakenTimeoutError(f"Request timeout for {endpoint}: {e}") from e
            except httpx.ConnectError as e:
                logger.error(f"Connection error for {endpoint}: {e}")
                raise KrakenConnectionError(f"Connection error for {endpoint}: {e}") from e
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for {endpoint}: {e}")
                raise KrakenHTTPError(f"HTTP error for {endpoint}: {e}") from e
            except httpx.RequestError as e:
                logger.error(f"Request failed for {endpoint}: {e}")
                raise

            # Parse response
            try:
                response_json = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise KrakenPayloadError(f"Invalid JSON response: {e}", "", 0) from e
            if "error" in response_json and response_json["error"]:
                error_msg = ", ".join(response_json["error"])
                logger.error(f"API error for {endpoint}: {error_msg}")
                raise KrakenAPIError(f"API error: {error_msg}")

            logger.info(f"Successfully completed request to {endpoint}")
            return response_json

    # Overloaded signatures for async methods
    @overload
    async def arequest(
        self, schema: TRequest, headers: Optional[Dict[str, str]] = None
    ) -> TResponse:
        """Make an async schema-based request (returns typed response)."""
        ...

    @overload
    async def arequest(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an async string-based request (returns dict)."""
        ...

    async def arequest(
        self, endpoint_or_schema, headers=None, **kwargs
    ) -> Dict[str, Any] | TResponse:
        """Make an asynchronous request to the Kraken API.

        This method supports two calling patterns:
        1. Schema-based (recommended): Pass a BaseRequestSchema instance for type-safe requests
        2. String-based (legacy): Pass an endpoint name string with kwargs

        Args:
            endpoint_or_schema: Either a BaseRequestSchema instance or endpoint name string
            headers: Optional headers dict (for schema-based calls)
            **kwargs: Additional request parameters (for string-based calls):
                - params: Query parameters for GET requests
                - data: Body parameters for POST requests
                - headers: Additional headers

        Returns:
            For schema-based calls: Typed BaseResponseWrapper subclass
            For string-based calls: Dict with API response data

        Raises:
            ValueError: If the endpoint is unknown or authentication fails
            KrakenTimeoutError: If request times out
            KrakenConnectionError: If connection to API fails
            KrakenHTTPError: If HTTP error occurs (4xx, 5xx)
            KrakenPayloadError: If JSON parsing fails
            KrakenAPIError: If the API returns an error response

        Example (schema-based):
            >>> from kraken.rest.schema.market import GetServerTimeRequest
            >>> request = GetServerTimeRequest()
            >>> response = await client.arequest(request)
            >>> if response.is_success:
            >>>     print(response.success.unixtime)

        Example (string-based):
            >>> await client.arequest("Time")
            {'error': [], 'result': {'unixtime': 1234567890, 'rfc1123': '...'}}
        """
        # Detect if this is a schema-based or string-based request
        if isinstance(endpoint_or_schema, BaseRequestSchema):
            # Schema-based request
            schema = endpoint_or_schema
            endpoint, response_class = get_endpoint_info(schema)

            # Serialize schema to dict
            data = schema.to_api_dict()

            # Make the request using the string-based logic, but catch API errors
            # to wrap them in the response object instead of raising
            raw_response = {}
            try:
                raw_response = await self.arequest(endpoint, data=data, headers=headers or {})
            except Exception as e:
                raw_response["error"] = [str(e)]

            # Parse and return typed response
            return response_class.from_response(raw_response)
        else:
            # String-based request (legacy path)
            endpoint = endpoint_or_schema
            api_type = self._get_api_type(endpoint)
            url_path = f"{api_type.path}{endpoint}"
            url = f"{self.API_DOMAIN}{url_path}"
            if headers is None:
                headers = kwargs.pop("headers", {})
            client = self._get_async_client()

            # Send request
            try:
                if api_type.is_private():  # Private endpoint - requires auth and always uses POST
                    if not self.api_key or not self.api_secret:
                        raise ValueError(
                            "API key and secret required for private endpoints. Set `KRAKEN_API_KEY` and `KRAKEN_API_SECRET` environment variables."
                        )
                    data = kwargs.pop("data", kwargs.pop("params", {}))
                    data = self._prepare_order_data(endpoint, data)
                    nonce = str(get_nonce())
                    data["nonce"] = nonce
                    signature = self._sign_request(url_path, data, nonce)
                    headers["API-Key"] = self.api_key
                    headers["API-Sign"] = signature
                    logger.debug(f"Making authenticated async POST request to {endpoint}")
                    response = await client.post(url, data=data, headers=headers, **kwargs)
                else:  # Public endpoint - always uses GET
                    logger.debug(f"Making public async GET request to {endpoint}")
                    response = await client.get(url, headers=headers, **kwargs)
                response.raise_for_status()
            except httpx.TimeoutException as e:
                logger.error(f"Request timeout for {endpoint}: {e}")
                raise KrakenTimeoutError(f"Request timeout for {endpoint}: {e}") from e
            except httpx.ConnectError as e:
                logger.error(f"Connection error for {endpoint}: {e}")
                raise KrakenConnectionError(f"Connection error for {endpoint}: {e}") from e
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for {endpoint}: {e}")
                raise KrakenHTTPError(f"HTTP error for {endpoint}: {e}") from e
            except httpx.RequestError as e:
                logger.error(f"Request failed for {endpoint}: {e}")
                raise

            # Parse response
            try:
                response_json = response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise KrakenPayloadError(f"Invalid JSON response: {e}", "", 0) from e
            if "error" in response_json and response_json["error"]:
                error_msg = ", ".join(response_json["error"])
                logger.error(f"API error for {endpoint}: {error_msg}")
                raise KrakenAPIError(f"API error: {error_msg}")

            logger.info(f"Successfully completed async request to {endpoint}")
            return response_json
