from typing import Literal, Tuple

from kraken.rest.schema.market import *

from .base import ChannelInterface


class MarketsChannel(ChannelInterface):
    def __init__(self, client):
        super().__init__(client, "market", False)

    def server_time(self) -> Tuple[GetServerTimeRequest, GetServerTimeResponse]:
        """Get the server's current time.

        This is a public endpoint that returns the Kraken server's current time
        in both Unix timestamp and RFC 1123 formats. Useful for synchronizing
        client time with the server.

        Returns:
            Tuple of (request, response) where request is the GetServerTimeRequest
            and response is the GetServerTimeResponse containing server time data.

        Example:
            >>> request, response = client.market.server_time()
            >>> if response.is_success:
            ...     print(f"Server time: {response.result.unixtime}")
        """
        request = GetServerTimeRequest()
        return self._request(request)

    def system_status(self) -> Tuple[GetSystemStatusRequest, GetSystemStatusResponse]:
        """Get the current system status or trading mode.

        Returns the operational status of the Kraken exchange, including whether
        the system is online, in maintenance mode, or experiencing issues.

        Returns:
            Tuple of (request, response) where request is the GetSystemStatusRequest
            and response is the GetSystemStatusResponse containing system status.

        Example:
            >>> request, response = client.market.system_status()
            >>> if response.is_success:
            ...     print(f"Status: {response.result.status}")
            ...     print(f"Timestamp: {response.result.timestamp}")
        """
        request = GetSystemStatusRequest()
        return self._request(request)

    def asset_info(
        self,
        assets: str | list[str] | None = None,
        aclass: Literal["currency", "tokenized_asset"] | None = None,
    ) -> Tuple[GetAssetInfoRequest, GetAssetInfoResponse]:
        """Get information about specific assets.

        Returns detailed information about one or more assets available on Kraken,
        including their display decimals, altname, and asset class.

        Args:
            assets: Comma-delimited list of assets to get info on, or list of strings.
                If None, returns information for all assets.
            aclass: Asset class to filter results. Options are "currency" or
                "tokenized_asset". Defaults to "currency" if None.

        Returns:
            Tuple of (request, response) where request is the GetAssetInfoRequest
            and response is the GetAssetInfoResponse containing asset details.

        Example:
            >>> request, response = client.market.asset_info(assets=["BTC", "ETH"])
            >>> if response.is_success:
            ...     for asset, info in response.result.items():
            ...         print(f"{asset}: {info.altname}")
        """
        request = GetAssetInfoRequest(asset=assets, aclass=aclass)
        return self._request(request)

    def asset_pairs(
        self,
        assets: str | list[str] | None = None,
        aclass: Literal["currency", "tokenized_asset"] | None = None,
        info: Literal["info", "leverage", "fees", "margin"] | None = None,
        country: str | None = None,
    ) -> Tuple[GetAssetPairsRequest, GetAssetPairsResponse]:
        """Get tradable asset pairs information.

        Returns detailed information about asset pairs available for trading on Kraken,
        including pair metadata, fees, leverage availability, and trading rules.

        Args:
            assets: Comma-delimited list of asset pairs to get info on, or list of strings.
                If None, returns information for all pairs.
            aclass: Asset class of the base asset. Options are "currency" or
                "tokenized_asset". Defaults to "currency" if None.
            info: Level of detail to return. Options are:
                - "info": All info (default)
                - "leverage": Leverage info only
                - "fees": Fee info only
                - "margin": Margin info only
            country: ISO 3166-1 alpha-2 country code to filter pairs available in
                that country.

        Returns:
            Tuple of (request, response) where request is the GetAssetPairsRequest
            and response is the GetAssetPairsResponse containing pair details.

        Example:
            >>> request, response = client.market.asset_pairs(assets="BTCUSD")
            >>> if response.is_success:
            ...     for pair, info in response.result.items():
            ...         print(f"{pair}: fees = {info.fees}")
        """
        request = GetAssetPairsRequest(
            pair=assets, aclass_base=aclass, info=info, country_code=country
        )
        return self._request(request)

    def ticker(
        self,
        pairs: str | list[str] | None = None,
        aclass: Literal["tokenized_asset", "forex"] | None = None,
    ) -> Tuple[GetTickerInformationRequest, GetTickerInformationResponse]:
        """Get ticker information for asset pairs.

        Returns real-time ticker data for one or more trading pairs, including
        current prices, volumes, bid/ask spreads, and daily statistics.

        Args:
            pairs: Comma-delimited list of asset pairs to get data for, or list of strings.
                If None, returns ticker data for all pairs.
            aclass: Asset class to filter results. Options are "tokenized_asset" or "forex".
                If None, no filtering is applied.

        Returns:
            Tuple of (request, response) where request is the GetTickerInformationRequest
            and response is the GetTickerInformationResponse containing ticker data.

        Example:
            >>> request, response = client.market.ticker(pairs=["BTCUSD", "ETHUSD"])
            >>> if response.is_success:
            ...     for pair, ticker in response.result.items():
            ...         print(f"{pair}: last price = {ticker.c[0]}")
        """
        request = GetTickerInformationRequest(pair=pairs, asset_class=aclass)
        return self._request(request)

    def ohlc(
        self,
        pair: str,
        interval: Literal[1, 5, 15, 30, 60, 240, 1440, 10080, 21600] | None = None,
        since: int | None = None,
        aclass: Literal["tokenized_asset"] | None = None,
    ) -> Tuple[GetOHLCDataRequest, GetOHLCDataResponse]:
        """Get OHLC (candlestick) data for an asset pair.

        Returns open, high, low, close, and volume data for a trading pair at
        specified time intervals. Useful for charting and technical analysis.

        Args:
            pair: Asset pair to get OHLC data for (e.g., 'BTCUSD').
            interval: Time frame interval in minutes. Valid options are:
                1, 5, 15, 30, 60, 240, 1440, 10080, 21600.
                Defaults to 1 (1 minute) if None.
            since: Return committed OHLC data since given Unix timestamp.
                If None, returns the most recent data.
            aclass: Asset class filter. Only "tokenized_asset" is supported.
                If None, no filtering is applied.

        Returns:
            Tuple of (request, response) where request is the GetOHLCDataRequest
            and response is the GetOHLCDataResponse containing OHLC candlestick data.

        Example:
            >>> request, response = client.market.ohlc(pair="BTCUSD", interval=60)
            >>> if response.is_success:
            ...     for candle in response.result.data:
            ...         print(f"Time: {candle[0]}, Close: {candle[4]}")
        """
        request = GetOHLCDataRequest(pair=pair, interval=interval, since=since, asset_class=aclass)
        return self._request(request)

    def order_book(
        self, pair: str, count: int | None = None, aclass: Literal["tokenized_asset"] | None = None
    ) -> Tuple[GetOrderBookRequest, GetOrderBookResponse]:
        """Get current order book data for an asset pair.

        Returns the current bid and ask order book for a trading pair, showing
        price levels and volumes available at each level.

        Args:
            pair: Asset pair to get order book for (e.g., 'BTCUSD').
            count: Maximum number of asks/bids to return. Valid range is 1-500.
                Defaults to 100 if None.
            aclass: Asset class filter. Only "tokenized_asset" is supported.
                If None, no filtering is applied.

        Returns:
            Tuple of (request, response) where request is the GetOrderBookRequest
            and response is the GetOrderBookResponse containing bid/ask data.

        Example:
            >>> request, response = client.market.order_book(pair="BTCUSD", count=10)
            >>> if response.is_success:
            ...     print(f"Best bid: {response.result.bids[0]}")
            ...     print(f"Best ask: {response.result.asks[0]}")
        """
        request = GetOrderBookRequest(pair=pair, count=count, asset_class=aclass)
        return self._request(request)

    def recent_trades(
        self,
        pair: str,
        since: int | None = None,
        count: int | None = None,
        aclass: Literal["tokenized_asset"] | None = None,
    ) -> Tuple[GetRecentTradesRequest, GetRecentTradesResponse]:
        """Get recent trades for an asset pair.

        Returns a list of the most recent completed trades for a trading pair,
        including price, volume, time, and trade type (buy/sell).

        Args:
            pair: Asset pair to get trade data for (e.g., 'BTCUSD').
            since: Return trade data since given Unix timestamp in nanoseconds.
                If None, returns the most recent trades.
            count: Maximum number of trades to return. Defaults to 1000 if None.
            aclass: Asset class filter. Only "tokenized_asset" is supported.
                If None, no filtering is applied.

        Returns:
            Tuple of (request, response) where request is the GetRecentTradesRequest
            and response is the GetRecentTradesResponse containing recent trade data.

        Example:
            >>> request, response = client.market.recent_trades(pair="BTCUSD", count=50)
            >>> if response.is_success:
            ...     for trade in response.result.trades:
            ...         print(f"Price: {trade[0]}, Volume: {trade[1]}")
        """
        request = GetRecentTradesRequest(pair=pair, since=since, count=count, asset_class=aclass)
        return self._request(request)

    def recent_spreads(
        self, pair: str, since: int | None = None, aclass: Literal["tokenized_asset"] | None = None
    ) -> Tuple[GetRecentSpreadsRequest, GetRecentSpreadsResponse]:
        """Get recent spread data for an asset pair.

        Returns historical bid-ask spread data for a trading pair, showing the
        difference between the best bid and ask prices over time.

        Args:
            pair: Asset pair to get spread data for (e.g., 'BTCUSD').
            since: Return spread data since given Unix timestamp in nanoseconds.
                If None, returns the most recent spread data.
            aclass: Asset class filter. Only "tokenized_asset" is supported.
                If None, no filtering is applied.

        Returns:
            Tuple of (request, response) where request is the GetRecentSpreadsRequest
            and response is the GetRecentSpreadsResponse containing spread data.

        Example:
            >>> request, response = client.market.recent_spreads(pair="BTCUSD")
            >>> if response.is_success:
            ...     for spread in response.result.spreads:
            ...         print(f"Time: {spread[0]}, Bid: {spread[1]}, Ask: {spread[2]}")
        """
        request = GetRecentSpreadsRequest(pair=pair, since=since, asset_class=aclass)
        return self._request(request)

    def pre_trade_data(
        self, symbol: str
    ) -> Tuple[GetPreTradeDataRequest, GetPreTradeDataResponse]:
        """Get pre-trade order book data for a symbol.

        Returns the price levels in the order book with aggregated order quantities
        at each price level. The top 10 levels are returned for each trading pair.

        Args:
            symbol: The symbol of the currency pair (e.g., 'BTC/USD').

        Returns:
            Tuple of (request, response) where request is the GetPreTradeDataRequest
            and response is the GetPreTradeDataResponse.
        """
        request = GetPreTradeDataRequest(symbol=symbol)
        return self._request(request)

    def post_trade_data(
        self,
        symbol: str | None = None,
        from_ts: str | None = None,
        to_ts: str | None = None,
        count: int | None = None,
    ) -> Tuple[GetPostTradeDataRequest, GetPostTradeDataResponse]:
        """Get post-trade data (recent trades) for a symbol.

        Returns a list of trades on the spot exchange. If no filter parameters
        are specified, the last 1000 trades for all pairs are received.

        Args:
            symbol: Filter the results to the currency pair (e.g., 'BTC/USD').
            from_ts: Filter the results to include trades after this timestamp (ISO 8601).
            to_ts: Filter the results to include trades before/at this timestamp (ISO 8601).
            count: The maximum number of trades to return (1-1000, default 1000).

        Returns:
            Tuple of (request, response) where request is the GetPostTradeDataRequest
            and response is the GetPostTradeDataResponse.
        """
        request = GetPostTradeDataRequest(symbol=symbol, from_ts=from_ts, to_ts=to_ts, count=count)
        return self._request(request)
