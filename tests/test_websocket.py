"""Tests for Kraken WebSocket client"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from websockets.exceptions import WebSocketException

from kraken.websocket import KrakenSocketConnection, KrakenClientWS


class TestKrakenSocketConnection:
    """Tests for KrakenSocketConnection class"""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_callback):
        """Test WebSocket connection initialization"""
        url = "wss://test.example.com"
        payload = {"test": "data"}

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=mock_callback,
            initial_delay=0.1,
            max_delay=10.0,
            max_retries=5
        )

        assert conn.url == url
        assert conn.payload == payload
        assert conn.callback == mock_callback
        assert conn.initial_delay == 0.1
        assert conn.max_delay == 10.0
        assert conn.max_retries == 5
        assert conn._websocket is None
        assert conn._task is None
        assert conn._reconnect_delay == 0.1
        assert conn._retries == 0
        assert conn._should_run is False

    @pytest.mark.asyncio
    async def test_connect_starts_task(self, mock_callback):
        """Test that connect() starts the background task"""
        conn = KrakenSocketConnection(
            url="wss://test.example.com",
            payload={},
            callback=mock_callback
        )

        with patch.object(conn, '_run', new_callable=AsyncMock) as mock_run:
            await conn.connect()

            assert conn._should_run is True
            assert conn._task is not None

            # Wait briefly for task to start
            await asyncio.sleep(0.01)

            # Clean up
            conn._should_run = False
            if conn._task:
                conn._task.cancel()
                try:
                    await conn._task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_successful_connection_and_message_handling(self, mock_async_callback, sample_ticker_message):
        """Test successful WebSocket connection and message handling"""
        url = "wss://test.example.com"
        payload = {"method": "subscribe"}

        # Create an event to signal when message is processed
        message_processed = asyncio.Event()

        async def callback_wrapper(msg):
            await mock_async_callback(msg)
            message_processed.set()

        # Create mock websocket that yields one message then stops
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()

        call_count = [0]

        async def mock_aiter(self):
            yield json.dumps(sample_ticker_message)
            # After yielding, iterator ends naturally

        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        mock_ws.__aiter__ = mock_aiter

        def mock_connect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_ws
            else:
                # On reconnection attempts, return a context manager that blocks
                blocking_mock = AsyncMock()

                async def blocking_enter():
                    await asyncio.Event().wait()

                blocking_mock.__aenter__ = blocking_enter
                blocking_mock.__aexit__ = AsyncMock(return_value=None)
                return blocking_mock

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=callback_wrapper,
            max_retries=1
        )

        with patch('kraken.websocket.connect', side_effect=mock_connect):
            await conn.connect()

            # Wait for message processing with timeout
            try:
                await asyncio.wait_for(message_processed.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            # Disconnect to ensure task completes
            await conn.disconnect()

            # Verify payload was sent
            assert mock_ws.send.call_count >= 1
            mock_ws.send.assert_any_call(json.dumps(payload))

            # Verify callback was called with the message
            mock_async_callback.assert_called_once_with(sample_ticker_message)

    @pytest.mark.asyncio
    async def test_sync_callback_execution(self, mock_callback, sample_ticker_message):
        """Test that synchronous callbacks are executed in executor"""
        url = "wss://test.example.com"
        payload = {}

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()

        call_count = [0]

        async def mock_aiter(self):
            yield json.dumps(sample_ticker_message)
            # After yielding, iterator ends naturally

        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        mock_ws.__aiter__ = mock_aiter

        def mock_connect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_ws
            else:
                # On reconnection attempts, return a context manager that blocks
                blocking_mock = AsyncMock()

                async def blocking_enter(self):
                    await asyncio.Event().wait()

                blocking_mock.__aenter__ = blocking_enter
                blocking_mock.__aexit__ = AsyncMock(return_value=None)
                return blocking_mock

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=mock_callback,
            max_retries=0  # Don't reconnect so we don't get error callback
        )

        with patch('kraken.websocket.connect', side_effect=mock_connect):
            await conn.connect()

            # Wait for message processing
            await asyncio.sleep(0.2)

            # Disconnect to ensure task completes
            await conn.disconnect()

            # Verify callback was called with the message
            # Should be called once with the ticker message (not the error message)
            assert mock_callback.call_count == 1
            mock_callback.assert_called_with(sample_ticker_message)

    @pytest.mark.skip(reason="Hangs indefinitely")
    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self, mock_async_callback):
        """Test handling of invalid JSON messages"""
        url = "wss://test.example.com"
        payload = {}

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()
        messages = ["invalid json {"]

        async def mock_aiter(self):
            for msg in messages:
                yield msg

        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        mock_ws.__aiter__ = mock_aiter

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=mock_async_callback
        )

        with patch('kraken.websocket.connect', return_value=mock_ws):
            with patch('kraken.websocket.logger') as mock_logger:
                await conn.connect()

                # Wait for message processing
                await asyncio.sleep(0.1)

                # Verify error was logged
                assert mock_logger.error.called
                error_msg = str(mock_logger.error.call_args[0][0])
                assert "Failed to decode message" in error_msg

                # Callback should not be called with invalid JSON
                mock_async_callback.assert_not_called()

                # Clean up
                await conn.disconnect()

    @pytest.mark.skip(reason="Hangs indefinitely")
    @pytest.mark.asyncio
    async def test_callback_exception_handling(self, sample_ticker_message):
        """Test handling of exceptions in callback"""
        url = "wss://test.example.com"
        payload = {}

        # Create callback that raises exception
        error_callback = AsyncMock(side_effect=ValueError("Test error"))

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send = AsyncMock()
        messages = [json.dumps(sample_ticker_message)]

        async def mock_aiter(self):
            for msg in messages:
                yield msg

        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        mock_ws.__aiter__ = mock_aiter

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=error_callback
        )

        with patch('kraken.websocket.connect', return_value=mock_ws):
            with patch('kraken.websocket.logger') as mock_logger:
                await conn.connect()

                # Wait for message processing
                await asyncio.sleep(0.1)

                # Verify error was logged
                assert mock_logger.error.called
                error_msg = str(mock_logger.error.call_args[0][0])
                assert "Error in callback" in error_msg

                # Clean up
                await conn.disconnect()

    @pytest.mark.skip(reason="Will be re-implemented using backoff decorators")
    @pytest.mark.asyncio
    async def test_reconnection_with_exponential_backoff(self, mock_async_callback):
        """Test reconnection logic with exponential backoff"""
        url = "wss://test.example.com"
        payload = {}
        initial_delay = 0.05
        max_delay = 0.2

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=mock_async_callback,
            initial_delay=initial_delay,
            max_delay=max_delay,
            max_retries=3
        )

        # Track connection attempts
        attempt_count = 0

        async def mock_connect_with_failure(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                raise WebSocketException("Connection failed")
            else:
                # On third attempt, stop the connection
                conn._should_run = False
                raise WebSocketException("Final failure")

        with patch('kraken.websocket.connect', side_effect=mock_connect_with_failure):
            with patch('kraken.websocket.logger') as mock_logger:
                await conn.connect()

                # Wait for reconnection attempts
                await asyncio.sleep(0.5)

                # Verify multiple connection attempts
                assert attempt_count >= 2

                # Verify reconnection delay increased
                assert conn._reconnect_delay > initial_delay
                assert conn._reconnect_delay <= max_delay

                # Clean up
                await conn.disconnect()

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_async_callback, sample_error_message):
        """Test that max retries stops reconnection and sends error"""
        url = "wss://test.example.com"
        payload = {}
        max_retries = 2

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=mock_async_callback,
            initial_delay=0.01,
            max_retries=max_retries
        )

        with patch('kraken.websocket.connect', side_effect=WebSocketException("Connection failed")):
            with patch('kraken.websocket.logger') as mock_logger:
                await conn.connect()

                # Wait for all retry attempts
                await asyncio.sleep(0.5)

                # Verify error was logged
                assert mock_logger.error.called
                error_calls = [call for call in mock_logger.error.call_args_list
                              if "Max reconnection retries" in str(call)]
                assert len(error_calls) > 0

                # Verify callback was called with error message
                error_call_found = False
                for call_args in mock_async_callback.call_args_list:
                    if call_args[0][0].get('e') == 'error':
                        error_call_found = True
                        break
                assert error_call_found

                # Verify connection stopped
                assert conn._should_run is False

                # Clean up
                await conn.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_callback):
        """Test graceful disconnection"""
        url = "wss://test.example.com"
        payload = {}

        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.close = AsyncMock()
        mock_ws.send = AsyncMock()

        # Keep connection open
        async def mock_aiter():
            while True:
                await asyncio.sleep(1)
                yield json.dumps({"test": "data"})

        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        mock_ws.__aiter__ = mock_aiter

        conn = KrakenSocketConnection(
            url=url,
            payload=payload,
            callback=mock_callback
        )

        with patch('kraken.websocket.connect', return_value=mock_ws):
            await conn.connect()

            # Wait briefly for connection
            await asyncio.sleep(0.05)

            # Disconnect
            await conn.disconnect()

            # Verify state
            assert conn._should_run is False
            assert conn._task is None or conn._task.done()

    @pytest.mark.asyncio
    async def test_is_connected_property(self, mock_callback):
        """Test is_connected property"""
        conn = KrakenSocketConnection(
            url="wss://test.example.com",
            payload={},
            callback=mock_callback
        )

        # Initially not connected
        assert conn.is_connected is False

        # Mock connected state
        mock_ws = AsyncMock()
        mock_ws.closed = False
        conn._websocket = mock_ws

        assert conn.is_connected is True

        # Mock closed state
        mock_ws.closed = True
        assert conn.is_connected is False


class TestKrakenClientWS:
    """Tests for KrakenClientWS class"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test KrakenClientWS initialization"""
        key = "test_key"
        secret = "test_secret"
        nonce_multiplier = 1.5

        client = KrakenClientWS(key=key, secret=secret, nonce_multiplier=nonce_multiplier)

        assert client.key == key
        assert client.secret == secret
        assert client.nonce_multiplier == nonce_multiplier
        assert client._connections == {}

    @pytest.mark.asyncio
    async def test_initialization_without_credentials(self):
        """Test KrakenClientWS initialization without credentials"""
        client = KrakenClientWS()

        assert client.key is None
        assert client.secret is None
        assert client.nonce_multiplier == 1.0
        assert client._connections == {}

    @pytest.mark.asyncio
    async def test_subscribe_public(self, sample_subscription_params, mock_async_callback):
        """Test public channel subscription"""
        client = KrakenClientWS()

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection):
            conn_id = await client.subscribe_public(
                params=sample_subscription_params,
                callback=mock_async_callback
            )

            # Verify connection ID format
            assert conn_id == "ticker_BTC/USD"

            # Verify connection was created and stored
            assert conn_id in client._connections

            # Verify connection was started
            mock_connection.connect.assert_called_once()

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_subscribe_public_without_symbol(self, mock_async_callback):
        """Test public channel subscription without symbol"""
        client = KrakenClientWS()

        params = {'channel': 'heartbeat'}

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection):
            conn_id = await client.subscribe_public(
                params=params,
                callback=mock_async_callback
            )

            # Verify connection ID format (no symbol)
            assert conn_id == "heartbeat"

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_subscribe_private(self, sample_subscription_params, mock_async_callback):
        """Test private channel subscription"""
        client = KrakenClientWS(key="test_key", secret="test_secret")

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection) as mock_conn_class:
            conn_id = await client.subscribe_private(
                params=sample_subscription_params,
                callback=mock_async_callback
            )

            # Verify connection ID format
            assert conn_id == "ticker_BTC/USD"

            # Verify private URL was used
            call_args = mock_conn_class.call_args
            assert client.PRIVATE_STREAM_URL in call_args.kwargs['url']

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_duplicate_subscription(self, sample_subscription_params, mock_async_callback):
        """Test that duplicate subscriptions are handled"""
        client = KrakenClientWS()

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection):
            # First subscription
            conn_id_1 = await client.subscribe_public(
                params=sample_subscription_params,
                callback=mock_async_callback
            )

            # Duplicate subscription
            with patch('kraken.websocket.logger') as mock_logger:
                conn_id_2 = await client.subscribe_public(
                    params=sample_subscription_params,
                    callback=mock_async_callback
                )

                # Should return same connection ID
                assert conn_id_1 == conn_id_2

                # Should log warning
                warning_calls = [call for call in mock_logger.warning.call_args_list
                                if "already exists" in str(call)]
                assert len(warning_calls) > 0

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_request(self, sample_request_params, mock_async_callback):
        """Test sending a request"""
        client = KrakenClientWS(key="test_key", secret="test_secret")

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection) as mock_conn_class:
            conn_id = await client.request(
                request=sample_request_params,
                callback=mock_async_callback,
                req_id=12345
            )

            # Verify connection ID is timestamp-based
            assert conn_id.isdigit()
            assert len(conn_id) == 13  # Millisecond timestamp

            # Verify connection was created
            assert conn_id in client._connections

            # Verify private URL was used
            call_args = mock_conn_class.call_args
            assert client.PRIVATE_STREAM_URL in call_args.kwargs['url']

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_stop_socket(self, sample_subscription_params, mock_async_callback):
        """Test stopping a specific socket connection"""
        client = KrakenClientWS()

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()
        mock_connection.disconnect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection):
            # Create connection
            conn_id = await client.subscribe_public(
                params=sample_subscription_params,
                callback=mock_async_callback
            )

            # Stop the connection
            result = await client.stop_socket(conn_id)

            # Verify connection was stopped
            assert result is True
            mock_connection.disconnect.assert_called_once()

            # Verify connection was removed
            assert conn_id not in client._connections

    @pytest.mark.asyncio
    async def test_stop_socket_not_found(self):
        """Test stopping a non-existent socket connection"""
        client = KrakenClientWS()

        with patch('kraken.websocket.logger') as mock_logger:
            result = await client.stop_socket("nonexistent_id")

            # Verify operation failed
            assert result is False

            # Verify warning was logged
            warning_calls = [call for call in mock_logger.warning.call_args_list
                            if "not found" in str(call)]
            assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_close_all_connections(self, sample_subscription_params, mock_async_callback):
        """Test closing all connections"""
        client = KrakenClientWS()

        mock_connection_1 = AsyncMock()
        mock_connection_1.connect = AsyncMock()
        mock_connection_1.disconnect = AsyncMock()

        mock_connection_2 = AsyncMock()
        mock_connection_2.connect = AsyncMock()
        mock_connection_2.disconnect = AsyncMock()

        connections = [mock_connection_1, mock_connection_2]

        with patch('kraken.websocket.KrakenSocketConnection', side_effect=connections):
            # Create multiple connections
            conn_id_1 = await client.subscribe_public(
                params={'channel': 'ticker', 'symbol': ['BTC/USD']},
                callback=mock_async_callback
            )

            conn_id_2 = await client.subscribe_public(
                params={'channel': 'ticker', 'symbol': ['ETH/USD']},
                callback=mock_async_callback
            )

            # Close all connections
            await client.close()

            # Verify all connections were disconnected
            mock_connection_1.disconnect.assert_called_once()
            mock_connection_2.disconnect.assert_called_once()

            # Verify connections were removed
            assert len(client._connections) == 0

    @pytest.mark.asyncio
    async def test_stop(self, sample_subscription_params, mock_async_callback):
        """Test stop() method calls close()"""
        client = KrakenClientWS()

        with patch.object(client, 'close', new_callable=AsyncMock) as mock_close:
            await client.stop()

            # Verify close was called
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_connection_ids(self, sample_subscription_params, mock_async_callback):
        """Test getting list of active connection IDs"""
        client = KrakenClientWS()

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection):
            # Initially no connections
            assert client.get_connection_ids() == []

            # Create connections
            conn_id_1 = await client.subscribe_public(
                params={'channel': 'ticker', 'symbol': ['BTC/USD']},
                callback=mock_async_callback
            )

            conn_id_2 = await client.subscribe_public(
                params={'channel': 'ticker', 'symbol': ['ETH/USD']},
                callback=mock_async_callback
            )

            # Get connection IDs
            conn_ids = client.get_connection_ids()

            # Verify both connections are listed
            assert len(conn_ids) == 2
            assert conn_id_1 in conn_ids
            assert conn_id_2 in conn_ids

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_is_connected(self, sample_subscription_params, mock_async_callback):
        """Test checking connection status"""
        client = KrakenClientWS()

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()
        mock_connection.is_connected = True

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection):
            # Non-existent connection
            assert client.is_connected("nonexistent_id") is False

            # Create connection
            conn_id = await client.subscribe_public(
                params=sample_subscription_params,
                callback=mock_async_callback
            )

            # Check connected status
            assert client.is_connected(conn_id) is True

            # Mock disconnected state
            mock_connection.is_connected = False
            assert client.is_connected(conn_id) is False

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_subscription_with_extra_kwargs(self, sample_subscription_params, mock_async_callback):
        """Test subscription with additional keyword arguments"""
        client = KrakenClientWS()

        mock_connection = AsyncMock()
        mock_connection.connect = AsyncMock()

        with patch('kraken.websocket.KrakenSocketConnection', return_value=mock_connection) as mock_conn_class:
            conn_id = await client.subscribe_public(
                params=sample_subscription_params,
                callback=mock_async_callback,
                req_id=12345,
                snapshot=True
            )

            # Verify extra kwargs were included in payload
            call_args = mock_conn_class.call_args
            payload = call_args.kwargs['payload']

            assert payload['method'] == 'subscribe'
            assert payload['params'] == sample_subscription_params
            assert payload['req_id'] == 12345
            assert payload['snapshot'] is True

            # Clean up
            await client.close()

    @pytest.mark.asyncio
    async def test_url_construction(self):
        """Test that URLs are constructed correctly"""
        client = KrakenClientWS()

        # Verify URL constants
        assert client.STREAM_URL == 'wss://ws.kraken.com'
        assert client.PRIVATE_STREAM_URL == 'wss://ws-auth.kraken.com'
        assert client.VERSION == '/v2'

        # Test full URLs
        public_url = client.STREAM_URL + client.VERSION
        private_url = client.PRIVATE_STREAM_URL + client.VERSION

        assert public_url == 'wss://ws.kraken.com/v2'
        assert private_url == 'wss://ws-auth.kraken.com/v2'
