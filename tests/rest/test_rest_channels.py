"""Unit tests for Kraken REST API Channels"""

from unittest.mock import MagicMock, patch

import pytest

from kraken.rest.channels import (
    AccountChannel,
    EarnChannel,
    FundingChannel,
    MarketChannel,
    TradingChannel,
)
from kraken.rest.client import KrakenRESTClient
from kraken.rest.schema.account import (
    AccountTransferRequest,
    AccountTransferResponse,
    CreateSubaccountRequest,
    CreateSubaccountResponse,
    DeleteExportRequest,
    DeleteExportResponse,
    GetBalanceRequest,
    GetBalanceResponse,
    GetClosedOrdersRequest,
    GetClosedOrdersResponse,
    GetExportStatusRequest,
    GetExportStatusResponse,
    GetExtendedBalanceRequest,
    GetExtendedBalanceResponse,
    GetLedgersRequest,
    GetLedgersResponse,
    GetOpenOrdersRequest,
    GetOpenOrdersResponse,
    GetOpenPositionsRequest,
    GetOpenPositionsResponse,
    GetOrderAmendsRequest,
    GetOrderAmendsResponse,
    GetTradeBalanceRequest,
    GetTradeBalanceResponse,
    GetTradesHistoryRequest,
    GetTradesHistoryResponse,
    GetTradeVolumeRequest,
    GetTradeVolumeResponse,
    QueryLedgersRequest,
    QueryLedgersResponse,
    QueryOrdersRequest,
    QueryOrdersResponse,
    QueryTradesRequest,
    QueryTradesResponse,
    RequestExportRequest,
    RequestExportResponse,
    RetrieveExportRequest,
    RetrieveExportResponse,
)
from kraken.rest.schema.earn import (
    AllocateEarnFundsRequest,
    AllocateEarnFundsResponse,
    DeallocateEarnFundsRequest,
    DeallocateEarnFundsResponse,
    GetAllocationStatusRequest,
    GetAllocationStatusResponse,
    GetDeallocationStatusRequest,
    GetDeallocationStatusResponse,
    ListEarnAllocationsRequest,
    ListEarnAllocationsResponse,
    ListEarnStrategiesRequest,
    ListEarnStrategiesResponse,
)
from kraken.rest.schema.funding import (
    GetDepositAddressesRequest,
    GetDepositAddressesResponse,
    GetDepositMethodsRequest,
    GetDepositMethodsResponse,
    GetDepositStatusRequest,
    GetDepositStatusResponse,
    GetWithdrawalAddressesRequest,
    GetWithdrawalAddressesResponse,
    GetWithdrawalInfoRequest,
    GetWithdrawalInfoResponse,
    GetWithdrawalMethodsRequest,
    GetWithdrawalMethodsResponse,
    GetWithdrawalStatusRequest,
    GetWithdrawalStatusResponse,
    RequestWalletTransferRequest,
    RequestWalletTransferResponse,
    RequestWithdrawalCancellationRequest,
    WithdrawCancelResponse,
    WithdrawFundsRequest,
    WithdrawFundsResponse,
)
from kraken.rest.schema.market import (
    GetAssetInfoRequest,
    GetAssetInfoResponse,
    GetAssetPairsRequest,
    GetAssetPairsResponse,
    GetOHLCDataRequest,
    GetOHLCDataResponse,
    GetOrderBookRequest,
    GetOrderBookResponse,
    GetPostTradeDataRequest,
    GetPostTradeDataResponse,
    GetPreTradeDataRequest,
    GetPreTradeDataResponse,
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


class TestMarketChannelPreTradeData:
    """Tests for pre_trade_data method"""

    def test_pre_trade_data_basic(self):
        """Test pre_trade_data with required symbol parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPreTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.pre_trade_data(symbol="BTC/USD")

        assert isinstance(request, GetPreTradeDataRequest)
        assert request.symbol == "BTC/USD"
        assert response is mock_response

    def test_pre_trade_data_with_eth_symbol(self):
        """Test pre_trade_data with ETH/USD symbol"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPreTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.pre_trade_data(symbol="ETH/USD")

        assert isinstance(request, GetPreTradeDataRequest)
        assert request.symbol == "ETH/USD"
        assert response is mock_response

    def test_pre_trade_data_returns_tuple(self):
        """Test that pre_trade_data returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPreTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        result = channel.pre_trade_data(symbol="BTC/USD")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, GetPreTradeDataRequest)
        assert response is mock_response

    def test_pre_trade_data_request_called_with_correct_schema(self):
        """Test that pre_trade_data calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPreTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, _ = channel.pre_trade_data(symbol="BTC/USD")

        mock_client.request.assert_called_once_with(request)


class TestMarketChannelPostTradeData:
    """Tests for post_trade_data method"""

    def test_post_trade_data_no_parameters(self):
        """Test post_trade_data with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data()

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.symbol is None
        assert request.from_ts is None
        assert request.to_ts is None
        assert request.count is None
        assert response is mock_response

    def test_post_trade_data_with_symbol(self):
        """Test post_trade_data with symbol parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data(symbol="BTC/USD")

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.symbol == "BTC/USD"
        assert response is mock_response

    def test_post_trade_data_with_from_ts(self):
        """Test post_trade_data with from_ts parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data(
            symbol="BTC/USD", from_ts="2024-05-30T12:34:56.1234567892Z"
        )

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.from_ts == "2024-05-30T12:34:56.1234567892Z"
        assert response is mock_response

    def test_post_trade_data_with_to_ts(self):
        """Test post_trade_data with to_ts parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data(
            symbol="BTC/USD", to_ts="2024-05-30T12:34:56.1234567892Z"
        )

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.to_ts == "2024-05-30T12:34:56.1234567892Z"
        assert response is mock_response

    def test_post_trade_data_with_count(self):
        """Test post_trade_data with count parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data(symbol="BTC/USD", count=100)

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.count == 100
        assert response is mock_response

    def test_post_trade_data_with_count_max(self):
        """Test post_trade_data with count=1000 (max)"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data(symbol="ETH/USD", count=1000)

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.count == 1000
        assert response is mock_response

    def test_post_trade_data_all_parameters(self):
        """Test post_trade_data with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, response = channel.post_trade_data(
            symbol="BTC/USD",
            from_ts="2024-05-30T12:00:00Z",
            to_ts="2024-05-30T18:00:00Z",
            count=500,
        )

        assert isinstance(request, GetPostTradeDataRequest)
        assert request.symbol == "BTC/USD"
        assert request.from_ts == "2024-05-30T12:00:00Z"
        assert request.to_ts == "2024-05-30T18:00:00Z"
        assert request.count == 500
        assert response is mock_response

    def test_post_trade_data_returns_tuple(self):
        """Test that post_trade_data returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        result = channel.post_trade_data()

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, GetPostTradeDataRequest)
        assert response is mock_response

    def test_post_trade_data_request_called_with_correct_schema(self):
        """Test that post_trade_data calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetPostTradeDataResponse)
        mock_client.request.return_value = mock_response

        channel = MarketChannel(mock_client)
        request, _ = channel.post_trade_data(symbol="BTC/USD")

        mock_client.request.assert_called_once_with(request)


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


# ============================================================================
# AccountChannel Tests
# ============================================================================


class TestAccountChannelInitialization:
    """Tests for AccountChannel initialization"""

    def test_init_with_client(self):
        """Test AccountChannel initialization with a client"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = AccountChannel(mock_client)

        assert channel.client is mock_client
        assert channel.channel == "account"
        assert channel.private is True

    def test_path_property(self):
        """Test that path property returns correct private path"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = AccountChannel(mock_client)

        assert channel.path == "/0/private/"


class TestAccountChannelGetBalance:
    """Tests for get_balance method"""

    def test_get_balance_no_parameters(self):
        """Test get_balance with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetBalanceResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_balance()

        assert isinstance(request, GetBalanceRequest)
        assert request.rebase_multiplier is None
        assert response is mock_response

    def test_get_balance_with_rebase_multiplier(self):
        """Test get_balance with rebase_multiplier parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetBalanceResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_balance(rebase_multiplier="base")

        assert isinstance(request, GetBalanceRequest)
        assert request.rebase_multiplier == "base"
        assert response is mock_response


class TestAccountChannelGetExtendedBalance:
    """Tests for get_extended_balance method"""

    def test_get_extended_balance_no_parameters(self):
        """Test get_extended_balance with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetExtendedBalanceResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_extended_balance()

        assert isinstance(request, GetExtendedBalanceRequest)
        assert request.rebase_multiplier is None
        assert response is mock_response


class TestAccountChannelGetTradeBalance:
    """Tests for get_trade_balance method"""

    def test_get_trade_balance_no_parameters(self):
        """Test get_trade_balance with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradeBalanceResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trade_balance()

        assert isinstance(request, GetTradeBalanceRequest)
        assert request.asset is None
        assert request.rebase_multiplier is None
        assert response is mock_response

    def test_get_trade_balance_with_asset(self):
        """Test get_trade_balance with asset parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradeBalanceResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trade_balance(asset="ZUSD")

        assert isinstance(request, GetTradeBalanceRequest)
        assert request.asset == "ZUSD"
        assert response is mock_response


class TestAccountChannelGetOpenOrders:
    """Tests for get_open_orders method"""

    def test_get_open_orders_no_parameters(self):
        """Test get_open_orders with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_orders()

        assert isinstance(request, GetOpenOrdersRequest)
        assert request.trades is False
        assert request.userref is None
        assert request.cl_ord_id is None
        assert response is mock_response

    def test_get_open_orders_with_trades(self):
        """Test get_open_orders with trades=True"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_orders(trades=True)

        assert isinstance(request, GetOpenOrdersRequest)
        assert request.trades is True
        assert response is mock_response

    def test_get_open_orders_with_userref(self):
        """Test get_open_orders with userref"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_orders(userref=12345)

        assert isinstance(request, GetOpenOrdersRequest)
        assert request.userref == 12345
        assert response is mock_response

    def test_get_open_orders_with_cl_ord_id_string(self):
        """Test get_open_orders with cl_ord_id as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_orders(cl_ord_id="order-123")

        assert isinstance(request, GetOpenOrdersRequest)
        assert request.cl_ord_id == "order-123"
        assert response is mock_response

    def test_get_open_orders_with_cl_ord_id_list(self):
        """Test get_open_orders with cl_ord_id as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_orders(cl_ord_id=["order-1", "order-2"])

        assert isinstance(request, GetOpenOrdersRequest)
        # List gets converted to comma-separated string
        assert request.cl_ord_id == "order-1,order-2"
        assert response is mock_response


class TestAccountChannelGetClosedOrders:
    """Tests for get_closed_orders method"""

    def test_get_closed_orders_no_parameters(self):
        """Test get_closed_orders with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetClosedOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_closed_orders()

        assert isinstance(request, GetClosedOrdersRequest)
        assert request.trades is False
        assert request.start is None
        assert request.end is None
        assert response is mock_response

    def test_get_closed_orders_with_timestamp_range(self):
        """Test get_closed_orders with start and end timestamps"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetClosedOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_closed_orders(start=1609459200, end=1612137600)

        assert isinstance(request, GetClosedOrdersRequest)
        assert request.start == 1609459200
        assert request.end == 1612137600
        assert response is mock_response

    def test_get_closed_orders_with_pagination(self):
        """Test get_closed_orders with pagination offset"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetClosedOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_closed_orders(ofs=50)

        assert isinstance(request, GetClosedOrdersRequest)
        assert request.ofs == 50
        assert response is mock_response

    def test_get_closed_orders_with_closetime(self):
        """Test get_closed_orders with closetime parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetClosedOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_closed_orders(closetime="both")

        assert isinstance(request, GetClosedOrdersRequest)
        assert request.closetime == "both"
        assert response is mock_response


class TestAccountChannelQueryOrders:
    """Tests for query_orders method"""

    def test_query_orders_with_single_txid_string(self):
        """Test query_orders with single txid as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=QueryOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.query_orders(txid="OQCLML-BW3P3-BUCMWZ")

        assert isinstance(request, QueryOrdersRequest)
        assert request.txid == "OQCLML-BW3P3-BUCMWZ"
        assert response is mock_response

    def test_query_orders_with_txid_list(self):
        """Test query_orders with txid as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=QueryOrdersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.query_orders(txid=["ORDER1", "ORDER2"])

        assert isinstance(request, QueryOrdersRequest)
        # List gets converted to comma-separated string
        assert request.txid == "ORDER1,ORDER2"
        assert response is mock_response


class TestAccountChannelGetOrderAmends:
    """Tests for get_order_amends method"""

    def test_get_order_amends_basic(self):
        """Test get_order_amends with order_id"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOrderAmendsResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_order_amends(order_id="OQCLML-BW3P3-BUCMWZ")

        assert isinstance(request, GetOrderAmendsRequest)
        assert request.order_id == "OQCLML-BW3P3-BUCMWZ"
        assert response is mock_response


class TestAccountChannelGetTradesHistory:
    """Tests for get_trades_history method"""

    def test_get_trades_history_no_parameters(self):
        """Test get_trades_history with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradesHistoryResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trades_history()

        assert isinstance(request, GetTradesHistoryRequest)
        assert request.type is None
        assert request.start is None
        assert request.end is None
        assert response is mock_response

    def test_get_trades_history_with_type(self):
        """Test get_trades_history with type parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradesHistoryResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trades_history(type="all")

        assert isinstance(request, GetTradesHistoryRequest)
        assert request.type == "all"
        assert response is mock_response

    def test_get_trades_history_with_ledgers(self):
        """Test get_trades_history with ledgers=True"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradesHistoryResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trades_history(ledgers=True)

        assert isinstance(request, GetTradesHistoryRequest)
        assert request.ledgers is True
        assert response is mock_response


class TestAccountChannelQueryTrades:
    """Tests for query_trades method"""

    def test_query_trades_with_single_txid(self):
        """Test query_trades with single txid"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=QueryTradesResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.query_trades(txid="THVRQM-33VKH-UCI7BS")

        assert isinstance(request, QueryTradesRequest)
        assert request.txid == "THVRQM-33VKH-UCI7BS"
        assert response is mock_response

    def test_query_trades_with_txid_list(self):
        """Test query_trades with txid as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=QueryTradesResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.query_trades(txid=["TRADE1", "TRADE2"])

        assert isinstance(request, QueryTradesRequest)
        assert request.txid == "TRADE1,TRADE2"
        assert response is mock_response


class TestAccountChannelGetOpenPositions:
    """Tests for get_open_positions method"""

    def test_get_open_positions_no_parameters(self):
        """Test get_open_positions with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenPositionsResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_positions()

        assert isinstance(request, GetOpenPositionsRequest)
        assert request.txid is None
        assert request.docalcs is False
        assert request.consolidation is None
        assert response is mock_response

    def test_get_open_positions_with_docalcs(self):
        """Test get_open_positions with docalcs=True"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenPositionsResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_positions(docalcs=True)

        assert isinstance(request, GetOpenPositionsRequest)
        assert request.docalcs is True
        assert response is mock_response

    def test_get_open_positions_with_consolidation(self):
        """Test get_open_positions with consolidation parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetOpenPositionsResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_open_positions(consolidation="market")

        assert isinstance(request, GetOpenPositionsRequest)
        assert request.consolidation == "market"
        assert response is mock_response


class TestAccountChannelGetLedgers:
    """Tests for get_ledgers method"""

    def test_get_ledgers_no_parameters(self):
        """Test get_ledgers with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetLedgersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_ledgers()

        assert isinstance(request, GetLedgersRequest)
        assert request.asset is None
        assert request.type is None
        assert response is mock_response

    def test_get_ledgers_with_asset_string(self):
        """Test get_ledgers with asset as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetLedgersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_ledgers(asset="XXBT")

        assert isinstance(request, GetLedgersRequest)
        assert request.asset == "XXBT"
        assert response is mock_response

    def test_get_ledgers_with_asset_list(self):
        """Test get_ledgers with asset as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetLedgersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_ledgers(asset=["XXBT", "ZUSD"])

        assert isinstance(request, GetLedgersRequest)
        assert request.asset == "XXBT,ZUSD"
        assert response is mock_response

    def test_get_ledgers_with_type(self):
        """Test get_ledgers with type parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetLedgersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_ledgers(type="deposit")

        assert isinstance(request, GetLedgersRequest)
        assert request.type == "deposit"
        assert response is mock_response


class TestAccountChannelQueryLedgers:
    """Tests for query_ledgers method"""

    def test_query_ledgers_with_single_id(self):
        """Test query_ledgers with single id"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=QueryLedgersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.query_ledgers(id="LQFCFM-ELBSU-CMH5EI")

        assert isinstance(request, QueryLedgersRequest)
        assert request.id == "LQFCFM-ELBSU-CMH5EI"
        assert response is mock_response

    def test_query_ledgers_with_id_list(self):
        """Test query_ledgers with id as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=QueryLedgersResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.query_ledgers(id=["LEDGER1", "LEDGER2"])

        assert isinstance(request, QueryLedgersRequest)
        assert request.id == "LEDGER1,LEDGER2"
        assert response is mock_response


class TestAccountChannelGetTradeVolume:
    """Tests for get_trade_volume method"""

    def test_get_trade_volume_no_parameters(self):
        """Test get_trade_volume with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradeVolumeResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trade_volume()

        assert isinstance(request, GetTradeVolumeRequest)
        assert request.pair is None
        assert response is mock_response

    def test_get_trade_volume_with_single_pair(self):
        """Test get_trade_volume with single pair"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradeVolumeResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trade_volume(pair="XXBTZUSD")

        assert isinstance(request, GetTradeVolumeRequest)
        assert request.pair == "XXBTZUSD"
        assert response is mock_response

    def test_get_trade_volume_with_pair_list(self):
        """Test get_trade_volume with pair as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetTradeVolumeResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_trade_volume(pair=["XXBTZUSD", "XETHZUSD"])

        assert isinstance(request, GetTradeVolumeRequest)
        assert request.pair == "XXBTZUSD,XETHZUSD"
        assert response is mock_response


class TestAccountChannelRequestExport:
    """Tests for request_export method"""

    def test_request_export_minimal_parameters(self):
        """Test request_export with minimal parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.request_export(report="trades", description="Q1 2024 trades")

        assert isinstance(request, RequestExportRequest)
        assert request.report == "trades"
        assert request.description == "Q1 2024 trades"
        assert request.format == "CSV"  # default
        assert response is mock_response

    def test_request_export_with_tsv_format(self):
        """Test request_export with TSV format"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.request_export(
            report="ledgers", description="Ledger export", format="TSV"
        )

        assert isinstance(request, RequestExportRequest)
        assert request.format == "TSV"
        assert response is mock_response

    def test_request_export_with_timestamps(self):
        """Test request_export with start and end timestamps"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.request_export(
            report="trades",
            description="Date range export",
            starttm=1609459200,
            endtm=1612137600,
        )

        assert isinstance(request, RequestExportRequest)
        assert request.starttm == 1609459200
        assert request.endtm == 1612137600
        assert response is mock_response

    def test_request_export_with_fields_list(self):
        """Test request_export with fields as list"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.request_export(
            report="trades",
            description="Custom fields",
            fields=["ordertxid", "time", "pair", "price"],
        )

        assert isinstance(request, RequestExportRequest)
        # List gets converted to comma-separated string
        assert request.fields == "ordertxid,time,pair,price"
        assert response is mock_response


class TestAccountChannelGetExportStatus:
    """Tests for get_export_status method"""

    def test_get_export_status_trades(self):
        """Test get_export_status for trades"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetExportStatusResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_export_status(report="trades")

        assert isinstance(request, GetExportStatusRequest)
        assert request.report == "trades"
        assert response is mock_response

    def test_get_export_status_ledgers(self):
        """Test get_export_status for ledgers"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetExportStatusResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.get_export_status(report="ledgers")

        assert isinstance(request, GetExportStatusRequest)
        assert request.report == "ledgers"
        assert response is mock_response


class TestAccountChannelRetrieveExport:
    """Tests for retrieve_export method"""

    def test_retrieve_export_basic(self):
        """Test retrieve_export with export id"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RetrieveExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.retrieve_export(id="TCJA")

        assert isinstance(request, RetrieveExportRequest)
        assert request.id == "TCJA"
        assert response is mock_response


class TestAccountChannelDeleteExport:
    """Tests for delete_export method"""

    def test_delete_export_with_delete_type(self):
        """Test delete_export with type='delete'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeleteExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.delete_export(id="TCJA", type="delete")

        assert isinstance(request, DeleteExportRequest)
        assert request.id == "TCJA"
        assert request.type == "delete"
        assert response is mock_response

    def test_delete_export_with_cancel_type(self):
        """Test delete_export with type='cancel'"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeleteExportResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.delete_export(id="TCJB", type="cancel")

        assert isinstance(request, DeleteExportRequest)
        assert request.id == "TCJB"
        assert request.type == "cancel"
        assert response is mock_response


class TestAccountChannelCreateSubaccount:
    """Tests for create_subaccount method"""

    def test_create_subaccount_with_valid_parameters(self):
        """Test create_subaccount with valid parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CreateSubaccountResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.create_subaccount(
            username="subaccount1", email="sub@example.com"
        )

        assert isinstance(request, CreateSubaccountRequest)
        assert request.username == "subaccount1"
        assert request.email == "sub@example.com"
        assert response is mock_response

    def test_create_subaccount_returns_tuple(self):
        """Test that create_subaccount returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=CreateSubaccountResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        result = channel.create_subaccount(username="test", email="test@example.com")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, CreateSubaccountRequest)
        assert response is mock_response


class TestAccountChannelAccountTransfer:
    """Tests for account_transfer method"""

    def test_account_transfer_minimal_parameters(self):
        """Test account_transfer with required parameters only"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AccountTransferResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.account_transfer(
            asset="XBT",
            amount="2.54",
            from_account="ABCD 1234 EFGH 5678",
            to_account="IJKL 0987 MNOP 6543",
        )

        assert isinstance(request, AccountTransferRequest)
        assert request.asset == "XBT"
        assert request.amount == "2.54"
        assert request.from_account == "ABCD 1234 EFGH 5678"
        assert request.to_account == "IJKL 0987 MNOP 6543"
        assert request.asset_class == "currency"
        assert response is mock_response

    def test_account_transfer_with_float_amount(self):
        """Test account_transfer with float amount (gets converted to string)"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AccountTransferResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.account_transfer(
            asset="ZUSD",
            amount=1000.50,
            from_account="ABCD",
            to_account="EFGH",
        )

        assert isinstance(request, AccountTransferRequest)
        assert request.amount == "1000.5"
        assert response is mock_response

    def test_account_transfer_with_tokenized_asset_class(self):
        """Test account_transfer with tokenized_asset asset class"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AccountTransferResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        request, response = channel.account_transfer(
            asset="AAPL",
            amount="10",
            from_account="ABCD",
            to_account="EFGH",
            asset_class="tokenized_asset",
        )

        assert isinstance(request, AccountTransferRequest)
        assert request.asset_class == "tokenized_asset"
        assert response is mock_response

    def test_account_transfer_returns_tuple(self):
        """Test that account_transfer returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AccountTransferResponse)
        mock_client.request.return_value = mock_response

        channel = AccountChannel(mock_client)
        result = channel.account_transfer(
            asset="XBT", amount="1", from_account="A", to_account="B"
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, AccountTransferRequest)
        assert response is mock_response


# ============================================================================
# FundingChannel Tests
# ============================================================================


class TestFundingChannelInitialization:
    """Tests for FundingChannel initialization"""

    def test_init_with_client(self):
        """Test FundingChannel initialization with a client"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = FundingChannel(mock_client)

        assert channel.client is mock_client
        assert channel.channel == "funding"
        assert channel.private is True

    def test_path_property(self):
        """Test that path property returns correct private path"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = FundingChannel(mock_client)

        assert channel.path == "/0/private/"


class TestFundingChannelGetDepositMethods:
    """Tests for get_deposit_methods method"""

    def test_get_deposit_methods_with_asset(self):
        """Test get_deposit_methods with required asset parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositMethodsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_methods(asset="XBT")

        assert isinstance(request, GetDepositMethodsRequest)
        assert request.asset == "XBT"
        assert request.aclass is None
        assert response is mock_response

    def test_get_deposit_methods_with_aclass(self):
        """Test get_deposit_methods with aclass parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositMethodsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_methods(asset="XBT", aclass="currency")

        assert isinstance(request, GetDepositMethodsRequest)
        assert request.asset == "XBT"
        assert request.aclass == "currency"
        assert response is mock_response

    def test_get_deposit_methods_returns_tuple(self):
        """Test that get_deposit_methods returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositMethodsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        result = channel.get_deposit_methods(asset="XBT")

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestFundingChannelGetDepositAddresses:
    """Tests for get_deposit_addresses method"""

    def test_get_deposit_addresses_minimal_parameters(self):
        """Test get_deposit_addresses with required parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_addresses(asset="XBT", method="Bitcoin")

        assert isinstance(request, GetDepositAddressesRequest)
        assert request.asset == "XBT"
        assert request.method == "Bitcoin"
        assert request.new is False
        assert request.amount is None
        assert response is mock_response

    def test_get_deposit_addresses_with_new_true(self):
        """Test get_deposit_addresses with new=True"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_addresses(asset="XBT", method="Bitcoin", new=True)

        assert isinstance(request, GetDepositAddressesRequest)
        assert request.new is True
        assert response is mock_response

    def test_get_deposit_addresses_with_amount(self):
        """Test get_deposit_addresses with amount for Lightning"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_addresses(
            asset="XBT", method="Bitcoin Lightning", amount="0.001"
        )

        assert isinstance(request, GetDepositAddressesRequest)
        assert request.amount == "0.001"
        assert response is mock_response

    def test_get_deposit_addresses_all_parameters(self):
        """Test get_deposit_addresses with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_addresses(
            asset="XBT",
            method="Bitcoin",
            new=True,
            amount="0.5",
            aclass="currency",
        )

        assert isinstance(request, GetDepositAddressesRequest)
        assert request.asset == "XBT"
        assert request.method == "Bitcoin"
        assert request.new is True
        assert request.amount == "0.5"
        assert request.aclass == "currency"
        assert response is mock_response


class TestFundingChannelGetDepositStatus:
    """Tests for get_deposit_status method"""

    def test_get_deposit_status_no_parameters(self):
        """Test get_deposit_status with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_status()

        assert isinstance(request, GetDepositStatusRequest)
        assert request.asset is None
        assert request.method is None
        assert response is mock_response

    def test_get_deposit_status_with_asset(self):
        """Test get_deposit_status with asset filter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_status(asset="XBT")

        assert isinstance(request, GetDepositStatusRequest)
        assert request.asset == "XBT"
        assert response is mock_response

    def test_get_deposit_status_with_pagination(self):
        """Test get_deposit_status with pagination parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_status(cursor=True, limit=50)

        assert isinstance(request, GetDepositStatusRequest)
        assert request.cursor is True
        assert request.limit == 50
        assert response is mock_response

    def test_get_deposit_status_all_parameters(self):
        """Test get_deposit_status with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDepositStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_deposit_status(
            asset="XBT",
            aclass="currency",
            method="Bitcoin",
            start="1609459200",
            end="1612137600",
            cursor=True,
            limit=100,
        )

        assert isinstance(request, GetDepositStatusRequest)
        assert request.asset == "XBT"
        assert request.aclass == "currency"
        assert request.method == "Bitcoin"
        assert request.start == "1609459200"
        assert request.end == "1612137600"
        assert request.cursor is True
        assert request.limit == 100
        assert response is mock_response


class TestFundingChannelGetWithdrawalMethods:
    """Tests for get_withdrawal_methods method"""

    def test_get_withdrawal_methods_no_parameters(self):
        """Test get_withdrawal_methods with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalMethodsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_methods()

        assert isinstance(request, GetWithdrawalMethodsRequest)
        assert request.asset is None
        assert request.network is None
        assert response is mock_response

    def test_get_withdrawal_methods_with_asset(self):
        """Test get_withdrawal_methods with asset filter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalMethodsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_methods(asset="XBT")

        assert isinstance(request, GetWithdrawalMethodsRequest)
        assert request.asset == "XBT"
        assert response is mock_response

    def test_get_withdrawal_methods_with_network(self):
        """Test get_withdrawal_methods with network filter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalMethodsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_methods(network="Bitcoin")

        assert isinstance(request, GetWithdrawalMethodsRequest)
        assert request.network == "Bitcoin"
        assert response is mock_response


class TestFundingChannelGetWithdrawalAddresses:
    """Tests for get_withdrawal_addresses method"""

    def test_get_withdrawal_addresses_no_parameters(self):
        """Test get_withdrawal_addresses with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_addresses()

        assert isinstance(request, GetWithdrawalAddressesRequest)
        assert request.asset is None
        assert request.verified is None
        assert response is mock_response

    def test_get_withdrawal_addresses_with_verified(self):
        """Test get_withdrawal_addresses with verified filter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_addresses(verified=True)

        assert isinstance(request, GetWithdrawalAddressesRequest)
        assert request.verified is True
        assert response is mock_response

    def test_get_withdrawal_addresses_with_key(self):
        """Test get_withdrawal_addresses with key filter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalAddressesResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_addresses(key="btc_main")

        assert isinstance(request, GetWithdrawalAddressesRequest)
        assert request.key == "btc_main"
        assert response is mock_response


class TestFundingChannelGetWithdrawalInfo:
    """Tests for get_withdrawal_info method"""

    def test_get_withdrawal_info_basic(self):
        """Test get_withdrawal_info with required parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalInfoResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_info(
            asset="XBT", key="btc_testnet", amount="0.725"
        )

        assert isinstance(request, GetWithdrawalInfoRequest)
        assert request.asset == "XBT"
        assert request.key == "btc_testnet"
        assert request.amount == "0.725"
        assert response is mock_response

    def test_get_withdrawal_info_with_float_amount(self):
        """Test get_withdrawal_info with float amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalInfoResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_info(asset="XBT", key="btc_testnet", amount=0.5)

        assert isinstance(request, GetWithdrawalInfoRequest)
        assert request.amount == "0.5"
        assert response is mock_response


class TestFundingChannelWithdrawFunds:
    """Tests for withdraw_funds method"""

    def test_withdraw_funds_minimal_parameters(self):
        """Test withdraw_funds with required parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=WithdrawFundsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.withdraw_funds(asset="XBT", key="btc_2709", amount="0.725")

        assert isinstance(request, WithdrawFundsRequest)
        assert request.asset == "XBT"
        assert request.key == "btc_2709"
        assert request.amount == "0.725"
        assert request.address is None
        assert request.max_fee is None
        assert response is mock_response

    def test_withdraw_funds_with_address(self):
        """Test withdraw_funds with address verification"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=WithdrawFundsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.withdraw_funds(
            asset="XBT",
            key="btc_2709",
            amount="0.725",
            address="bc1kar0ssrr7xf3vy5l6d3lydnwkre5og2z3f51dq",
        )

        assert isinstance(request, WithdrawFundsRequest)
        assert request.address == "bc1kar0ssrr7xf3vy5l6d3lydnwkre5og2z3f51dq"
        assert response is mock_response

    def test_withdraw_funds_with_max_fee(self):
        """Test withdraw_funds with max_fee"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=WithdrawFundsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.withdraw_funds(
            asset="XBT", key="btc_2709", amount="0.725", max_fee="0.0001"
        )

        assert isinstance(request, WithdrawFundsRequest)
        assert request.max_fee == "0.0001"
        assert response is mock_response

    def test_withdraw_funds_with_float_amount(self):
        """Test withdraw_funds with float amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=WithdrawFundsResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.withdraw_funds(asset="XBT", key="btc_2709", amount=0.5)

        assert isinstance(request, WithdrawFundsRequest)
        assert request.amount == "0.5"
        assert response is mock_response


class TestFundingChannelGetWithdrawalStatus:
    """Tests for get_withdrawal_status method"""

    def test_get_withdrawal_status_no_parameters(self):
        """Test get_withdrawal_status with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_status()

        assert isinstance(request, GetWithdrawalStatusRequest)
        assert request.asset is None
        assert request.method is None
        assert response is mock_response

    def test_get_withdrawal_status_with_asset(self):
        """Test get_withdrawal_status with asset filter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_status(asset="XBT")

        assert isinstance(request, GetWithdrawalStatusRequest)
        assert request.asset == "XBT"
        assert response is mock_response

    def test_get_withdrawal_status_with_pagination(self):
        """Test get_withdrawal_status with pagination"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetWithdrawalStatusResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.get_withdrawal_status(cursor=True, limit=100)

        assert isinstance(request, GetWithdrawalStatusRequest)
        assert request.cursor is True
        assert request.limit == 100
        assert response is mock_response


class TestFundingChannelRequestWithdrawalCancellation:
    """Tests for request_withdrawal_cancellation method"""

    def test_request_withdrawal_cancellation_basic(self):
        """Test request_withdrawal_cancellation with required parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=WithdrawCancelResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.request_withdrawal_cancellation(
            asset="XBT", refid="FTQcuak-V6Za8qrWnhzTx67yYHz8Tg"
        )

        assert isinstance(request, RequestWithdrawalCancellationRequest)
        assert request.asset == "XBT"
        assert request.refid == "FTQcuak-V6Za8qrWnhzTx67yYHz8Tg"
        assert response is mock_response

    def test_request_withdrawal_cancellation_returns_tuple(self):
        """Test that request_withdrawal_cancellation returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=WithdrawCancelResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        result = channel.request_withdrawal_cancellation(asset="XBT", refid="ABC123")

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestFundingChannelRequestWalletTransfer:
    """Tests for request_wallet_transfer method"""

    def test_request_wallet_transfer_basic(self):
        """Test request_wallet_transfer with required parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestWalletTransferResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.request_wallet_transfer(
            asset="XBT",
            from_wallet="Spot Wallet",
            to_wallet="Futures Wallet",
            amount="2.54",
        )

        assert isinstance(request, RequestWalletTransferRequest)
        assert request.asset == "XBT"
        assert request.from_wallet == "Spot Wallet"
        assert request.to_wallet == "Futures Wallet"
        assert request.amount == "2.54"
        assert response is mock_response

    def test_request_wallet_transfer_with_float_amount(self):
        """Test request_wallet_transfer with float amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestWalletTransferResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        request, response = channel.request_wallet_transfer(
            asset="XBT",
            from_wallet="Spot Wallet",
            to_wallet="Futures Wallet",
            amount=1.5,
        )

        assert isinstance(request, RequestWalletTransferRequest)
        assert request.amount == "1.5"
        assert response is mock_response

    def test_request_wallet_transfer_returns_tuple(self):
        """Test that request_wallet_transfer returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=RequestWalletTransferResponse)
        mock_client.request.return_value = mock_response

        channel = FundingChannel(mock_client)
        result = channel.request_wallet_transfer(
            asset="XBT",
            from_wallet="Spot Wallet",
            to_wallet="Futures Wallet",
            amount="1.0",
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, RequestWalletTransferRequest)
        assert response is mock_response


# ============================================================================
# EarnChannel Tests
# ============================================================================


class TestEarnChannelInitialization:
    """Tests for EarnChannel initialization"""

    def test_init_with_client(self):
        """Test EarnChannel initialization with a client"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = EarnChannel(mock_client)

        assert channel.client is mock_client
        assert channel.channel == "earn"
        assert channel.private is True

    def test_path_property(self):
        """Test that path property returns correct private path"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        channel = EarnChannel(mock_client)

        assert channel.path == "/0/private/"


class TestEarnChannelListStrategies:
    """Tests for list_strategies method"""

    def test_list_strategies_no_parameters(self):
        """Test list_strategies with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies()

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.ascending is None
        assert request.asset is None
        assert request.cursor is None
        assert request.limit is None
        assert request.lock_type is None
        assert response is mock_response

    def test_list_strategies_with_asset(self):
        """Test list_strategies with asset parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(asset="XBT")

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.asset == "XBT"
        assert response is mock_response

    def test_list_strategies_with_ascending(self):
        """Test list_strategies with ascending parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(ascending=True)

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.ascending is True
        assert response is mock_response

    def test_list_strategies_with_limit(self):
        """Test list_strategies with limit parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(limit=10)

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.limit == 10
        assert response is mock_response

    def test_list_strategies_with_lock_type(self):
        """Test list_strategies with lock_type parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(lock_type=["flex", "bonded"])

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.lock_type == ["flex", "bonded"]
        assert response is mock_response

    def test_list_strategies_with_cursor_string(self):
        """Test list_strategies with cursor as string"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(cursor="next_page_cursor")

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.cursor == "next_page_cursor"
        assert response is mock_response

    def test_list_strategies_with_cursor_bool(self):
        """Test list_strategies with cursor as boolean"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(cursor=True)

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.cursor is True
        assert response is mock_response

    def test_list_strategies_all_parameters(self):
        """Test list_strategies with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_strategies(
            ascending=True,
            asset="ETH",
            cursor=True,
            limit=25,
            lock_type=["flex"],
        )

        assert isinstance(request, ListEarnStrategiesRequest)
        assert request.ascending is True
        assert request.asset == "ETH"
        assert request.cursor is True
        assert request.limit == 25
        assert request.lock_type == ["flex"]
        assert response is mock_response

    def test_list_strategies_returns_tuple(self):
        """Test that list_strategies returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnStrategiesResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        result = channel.list_strategies()

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, ListEarnStrategiesRequest)
        assert response is mock_response


class TestEarnChannelListAllocations:
    """Tests for list_allocations method"""

    def test_list_allocations_no_parameters(self):
        """Test list_allocations with no parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations()

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.ascending is None
        assert request.asset is None
        assert request.converted_asset is None
        assert request.cursor is None
        assert request.hide_zero_allocations is None
        assert response is mock_response

    def test_list_allocations_with_asset(self):
        """Test list_allocations with asset parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations(asset="XBT")

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.asset == "XBT"
        assert response is mock_response

    def test_list_allocations_with_converted_asset(self):
        """Test list_allocations with converted_asset parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations(converted_asset="USD")

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.converted_asset == "USD"
        assert response is mock_response

    def test_list_allocations_with_hide_zero_allocations(self):
        """Test list_allocations with hide_zero_allocations parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations(hide_zero_allocations=True)

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.hide_zero_allocations is True
        assert response is mock_response

    def test_list_allocations_with_ascending(self):
        """Test list_allocations with ascending parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations(ascending=False)

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.ascending is False
        assert response is mock_response

    def test_list_allocations_with_cursor(self):
        """Test list_allocations with cursor parameter"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations(cursor="cursor_value")

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.cursor == "cursor_value"
        assert response is mock_response

    def test_list_allocations_all_parameters(self):
        """Test list_allocations with all parameters"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.list_allocations(
            ascending=True,
            asset="ETH",
            converted_asset="USD",
            cursor=False,
            hide_zero_allocations=True,
        )

        assert isinstance(request, ListEarnAllocationsRequest)
        assert request.ascending is True
        assert request.asset == "ETH"
        assert request.converted_asset == "USD"
        assert request.cursor is False
        assert request.hide_zero_allocations is True
        assert response is mock_response

    def test_list_allocations_returns_tuple(self):
        """Test that list_allocations returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=ListEarnAllocationsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        result = channel.list_allocations()

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, ListEarnAllocationsRequest)
        assert response is mock_response


class TestEarnChannelAllocateFunds:
    """Tests for allocate_funds method"""

    def test_allocate_funds_with_string_amount(self):
        """Test allocate_funds with string amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AllocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.allocate_funds(
            amount="4.3", strategy_id="ESRFUO3-Q62XD-WIOIL7"
        )

        assert isinstance(request, AllocateEarnFundsRequest)
        assert request.amount == "4.3"
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_allocate_funds_with_float_amount(self):
        """Test allocate_funds with float amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AllocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.allocate_funds(amount=10.5, strategy_id="ESRFUO3-Q62XD-WIOIL7")

        assert isinstance(request, AllocateEarnFundsRequest)
        assert request.amount == "10.5"
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_allocate_funds_with_int_amount(self):
        """Test allocate_funds with integer amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AllocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.allocate_funds(amount=5, strategy_id="ESRFUO3-Q62XD-WIOIL7")

        assert isinstance(request, AllocateEarnFundsRequest)
        assert request.amount == "5"
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_allocate_funds_returns_tuple(self):
        """Test that allocate_funds returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AllocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        result = channel.allocate_funds(amount="1.0", strategy_id="STRAT123")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, AllocateEarnFundsRequest)
        assert response is mock_response

    def test_allocate_funds_request_called_with_correct_schema(self):
        """Test that allocate_funds calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=AllocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, _ = channel.allocate_funds(amount="2.0", strategy_id="STRAT456")

        mock_client.request.assert_called_once_with(request)


class TestEarnChannelDeallocateFunds:
    """Tests for deallocate_funds method"""

    def test_deallocate_funds_with_string_amount(self):
        """Test deallocate_funds with string amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeallocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.deallocate_funds(
            amount="4.3", strategy_id="ESRFUO3-Q62XD-WIOIL7"
        )

        assert isinstance(request, DeallocateEarnFundsRequest)
        assert request.amount == "4.3"
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_deallocate_funds_with_float_amount(self):
        """Test deallocate_funds with float amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeallocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.deallocate_funds(
            amount=7.8, strategy_id="ESRFUO3-Q62XD-WIOIL7"
        )

        assert isinstance(request, DeallocateEarnFundsRequest)
        assert request.amount == "7.8"
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_deallocate_funds_with_int_amount(self):
        """Test deallocate_funds with integer amount"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeallocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.deallocate_funds(amount=3, strategy_id="ESRFUO3-Q62XD-WIOIL7")

        assert isinstance(request, DeallocateEarnFundsRequest)
        assert request.amount == "3"
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_deallocate_funds_returns_tuple(self):
        """Test that deallocate_funds returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeallocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        result = channel.deallocate_funds(amount="1.0", strategy_id="STRAT123")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, DeallocateEarnFundsRequest)
        assert response is mock_response

    def test_deallocate_funds_request_called_with_correct_schema(self):
        """Test that deallocate_funds calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=DeallocateEarnFundsResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, _ = channel.deallocate_funds(amount="2.0", strategy_id="STRAT456")

        mock_client.request.assert_called_once_with(request)


class TestEarnChannelGetAllocationStatus:
    """Tests for get_allocation_status method"""

    def test_get_allocation_status_basic(self):
        """Test get_allocation_status with strategy_id"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAllocationStatusResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.get_allocation_status(strategy_id="ESRFUO3-Q62XD-WIOIL7")

        assert isinstance(request, GetAllocationStatusRequest)
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_get_allocation_status_returns_tuple(self):
        """Test that get_allocation_status returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAllocationStatusResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        result = channel.get_allocation_status(strategy_id="STRAT123")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, GetAllocationStatusRequest)
        assert response is mock_response

    def test_get_allocation_status_request_called_with_correct_schema(self):
        """Test that get_allocation_status calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetAllocationStatusResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, _ = channel.get_allocation_status(strategy_id="STRAT456")

        mock_client.request.assert_called_once_with(request)


class TestEarnChannelGetDeallocationStatus:
    """Tests for get_deallocation_status method"""

    def test_get_deallocation_status_basic(self):
        """Test get_deallocation_status with strategy_id"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDeallocationStatusResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, response = channel.get_deallocation_status(strategy_id="ESRFUO3-Q62XD-WIOIL7")

        assert isinstance(request, GetDeallocationStatusRequest)
        assert request.strategy_id == "ESRFUO3-Q62XD-WIOIL7"
        assert response is mock_response

    def test_get_deallocation_status_returns_tuple(self):
        """Test that get_deallocation_status returns proper tuple"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDeallocationStatusResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        result = channel.get_deallocation_status(strategy_id="STRAT123")

        assert isinstance(result, tuple)
        assert len(result) == 2
        request, response = result
        assert isinstance(request, GetDeallocationStatusRequest)
        assert response is mock_response

    def test_get_deallocation_status_request_called_with_correct_schema(self):
        """Test that get_deallocation_status calls client.request with correct schema"""
        mock_client = MagicMock(spec=KrakenRESTClient)
        mock_response = MagicMock(spec=GetDeallocationStatusResponse)
        mock_client.request.return_value = mock_response

        channel = EarnChannel(mock_client)
        request, _ = channel.get_deallocation_status(strategy_id="STRAT456")

        mock_client.request.assert_called_once_with(request)
