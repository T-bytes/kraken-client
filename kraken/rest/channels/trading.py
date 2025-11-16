from typing import Literal, Tuple, TypeVar

from kraken.rest.schema.trading import *
from kraken.utilities import is_txid, is_uuid, rand_uuid

from .base import ChannelInterface


class TradingChannel(ChannelInterface):
    def __init__(self, client):
        super().__init__(client, "trading", True)

    def add_order(
        self,
        pair: str,
        otype: ORDER_TYPE,
        direction: ORDER_DIRECTION,
        price: float | int | Tuple[float | int, float | int],
        volume: float | int,
        leverage: int | None = None,
        **kwargs,
    ) -> Tuple[AddOrderRequest, AddOrderResponse]:
        request = AddOrderRequest(
            cl_ord_id=kwargs.pop("cl_ord_id", rand_uuid()),  # TODO more sophisticated ID approach
            pair=pair,
            ordertype=otype,
            type=direction,
            volume=volume,
            price=str(price) if isinstance(price, (int, float)) else str(price[0]),
            price2=None if not isinstance(price, tuple) else str(price[1]),
            displayvol=kwargs.pop("displayvol", None if otype != "iceberg" else volume),
            leverage=leverage,
            **kwargs,
        )
        return self._request(request)

    def amend_order(
        self,
        txid_or_uuid: str,
        pair: str,
        quantity: float | int = None,
        limit: float | int | None = None,
        trigger: float | int | None = None,
        deadline: str | None = None,
        **kwargs,
    ) -> Tuple[AmendOrderRequest, AmendOrderResponse]:
        txid = txid_or_uuid if is_txid(txid_or_uuid) else None
        uuid = txid_or_uuid if is_uuid(txid_or_uuid) else None
        request = AmendOrderRequest(
            txid=txid,
            cl_ord_id=uuid,
            pair=pair,
            order_qty=quantity,
            limit_price=str(limit) if limit is not None else None,
            trigger_price=str(trigger) if trigger is not None else None,
            deadline=deadline,
            **kwargs,
        )
        return self._request(request)

    def cancel_order(self, txid_or_uuid: str) -> Tuple[CancelOrderRequest, CancelOrderResponse]:
        txid = txid_or_uuid if is_txid(txid_or_uuid) else None
        uuid = txid_or_uuid if is_uuid(txid_or_uuid) else None
        request = CancelOrderRequest(txid=txid, cl_ord_id=uuid)
        return self._request(request)

    def cancel_all_orders(
        self, timeout: int | None = None
    ) -> Tuple[CancelAllRequest, CancelOrderResponse]:
        request = CancelAllRequest(timeout=timeout)
        return self._request(request)

    def get_websockets_token(self) -> Tuple[GetWebSocketsTokenRequest, GetWebSocketsTokenResponse]:
        request = GetWebSocketsTokenRequest()
        return self._request(request)
