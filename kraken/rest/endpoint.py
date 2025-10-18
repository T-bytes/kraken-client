from enum import Enum


class KrakenEndpoint(Enum):
    """Enumeration of Kraken API endpoint types

    Each type corresponds to a different category of API endpoints
    and has an associated set of available channels.
    """

    PUBLIC = "public"
    PRIVATE = "private"
    TRADING = "trading"
    FUNDING = "funding"
    STAKING = "staking"

    @property
    def channels(self) -> set:
        """Get the set of available channels for this API type.

        Returns:
            Set of channel/endpoint names available for this API type
        """
        _channels = {
            KrakenEndpoint.PUBLIC: {
                "Time",
                "Assets",
                "AssetPairs",
                "Ticker",
                "OHLC",
                "Depth",
                "Trades",
                "Spread",
                "SystemStatus",
            },
            KrakenEndpoint.PRIVATE: {
                "Balance",
                "BalanceEx",
                "TradeBalance",
                "OpenOrders",
                "ClosedOrders",
                "QueryOrders",
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
                "GetWebSocketsToken",
                "CreateSubaccount",
                "AccountTransfer",
            },
            KrakenEndpoint.TRADING: {
                "AddOrder",
                "AddOrderBatch",
                "EditOrder",
                "CancelOrder",
                "CancelOrderBatch",
                "CancelAll",
                "CancelAllOrdersAfter",
            },
            KrakenEndpoint.FUNDING: {
                "DepositMethods",
                "DepositAddresses",
                "DepositStatus",
                "WithdrawInfo",
                "Withdraw",
                "WithdrawStatus",
                "WithdrawCancel",
                "WalletTransfer",
            },
            KrakenEndpoint.STAKING: {
                "Earn/Strategies",
                "Earn/Allocations",
                "Earn/Allocate",
                "Earn/Deallocate",
                "Earn/AllocateStatus",
                "Earn/DeallocateStatus",
                "Staking/Assets",
                "Staking/Balance",
                "Stake",
                "Unstake",
                "Staking/Pending",
                "Staking/Transactions",
            },
        }
        return _channels[self]

    @property
    def path(self) -> str:
        """Get the API path prefix for this type.

        Returns:
            API path prefix (i.e., "/0/public/" or "/0/private/")
        """
        if self == KrakenEndpoint.PUBLIC:
            return "/0/public/"
        return "/0/private/"

    def is_private(self) -> bool:
        """Check if this API type requires authentication.

        Returns:
            True if authentication is required, False otherwise
        """
        return self != KrakenEndpoint.PUBLIC
