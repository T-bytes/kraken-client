"""Kraken WebSocket API Client

This module provides a unified interface to the Kraken WebSocket API supporting both
synchronous and asynchronous operations. Sync and async methods can be mixed
within the same client instance.

The client manages WebSocket connections for subscriptions and requests, providing
connection management, reconnection logic, and error handling.

Example (Synchronous):
    >>> from kraken.ws import KrakenWSClient
    >>> client = KrakenWSClient()
    >>> conn_id = client.subscribe_public(
    ...     params={"channel": "ticker", "symbol": ["BTC/USD"]},
    ...     callback=lambda msg: print(msg)
    ... )
    >>> client.close()

Example (Asynchronous):
    >>> from kraken.ws import KrakenWSClient
    >>> import asyncio
    >>>
    >>> async def handle_message(msg):
    ...     print(msg)
    >>>
    >>> client = KrakenWSClient()
    >>> conn_id = await client.asubscribe_public(
    ...     params={"channel": "ticker", "symbol": ["BTC/USD"]},
    ...     callback=handle_message
    ... )
    >>> await client.aclose()

Example (Mixed sync/async):
    >>> client = KrakenWSClient()
    >>> # Synchronous subscription
    >>> sync_conn = client.subscribe_public(params={"channel": "heartbeat"}, callback=sync_handler)
    >>> # Asynchronous subscription
    >>> async_conn = await client.asubscribe_public(
    ...     params={"channel": "ticker", "symbol": ["ETH/USD"]},
    ...     callback=async_handler
    ... )
    >>> # Clean up both
    >>> client.close()
    >>> await client.aclose()

Example (Context managers):
    >>> # Synchronous context
    >>> with KrakenWSClient() as client:
    ...     conn_id = client.subscribe_public(params, callback)
    >>>
    >>> # Asynchronous context
    >>> async with KrakenWSClient() as client:
    ...     conn_id = await client.asubscribe_public(params, callback)
"""

import asyncio
import logging
import threading
import time
from typing import Callable, Dict, Optional

from kraken.ws.connection import KrakenSocketAsyncConnection, KrakenSocketConnection

logger = logging.getLogger(__name__)


class KrakenWSClient:
    """Unified WebSocket client for Kraken API supporting both sync and async operations.

    This client provides an interface to interact with Kraken's WebSocket API,
    supporting both synchronous and asynchronous methods within a single instance.
    The client maintains separate connection pools for sync and async operations
    to handle different concurrency paradigms.

    The client uses lazy initialization for async locks and maintains isolation
    between sync and async connection pools.

    Attributes:
        STREAM_URL: Public WebSocket API URL
        PRIVATE_STREAM_URL: Private (authenticated) WebSocket API URL
        VERSION: API version path

    Synchronous Methods:
        subscribe_public(params, callback, **kwargs): Subscribe to public channel
        subscribe_private(params, callback, **kwargs): Subscribe to private channel
        request(request, callback, **kwargs): Send WebSocket request
        stop_socket(conn_id): Stop specific connection
        close(): Close all synchronous connections
        stop(): Alias for close()

    Asynchronous Methods:
        asubscribe_public(params, callback, **kwargs): Async subscribe to public channel
        asubscribe_private(params, callback, **kwargs): Async subscribe to private channel
        arequest(request, callback, **kwargs): Async send WebSocket request
        astop_socket(conn_id): Async stop specific connection
        aclose(): Close all asynchronous connections
        astop(): Alias for aclose()

    Shared Methods:
        get_connection_ids(): Get list of all active connection IDs
        is_connected(conn_id): Check if specific connection is active

    Example:
        >>> # Without context manager
        >>> client = KrakenWSClient(key="your_key", secret="your_secret")
        >>> conn_id = client.subscribe_public(params, callback)
        >>> async_conn = await client.asubscribe_private(params, async_callback)
        >>> client.close()
        >>> await client.aclose()
        >>>
        >>> # With context manager (recommended)
        >>> with KrakenWSClient() as client:
        ...     conn_id = client.subscribe_public(params, callback)
        >>>
        >>> async with KrakenWSClient() as client:
        ...     conn_id = await client.asubscribe_public(params, callback)
    """

    STREAM_URL = "wss://ws.kraken.com"
    PRIVATE_STREAM_URL = "wss://ws-auth.kraken.com"
    VERSION = "/v2"

    def __init__(
        self,
        key: Optional[str] = None,
        secret: Optional[str] = None,
        nonce_multiplier: float = 1.0,
    ):
        """Initialize the WebSocket client.

        Args:
            key: API key for authenticated endpoints
            secret: API secret for authenticated endpoints
            nonce_multiplier: Multiplier for nonce generation

        Example:
            >>> client = KrakenWSClient()  # Public endpoints only
            >>> client_auth = KrakenWSClient(key="api_key", secret="api_secret")
        """
        self.key = key
        self.secret = secret
        self.nonce_multiplier = nonce_multiplier

        self._sync_connections: Dict[str, KrakenSocketConnection] = {}
        self._async_connections: Dict[str, KrakenSocketAsyncConnection] = {}
        self._sync_lock = threading.Lock()
        self._async_lock: Optional[asyncio.Lock] = None

        logger.info("Kraken WebSocket client initialized")

    def _get_async_lock(self) -> asyncio.Lock:
        """Get or create the asynchronous lock.

        The async lock is lazy-initialized because asyncio.Lock requires
        an event loop, which may not exist at __init__ time.

        Returns:
            Initialized asyncio.Lock instance
        """
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
            logger.debug("Asynchronous lock initialized")
        return self._async_lock

    # Synchronous public methods

    def subscribe_public(self, params: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Subscribe to a public WebSocket channel (synchronous).

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription

        Example:
            >>> def handle_ticker(msg):
            ...     print(f"Ticker: {msg}")
            >>>
            >>> client = KrakenWSClient()
            >>> conn_id = client.subscribe_public(
            ...     params={"channel": "ticker", "symbol": ["BTC/USD"]},
            ...     callback=handle_ticker
            ... )
            >>> print(f"Subscribed with ID: {conn_id}")
        """
        return self._subscribe(params, callback, False, **kwargs)

    def subscribe_private(self, params: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Subscribe to a private WebSocket channel (synchronous).

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription

        Example:
            >>> def handle_orders(msg):
            ...     print(f"Order update: {msg}")
            >>>
            >>> client = KrakenWSClient(key="api_key", secret="api_secret")
            >>> conn_id = client.subscribe_private(
            ...     params={"channel": "executions"},
            ...     callback=handle_orders
            ... )
        """
        return self._subscribe(params, callback, True, **kwargs)

    def _subscribe(
        self, params: dict, callback: Callable[[dict], None], private: bool, **kwargs
    ) -> str:
        """Internal method to handle synchronous subscriptions.

        Args:
            params: Subscription parameters
            callback: Message handler callback
            private: Whether this is a private (authenticated) connection
            **kwargs: Additional subscription parameters

        Returns:
            Connection ID
        """
        # Generate connection ID based on channel and symbol
        if "symbol" in params:
            conn_id = "_".join([params["channel"], params["symbol"][0]])
        else:
            conn_id = "_".join([params["channel"]])

        with self._sync_lock:
            # Check if connection already exists
            if conn_id in self._sync_connections:
                logger.warning(f"Connection {conn_id} already exists")
                return conn_id

            # Build subscription message
            data = {
                "method": "subscribe",
                "params": params,
            }
            data.update(**kwargs)

            # Select appropriate URL
            url = (self.PRIVATE_STREAM_URL if private else self.STREAM_URL) + self.VERSION

            # Create and start connection
            connection = KrakenSocketConnection(
                url=url,
                payload=data,
                callback=callback,
            )

            self._sync_connections[conn_id] = connection
            connection.connect()

            logger.info(f"Subscribed to {conn_id}")
            return conn_id

    def request(self, request: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Send a synchronous request to Kraken WebSocket API.

        Args:
            request: Request payload
            callback: Function to call when response is received
            **kwargs: Additional parameters (e.g., req_id)

        Returns:
            Connection ID for this request

        Example:
            >>> def handle_response(msg):
            ...     print(f"Response: {msg}")
            >>>
            >>> client = KrakenWSClient(key="api_key", secret="api_secret")
            >>> conn_id = client.request(
            ...     request={"method": "ping"},
            ...     callback=handle_response
            ... )
        """
        conn_id = str(int(time.time() * 1000))

        if "req_id" in kwargs:
            request.update(**kwargs)

        with self._sync_lock:
            url = self.PRIVATE_STREAM_URL + self.VERSION

            connection = KrakenSocketConnection(
                url=url,
                payload=request,
                callback=callback,
            )

            self._sync_connections[conn_id] = connection
            connection.connect()

            return conn_id

    def stop_socket(self, conn_id: str) -> bool:
        """Stop a specific synchronous WebSocket connection.

        Args:
            conn_id: Connection ID to stop

        Returns:
            True if connection was stopped, False if not found

        Example:
            >>> client = KrakenWSClient()
            >>> conn_id = client.subscribe_public(params, callback)
            >>> # ... later ...
            >>> if client.stop_socket(conn_id):
            ...     print("Connection stopped")
        """
        with self._sync_lock:
            if conn_id not in self._sync_connections:
                logger.warning(f"Connection {conn_id} not found")
                return False

            connection = self._sync_connections[conn_id]
            connection.disconnect()
            del self._sync_connections[conn_id]

            logger.info(f"Stopped connection {conn_id}")
            return True

    def close(self):
        """Close all synchronous WebSocket connections.

        Disconnects all active synchronous connections and cleans up resources.

        Example:
            >>> client = KrakenWSClient()
            >>> # ... create connections ...
            >>> client.close()
        """
        with self._sync_lock:
            conn_ids = list(self._sync_connections.keys())

        for conn_id in conn_ids:
            self.stop_socket(conn_id)

        logger.info("All synchronous connections closed")

    def stop(self):
        """Stop the client and close all synchronous connections.

        Alias for close() method.
        """
        self.close()

    # Asynchronous public methods

    async def asubscribe_public(
        self, params: dict, callback: Callable[[dict], None], **kwargs
    ) -> str:
        """Subscribe to a public WebSocket channel (asynchronous).

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription

        Example:
            >>> async def handle_ticker(msg):
            ...     print(f"Ticker: {msg}")
            >>>
            >>> client = KrakenWSClient()
            >>> conn_id = await client.asubscribe_public(
            ...     params={"channel": "ticker", "symbol": ["BTC/USD"]},
            ...     callback=handle_ticker
            ... )
            >>> print(f"Subscribed with ID: {conn_id}")
        """
        return await self._asubscribe(params, callback, False, **kwargs)

    async def asubscribe_private(
        self, params: dict, callback: Callable[[dict], None], **kwargs
    ) -> str:
        """Subscribe to a private WebSocket channel (asynchronous).

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription

        Example:
            >>> async def handle_orders(msg):
            ...     print(f"Order update: {msg}")
            >>>
            >>> client = KrakenWSClient(key="api_key", secret="api_secret")
            >>> conn_id = await client.asubscribe_private(
            ...     params={"channel": "executions"},
            ...     callback=handle_orders
            ... )
        """
        return await self._asubscribe(params, callback, True, **kwargs)

    async def _asubscribe(
        self, params: dict, callback: Callable[[dict], None], private: bool, **kwargs
    ) -> str:
        """Internal method to handle asynchronous subscriptions.

        Args:
            params: Subscription parameters
            callback: Message handler callback
            private: Whether this is a private (authenticated) connection
            **kwargs: Additional subscription parameters

        Returns:
            Connection ID
        """
        # Generate connection ID based on channel and symbol
        if "symbol" in params:
            conn_id = "_".join([params["channel"], params["symbol"][0]])
        else:
            conn_id = "_".join([params["channel"]])

        async with self._get_async_lock():
            # Check if connection already exists
            if conn_id in self._async_connections:
                logger.warning(f"Connection {conn_id} already exists")
                return conn_id

            # Build subscription message
            data = {
                "method": "subscribe",
                "params": params,
            }
            data.update(**kwargs)

            # Select appropriate URL
            url = (self.PRIVATE_STREAM_URL if private else self.STREAM_URL) + self.VERSION

            # Create and start connection
            connection = KrakenSocketAsyncConnection(
                url=url,
                payload=data,
                callback=callback,
            )

            self._async_connections[conn_id] = connection
            await connection.connect()

            logger.info(f"Subscribed to {conn_id}")
            return conn_id

    async def arequest(self, request: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Send an asynchronous request to Kraken WebSocket API.

        Args:
            request: Request payload
            callback: Function to call when response is received
            **kwargs: Additional parameters (e.g., req_id)

        Returns:
            Connection ID for this request

        Example:
            >>> async def handle_response(msg):
            ...     print(f"Response: {msg}")
            >>>
            >>> client = KrakenWSClient(key="api_key", secret="api_secret")
            >>> conn_id = await client.arequest(
            ...     request={"method": "ping"},
            ...     callback=handle_response
            ... )
        """
        import time

        conn_id = str(int(time.time() * 1000))

        if "req_id" in kwargs:
            request.update(**kwargs)

        async with self._get_async_lock():
            url = self.PRIVATE_STREAM_URL + self.VERSION

            connection = KrakenSocketAsyncConnection(
                url=url,
                payload=request,
                callback=callback,
            )

            self._async_connections[conn_id] = connection
            await connection.connect()

            return conn_id

    async def astop_socket(self, conn_id: str) -> bool:
        """Stop a specific asynchronous WebSocket connection.

        Args:
            conn_id: Connection ID to stop

        Returns:
            True if connection was stopped, False if not found

        Example:
            >>> client = KrakenWSClient()
            >>> conn_id = await client.asubscribe_public(params, callback)
            >>> # ... later ...
            >>> if await client.astop_socket(conn_id):
            ...     print("Connection stopped")
        """
        async with self._get_async_lock():
            if conn_id not in self._async_connections:
                logger.warning(f"Connection {conn_id} not found")
                return False

            connection = self._async_connections[conn_id]
            await connection.disconnect()
            del self._async_connections[conn_id]

            logger.info(f"Stopped connection {conn_id}")
            return True

    async def aclose(self):
        """Close all asynchronous WebSocket connections.

        Disconnects all active asynchronous connections and cleans up resources.

        Example:
            >>> client = KrakenWSClient()
            >>> # ... create async connections ...
            >>> await client.aclose()
        """
        async with self._get_async_lock():
            conn_ids = list(self._async_connections.keys())

        for conn_id in conn_ids:
            await self.astop_socket(conn_id)

        logger.info("All asynchronous connections closed")

    async def astop(self):
        """Stop the client and close all asynchronous connections.

        Alias for aclose() method.
        """
        await self.aclose()

    # Shared methods

    def get_connection_ids(self) -> list:
        """Get list of all active connection IDs (both sync and async).

        Returns:
            List of active connection ID strings

        Example:
            >>> client = KrakenWSClient()
            >>> sync_id = client.subscribe_public(params, callback)
            >>> async_id = await client.asubscribe_public(params, async_callback)
            >>> ids = client.get_connection_ids()
            >>> print(f"Active connections: {ids}")
        """
        sync_ids = list(self._sync_connections.keys())
        async_ids = list(self._async_connections.keys())
        return sync_ids + async_ids

    def is_connected(self, conn_id: str) -> bool:
        """Check if a specific connection is active.

        Checks both synchronous and asynchronous connection pools.

        Args:
            conn_id: Connection ID to check

        Returns:
            True if connected, False otherwise

        Example:
            >>> client = KrakenWSClient()
            >>> conn_id = client.subscribe_public(params, callback)
            >>> if client.is_connected(conn_id):
            ...     print("Connected!")
        """
        if conn_id in self._sync_connections:
            return self._sync_connections[conn_id].is_connected
        if conn_id in self._async_connections:
            return self._async_connections[conn_id].is_connected
        return False

    # Context manager support - Synchronous

    def __enter__(self):
        """Synchronous context manager entry.

        Example:
            >>> with KrakenWSClient() as client:
            ...     conn_id = client.subscribe_public(params, callback)
            ...     # connections automatically closed on exit
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit."""
        self.close()
        return False

    # Context manager support - Asynchronous

    async def __aenter__(self):
        """Asynchronous context manager entry.

        Example:
            >>> async with KrakenWSClient() as client:
            ...     conn_id = await client.asubscribe_public(params, callback)
            ...     # connections automatically closed on exit
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit."""
        await self.aclose()
        return False
