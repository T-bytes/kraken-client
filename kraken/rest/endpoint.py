from enum import StrEnum
from typing import Type


class KrakenChannel(StrEnum):
    """Enumeration of Kraken API endpoint types

    Each type corresponds to a different category of API endpoints
    and has an associated set of available channels.
    """

    ACCOUNT = "account"
    EARNING = "earning"
    FUNDING = "funding"
    MARKETS = "markets"
    TRADING = "trading"

    @property
    def channels(self) -> set:
        """Get the set of available channels for this API type.

        Returns:
            Set of channel/endpoint names available for this API type
        """
        _channels = {
            KrakenChannel.ACCOUNT: {
                "Balance",
                "BalanceEx",
                "CreditLines",
                "TradeBalance",
                "OpenOrders",
                "ClosedOrders",
                "QueryOrders",
                "OrderAmends",
                "TradesHistory",
                "QueryTrades",
                "OpenPositions",
                "Ledgers",
                "QueryLedgers",
                "TradeVolume",
                "AddExport",
                "ExportStatus",
                "RetrieveExport",
                "RemoveExport",
                "CreateSubaccount",
                "AccountTransfer",
            },
            KrakenChannel.EARNING: {
                "Earn/Strategies",
                "Earn/Allocations",
                "Earn/Allocate",
                "Earn/Deallocate",
                "Earn/AllocateStatus",
                "Earn/DeallocateStatus",
            },
            KrakenChannel.FUNDING: {
                "DepositMethods",
                "DepositAddresses",
                "DepositStatus",
                "WithdrawInfo",
                "Withdraw",
                "WithdrawStatus",
                "WithdrawCancel",
                "WalletTransfer",
            },
            KrakenChannel.MARKETS: {
                "Time",
                "SystemStatus",
                "Assets",
                "AssetPairs",
                "Ticker",
                "OHLC",
                "Depth",
                "Trades",
                "Spreads",
                "PreTrade",
                "PostTrade",
            },
            KrakenChannel.TRADING: {
                "AddOrder",
                "AddOrderBatch",
                "EditOrder",
                "CancelOrder",
                "CancelOrderBatch",
                "CancelAll",
                "CancelAllOrdersAfter",
                "GetWebSocketsToken",
            },
        }
        return _channels[self]

    @property
    def path(self) -> str:
        """Get the API path prefix for this type.

        Returns:
            API path prefix (i.e., "/0/public/" or "/0/private/")
        """
        if self in {KrakenChannel.MARKETS}:
            return "/0/public/"
        return "/0/private/"

    def is_private(self) -> bool:
        """Check if this API type requires authentication.

        Returns:
            True if authentication is required, False otherwise
        """
        return "private" in self.path
