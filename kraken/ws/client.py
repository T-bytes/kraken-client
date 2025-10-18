import asyncio
import json
import logging
import threading
import time
from typing import Callable, Dict, Optional

from kraken.ws.connection import KrakenSocketAsyncConnection, KrakenSocketConnection

logger = logging.getLogger(__name__)


class KrakenClientAsyncWS:
    """Asynchronous WebSocket client for Kraken.

    This client provides an async interface to interact with Kraken's WebSocket API,
    handling subscriptions, authentication, and connection management automatically.

    Attributes:
        STREAM_URL: Public WebSocket API URL
        PRIVATE_STREAM_URL: Private (authenticated) WebSocket API URL
        VERSION: API version path
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
        """
        self.key = key
        self.secret = secret
        self.nonce_multiplier = nonce_multiplier

        self._connections: Dict[str, KrakenSocketAsyncConnection] = {}
        self._lock = asyncio.Lock()

    async def subscribe_public(
        self, params: dict, callback: Callable[[dict], None], **kwargs
    ) -> str:
        """Subscribe to a public WebSocket channel.

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription
        """
        return await self._subscribe(params, callback, False, **kwargs)

    async def subscribe_private(
        self, params: dict, callback: Callable[[dict], None], **kwargs
    ) -> str:
        """Subscribe to a private WebSocket channel.

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription
        """
        return await self._subscribe(params, callback, True, **kwargs)

    async def _subscribe(
        self, params: dict, callback: Callable[[dict], None], private: bool, **kwargs
    ) -> str:
        """Internal method to handle subscriptions.

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

        async with self._lock:
            # Check if connection already exists
            if conn_id in self._connections:
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

            self._connections[conn_id] = connection
            await connection.connect()

            logger.info(f"Subscribed to {conn_id}")
            return conn_id

    async def request(self, request: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Send a request to Kraken WebSocket API.

        Args:
            request: Request payload
            callback: Function to call when response is received
            **kwargs: Additional parameters (e.g., req_id)

        Returns:
            Connection ID for this request
        """
        import time

        conn_id = str(int(time.time() * 1000))

        if "req_id" in kwargs:
            request.update(**kwargs)

        async with self._lock:
            url = self.PRIVATE_STREAM_URL + self.VERSION

            connection = KrakenSocketAsyncConnection(
                url=url,
                payload=request,
                callback=callback,
            )

            self._connections[conn_id] = connection
            await connection.connect()

            return conn_id

    async def stop_socket(self, conn_id: str) -> bool:
        """Stop a specific WebSocket connection.

        Args:
            conn_id: Connection ID to stop

        Returns:
            True if connection was stopped, False if not found
        """
        async with self._lock:
            if conn_id not in self._connections:
                logger.warning(f"Connection {conn_id} not found")
                return False

            connection = self._connections[conn_id]
            await connection.disconnect()
            del self._connections[conn_id]

            logger.info(f"Stopped connection {conn_id}")
            return True

    async def close(self):
        """Close all WebSocket connections.

        Disconnects all active connections and cleans up resources.
        """
        async with self._lock:
            conn_ids = list(self._connections.keys())

        for conn_id in conn_ids:
            await self.stop_socket(conn_id)

        logger.info("All connections closed")

    async def stop(self):
        """Stop the client and close all connections.

        Alias for close() method.
        """
        await self.close()

    def get_connection_ids(self) -> list:
        """Get list of active connection IDs.

        Returns:
            List of active connection ID strings
        """
        return list(self._connections.keys())

    def is_connected(self, conn_id: str) -> bool:
        """Check if a specific connection is active.

        Args:
            conn_id: Connection ID to check

        Returns:
            True if connected, False otherwise
        """
        if conn_id not in self._connections:
            return False
        return self._connections[conn_id].is_connected


class KrakenClientWS:
    """Synchronous WebSocket client for Kraken.

    This client provides a synchronous interface to interact with Kraken's WebSocket API,
    handling subscriptions, authentication, and connection management automatically.

    Attributes:
        STREAM_URL: Public WebSocket API URL
        PRIVATE_STREAM_URL: Private (authenticated) WebSocket API URL
        VERSION: API version path
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
        """
        self.key = key
        self.secret = secret
        self.nonce_multiplier = nonce_multiplier

        self._connections: Dict[str, KrakenSocketConnection] = {}
        self._lock = threading.Lock()

    def subscribe_public(self, params: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Subscribe to a public WebSocket channel.

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription
        """
        return self._subscribe(params, callback, False, **kwargs)

    def subscribe_private(self, params: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Subscribe to a private WebSocket channel.

        Args:
            params: Subscription parameters (channel, symbol, etc.)
            callback: Function to call when messages are received
            **kwargs: Additional parameters to include in subscription message

        Returns:
            Connection ID for this subscription
        """
        return self._subscribe(params, callback, True, **kwargs)

    def _subscribe(
        self, params: dict, callback: Callable[[dict], None], private: bool, **kwargs
    ) -> str:
        """Internal method to handle subscriptions.

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

        with self._lock:
            # Check if connection already exists
            if conn_id in self._connections:
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

            self._connections[conn_id] = connection
            connection.connect()

            logger.info(f"Subscribed to {conn_id}")
            return conn_id

    def request(self, request: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Send a request to Kraken WebSocket API.

        Args:
            request: Request payload
            callback: Function to call when response is received
            **kwargs: Additional parameters (e.g., req_id)

        Returns:
            Connection ID for this request
        """
        conn_id = str(int(time.time() * 1000))

        if "req_id" in kwargs:
            request.update(**kwargs)

        with self._lock:
            url = self.PRIVATE_STREAM_URL + self.VERSION

            connection = KrakenSocketConnection(
                url=url,
                payload=request,
                callback=callback,
            )

            self._connections[conn_id] = connection
            connection.connect()

            return conn_id

    def stop_socket(self, conn_id: str) -> bool:
        """Stop a specific WebSocket connection.

        Args:
            conn_id: Connection ID to stop

        Returns:
            True if connection was stopped, False if not found
        """
        with self._lock:
            if conn_id not in self._connections:
                logger.warning(f"Connection {conn_id} not found")
                return False

            connection = self._connections[conn_id]
            connection.disconnect()
            del self._connections[conn_id]

            logger.info(f"Stopped connection {conn_id}")
            return True

    def close(self):
        """Close all WebSocket connections.

        Disconnects all active connections and cleans up resources.
        """
        with self._lock:
            conn_ids = list(self._connections.keys())

        for conn_id in conn_ids:
            self.stop_socket(conn_id)

        logger.info("All connections closed")

    def stop(self):
        """Stop the client and close all connections.

        Alias for close() method.
        """
        self.close()

    def get_connection_ids(self) -> list:
        """Get list of active connection IDs.

        Returns:
            List of active connection ID strings
        """
        return list(self._connections.keys())

    def is_connected(self, conn_id: str) -> bool:
        """Check if a specific connection is active.

        Args:
            conn_id: Connection ID to check

        Returns:
            True if connected, False otherwise
        """
        if conn_id not in self._connections:
            return False
        return self._connections[conn_id].is_connected
