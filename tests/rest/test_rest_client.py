"""Unit tests for Kraken REST API client"""

import base64
import os
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from kraken.exceptions import (
    KrakenAPIError,
    KrakenConnectionError,
    KrakenHTTPError,
    KrakenPayloadError,
    KrakenTimeoutError,
)
from kraken.rest.client import KrakenRESTClient
from kraken.rest.endpoint import KrakenChannel


class TestAPIType:
    """Tests for APIType enum"""

    def test_public_channels(self):
        """Test that MARKETS type returns correct channels"""
        channels = KrakenChannel.MARKETS.channels
        assert isinstance(channels, set)
        assert "Time" in channels
        assert "Assets" in channels
        assert "Ticker" in channels
        assert len(channels) == 11

    def test_private_channels(self):
        """Test that ACCOUNT type returns correct channels"""
        channels = KrakenChannel.ACCOUNT.channels
        assert isinstance(channels, set)
        assert "Balance" in channels
        assert "TradeBalance" in channels
        assert "OpenOrders" in channels
        assert len(channels) == 20

    def test_trading_channels(self):
        """Test that TRADING type returns correct channels"""
        channels = KrakenChannel.TRADING.channels
        assert isinstance(channels, set)
        assert "AddOrder" in channels
        assert "CancelOrder" in channels
        assert len(channels) == 8

    def test_funding_channels(self):
        """Test that FUNDING type returns correct channels"""
        channels = KrakenChannel.FUNDING.channels
        assert isinstance(channels, set)
        assert "DepositMethods" in channels
        assert "Withdraw" in channels
        assert len(channels) == 8

    def test_earning_channels(self):
        """Test that EARNING type returns correct channels"""
        channels = KrakenChannel.EARNING.channels
        assert isinstance(channels, set)
        assert "Earn/Strategies" in channels
        assert "Earn/Allocate" in channels
        assert len(channels) == 6

    def test_public_path(self):
        """Test that MARKETS type returns correct path"""
        assert KrakenChannel.MARKETS.path == "/0/public/"

    def test_private_path(self):
        """Test that ACCOUNT type returns correct path"""
        assert KrakenChannel.ACCOUNT.path == "/0/private/"

    def test_is_private(self):
        """Test is_private method"""
        assert not KrakenChannel.MARKETS.is_private()
        assert KrakenChannel.ACCOUNT.is_private()
        assert KrakenChannel.TRADING.is_private()
        assert KrakenChannel.FUNDING.is_private()
        assert KrakenChannel.EARNING.is_private()


class TestKrakenRESTClientInitialization:
    """Tests for KrakenRESTClient initialization"""

    def test_init_with_credentials(self):
        """Test initialization with explicit credentials"""
        api_key = "test_key"
        api_secret = base64.b64encode(b"test_secret").decode()

        client = KrakenRESTClient(api_key=api_key, api_secret=api_secret)

        assert client.api_key == api_key
        assert client.api_secret == b"test_secret"
        assert client.timeout == 30
        assert client._sync_client is None  # Lazy initialization

    def test_init_without_credentials(self):
        """Test initialization without credentials"""
        client = KrakenRESTClient()

        # Should not raise error, credentials are optional
        assert client.api_key is None or isinstance(client.api_key, str)
        assert client._sync_client is None  # Lazy initialization

    @patch.dict(os.environ, {"KRAKEN_API_KEY": "env_key", "KRAKEN_API_SECRET": ""})
    def test_init_with_env_variables(self):
        """Test initialization with environment variables"""
        api_secret = base64.b64encode(b"env_secret").decode()

        with patch.dict(os.environ, {"KRAKEN_API_SECRET": api_secret}):
            client = KrakenRESTClient()

            assert client.api_key == "env_key"
            assert client.api_secret == b"env_secret"

    def test_init_with_invalid_secret(self):
        """Test initialization with invalid base64 secret"""
        with pytest.raises(ValueError):
            KrakenRESTClient(api_key="test", api_secret="invalid_base64!@#$%")

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout"""
        client = KrakenRESTClient(timeout=60)
        assert client.timeout == 60

    def test_context_manager(self):
        """Test that client works as context manager"""
        with KrakenRESTClient() as client:
            assert isinstance(client, KrakenRESTClient)
            assert isinstance(client._sync_client, httpx.Client)

        # Client should be closed after exiting context
        assert client._sync_client is None


class TestKrakenRESTClientMethods:
    """Tests for KrakenRESTClient methods"""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing"""
        api_key = "test_key"
        api_secret = base64.b64encode(b"test_secret").decode()
        return KrakenRESTClient(api_key=api_key, api_secret=api_secret)

    @pytest.fixture
    def client_no_auth(self):
        """Create a client instance without authentication"""
        return KrakenRESTClient()

    def test_get_api_type_public(self, client):
        """Test _get_api_type for public endpoints"""
        assert client._get_api_type("Time") == KrakenChannel.MARKETS
        assert client._get_api_type("Ticker") == KrakenChannel.MARKETS

    def test_get_api_type_private(self, client):
        """Test _get_api_type for private endpoints"""
        assert client._get_api_type("Balance") == KrakenChannel.ACCOUNT
        assert client._get_api_type("TradeBalance") == KrakenChannel.ACCOUNT

    def test_get_api_type_trading(self, client):
        """Test _get_api_type for trading endpoints"""
        assert client._get_api_type("AddOrder") == KrakenChannel.TRADING
        assert client._get_api_type("CancelOrder") == KrakenChannel.TRADING

    def test_get_api_type_funding(self, client):
        """Test _get_api_type for funding endpoints"""
        assert client._get_api_type("Withdraw") == KrakenChannel.FUNDING
        assert client._get_api_type("DepositMethods") == KrakenChannel.FUNDING

    def test_get_api_type_earning(self, client):
        """Test _get_api_type for earning endpoints"""
        assert client._get_api_type("Earn/Strategies") == KrakenChannel.EARNING
        assert client._get_api_type("Earn/Allocate") == KrakenChannel.EARNING

    def test_get_api_type_unknown(self, client):
        """Test _get_api_type with unknown method"""
        with pytest.raises(ValueError, match="Unknown API method"):
            client._get_api_type("InvalidMethod")

    def test_sign_request(self, client):
        """Test request signing"""
        url_path = "/0/private/Balance"
        data = {"nonce": "1234567890"}
        nonce = "1234567890"

        signature = client._sign_request(url_path, data, nonce)

        assert isinstance(signature, str)
        # Signature should be base64 encoded
        assert len(signature) > 0
        # Should be valid base64
        base64.b64decode(signature)

    def test_sign_request_without_secret(self, client_no_auth):
        """Test request signing without API secret"""
        with pytest.raises(ValueError, match="API secret required"):
            client_no_auth._sign_request("/0/private/Balance", {}, "123")

    @patch("httpx.Client.get")
    def test_request_public_endpoint(self, mock_get, client_no_auth):
        """Test making a request to public endpoint"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": [], "result": {"unixtime": 1234567890}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = client_no_auth.request("Time")

        assert result["error"] == []
        assert "result" in result
        mock_get.assert_called_once()

    @patch("httpx.Client.post")
    def test_request_private_endpoint(self, mock_post, client):
        """Test making a request to private endpoint"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": [], "result": {"balance": "1000"}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = client.request("Balance")

        assert result["error"] == []
        assert "result" in result
        mock_post.assert_called_once()

        # Verify authentication headers were added
        call_kwargs = mock_post.call_args[1]
        assert "headers" in call_kwargs
        assert "API-Key" in call_kwargs["headers"]
        assert "API-Sign" in call_kwargs["headers"]

    def test_request_private_without_auth(self, client_no_auth):
        """Test making a private request without credentials"""
        with patch("httpx.Client.post") as mock_post:
            with pytest.raises(ValueError, match="API key and secret required"):
                client_no_auth.request("Balance")

    @patch("httpx.Client.get")
    def test_request_with_params(self, mock_get, client_no_auth):
        """Test request with parameters"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": [], "result": {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client_no_auth.request("Ticker", params={"pair": "XBTUSD"})

        call_kwargs = mock_get.call_args[1]
        assert "params" in call_kwargs
        assert call_kwargs["params"]["pair"] == "XBTUSD"

    @patch("httpx.Client.get")
    def test_request_timeout(self, mock_get, client_no_auth):
        """Test request timeout"""
        mock_get.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(KrakenTimeoutError):
            client_no_auth.request("Time")

    @patch("httpx.Client.get")
    def test_request_connection_error(self, mock_get, client_no_auth):
        """Test connection error"""
        mock_get.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(KrakenConnectionError):
            client_no_auth.request("Time")

    @patch("httpx.Client.get")
    def test_request_http_error(self, mock_get, client_no_auth):
        """Test HTTP error (4xx, 5xx)"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=Mock(), response=Mock()
        )
        mock_get.return_value = mock_response

        with pytest.raises(KrakenHTTPError):
            client_no_auth.request("Time")

    @patch("httpx.Client.get")
    def test_request_generic_exception(self, mock_get, client_no_auth):
        """Test generic request exception"""
        mock_get.side_effect = httpx.RequestError("Generic error")

        with pytest.raises(httpx.RequestError):
            client_no_auth.request("Time")

    @patch("httpx.Client.get")
    def test_request_invalid_json(self, mock_get, client_no_auth):
        """Test invalid JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(KrakenPayloadError, match="Invalid JSON response"):
            client_no_auth.request("Time")

    @patch("httpx.Client.get")
    def test_request_api_error(self, mock_get, client_no_auth):
        """Test API error in response"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": ["EGeneral:Invalid arguments"]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(KrakenAPIError, match="API error"):
            client_no_auth.request("Time")

    def test_close(self, client):
        """Test closing the client"""
        # Initialize the client first
        _ = client._get_sync_client()
        assert client._sync_client is not None

        client.close()

        assert client._sync_client is None


class TestExceptionHierarchy:
    """Tests for exception hierarchy"""

    def test_exception_inheritance(self):
        """Test that KrakenAPIError inherits from RuntimeError"""
        assert issubclass(KrakenAPIError, RuntimeError)

    def test_exception_instantiation(self):
        """Test that KrakenAPIError can be instantiated with messages"""
        exc = KrakenAPIError("test message")
        assert str(exc) == "test message"

    def test_timeout_error_inheritance(self):
        """Test KrakenTimeoutError inherits from both custom and library exceptions"""
        assert issubclass(KrakenTimeoutError, KrakenAPIError)
        assert issubclass(KrakenTimeoutError, httpx.TimeoutException)

    def test_connection_error_inheritance(self):
        """Test KrakenConnectionError inherits from both custom and library exceptions"""
        assert issubclass(KrakenConnectionError, KrakenAPIError)
        assert issubclass(KrakenConnectionError, httpx.ConnectError)

    def test_http_error_inheritance(self):
        """Test KrakenHTTPError inherits from both custom and library exceptions"""
        assert issubclass(KrakenHTTPError, KrakenAPIError)
        assert issubclass(KrakenHTTPError, httpx.HTTPError)

    def test_payload_error_inheritance(self):
        """Test KrakenPayloadError inherits from both custom and library exceptions"""
        import json

        assert issubclass(KrakenPayloadError, KrakenAPIError)
        assert issubclass(KrakenPayloadError, json.JSONDecodeError)

    def test_httpx_compatibility_timeout(self):
        """Test that KrakenTimeoutError can be caught as httpx.TimeoutException"""
        try:
            raise KrakenTimeoutError("test")
        except httpx.TimeoutException:
            pass  # Should be caught

    def test_httpx_compatibility_connection(self):
        """Test that KrakenConnectionError can be caught as httpx.ConnectError"""
        try:
            raise KrakenConnectionError("test")
        except httpx.ConnectError:
            pass  # Should be caught

    def test_httpx_compatibility_http(self):
        """Test that KrakenHTTPError can be caught as httpx.HTTPError"""
        try:
            raise KrakenHTTPError("test")
        except httpx.HTTPError:
            pass  # Should be caught


class TestKrakenRESTClientAsync:
    """Tests for KrakenRESTClient async functionality"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test that async client works as context manager"""
        async with KrakenRESTClient() as client:
            assert isinstance(client, KrakenRESTClient)
            assert isinstance(client._async_client, httpx.AsyncClient)

        # Client should be closed after exiting context
        assert client._async_client is None


class TestKrakenRESTClientAsyncMethods:
    """Tests for KrakenRESTClient async methods"""

    @pytest.fixture
    def async_client(self):
        """Create an async client instance for testing"""
        api_key = "test_key"
        api_secret = base64.b64encode(b"test_secret").decode()
        return KrakenRESTClient(api_key=api_key, api_secret=api_secret)

    @pytest.fixture
    def async_client_no_auth(self):
        """Create an async client instance without authentication"""
        return KrakenRESTClient()

    @pytest.mark.asyncio
    async def test_get_api_type_unknown(self, async_client_no_auth):
        """Test _get_api_type with unknown method"""
        with pytest.raises(ValueError, match="Unknown API method"):
            async_client_no_auth._get_api_type("InvalidMethod")

    @pytest.mark.asyncio
    async def test_sign_request_without_secret(self, async_client_no_auth):
        """Test request signing without API secret"""
        with pytest.raises(ValueError, match="API secret required"):
            async_client_no_auth._sign_request("/0/private/Balance", {}, "123")

    @pytest.mark.asyncio
    async def test_request_public_endpoint(self, async_client_no_auth):
        """Test making an async request to public endpoint"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"error": [], "result": {"unixtime": 1234567890}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            async with async_client_no_auth as client:
                result = await client.arequest("Time")

            assert result["error"] == []
            assert "result" in result
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_private_endpoint(self, async_client):
        """Test making an async request to private endpoint"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"error": [], "result": {"balance": "1000"}}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            async with async_client as client:
                result = await client.arequest("Balance")

            assert result["error"] == []
            assert "result" in result
            mock_post.assert_called_once()

            # Verify authentication headers were added
            call_kwargs = mock_post.call_args[1]
            assert "headers" in call_kwargs
            assert "API-Key" in call_kwargs["headers"]
            assert "API-Sign" in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_request_private_without_auth(self, async_client_no_auth):
        """Test making a private async request without credentials"""
        async with async_client_no_auth as client:
            with pytest.raises(ValueError, match="API key and secret required"):
                await client.arequest("Balance")

    @pytest.mark.asyncio
    async def test_request_with_params(self, async_client_no_auth):
        """Test async request with parameters"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"error": [], "result": {}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            async with async_client_no_auth as client:
                await client.arequest("Ticker", params={"pair": "XBTUSD"})

            call_kwargs = mock_get.call_args[1]
            assert "params" in call_kwargs
            assert call_kwargs["params"]["pair"] == "XBTUSD"

    @pytest.mark.asyncio
    async def test_request_timeout(self, async_client_no_auth):
        """Test async request timeout"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")

            async with async_client_no_auth as client:
                with pytest.raises(KrakenTimeoutError):
                    await client.arequest("Time")

    @pytest.mark.asyncio
    async def test_request_connection_error(self, async_client_no_auth):
        """Test async connection error"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")

            async with async_client_no_auth as client:
                with pytest.raises(KrakenConnectionError):
                    await client.arequest("Time")

    @pytest.mark.asyncio
    async def test_request_http_error(self, async_client_no_auth):
        """Test async HTTP error (4xx, 5xx)"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response

            async with async_client_no_auth as client:
                with pytest.raises(KrakenHTTPError):
                    await client.arequest("Time")

    @pytest.mark.asyncio
    async def test_request_generic_exception(self, async_client_no_auth):
        """Test async generic request exception"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.RequestError("Generic error")

            async with async_client_no_auth as client:
                with pytest.raises(httpx.RequestError):
                    await client.arequest("Time")

    @pytest.mark.asyncio
    async def test_request_invalid_json(self, async_client_no_auth):
        """Test async invalid JSON response"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            async with async_client_no_auth as client:
                with pytest.raises(KrakenPayloadError, match="Invalid JSON response"):
                    await client.arequest("Time")

    @pytest.mark.asyncio
    async def test_request_api_error(self, async_client_no_auth):
        """Test async API error in response"""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"error": ["EGeneral:Invalid arguments"]}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            async with async_client_no_auth as client:
                with pytest.raises(KrakenAPIError, match="API error"):
                    await client.arequest("Time")

    @pytest.mark.asyncio
    async def test_aclose(self, async_client):
        """Test closing the async client"""
        from unittest.mock import AsyncMock

        async with async_client:
            pass  # Client initialized

        # Should already be closed by context manager
        assert async_client._async_client is None

        # Test explicit close
        mock_client = Mock(spec=httpx.AsyncClient)
        aclose_mock = AsyncMock()
        mock_client.aclose = aclose_mock
        async_client._async_client = mock_client

        await async_client.aclose()

        aclose_mock.assert_called_once()
        assert async_client._async_client is None
