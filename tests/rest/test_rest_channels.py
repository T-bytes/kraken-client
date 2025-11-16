"""Unit tests for Kraken REST API Channels"""

from unittest.mock import MagicMock, patch

import pytest

from kraken.rest.channels import MarketChannel, TradingChannel
from kraken.rest.client import KrakenRESTClient
from kraken.rest.schema.market import (
    GetAssetInfoRequest,
    GetAssetInfoResponse,
    GetAssetPairsRequest,
    GetAssetPairsResponse,
    GetOHLCDataRequest,
    GetOHLCDataResponse,
    GetOrderBookRequest,
    GetOrderBookResponse,
    GetRecentSpreadsRequest,
    GetRecentSpreadsResponse,
    GetRecentTradesRequest,
    GetRecentTradesResponse,
    GetServerTimeRequest,
    GetServerTimeResponse,
    GetSystemStatusRequest,
    GetSystemStatusResponse,
    GetTickerInformationRequest,
    GetTickerInformationResponse,
)
from kraken.rest.schema.trading import (
    AddOrderRequest,
    AddOrderResponse,
    AmendOrderRequest,
    AmendOrderResponse,
    CancelAllRequest,
    CancelOrderRequest,
    CancelOrderResponse,
    GetWebSocketsTokenRequest,
    GetWebSocketsTokenResponse,
)


class TestMarketChannelInitialization:
    """Tests for MarketChannel initialization"""

    def test_init_with_client(self):
        """Test MarketChannel initialization with a client"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = MarketChannel(mock_client)

        assert channel.client is mock_client
        assert channel.channel == "market"
        assert channel.private is False

    def test_path_property(self):
        """Test that path property returns correct public path"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = MarketChannel(mock_client)

        assert channel.path == "/0/public/"


class TestMarketChannelServerTime:
    """Tests for server_time method"""

    def test_server_time_basic(self):
        """Test server_time method returns request and response"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetServerTimeResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        result = channel.server_time()

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, GetServerTimeRequest)
        assert response is mock_response
        mock_client.request.assert_called_once()

    def test_server_time_request_called_with_correct_schema(self):
        """Test that server_time calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetServerTimeResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, _ = channel.server_time()

        mock_client.request.assert_called_once_with(request)


class TestMarketChannelSystemStatus:
    """Tests for system_status method"""

    def test_system_status_basic(self):
        """Test system_status method returns request and response"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetSystemStatusResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.system_status()

        assert isinstance(request, GetSystemStatusRequest)
        assert response is mock_response
        mock_client.request.assert_called_once()

    def test_system_status_request_called_with_correct_schema(self):
        """Test that system_status calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetSystemStatusResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, _ = channel.system_status()

        mock_client.request.assert_called_once_with(request)


class TestMarketChannelAssetInfo:
    """Tests for asset_info method"""

    def test_asset_info_no_parameters(self):
        """Test asset_info with no parameters - should raise validation error for missing asset"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)

        # asset parameter is required, so this should raise validation error
        with pytest.raises(Exception):  # ValidationError or ValueError
            request, response = channel.asset_info()

    def test_asset_info_with_single_asset_string(self):
        """Test asset_info with single asset as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_info(assets="XBT", aclass="currency")

        assert isinstance(request, GetAssetInfoRequest)
        assert request.asset == "XBT"
        assert response is mock_response

    def test_asset_info_with_multiple_assets_string(self):
        """Test asset_info with multiple assets as comma-separated string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_info(assets="XBT,ETH,USD", aclass="currency")

        assert isinstance(request, GetAssetInfoRequest)
        assert request.asset == "XBT,ETH,USD"
        assert response is mock_response

    def test_asset_info_with_asset_list(self):
        """Test asset_info with assets as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_info(assets=["XBT", "ETH", "USD"], aclass="currency")

        assert isinstance(request, GetAssetInfoRequest)
        # List gets normalized to comma-separated string, order preserved with duplicates removed
        assert set(request.asset.split(",")) == {"XBT", "ETH", "USD"}
        assert response is mock_response

    def test_asset_info_with_aclass_currency(self):
        """Test asset_info with aclass parameter set to currency"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_info(assets="XBT", aclass="currency")

        assert isinstance(request, GetAssetInfoRequest)
        assert request.aclass == "currency"
        assert response is mock_response

    def test_asset_info_with_aclass_tokenized_asset(self):
        """Test asset_info with aclass parameter set to tokenized_asset"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_info(assets="XBT", aclass="tokenized_asset")

        assert isinstance(request, GetAssetInfoRequest)
        assert request.aclass == "tokenized_asset"
        assert response is mock_response

    def test_asset_info_all_parameters(self):
        """Test asset_info with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetInfoResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_info(assets=["XBT", "ETH"], aclass="currency")

        assert isinstance(request, GetAssetInfoRequest)
        assert set(request.asset.split(",")) == {"XBT", "ETH"}
        assert request.aclass == "currency"
        assert response is mock_response


class TestMarketChannelAssetPairs:
    """Tests for asset_pairs method"""

    def test_asset_pairs_no_parameters(self):
        """Test asset_pairs with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs()

        assert isinstance(request, GetAssetPairsRequest)
        assert request.pair is None
        assert request.aclass_base is None
        assert request.info is None
        assert request.country_code is None
        assert response is mock_response

    def test_asset_pairs_with_single_pair_string(self):
        """Test asset_pairs with single pair as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(assets="XBTUSD")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.pair == "XBTUSD"
        assert response is mock_response

    def test_asset_pairs_with_multiple_pairs_list(self):
        """Test asset_pairs with multiple pairs as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(assets=["XBTUSD", "ETHUSD"])

        assert isinstance(request, GetAssetPairsRequest)
        assert response is mock_response

    def test_asset_pairs_with_aclass_currency(self):
        """Test asset_pairs with aclass parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(aclass="currency")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.aclass_base == "currency"
        assert response is mock_response

    def test_asset_pairs_with_aclass_tokenized_asset(self):
        """Test asset_pairs with aclass tokenized_asset"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(aclass="tokenized_asset")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.aclass_base == "tokenized_asset"
        assert response is mock_response

    def test_asset_pairs_with_info_parameter_info(self):
        """Test asset_pairs with info='info'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(info="info")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.info == "info"
        assert response is mock_response

    def test_asset_pairs_with_info_parameter_leverage(self):
        """Test asset_pairs with info='leverage'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(info="leverage")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.info == "leverage"
        assert response is mock_response

    def test_asset_pairs_with_info_parameter_fees(self):
        """Test asset_pairs with info='fees'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(info="fees")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.info == "fees"
        assert response is mock_response

    def test_asset_pairs_with_info_parameter_margin(self):
        """Test asset_pairs with info='margin'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(info="margin")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.info == "margin"
        assert response is mock_response

    def test_asset_pairs_with_country_code(self):
        """Test asset_pairs with country parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(country="US")

        assert isinstance(request, GetAssetPairsRequest)
        assert request.country_code == "US"
        assert response is mock_response

    def test_asset_pairs_all_parameters(self):
        """Test asset_pairs with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAssetPairsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.asset_pairs(
            assets=["XBTUSD", "ETHUSD"],
            aclass="currency",
            info="fees",
            country="US",
        )

        assert isinstance(request, GetAssetPairsRequest)
        assert request.aclass_base == "currency"
        assert request.info == "fees"
        assert request.country_code == "US"
        assert response is mock_response


class TestMarketChannelTicker:
    """Tests for ticker method"""

    def test_ticker_no_parameters(self):
        """Test ticker with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker()

        assert isinstance(request, GetTickerInformationRequest)
        assert request.pair is None
        assert request.asset_class is None
        assert response is mock_response

    def test_ticker_with_single_pair_string(self):
        """Test ticker with single pair as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker(pairs="XBTUSD")

        assert isinstance(request, GetTickerInformationRequest)
        assert request.pair == "XBTUSD"
        assert response is mock_response

    def test_ticker_with_multiple_pairs_string(self):
        """Test ticker with multiple pairs as comma-separated string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker(pairs="XBTUSD,ETHUSD")

        assert isinstance(request, GetTickerInformationRequest)
        assert request.pair == "XBTUSD,ETHUSD"
        assert response is mock_response

    def test_ticker_with_pairs_list(self):
        """Test ticker with pairs as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker(pairs=["XBTUSD", "ETHUSD"])

        assert isinstance(request, GetTickerInformationRequest)
        assert response is mock_response

    def test_ticker_with_aclass_tokenized_asset(self):
        """Test ticker with asset_class='tokenized_asset'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker(aclass="tokenized_asset")

        assert isinstance(request, GetTickerInformationRequest)
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response

    def test_ticker_with_aclass_forex(self):
        """Test ticker with asset_class='forex'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker(aclass="forex")

        assert isinstance(request, GetTickerInformationRequest)
        assert request.asset_class == "forex"
        assert response is mock_response

    def test_ticker_all_parameters(self):
        """Test ticker with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTickerInformationResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ticker(pairs=["XBTUSD"], aclass="forex")

        assert isinstance(request, GetTickerInformationRequest)
        assert request.asset_class == "forex"
        assert response is mock_response


class TestMarketChannelOHLC:
    """Tests for ohlc method"""

    def test_ohlc_minimal_parameters(self):
        """Test ohlc with only required pair parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD")

        assert isinstance(request, GetOHLCDataRequest)
        assert request.pair == "XBTUSD"
        assert request.interval is None
        assert request.since is None
        assert request.asset_class is None
        assert response is mock_response

    def test_ohlc_with_interval_1(self):
        """Test ohlc with interval=1"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=1)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 1
        assert response is mock_response

    def test_ohlc_with_interval_5(self):
        """Test ohlc with interval=5"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=5)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 5
        assert response is mock_response

    def test_ohlc_with_interval_15(self):
        """Test ohlc with interval=15"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=15)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 15
        assert response is mock_response

    def test_ohlc_with_interval_30(self):
        """Test ohlc with interval=30"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=30)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 30
        assert response is mock_response

    def test_ohlc_with_interval_60(self):
        """Test ohlc with interval=60"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=60)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 60
        assert response is mock_response

    def test_ohlc_with_interval_240(self):
        """Test ohlc with interval=240"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=240)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 240
        assert response is mock_response

    def test_ohlc_with_interval_1440(self):
        """Test ohlc with interval=1440 (daily)"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=1440)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 1440
        assert response is mock_response

    def test_ohlc_with_interval_10080(self):
        """Test ohlc with interval=10080 (weekly)"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=10080)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 10080
        assert response is mock_response

    def test_ohlc_with_interval_21600(self):
        """Test ohlc with interval=21600"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", interval=21600)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.interval == 21600
        assert response is mock_response

    def test_ohlc_with_since_parameter(self):
        """Test ohlc with since parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", since=1609459200)

        assert isinstance(request, GetOHLCDataRequest)
        assert request.since == 1609459200
        assert response is mock_response

    def test_ohlc_with_aclass_tokenized_asset(self):
        """Test ohlc with aclass='tokenized_asset'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(pair="XBTUSD", aclass="tokenized_asset")

        assert isinstance(request, GetOHLCDataRequest)
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response

    def test_ohlc_all_parameters(self):
        """Test ohlc with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOHLCDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.ohlc(
            pair="XBTUSD", interval=60, since=1609459200, aclass="tokenized_asset"
        )

        assert isinstance(request, GetOHLCDataRequest)
        assert request.pair == "XBTUSD"
        assert request.interval == 60
        assert request.since == 1609459200
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response


class TestMarketChannelOrderBook:
    """Tests for order_book method"""

    def test_order_book_minimal_parameters(self):
        """Test order_book with only required pair parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOrderBookResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.order_book(pair="XBTUSD")

        assert isinstance(request, GetOrderBookRequest)
        assert request.pair == "XBTUSD"
        assert request.count is None
        assert request.asset_class is None
        assert response is mock_response

    def test_order_book_with_count(self):
        """Test order_book with count parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOrderBookResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.order_book(pair="XBTUSD", count=10)

        assert isinstance(request, GetOrderBookRequest)
        assert request.count == 10
        assert response is mock_response

    def test_order_book_with_count_100(self):
        """Test order_book with count=100"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOrderBookResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.order_book(pair="XBTUSD", count=100)

        assert isinstance(request, GetOrderBookRequest)
        assert request.count == 100
        assert response is mock_response

    def test_order_book_with_aclass_tokenized_asset(self):
        """Test order_book with aclass='tokenized_asset'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOrderBookResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.order_book(pair="XBTUSD", aclass="tokenized_asset")

        assert isinstance(request, GetOrderBookRequest)
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response

    def test_order_book_all_parameters(self):
        """Test order_book with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOrderBookResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.order_book(pair="XBTUSD", count=50, aclass="tokenized_asset")

        assert isinstance(request, GetOrderBookRequest)
        assert request.pair == "XBTUSD"
        assert request.count == 50
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response


class TestMarketChannelRecentTrades:
    """Tests for recent_trades method"""

    def test_recent_trades_minimal_parameters(self):
        """Test recent_trades with only required pair parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentTradesResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_trades(pair="XBTUSD")

        assert isinstance(request, GetRecentTradesRequest)
        assert request.pair == "XBTUSD"
        assert request.since is None
        assert request.count is None
        assert request.asset_class is None
        assert response is mock_response

    def test_recent_trades_with_since(self):
        """Test recent_trades with since parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentTradesResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_trades(pair="XBTUSD", since="1609459200")

        assert isinstance(request, GetRecentTradesRequest)
        assert request.since == "1609459200"
        assert response is mock_response

    def test_recent_trades_with_count(self):
        """Test recent_trades with count parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentTradesResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_trades(pair="XBTUSD", count=100)

        assert isinstance(request, GetRecentTradesRequest)
        assert request.count == 100
        assert response is mock_response

    def test_recent_trades_with_aclass_tokenized_asset(self):
        """Test recent_trades with aclass='tokenized_asset'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentTradesResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_trades(pair="XBTUSD", aclass="tokenized_asset")

        assert isinstance(request, GetRecentTradesRequest)
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response

    def test_recent_trades_all_parameters(self):
        """Test recent_trades with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentTradesResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_trades(
            pair="XBTUSD", since="1609459200", count=100, aclass="tokenized_asset"
        )

        assert isinstance(request, GetRecentTradesRequest)
        assert request.pair == "XBTUSD"
        assert request.since == "1609459200"
        assert request.count == 100
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response


class TestMarketChannelRecentSpreads:
    """Tests for recent_spreads method"""

    def test_recent_spreads_minimal_parameters(self):
        """Test recent_spreads with only required pair parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentSpreadsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_spreads(pair="XBTUSD")

        assert isinstance(request, GetRecentSpreadsRequest)
        assert request.pair == "XBTUSD"
        assert request.since is None
        assert request.asset_class is None
        assert response is mock_response

    def test_recent_spreads_with_since(self):
        """Test recent_spreads with since parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentSpreadsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_spreads(pair="XBTUSD", since="1609459200")

        assert isinstance(request, GetRecentSpreadsRequest)
        # since gets converted to int
        assert request.since == 1609459200
        assert response is mock_response

    def test_recent_spreads_with_aclass_tokenized_asset(self):
        """Test recent_spreads with aclass='tokenized_asset'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentSpreadsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_spreads(pair="XBTUSD", aclass="tokenized_asset")

        assert isinstance(request, GetRecentSpreadsRequest)
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response

    def test_recent_spreads_all_parameters(self):
        """Test recent_spreads with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetRecentSpreadsResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.recent_spreads(
            pair="XBTUSD", since="1609459200", aclass="tokenized_asset"
        )

        assert isinstance(request, GetRecentSpreadsRequest)
        assert request.pair == "XBTUSD"
        # since gets converted to int
        assert request.since == 1609459200
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response


class TestTradingChannelInitialization:
    """Tests for TradingChannel initialization"""

    def test_init_with_client(self):
        """Test TradingChannel initialization with a client"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = TradingChannel(mock_client)

        assert channel.client is mock_client
        assert channel.channel == "trading"
        assert channel.private is True

    def test_path_property(self):
        """Test that path property returns correct private path"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = TradingChannel(mock_client)

        assert channel.path == "/0/private/"


class TestTradingChannelAddOrder:
    """Tests for add_order method"""

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_minimal_market_order(self, mock_uuid):
        """Test add_order with minimal parameters for market order"""
        mock_uuid.return_value = "test-uuid-123"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="XBTUSD", otype="market", direction="buy", price=50000, volume=1.5
        )

        assert isinstance(request, AddOrderRequest)
        assert request.pair == "XBTUSD"
        assert request.ordertype == "market"
        assert request.type == "buy"
        assert request.price == "50000"
        assert request.volume == "1.5"
        assert request.cl_ord_id == "test-uuid-123"
        assert response is mock_response

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_limit_order(self, mock_uuid):
        """Test add_order with limit order"""
        mock_uuid.return_value = "test-uuid-456"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="ETHUSD", otype="limit", direction="sell", price=3000.50, volume=2.0
        )

        assert isinstance(request, AddOrderRequest)
        assert request.pair == "ETHUSD"
        assert request.ordertype == "limit"
        assert request.type == "sell"
        assert request.price == "3000.5"
        assert request.volume == "2.0"

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_with_leverage(self, mock_uuid):
        """Test add_order with leverage parameter"""
        mock_uuid.return_value = "test-uuid-789"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="XBTUSD",
            otype="market",
            direction="buy",
            price=50000,
            volume=1.0,
            leverage=5,
        )

        assert isinstance(request, AddOrderRequest)
        assert request.leverage == "5"

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_with_tuple_price(self, mock_uuid):
        """Test add_order with tuple price (stop-loss-limit order)"""
        mock_uuid.return_value = "test-uuid-abc"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="XBTUSD",
            otype="stop-loss-limit",
            direction="sell",
            price=(45000, 44500),
            volume=1.0,
        )

        assert isinstance(request, AddOrderRequest)
        assert request.price == "45000"
        assert request.price2 == "44500"

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_iceberg_with_displayvol(self, mock_uuid):
        """Test add_order for iceberg order with automatic displayvol"""
        mock_uuid.return_value = "test-uuid-def"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="XBTUSD", otype="iceberg", direction="buy", price=50000, volume=10.0
        )

        assert isinstance(request, AddOrderRequest)
        assert request.ordertype == "iceberg"
        # For iceberg orders, displayvol should default to volume if not specified
        assert request.displayvol == "10.0"

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_with_custom_cl_ord_id(self, mock_uuid):
        """Test add_order with custom client order ID"""
        mock_uuid.return_value = "should-not-be-used"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="XBTUSD",
            otype="market",
            direction="buy",
            price=50000,
            volume=1.0,
            cl_ord_id="my-custom-id-123",
        )

        assert isinstance(request, AddOrderRequest)
        assert request.cl_ord_id == "my-custom-id-123"

    @patch("kraken.rest.channels.trading.rand_uuid")
    def test_add_order_with_kwargs(self, mock_uuid):
        """Test add_order with additional kwargs"""
        mock_uuid.return_value = "test-uuid"
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AddOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.add_order(
            pair="XBTUSD",
            otype="limit",
            direction="buy",
            price=50000,
            volume=1.0,
            oflags="post",
            timeinforce="GTC",
        )

        assert isinstance(request, AddOrderRequest)
        assert request.oflags == "post"
        assert request.timeinforce == "GTC"


class TestTradingChannelAmendOrder:
    """Tests for amend_order method"""

    def test_amend_order_with_txid(self):
        """Test amend_order using txid"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.amend_order(
            txid_or_uuid="ABC123-DEF45-GHI678", pair="XBTUSD", quantity=2.0
        )

        assert isinstance(request, AmendOrderRequest)
        assert request.txid == "ABC123-DEF45-GHI678"
        assert request.cl_ord_id is None
        assert request.pair == "XBTUSD"
        assert request.order_qty == "2.0"
        assert response is mock_response

    def test_amend_order_with_uuid(self):
        """Test amend_order using UUID"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        request, response = channel.amend_order(txid_or_uuid=uuid, pair="ETHUSD", quantity=3.0)

        assert isinstance(request, AmendOrderRequest)
        assert request.txid is None
        assert request.cl_ord_id == uuid
        assert request.pair == "ETHUSD"
        assert request.order_qty == "3.0"

    def test_amend_order_with_limit_price(self):
        """Test amend_order with limit price"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.amend_order(
            txid_or_uuid="ABC123-DEF45-GHI678",
            pair="XBTUSD",
            quantity=2.0,
            limit=51000.0,
        )

        assert isinstance(request, AmendOrderRequest)
        assert request.limit_price == "51000.0"
        assert request.order_qty == "2.0"

    def test_amend_order_with_trigger_price(self):
        """Test amend_order with trigger price"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.amend_order(
            txid_or_uuid="ABC123-DEF45-GHI678",
            pair="XBTUSD",
            quantity=2.0,
            trigger=48000.0,
        )

        assert isinstance(request, AmendOrderRequest)
        assert request.trigger_price == "48000.0"

    def test_amend_order_with_deadline(self):
        """Test amend_order with deadline"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        deadline = "2024-01-01T12:00:00Z"
        request, response = channel.amend_order(
            txid_or_uuid="ABC123-DEF45-GHI678",
            pair="XBTUSD",
            quantity=2.0,
            deadline=deadline,
        )

        assert isinstance(request, AmendOrderRequest)
        # deadline gets auto-generated if provided as a string, so just verify it exists
        assert request.deadline is not None

    def test_amend_order_all_parameters(self):
        """Test amend_order with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        deadline = "2024-01-01T12:00:00Z"
        request, response = channel.amend_order(
            txid_or_uuid="ABC123-DEF45-GHI678",
            pair="XBTUSD",
            quantity=2.5,
            limit=52000.0,
            trigger=48000.0,
            deadline=deadline,
        )

        assert isinstance(request, AmendOrderRequest)
        assert request.txid == "ABC123-DEF45-GHI678"
        assert request.pair == "XBTUSD"
        assert request.order_qty == "2.5"
        assert request.limit_price == "52000.0"
        assert request.trigger_price == "48000.0"
        # deadline gets auto-generated if provided as a string, so just verify it exists
        assert request.deadline is not None

    def test_amend_order_with_kwargs(self):
        """Test amend_order with additional kwargs"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AmendOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.amend_order(
            txid_or_uuid="ABC123-DEF45-GHI678",
            pair="XBTUSD",
            quantity=2.0,
            post_only=True,
        )

        assert isinstance(request, AmendOrderRequest)
        assert request.post_only is True


class TestTradingChannelCancelOrder:
    """Tests for cancel_order method"""

    def test_cancel_order_with_txid(self):
        """Test cancel_order using txid"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.cancel_order(txid_or_uuid="ABC123-DEF45-GHI678")

        assert isinstance(request, CancelOrderRequest)
        assert request.txid == "ABC123-DEF45-GHI678"
        assert request.cl_ord_id is None
        assert response is mock_response

    def test_cancel_order_with_uuid(self):
        """Test cancel_order using UUID"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        request, response = channel.cancel_order(txid_or_uuid=uuid)

        assert isinstance(request, CancelOrderRequest)
        assert request.txid is None
        assert request.cl_ord_id == uuid
        assert response is mock_response

    def test_cancel_order_returns_tuple(self):
        """Test that cancel_order returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        result = channel.cancel_order(txid_or_uuid="ABC123-DEF45-GHI678")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, CancelOrderRequest)
        assert response is mock_response


class TestTradingChannelCancelAllOrders:
    """Tests for cancel_all_orders method"""

    def test_cancel_all_orders_no_timeout(self):
        """Test cancel_all_orders without timeout"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.cancel_all_orders()

        assert isinstance(request, CancelAllRequest)
        assert request.timeout is None
        assert response is mock_response

    def test_cancel_all_orders_with_timeout(self):
        """Test cancel_all_orders with timeout parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.cancel_all_orders(timeout=60)

        assert isinstance(request, CancelAllRequest)
        assert request.timeout == 60
        assert response is mock_response

    def test_cancel_all_orders_with_timeout_zero(self):
        """Test cancel_all_orders with timeout=0"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.cancel_all_orders(timeout=0)

        assert isinstance(request, CancelAllRequest)
        assert request.timeout == 0
        assert response is mock_response

    def test_cancel_all_orders_returns_tuple(self):
        """Test that cancel_all_orders returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CancelOrderResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        result = channel.cancel_all_orders()

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, CancelAllRequest)
        assert response is mock_response


class TestTradingChannelGetWebSocketsToken:
    """Tests for get_websockets_token method"""

    def test_get_websockets_token_basic(self):
        """Test get_websockets_token method"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWebSocketsTokenResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, response = channel.get_websockets_token()

        assert isinstance(request, GetWebSocketsTokenRequest)
        assert response is mock_response

    def test_get_websockets_token_request_called(self):
        """Test that get_websockets_token calls client.request"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWebSocketsTokenResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        request, _ = channel.get_websockets_token()

        mock_client.request.assert_called_once()

    def test_get_websockets_token_returns_tuple(self):
        """Test that get_websockets_token returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWebSocketsTokenResponse)
        mock_client.request.return_value = mock_response

        channel = TradingChannel(mock_client)
        result = channel.get_websockets_token()

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, GetWebSocketsTokenRequest)
        assert response is mock_response
