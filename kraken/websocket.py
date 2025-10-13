import asyncio
import json
import logging
from typing import Callable, Dict, Optional

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


class KrakenSocketConnection:
    """Manages a single WebSocket connection with reconnection logic"""

    def __init__(
        self,
        url: str,
        payload: dict,
        callback: Callable[[dict], None],
        initial_delay: float = 0.1,
        max_delay: float = 20.0,
        max_retries: int = 30,
    ):
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
        """Establish WebSocket connection and start message handling"""
        self._should_run = True
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        """Main connection loop with automatic reconnection"""
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
        """Handle incoming message by calling the callback"""
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
        """Handle reconnection with exponential backoff"""
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
        """Gracefully close the WebSocket connection"""
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
        """Check if WebSocket is currently connected"""
        return self._websocket is not None and not self._websocket.closed


class KrakenClientWS:
    """Asynchronous WebSocket client for Kraken"""

    STREAM_URL = "wss://ws.kraken.com"
    PRIVATE_STREAM_URL = "wss://ws-auth.kraken.com"
    VERSION = "/v2"

    def __init__(
        self,
        key: Optional[str] = None,
        secret: Optional[str] = None,
        nonce_multiplier: float = 1.0,
    ):
        """Initialize the WssClient

        Parameters
        ----------
        key : str, optional
            API key for authenticated endpoints
        secret : str, optional
            API secret for authenticated endpoints
        nonce_multiplier : float, optional
            Multiplier for nonce generation
        """
        self.key = key
        self.secret = secret
        self.nonce_multiplier = nonce_multiplier

        self._connections: Dict[str, KrakenSocketConnection] = {}
        self._lock = asyncio.Lock()

    async def subscribe_public(
        self, params: dict, callback: Callable[[dict], None], **kwargs
    ) -> str:
        """Subscribe to a public WebSocket channel

        Parameters
        ----------
        params : dict
            Subscription parameters (channel, symbol, etc.)
        callback : callable
            Function to call when messages are received
        **kwargs
            Additional parameters to include in subscription message

        Returns
        -------
        str
            Connection ID for this subscription
        """
        return await self._subscribe(params, callback, False, **kwargs)

    async def subscribe_private(
        self, params: dict, callback: Callable[[dict], None], **kwargs
    ) -> str:
        """Subscribe to a private WebSocket channel

        Parameters
        ----------
        params : dict
            Subscription parameters (channel, symbol, etc.)
        callback : callable
            Function to call when messages are received
        **kwargs
            Additional parameters to include in subscription message

        Returns
        -------
        str
            Connection ID for this subscription
        """
        return await self._subscribe(params, callback, True, **kwargs)

    async def _subscribe(
        self, params: dict, callback: Callable[[dict], None], private: bool, **kwargs
    ) -> str:
        """Internal method to handle subscriptions

        Parameters
        ----------
        params : dict
            Subscription parameters
        callback : callable
            Message handler callback
        private : bool
            Whether this is a private (authenticated) connection
        **kwargs
            Additional subscription parameters

        Returns
        -------
        str
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
            connection = KrakenSocketConnection(
                url=url,
                payload=data,
                callback=callback,
            )

            self._connections[conn_id] = connection
            await connection.connect()

            logger.info(f"Subscribed to {conn_id}")
            return conn_id

    async def request(self, request: dict, callback: Callable[[dict], None], **kwargs) -> str:
        """Send a request to Kraken WebSocket API

        Parameters
        ----------
        request : dict
            Request payload
        callback : callable
            Function to call when response is received
        **kwargs
            Additional parameters (e.g., req_id)

        Returns
        -------
        str
            Connection ID for this request
        """
        import time

        conn_id = str(int(time.time() * 1000))

        if "req_id" in kwargs:
            request.update(**kwargs)

        async with self._lock:
            url = self.PRIVATE_STREAM_URL + self.VERSION

            connection = KrakenSocketConnection(
                url=url,
                payload=request,
                callback=callback,
            )

            self._connections[conn_id] = connection
            await connection.connect()

            return conn_id

    async def stop_socket(self, conn_id: str) -> bool:
        """Stop a specific WebSocket connection

        Parameters
        ----------
        conn_id : str
            Connection ID to stop

        Returns
        -------
        bool
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
        """Close all WebSocket connections"""
        async with self._lock:
            conn_ids = list(self._connections.keys())

        for conn_id in conn_ids:
            await self.stop_socket(conn_id)

        logger.info("All connections closed")

    async def stop(self):
        """Stop the client and close all connections"""
        await self.close()

    def get_connection_ids(self) -> list:
        """Get list of active connection IDs

        Returns
        -------
        list
            List of active connection ID strings
        """
        return list(self._connections.keys())

    def is_connected(self, conn_id: str) -> bool:
        """Check if a specific connection is active

        Parameters
        ----------
        conn_id : str
            Connection ID to check

        Returns
        -------
        bool
            True if connected, False otherwise
        """
        if conn_id not in self._connections:
            return False
        return self._connections[conn_id].is_connected
