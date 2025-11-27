"""Channel interfaces for organizing REST API endpoints by domain.

This module provides the channel system that groups related API endpoints into
domain-specific interfaces. Channels offer convenience methods that wrap schema-based
requests, making it easier to interact with the API while maintaining type safety.

Architecture Overview
--------------------
The channel system uses a layered architecture to organize API functionality:

1. **Channel Interfaces**: Domain-specific classes that provide high-level methods
   for related API operations (e.g., AccountChannel for account data, TradingChannel
   for order management).

2. **Channel Enum**: The `KrakenChannel` enum maps channels to their implementation
   classes, endpoint sets, and API path prefixes.

3. **Base Interface**: All channel classes extend `ChannelInterface`, which provides
   the `_request()` method for delegating to the client while maintaining type safety.

4. **Client Integration**: The REST client lazy-loads channel interfaces as properties,
   providing a clean API like `client.account.get_balance()`.
"""

from enum import Enum

from .account import AccountChannel
from .earn import EarningChannel
from .funding import FundingChannel
from .market import MarketsChannel
from .trading import TradingChannel


class KrakenChannel(Enum):
    ACCOUNT = AccountChannel
    EARNING = EarningChannel
    FUNDING = FundingChannel
    MARKETS = MarketsChannel
    TRADING = TradingChannel

    @property
    def interface(self) -> object:
        return self.value

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
