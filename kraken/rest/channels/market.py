from typing import Literal, Tuple

from kraken.rest.schema.market import *

from .base import ChannelInterface


class MarketChannel(ChannelInterface):
    def __init__(self, client):
        super().__init__(client, "market", False)

    def server_time(self) -> Tuple[GetServerTimeRequest, GetServerTimeResponse]:
        request = GetServerTimeRequest()
        return self._request(request)

    def system_status(self) -> Tuple[GetSystemStatusRequest, GetSystemStatusResponse]:
        request = GetSystemStatusRequest()
        return self._request(request)

    def asset_info(
        self,
        assets: str | list[str] | None = None,
        aclass: Literal["currency", "tokenized_asset"] | None = None,
    ) -> Tuple[GetAssetInfoRequest, GetAssetInfoResponse]:
        request = GetAssetInfoRequest(asset=assets, aclass=aclass)
        return self._request(request)

    def asset_pairs(
        self,
        assets: str | list[str] | None = None,
        aclass: Literal["currency", "tokenized_asset"] | None = None,
        info: Literal["info", "leverage", "fees", "margin"] | None = None,
        country: str | None = None,
    ) -> Tuple[GetAssetPairsRequest, GetAssetPairsResponse]:
        request = GetAssetPairsRequest(
            pair=assets, aclass_base=aclass, info=info, country_code=country
        )
        return self._request(request)

    def ticker(
        self,
        pairs: str | list[str] | None = None,
        aclass: Literal["tokenized_asset", "forex"] | None = None,
    ) -> Tuple[GetTickerInformationRequest, GetTickerInformationResponse]:
        request = GetTickerInformationRequest(pair=pairs, asset_class=aclass)
        return self._request(request)

    def ohlc(
        self,
        pair: str,
        interval: Literal[1, 5, 15, 30, 60, 240, 1440, 10080, 21600] | None = None,
        since: int | None = None,
        aclass: Literal["tokenized_asset"] | None = None,
    ) -> Tuple[GetOHLCDataRequest, GetOHLCDataResponse]:
        request = GetOHLCDataRequest(pair=pair, interval=interval, since=since, asset_class=aclass)
        return self._request(request)

    def order_book(
        self, pair: str, count: int | None = None, aclass: Literal["tokenized_asset"] | None = None
    ) -> Tuple[GetOrderBookRequest, GetOrderBookResponse]:
        request = GetOrderBookRequest(pair=pair, count=count, asset_class=aclass)
        return self._request(request)

    def recent_trades(
        self,
        pair: str,
        since: int | None = None,
        count: int | None = None,
        aclass: Literal["tokenized_asset"] | None = None,
    ) -> Tuple[GetRecentTradesRequest, GetRecentTradesResponse]:
        request = GetRecentTradesRequest(pair=pair, since=since, count=count, asset_class=aclass)
        return self._request(request)

    def recent_spreads(
        self, pair: str, since: int | None = None, aclass: Literal["tokenized_asset"] | None = None
    ) -> Tuple[GetRecentSpreadsRequest, GetRecentSpreadsResponse]:
        request = GetRecentSpreadsRequest(pair=pair, since=since, asset_class=aclass)
        return self._request(request)
