"""REST schema for requests and responses."""

from typing import Type

from .account import *
from .base import BaseRequestSchema, BaseResponseWrapper
from .earn import *
from .funding import *
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
    GetPreTradeDataRequest: ("PreTrade", GetPreTradeDataResponse),
    GetPostTradeDataRequest: ("PostTrade", GetPostTradeDataResponse),
    # Trading endpoints
    AddOrderRequest: ("AddOrder", AddOrderResponse),
    AmendOrderRequest: ("EditOrder", AmendOrderResponse),
    CancelOrderRequest: ("CancelOrder", CancelOrderResponse),
    CancelAllRequest: ("CancelAll", CancelOrderResponse),
    GetWebSocketsTokenRequest: ("GetWebSocketsToken", GetWebSocketsTokenResponse),
    AddOrderBatchRequest: ("AddOrderBatch", AddOrderBatchResponse),
    CancelOrderBatchRequest: ("CancelOrderBatch", CancelOrderBatchResponse),
    # Account endpoints
    GetBalanceRequest: ("Balance", GetBalanceResponse),
    GetExtendedBalanceRequest: ("BalanceEx", GetExtendedBalanceResponse),
    GetCreditLinesRequest: ("CreditLines", GetCreditLinesResponse),
    GetTradeBalanceRequest: ("TradeBalance", GetTradeBalanceResponse),
    GetOpenOrdersRequest: ("OpenOrders", GetOpenOrdersResponse),
    GetClosedOrdersRequest: ("ClosedOrders", GetClosedOrdersResponse),
    QueryOrdersRequest: ("QueryOrders", QueryOrdersResponse),
    GetOrderAmendsRequest: ("OrderAmends", GetOrderAmendsResponse),
    GetTradesHistoryRequest: ("TradesHistory", GetTradesHistoryResponse),
    QueryTradesRequest: ("QueryTrades", QueryTradesResponse),
    GetOpenPositionsRequest: ("OpenPositions", GetOpenPositionsResponse),
    GetLedgersRequest: ("Ledgers", GetLedgersResponse),
    QueryLedgersRequest: ("QueryLedgers", QueryLedgersResponse),
    GetTradeVolumeRequest: ("TradeVolume", GetTradeVolumeResponse),
    RequestExportRequest: ("AddExport", RequestExportResponse),
    GetExportStatusRequest: ("ExportStatus", GetExportStatusResponse),
    RetrieveExportRequest: ("RetrieveExport", RetrieveExportResponse),
    DeleteExportRequest: ("RemoveExport", DeleteExportResponse),
    CreateSubaccountRequest: ("CreateSubaccount", CreateSubaccountResponse),
    AccountTransferRequest: ("AccountTransfer", AccountTransferResponse),
    # Funding endpoints
    GetDepositMethodsRequest: ("DepositMethods", GetDepositMethodsResponse),
    GetDepositAddressesRequest: ("DepositAddresses", GetDepositAddressesResponse),
    GetDepositStatusRequest: ("DepositStatus", GetDepositStatusResponse),
    GetWithdrawalMethodsRequest: ("WithdrawMethods", GetWithdrawalMethodsResponse),
    GetWithdrawalAddressesRequest: ("WithdrawAddresses", GetWithdrawalAddressesResponse),
    GetWithdrawalInfoRequest: ("WithdrawInfo", GetWithdrawalInfoResponse),
    WithdrawFundsRequest: ("Withdraw", WithdrawFundsResponse),
    GetWithdrawalStatusRequest: ("WithdrawStatus", GetWithdrawalStatusResponse),
    RequestWithdrawalCancellationRequest: ("WithdrawCancel", WithdrawCancelResponse),
    RequestWalletTransferRequest: ("WalletTransfer", RequestWalletTransferResponse),
    # Earn endpoints
    ListEarnStrategiesRequest: ("Earn/Strategies", ListEarnStrategiesResponse),
    ListEarnAllocationsRequest: ("Earn/Allocations", ListEarnAllocationsResponse),
    AllocateEarnFundsRequest: ("Earn/Allocate", AllocateEarnFundsResponse),
    DeallocateEarnFundsRequest: ("Earn/Deallocate", DeallocateEarnFundsResponse),
    GetAllocationStatusRequest: ("Earn/AllocateStatus", GetAllocationStatusResponse),
    GetDeallocationStatusRequest: ("Earn/DeallocateStatus", GetDeallocationStatusResponse),
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

    # Special case: CancelAllRequest routes to different endpoints based on timeout
    if schema_type == CancelAllRequest:
        from kraken.rest.schema.trading import CancelAllRequest as CancelAllReq

        if isinstance(schema, CancelAllReq) and schema.timeout is not None:
            return ("CancelAllOrdersAfter", CancelOrderResponse)

    return SCHEMA_REGISTRY[schema_type]
