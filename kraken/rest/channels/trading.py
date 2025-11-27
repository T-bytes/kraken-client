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
        """Add a new order to the exchange.

        Creates a new order with the specified parameters. Supports various order types
        including limit, market, stop-loss, take-profit, and iceberg orders.

        Args:
            pair: Asset pair to trade (e.g., 'BTCUSD').
            otype: Order type. Options are: 'market', 'limit', 'stop-loss', 'take-profit',
                'stop-loss-limit', 'take-profit-limit', 'settle-position', 'iceberg'.
            direction: Order direction, either 'buy' or 'sell'.
            price: Order price. For single-price orders (limit, stop-loss, take-profit),
                provide a float/int. For two-price orders (stop-loss-limit,
                take-profit-limit), provide a tuple of (trigger_price, limit_price).
            volume: Order quantity in terms of the base asset.
            leverage: Leverage multiplier (e.g., 2 for 2x leverage). Only applicable
                for margin trading. Defaults to no leverage if None.
            **kwargs: Additional optional parameters:
                - cl_ord_id: Client order ID (auto-generated UUID if not provided)
                - displayvol: Visible order quantity for iceberg orders
                - oflags: Order flags (e.g., 'post', 'fcib', 'fciq', 'nompp')
                - timeinforce: Time in force (e.g., 'GTC', 'IOC', 'GTD')
                - starttm: Scheduled start time
                - expiretm: Expiration time
                - close: Close position details
                - validate: If True, only validate order without placing it

        Returns:
            Tuple of (request, response) where request is the AddOrderRequest
            and response is the AddOrderResponse containing order details and txid.

        Example:
            >>> # Place a limit buy order
            >>> request, response = client.trading.add_order(
            ...     pair="BTCUSD",
            ...     otype="limit",
            ...     direction="buy",
            ...     price=50000.0,
            ...     volume=0.1
            ... )
            >>> if response.is_success:
            ...     print(f"Order ID: {response.result.txid}")
        """
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
        """Amend an existing order.

        Modifies an existing open order by changing its quantity, limit price,
        or trigger price. Only certain order types can be amended.

        Args:
            txid_or_uuid: Order identifier, either the transaction ID (txid) from
                Kraken or the client order ID (UUID) if provided when creating the order.
            pair: Asset pair for the order (e.g., 'BTCUSD').
            quantity: New order quantity. If None, quantity remains unchanged.
            limit: New limit price. If None, limit price remains unchanged.
            trigger: New trigger price (for stop-loss/take-profit orders).
                If None, trigger price remains unchanged.
            deadline: RFC3339 timestamp after which the amendment request expires.
                If None, uses a default deadline.
            **kwargs: Additional optional parameters:
                - displayvol: New visible quantity for iceberg orders
                - oflags: Order flags to modify
                - validate: If True, only validate amendment without executing it

        Returns:
            Tuple of (request, response) where request is the AmendOrderRequest
            and response is the AmendOrderResponse containing updated order details.

        Example:
            >>> # Amend order quantity and limit price
            >>> request, response = client.trading.amend_order(
            ...     txid_or_uuid="O5TDV2-VB5L6-UCI7P4",
            ...     pair="BTCUSD",
            ...     quantity=0.2,
            ...     limit=51000.0
            ... )
            >>> if response.is_success:
            ...     print(f"Order amended: {response.result.order_id}")
        """
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
        """Cancel a specific order.

        Cancels an open order identified by its transaction ID or client order ID.
        The order must be in an open state to be cancelled.

        Args:
            txid_or_uuid: Order identifier, either the transaction ID (txid) from
                Kraken or the client order ID (UUID) if provided when creating the order.

        Returns:
            Tuple of (request, response) where request is the CancelOrderRequest
            and response is the CancelOrderResponse containing cancellation details.

        Example:
            >>> # Cancel order by transaction ID
            >>> request, response = client.trading.cancel_order("O5TDV2-VB5L6-UCI7P4")
            >>> if response.is_success:
            ...     print(f"Cancelled: {response.result.count} order(s)")
        """
        txid = txid_or_uuid if is_txid(txid_or_uuid) else None
        uuid = txid_or_uuid if is_uuid(txid_or_uuid) else None
        request = CancelOrderRequest(txid=txid, cl_ord_id=uuid)
        return self._request(request)

    def cancel_all_orders(
        self, timeout: int | None = None
    ) -> Tuple[CancelAllRequest, CancelOrderResponse]:
        """Cancel all open orders.

        Cancels all open orders with an optional timeout. If timeout is specified,
        this triggers a "Dead Man's Switch" that will automatically cancel all orders
        after the timeout period unless the timer is reset.

        Args:
            timeout: Optional timeout in seconds for the Dead Man's Switch. If provided,
                all orders will be automatically cancelled after this duration unless
                the timer is extended by calling this method again. If None, simply
                cancels all open orders immediately without setting up a timer.

        Returns:
            Tuple of (request, response) where request is the CancelAllRequest
            and response is the CancelOrderResponse containing cancellation count.

        Example:
            >>> # Cancel all orders immediately
            >>> request, response = client.trading.cancel_all_orders()
            >>> if response.is_success:
            ...     print(f"Cancelled {response.result.count} orders")
            >>>
            >>> # Set up Dead Man's Switch with 60 second timeout
            >>> request, response = client.trading.cancel_all_orders(timeout=60)
        """
        request = CancelAllRequest(timeout=timeout)
        return self._request(request)

    def get_websockets_token(self) -> Tuple[GetWebSocketsTokenRequest, GetWebSocketsTokenResponse]:
        """Get an authentication token for WebSocket API connections.

        Retrieves a token that can be used to authenticate private WebSocket
        connections. The token is valid for a limited time and provides access
        to private WebSocket feeds.

        Returns:
            Tuple of (request, response) where request is the GetWebSocketsTokenRequest
            and response is the GetWebSocketsTokenResponse containing the auth token.

        Example:
            >>> request, response = client.trading.get_websockets_token()
            >>> if response.is_success:
            ...     token = response.result.token
            ...     expires = response.result.expires
            ...     print(f"Token: {token}, expires in {expires} seconds")
        """
        request = GetWebSocketsTokenRequest()
        return self._request(request)
