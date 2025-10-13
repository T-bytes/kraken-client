import asyncio
import json
import logging
import threading
import time
from typing import Callable, Dict, Optional

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import WebSocketException
from websockets.sync.client import ClientConnection as SyncClientConnection
from websockets.sync.client import connect as sync_connect

logger = logging.getLogger(__name__)


class KrakenSocketAsyncConnection:
    """Manages a single asynchronous WebSocket connection with reconnection logic.

    This class handles automatic reconnection with exponential backoff when
    the connection is lost, and manages message handling through callbacks.
    """

    def __init__(
        self,
        url: str,
        payload: dict,
        callback: Callable[[dict], None],
        initial_delay: float = 0.1,
        max_delay: float = 20.0,
        max_retries: int = 30,
    ):
        """Initialize the WebSocket connection manager.

        Args:
            url: WebSocket URL to connect to
            payload: Initial payload to send upon connection
            callback: Function to call when messages are received
            initial_delay: Initial reconnection delay in seconds
            max_delay: Maximum reconnection delay in seconds
            max_retries: Maximum number of reconnection attempts
        """
        self.url = url
        self.payload = payload
        self.callback = callback
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        self._websocket: Optional[ClientConnection] = None
        self._task: Optional[asyncio.Task] = None
        self._reconnect_delay = initial_delay
        self._retries = 0
        self._should_run = False
        self._lock = asyncio.Lock()

    async def connect(self):
        """Establish WebSocket connection and start message handling.

        Creates an asyncio task that runs the connection loop in the background.
        """
        self._should_run = True
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        """Main connection loop with automatic reconnection.

        Continuously attempts to maintain a WebSocket connection, handling
        disconnections and reconnections automatically.
        """
        while self._should_run:
            try:
                async with connect(self.url) as websocket:
                    self._websocket = websocket
                    logger.info(f"Connected to {self.url}")

                    # Send initial payload on connection
                    if self.payload:
                        await websocket.send(json.dumps(self.payload))

                    # Reset reconnection parameters on successful connection
                    self._reconnect_delay = self.initial_delay
                    self._retries = 0

                    # Handle incoming messages
                    async for message in websocket:
                        try:
                            payload_obj = json.loads(message)
                            await self._handle_message(payload_obj)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to decode message: {e}")
                        except Exception as e:
                            logger.error(f"Error handling message: {e}")

            except (WebSocketException, ConnectionError, OSError) as e:
                self._websocket = None
                if self._should_run:
                    await self._handle_reconnection(e)
                else:
                    break
            except asyncio.CancelledError:
                logger.info("Connection task cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if self._should_run:
                    await self._handle_reconnection(e)
                else:
                    break

    async def _handle_message(self, payload_obj: dict):
        """Handle incoming message by calling the callback.

        Args:
            payload_obj: Parsed JSON message from the WebSocket
        """
        try:
            # Call callback in a non-blocking way
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(payload_obj)
            else:
                # Run synchronous callback in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.callback, payload_obj)
        except Exception as e:
            logger.error(f"Error in callback: {e}")

    async def _handle_reconnection(self, error: Exception):
        """Handle reconnection with exponential backoff.

        Args:
            error: The exception that caused the disconnection
        """
        self._retries += 1

        if self._retries > self.max_retries:
            error_msg = f"Max reconnection retries ({self.max_retries}) reached"
            logger.error(error_msg)
            error_payload = {"e": "error", "m": error_msg}
            await self._handle_message(error_payload)
            self._should_run = False
            return

        logger.warning(
            f"Connection lost ({error}). Reconnecting in {self._reconnect_delay}s "
            f"(attempt {self._retries}/{self.max_retries})"
        )

        await asyncio.sleep(self._reconnect_delay)

        # Exponential backoff
        self._reconnect_delay = min(self._reconnect_delay * 2, self.max_delay)

    async def disconnect(self):
        """Gracefully close the WebSocket connection.

        Stops the connection loop and closes the underlying WebSocket.
        """
        self._should_run = False

        if self._websocket and not self._websocket.closed:
            await self._websocket.close()

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected.

        Returns:
            True if the WebSocket is connected and not closed, False otherwise
        """
        return self._websocket is not None and not self._websocket.closed


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


class KrakenSocketConnection:
    """Manages a single synchronous WebSocket connection with reconnection logic.

    This class handles automatic reconnection with exponential backoff when
    the connection is lost, and manages message handling through callbacks.
    """

    def __init__(
        self,
        url: str,
        payload: dict,
        callback: Callable[[dict], None],
        initial_delay: float = 0.1,
        max_delay: float = 20.0,
        max_retries: int = 30,
    ):
        """Initialize the WebSocket connection manager.

        Args:
            url: WebSocket URL to connect to
            payload: Initial payload to send upon connection
            callback: Function to call when messages are received
            initial_delay: Initial reconnection delay in seconds
            max_delay: Maximum reconnection delay in seconds
            max_retries: Maximum number of reconnection attempts
        """
        self.url = url
        self.payload = payload
        self.callback = callback
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

        self._websocket: Optional[SyncClientConnection] = None
        self._thread: Optional[threading.Thread] = None
        self._reconnect_delay = initial_delay
        self._retries = 0
        self._should_run = False
        self._lock = threading.Lock()

    def connect(self):
        """Establish WebSocket connection and start message handling.

        Creates a daemon thread that runs the connection loop in the background.
        """
        self._should_run = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Main connection loop with automatic reconnection.

        Continuously attempts to maintain a WebSocket connection, handling
        disconnections and reconnections automatically.
        """
        while self._should_run:
            try:
                with sync_connect(self.url) as websocket:
                    self._websocket = websocket
                    logger.info(f"Connected to {self.url}")

                    # Send initial payload on connection
                    if self.payload:
                        websocket.send(json.dumps(self.payload))

                    # Reset reconnection parameters on successful connection
                    self._reconnect_delay = self.initial_delay
                    self._retries = 0

                    # Handle incoming messages
                    for message in websocket:
                        try:
                            payload_obj = json.loads(message)
                            self._handle_message(payload_obj)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to decode message: {e}")
                        except Exception as e:
                            logger.error(f"Error handling message: {e}")

            except (WebSocketException, ConnectionError, OSError) as e:
                self._websocket = None
                if self._should_run:
                    self._handle_reconnection(e)
                else:
                    break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if self._should_run:
                    self._handle_reconnection(e)
                else:
                    break

    def _handle_message(self, payload_obj: dict):
        """Handle incoming message by calling the callback.

        Args:
            payload_obj: Parsed JSON message from the WebSocket
        """
        try:
            self.callback(payload_obj)
        except Exception as e:
            logger.error(f"Error in callback: {e}")

    def _handle_reconnection(self, error: Exception):
        """Handle reconnection with exponential backoff.

        Args:
            error: The exception that caused the disconnection
        """
        self._retries += 1

        if self._retries > self.max_retries:
            error_msg = f"Max reconnection retries ({self.max_retries}) reached"
            logger.error(error_msg)
            error_payload = {"e": "error", "m": error_msg}
            self._handle_message(error_payload)
            self._should_run = False
            return

        logger.warning(
            f"Connection lost ({error}). Reconnecting in {self._reconnect_delay}s "
            f"(attempt {self._retries}/{self.max_retries})"
        )

        time.sleep(self._reconnect_delay)

        # Exponential backoff
        self._reconnect_delay = min(self._reconnect_delay * 2, self.max_delay)

    def disconnect(self):
        """Gracefully close the WebSocket connection.

        Stops the connection loop and closes the underlying WebSocket.
        """
        self._should_run = False

        if self._websocket and not self._websocket.closed:
            self._websocket.close()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected.

        Returns:
            True if the WebSocket is connected and not closed, False otherwise
        """
        return self._websocket is not None and not self._websocket.closed


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
