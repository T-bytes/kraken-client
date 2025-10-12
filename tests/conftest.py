"""Shared pytest fixtures for Kraken tests"""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing"""
    ws = AsyncMock()
    ws.closed = False
    ws.close = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([]))
    return ws


@pytest.fixture
def mock_callback():
    """Mock callback function for WebSocket message handling"""
    return MagicMock()


@pytest.fixture
def mock_async_callback():
    """Mock async callback function for WebSocket message handling"""
    return AsyncMock()


@pytest.fixture
def sample_subscription_params():
    """Sample subscription parameters for testing"""
    return {
        'channel': 'ticker',
        'symbol': ['BTC/USD']
    }


@pytest.fixture
def sample_request_params():
    """Sample request parameters for testing"""
    return {
        'method': 'add_order',
        'params': {
            'order_type': 'limit',
            'side': 'buy',
            'symbol': 'BTC/USD',
            'limit_price': 50000.0,
            'order_qty': 0.1
        }
    }


@pytest.fixture
def sample_ticker_message():
    """Sample ticker message from Kraken WebSocket"""
    return {
        'channel': 'ticker',
        'type': 'update',
        'data': [{
            'symbol': 'BTC/USD',
            'bid': 50000.0,
            'ask': 50010.0,
            'last': 50005.0,
            'volume': 1234.56,
            'vwap': 50000.0,
            'low': 49500.0,
            'high': 50500.0
        }]
    }


@pytest.fixture
def sample_error_message():
    """Sample error message from Kraken WebSocket"""
    return {
        'e': 'error',
        'm': 'Max reconnect retries reached'
    }
