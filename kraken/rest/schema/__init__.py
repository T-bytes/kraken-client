"""REST schema for requests and responses."""

from typing import Type

from .base import BaseRequestSchema, BaseResponseWrapper
from .market import *
from .trading import *

# Schema Registry: Maps Request schema classes to (endpoint_name, Response schema class)
SCHEMA_REGISTRY: dict[Type[BaseRequestSchema], tuple[str, Type[BaseResponseWrapper]]] = {
    # Market endpoints
    GetAssetInfoRequest: ("Assets", GetAssetInfoResponse),
    GetSystemStatusRequest: ("SystemStatus", GetSystemStatusResponse),
    GetServerTimeRequest: ("Time", GetServerTimeResponse),
    GetAssetPairsRequest: ("AssetPairs", GetAssetPairsResponse),
    GetTickerInformationRequest: ("Ticker", GetTickerInformationResponse),
    GetOHLCDataRequest: ("OHLC", GetOHLCDataResponse),
    GetOrderBookRequest: ("Depth", GetOrderBookResponse),
    GetRecentTradesRequest: ("Trades", GetRecentTradesResponse),
    GetRecentSpreadsRequest: ("Spread", GetRecentSpreadsResponse),
    # Trading endpoints
    AddOrderRequest: ("AddOrder", AddOrderResponse),
    AmendOrderRequest: ("EditOrder", AmendOrderResponse),
    CancelOrderRequest: ("CancelOrder", CancelOrderResponse),
    CancelAllRequest: ("CancelAll", CancelAllResponse),
    CancelAllOrdersAfterRequest: ("CancelAllOrdersAfter", CancelAllOrdersAfterResponse),
    GetWebSocketsTokenRequest: ("GetWebSocketsToken", GetWebSocketsTokenResponse),
    AddOrderBatchRequest: ("AddOrderBatch", AddOrderBatchResponse),
    CancelOrderBatchRequest: ("CancelOrderBatch", CancelOrderBatchResponse),
}


def get_endpoint_info(
    schema: BaseRequestSchema,
) -> tuple[str, Type[BaseResponseWrapper]]:
    """Get endpoint name and response class for a request schema.

    Args:
        schema: Request schema instance

    Returns:
        Tuple of (endpoint_name, ResponseClass)

    Raises:
        ValueError: If schema type is not registered
    """
    schema_type = type(schema)
    if schema_type not in SCHEMA_REGISTRY:
        raise ValueError(
            f"Unknown request schema type: {schema_type.__name__}. "
            f"Available types: {', '.join(cls.__name__ for cls in SCHEMA_REGISTRY.keys())}"
        )
    return SCHEMA_REGISTRY[schema_type]
