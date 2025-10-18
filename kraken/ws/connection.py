import asyncio
import json
import threading
from asyncio.log import logger
from typing import Callable, Optional

import backoff
from websockets import ClientConnection, WebSocketException, connect
from websockets.sync.client import ClientConnection as SyncClientConnection
from websockets.sync.client import connect as sync_connect

from kraken.constants import RETRY_TIME_LIMIT


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
    ):
        """Initialize the WebSocket connection manager.

        Args:
            url: WebSocket URL to connect to
            payload: Initial payload to send upon connection
            callback: Function to call when messages are received
        """
        self.url = url
        self.payload = payload
        self.callback = callback

        self._websocket: Optional[SyncClientConnection] = None
        self._thread: Optional[threading.Thread] = None
        self._should_run = False
        self._lock = threading.Lock()

    def connect(self):
        """Establish WebSocket connection and start message handling.

        Creates a daemon thread that runs the connection loop in the background.
        """
        self._should_run = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _log_backoff(self, details):
        """Callback for backoff events to log reconnection attempts.

        Args:
            details: Dictionary containing backoff information (wait, tries, etc.)
        """
        logger.warning(
            f"Connection lost. Reconnecting in {details['wait']:.1f}s (attempt {details['tries']})"
        )

    def _log_giveup(self, details):
        """Callback when backoff gives up after max time.

        Args:
            details: Dictionary containing backoff information
        """
        error_msg = f"Max reconnection time ({RETRY_TIME_LIMIT}s) reached"
        logger.error(error_msg)

    def _run(self):
        """Main connection loop with automatic reconnection.

        Continuously attempts to maintain a WebSocket connection, handling
        disconnections and reconnections automatically via backoff decorator.
        """
        # Create decorated connection function with instance callbacks
        connect_with_backoff = backoff.on_exception(
            backoff.expo,
            (WebSocketException, ConnectionError, OSError),
            max_time=RETRY_TIME_LIMIT,
            max_value=20,
            on_backoff=self._log_backoff,
            on_giveup=self._log_giveup,
        )(self._connect_once)

        while self._should_run:
            try:
                connect_with_backoff()
            except (WebSocketException, ConnectionError, OSError) as e:
                # Backoff gave up after max_time
                self._websocket = None
                if self._should_run:
                    error_msg = f"Connection failed after {RETRY_TIME_LIMIT}s: {e}"
                    logger.error(error_msg)
                    error_payload = {"e": "error", "m": error_msg}
                    self._handle_message(error_payload)
                    self._should_run = False
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self._should_run = False
                break

    def _connect_once(self):
        """Establish a single WebSocket connection and handle messages.

        This method is wrapped by backoff decorator in _run(). It will be retried
        automatically if it raises WebSocketException, ConnectionError, or OSError.
        """
        with sync_connect(self.url) as websocket:
            self._websocket = websocket
            logger.info(f"Connected to {self.url}")

            # Send initial payload on connection
            if self.payload:
                websocket.send(json.dumps(self.payload))

            # Handle incoming messages
            for message in websocket:
                if not self._should_run:
                    break
                try:
                    payload_obj = json.loads(message)
                    self._handle_message(payload_obj)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

    def _handle_message(self, payload_obj: dict):
        """Handle incoming message by calling the callback.

        Args:
            payload_obj: Parsed JSON message from the WebSocket
        """
        try:
            self.callback(payload_obj)
        except Exception as e:
            logger.error(f"Error in callback: {e}")

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
    ):
        """Initialize the WebSocket connection manager.

        Args:
            url: WebSocket URL to connect to
            payload: Initial payload to send upon connection
            callback: Function to call when messages are received
        """
        self.url = url
        self.payload = payload
        self.callback = callback

        self._websocket: Optional[ClientConnection] = None
        self._task: Optional[asyncio.Task] = None
        self._should_run = False
        self._lock = asyncio.Lock()

    async def connect(self):
        """Establish WebSocket connection and start message handling.

        Creates an asyncio task that runs the connection loop in the background.
        """
        self._should_run = True
        self._task = asyncio.create_task(self._run())

    def _log_backoff(self, details):
        """Callback for backoff events to log reconnection attempts.

        Args:
            details: Dictionary containing backoff information (wait, tries, etc.)
        """
        logger.warning(
            f"Connection lost. Reconnecting in {details['wait']:.1f}s (attempt {details['tries']})"
        )

    def _log_giveup(self, details):
        """Callback when backoff gives up after max time.

        Args:
            details: Dictionary containing backoff information
        """
        error_msg = f"Max reconnection time ({RETRY_TIME_LIMIT}s) reached"
        logger.error(error_msg)

    async def _run(self):
        """Main connection loop with automatic reconnection.

        Continuously attempts to maintain a WebSocket connection, handling
        disconnections and reconnections automatically via backoff decorator.
        """
        # Create decorated connection function with instance callbacks
        connect_with_backoff = backoff.on_exception(
            backoff.expo,
            (WebSocketException, ConnectionError, OSError),
            max_time=RETRY_TIME_LIMIT,
            max_value=20,
            on_backoff=self._log_backoff,
            on_giveup=self._log_giveup,
        )(self._connect_once)

        while self._should_run:
            try:
                await connect_with_backoff()
            except (WebSocketException, ConnectionError, OSError) as e:
                # Backoff gave up after max_time
                self._websocket = None
                if self._should_run:
                    error_msg = f"Connection failed after {RETRY_TIME_LIMIT}s: {e}"
                    logger.error(error_msg)
                    error_payload = {"e": "error", "m": error_msg}
                    await self._handle_message(error_payload)
                    self._should_run = False
                break
            except asyncio.CancelledError:
                logger.info("Connection task cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self._should_run = False
                break

    async def _connect_once(self):
        """Establish a single WebSocket connection and handle messages.

        This method is wrapped by backoff decorator in _run(). It will be retried
        automatically if it raises WebSocketException, ConnectionError, or OSError.
        """
        async with connect(self.url) as websocket:
            self._websocket = websocket
            logger.info(f"Connected to {self.url}")

            # Send initial payload on connection
            if self.payload:
                await websocket.send(json.dumps(self.payload))

            # Handle incoming messages
            async for message in websocket:
                if not self._should_run:
                    break
                try:
                    payload_obj = json.loads(message)
                    await self._handle_message(payload_obj)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

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
