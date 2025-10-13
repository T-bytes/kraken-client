"""Unit tests for Kraken REST API client"""

import base64
import os
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from kraken.exceptions import KrakenAPIError
from kraken.rest import KrakenClientREST, KrakenEndpoint


class TestAPIType:
    """Tests for APIType enum"""

    def test_public_channels(self):
        """Test that PUBLIC type returns correct channels"""
        channels = KrakenEndpoint.PUBLIC.channels
        assert isinstance(channels, set)
        assert "Time" in channels
        assert "Assets" in channels
        assert "Ticker" in channels
        assert len(channels) == 9

    def test_private_channels(self):
        """Test that PRIVATE type returns correct channels"""
        channels = KrakenEndpoint.PRIVATE.channels
        assert isinstance(channels, set)
        assert "Balance" in channels
        assert "TradeBalance" in channels
        assert "OpenOrders" in channels
        assert len(channels) == 19

    def test_trading_channels(self):
        """Test that TRADING type returns correct channels"""
        channels = KrakenEndpoint.TRADING.channels
        assert isinstance(channels, set)
        assert "AddOrder" in channels
        assert "CancelOrder" in channels
        assert len(channels) == 7

    def test_funding_channels(self):
        """Test that FUNDING type returns correct channels"""
        channels = KrakenEndpoint.FUNDING.channels
        assert isinstance(channels, set)
        assert "DepositMethods" in channels
        assert "Withdraw" in channels
        assert len(channels) == 8

    def test_staking_channels(self):
        """Test that STAKING type returns correct channels"""
        channels = KrakenEndpoint.STAKING.channels
        assert isinstance(channels, set)
        assert "Stake" in channels
        assert "Unstake" in channels
        assert len(channels) == 12

    def test_public_path(self):
        """Test that PUBLIC type returns correct path"""
        assert KrakenEndpoint.PUBLIC.path == "/0/public/"

    def test_private_path(self):
        """Test that PRIVATE type returns correct path"""
        assert KrakenEndpoint.PRIVATE.path == "/0/private/"

    def test_is_private(self):
        """Test is_private method"""
        assert not KrakenEndpoint.PUBLIC.is_private()
        assert KrakenEndpoint.PRIVATE.is_private()
        assert KrakenEndpoint.TRADING.is_private()
        assert KrakenEndpoint.FUNDING.is_private()
        assert KrakenEndpoint.STAKING.is_private()


class TestKrakenClientRESTInitialization:
    """Tests for KrakenClientREST initialization"""

    def test_init_with_credentials(self):
        """Test initialization with explicit credentials"""
        api_key = "test_key"
        api_secret = base64.b64encode(b"test_secret").decode()

        client = KrakenClientREST(api_key=api_key, api_secret=api_secret)

        assert client.api_key == api_key
        assert client.api_secret == b"test_secret"
        assert client.timeout == 30
        assert isinstance(client.session, requests.Session)

    def test_init_without_credentials(self):
        """Test initialization without credentials"""
        client = KrakenClientREST()

        # Should not raise error, credentials are optional
        assert client.api_key is None or isinstance(client.api_key, str)
        assert isinstance(client.session, requests.Session)

    @patch.dict(os.environ, {"KRAKEN_API_KEY": "env_key", "KRAKEN_API_SECRET": ""})
    def test_init_with_env_variables(self):
        """Test initialization with environment variables"""
        api_secret = base64.b64encode(b"env_secret").decode()

        with patch.dict(os.environ, {"KRAKEN_API_SECRET": api_secret}):
            client = KrakenClientREST()

            assert client.api_key == "env_key"
            assert client.api_secret == b"env_secret"

    def test_init_with_invalid_secret(self):
        """Test initialization with invalid base64 secret"""
        with pytest.raises(ValueError):
            KrakenClientREST(api_key="test", api_secret="invalid_base64!@#$%")

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout"""
        client = KrakenClientREST(timeout=60)
        assert client.timeout == 60

    def test_context_manager(self):
        """Test that client works as context manager"""
        with KrakenClientREST() as client:
            assert isinstance(client, KrakenClientREST)
            assert isinstance(client.session, requests.Session)

        # Session should be closed after exiting context
        assert client.session  # Session object still exists


class TestKrakenClientRESTMethods:
    """Tests for KrakenClientREST methods"""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing"""
        api_key = "test_key"
        api_secret = base64.b64encode(b"test_secret").decode()
        return KrakenClientREST(api_key=api_key, api_secret=api_secret)

    @pytest.fixture
    def client_no_auth(self):
        """Create a client instance without authentication"""
        return KrakenClientREST()

    def test_get_api_type_public(self, client):
        """Test _get_api_type for public endpoints"""
        assert client._get_api_type("Time") == KrakenEndpoint.PUBLIC
        assert client._get_api_type("Ticker") == KrakenEndpoint.PUBLIC

    def test_get_api_type_private(self, client):
        """Test _get_api_type for private endpoints"""
        assert client._get_api_type("Balance") == KrakenEndpoint.PRIVATE
        assert client._get_api_type("TradeBalance") == KrakenEndpoint.PRIVATE

    def test_get_api_type_trading(self, client):
        """Test _get_api_type for trading endpoints"""
        assert client._get_api_type("AddOrder") == KrakenEndpoint.TRADING
        assert client._get_api_type("CancelOrder") == KrakenEndpoint.TRADING

    def test_get_api_type_funding(self, client):
        """Test _get_api_type for funding endpoints"""
        assert client._get_api_type("Withdraw") == KrakenEndpoint.FUNDING
        assert client._get_api_type("DepositMethods") == KrakenEndpoint.FUNDING

    def test_get_api_type_staking(self, client):
        """Test _get_api_type for staking endpoints"""
        assert client._get_api_type("Stake") == KrakenEndpoint.STAKING
        assert client._get_api_type("Unstake") == KrakenEndpoint.STAKING

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

    @patch("kraken.rest.requests.Session.get")
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

    @patch("kraken.rest.requests.Session.post")
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
        with patch("kraken.rest.requests.Session.post") as mock_post:
            with pytest.raises(ValueError, match="API key and secret required"):
                client_no_auth.request("Balance")

    @patch("kraken.rest.requests.Session.get")
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

    @patch("kraken.rest.requests.Session.get")
    def test_request_timeout(self, mock_get, client_no_auth):
        """Test request timeout"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(requests.exceptions.Timeout):
            client_no_auth.request("Time")

    @patch("kraken.rest.requests.Session.get")
    def test_request_connection_error(self, mock_get, client_no_auth):
        """Test connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            client_no_auth.request("Time")

    @patch("kraken.rest.requests.Session.get")
    def test_request_http_error(self, mock_get, client_no_auth):
        """Test HTTP error (4xx, 5xx)"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            client_no_auth.request("Time")

    @patch("kraken.rest.requests.Session.get")
    def test_request_invalid_json(self, mock_get, client_no_auth):
        """Test invalid JSON response"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid JSON response"):
            client_no_auth.request("Time")

    @patch("kraken.rest.requests.Session.get")
    def test_request_api_error(self, mock_get, client_no_auth):
        """Test API error in response"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": ["EGeneral:Invalid arguments"]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(KrakenAPIError, match="API error"):
            client_no_auth.request("Time")

    @patch("kraken.rest.requests.Session.get")
    def test_get_method(self, mock_get, client_no_auth):
        """Test get convenience method"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": [], "result": {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = client_no_auth.get("Time")

        assert result["error"] == []
        mock_get.assert_called_once()

    @patch("kraken.rest.requests.Session.post")
    def test_post_method(self, mock_post, client):
        """Test post convenience method"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": [], "result": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = client.post("Balance")

        assert result["error"] == []
        mock_post.assert_called_once()

    def test_close(self, client):
        """Test closing the client"""
        mock_session = Mock()
        client.session = mock_session

        client.close()

        mock_session.close.assert_called_once()


class TestExceptionHierarchy:
    """Tests for exception hierarchy"""

    def test_exception_inheritance(self):
        """Test that KrakenAPIError inherits from Exception"""
        assert issubclass(KrakenAPIError, Exception)

    def test_exception_instantiation(self):
        """Test that KrakenAPIError can be instantiated with messages"""
        exc = KrakenAPIError("test message")
        assert str(exc) == "test message"
