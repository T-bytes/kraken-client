from typing import Literal, Tuple

from kraken.rest.schema.account import *

from .base import ChannelInterface


class AccountChannel(ChannelInterface):
    """Channel for Account Data endpoints.

    Provides access to all account-related endpoints including balances,
    orders, trades, positions, ledgers, and export functionality.
    """

    def __init__(self, client):
        super().__init__(client, "account", True)

    def get_balance(
        self, rebase_multiplier: REBASE_MULTIPLIER | None = None
    ) -> Tuple[GetBalanceRequest, GetBalanceResponse]:
        """Get account balance.

        Retrieve all cash balances, net of pending withdrawals.

        Args:
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_balance()
            >>> if response.is_success:
            ...     print(response.success.balances)
        """
        request = GetBalanceRequest(rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_extended_balance(
        self, rebase_multiplier: REBASE_MULTIPLIER | None = None
    ) -> Tuple[GetExtendedBalanceRequest, GetExtendedBalanceResponse]:
        """Get extended balance.

        Retrieve all extended account balances, including credits and held amounts.

        Args:
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_extended_balance()
            >>> if response.is_success:
            ...     for asset, details in response.success.assets.items():
            ...         print(f"{asset}: {details.balance}")
        """
        request = GetExtendedBalanceRequest(rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_credit_lines(
        self, rebase_multiplier: REBASE_MULTIPLIER | None = None
    ) -> Tuple[GetCreditLinesRequest, GetCreditLinesResponse]:
        """Get credit lines.

        Retrieve all credit line details for VIPs with this functionality.

        Args:
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_credit_lines()
            >>> if response.is_success:
            ...     print(response.success.limits_monitor.equity_usd)
        """
        request = GetCreditLinesRequest(rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_trade_balance(
        self,
        asset: str | None = None,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetTradeBalanceRequest, GetTradeBalanceResponse]:
        """Get trade balance.

        Retrieve a summary of collateral balances, margin position valuations,
        equity and margin level.

        Args:
            asset: Base asset used to determine balance (Default: ZUSD)
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_trade_balance(asset="ZUSD")
            >>> if response.is_success:
            ...     print(f"Equity: {response.success.e}")
            ...     print(f"Free margin: {response.success.mf}")
        """
        request = GetTradeBalanceRequest(asset=asset, rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_open_orders(
        self,
        trades: bool = False,
        userref: int | None = None,
        cl_ord_id: str | list[str] | None = None,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetOpenOrdersRequest, GetOpenOrdersResponse]:
        """Get open orders.

        Retrieve information about currently open orders.

        Args:
            trades: Whether or not to include trades related to position in output
            userref: Restrict results to given user reference id
            cl_ord_id: Client order ID(s) to limit output to (string or list)
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_open_orders(trades=True)
            >>> if response.is_success:
            ...     for order_id, order in response.success.open.items():
            ...         print(f"{order_id}: {order.descr.order}")
        """
        request = GetOpenOrdersRequest(
            trades=trades,
            userref=userref,
            cl_ord_id=cl_ord_id,
            rebase_multiplier=rebase_multiplier,
        )
        return self._request(request)

    def get_closed_orders(
        self,
        trades: bool = False,
        userref: int | None = None,
        start: int | None = None,
        end: int | None = None,
        ofs: int | None = None,
        closetime: CLOSETIME_TYPE | None = None,
        consolidate_taker: bool = False,
        without_count: bool = False,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetClosedOrdersRequest, GetClosedOrdersResponse]:
        """Get closed orders.

        Retrieve information about orders that have been closed (filled or cancelled).
        50 results are returned at a time, the most recent by default.

        Args:
            trades: Whether or not to include trades related to position in output
            userref: Restrict results to given user reference id
            start: Starting unix timestamp or order tx ID of results (exclusive)
            end: Ending unix timestamp or order tx ID of results (inclusive)
            ofs: Result offset for pagination
            closetime: Which time to use for filtering
            consolidate_taker: Whether or not to consolidate trades by individual taker trades
            without_count: Whether or not to include the count of order matching criteria in output
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_closed_orders(start=1609459200)
            >>> if response.is_success:
            ...     print(f"Total count: {response.success.count}")
            ...     for order_id, order in response.success.closed.items():
            ...         print(f"{order_id}: {order.status}")
        """
        request = GetClosedOrdersRequest(
            trades=trades,
            userref=userref,
            start=start,
            end=end,
            ofs=ofs,
            closetime=closetime,
            consolidate_taker=consolidate_taker,
            without_count=without_count,
            rebase_multiplier=rebase_multiplier,
        )
        return self._request(request)

    def query_orders(
        self,
        txid: str | list[str] | None = None,
        trades: bool = False,
        userref: int | None = None,
        consolidate_taker: bool = False,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[QueryOrdersRequest, QueryOrdersResponse]:
        """Query orders info.

        Retrieve information about specific orders.

        Args:
            txid: Transaction ID(s) to query info about (50 maximum, string or list)
            trades: Whether or not to include trades related to position in output
            userref: Restrict results to given user reference id
            consolidate_taker: Whether or not to consolidate trades by individual taker trades
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.query_orders(
            ...     txid="OQCLML-BW3P3-BUCMWZ"
            ... )
            >>> if response.is_success:
            ...     for order_id, order in response.success.orders.items():
            ...         print(f"{order_id}: {order.vol}")
        """
        request = QueryOrdersRequest(
            txid=txid,
            trades=trades,
            userref=userref,
            consolidate_taker=consolidate_taker,
            rebase_multiplier=rebase_multiplier,
        )
        return self._request(request)

    def get_order_amends(
        self, order_id: str, rebase_multiplier: REBASE_MULTIPLIER | None = None
    ) -> Tuple[GetOrderAmendsRequest, GetOrderAmendsResponse]:
        """Get order amends.

        Retrieves an audit trail of amend transactions on the specified order.

        Args:
            order_id: The Kraken order identifier for the amended order
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_order_amends(
            ...     order_id="OQCLML-BW3P3-BUCMWZ"
            ... )
            >>> if response.is_success:
            ...     print(f"Total amends: {response.success.count}")
            ...     for amend in response.success.amends:
            ...         print(f"{amend.amend_type}: {amend.reason}")
        """
        request = GetOrderAmendsRequest(order_id=order_id, rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_trades_history(
        self,
        type: str | None = None,
        trades: bool = False,
        start: int | None = None,
        end: int | None = None,
        ofs: int | None = None,
        consolidation_type: str | None = None,
        ledgers: bool = False,
        without_count: bool = False,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetTradesHistoryRequest, GetTradesHistoryResponse]:
        """Get trades history.

        Retrieve information about trades/fills. 50 results are returned at a time,
        the most recent by default.

        Args:
            type: Type of trade (all/any position/no position/closing position/closed position)
            trades: Whether or not to include trades related to position in output
            start: Starting unix timestamp or trade tx ID of results (exclusive)
            end: Ending unix timestamp or trade tx ID of results (inclusive)
            ofs: Result offset for pagination
            consolidation_type: Type of consolidation
            ledgers: Whether or not to include related ledgers in output
            without_count: Whether or not to include the count of orders and trades
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_trades_history(type="all")
            >>> if response.is_success:
            ...     print(f"Total count: {response.success.count}")
            ...     for trade_id, trade in response.success.trades.items():
            ...         print(f"{trade_id}: {trade.pair} @ {trade.price}")
        """
        request = GetTradesHistoryRequest(
            type=type,
            trades=trades,
            start=start,
            end=end,
            ofs=ofs,
            consolidation_type=consolidation_type,
            ledgers=ledgers,
            without_count=without_count,
            rebase_multiplier=rebase_multiplier,
        )
        return self._request(request)

    def query_trades(
        self,
        txid: str | list[str],
        trades: bool = False,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[QueryTradesRequest, QueryTradesResponse]:
        """Query trades info.

        Retrieve information about specific trades/fills.

        Args:
            txid: Transaction ID(s) to query info about (20 maximum, string or list)
            trades: Whether or not to include trades related to position in output
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.query_trades(
            ...     txid="THVRQM-33VKH-UCI7BS"
            ... )
            >>> if response.is_success:
            ...     for trade_id, trade in response.success.trades.items():
            ...         print(f"{trade_id}: {trade.vol} @ {trade.price}")
        """
        request = QueryTradesRequest(txid=txid, trades=trades, rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_open_positions(
        self,
        txid: str | list[str] | None = None,
        docalcs: bool = False,
        consolidation: Literal["market"] | None = None,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetOpenPositionsRequest, GetOpenPositionsResponse]:
        """Get open positions.

        Get information about open margin positions.

        Args:
            txid: Transaction ID(s) to limit output to (string or list)
            docalcs: Whether to include P&L calculations
            consolidation: Consolidate positions by market/pair
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_open_positions(docalcs=True)
            >>> if response.is_success:
            ...     for pos_id, position in response.success.positions.items():
            ...         print(f"{pos_id}: {position.pair} - Net: {position.net}")
        """
        request = GetOpenPositionsRequest(
            txid=txid,
            docalcs=docalcs,
            consolidation=consolidation,
            rebase_multiplier=rebase_multiplier,
        )
        return self._request(request)

    def get_ledgers(
        self,
        asset: str | list[str] | None = None,
        aclass: str | None = None,
        type: LEDGER_TYPE | None = None,
        start: int | None = None,
        end: int | None = None,
        ofs: int | None = None,
        without_count: bool = False,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetLedgersRequest, GetLedgersResponse]:
        """Get ledgers info.

        Retrieve information about ledger entries. 50 results are returned at a time,
        the most recent by default.

        Args:
            asset: Filter by asset(s) (string or list)
            aclass: Filter output by asset class (Default: currency)
            type: Type of ledger to retrieve
            start: Starting unix timestamp or ledger ID of results (exclusive)
            end: Ending unix timestamp or ledger ID of results (inclusive)
            ofs: Result offset for pagination
            without_count: If true, does not retrieve count of ledger entries
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_ledgers(
            ...     asset="XXBT", type="deposit"
            ... )
            >>> if response.is_success:
            ...     print(f"Total count: {response.success.count}")
            ...     for ledger_id, ledger in response.success.ledger.items():
            ...         print(f"{ledger_id}: {ledger.type} - {ledger.amount}")
        """
        request = GetLedgersRequest(
            asset=asset,
            aclass=aclass,
            type=type,
            start=start,
            end=end,
            ofs=ofs,
            without_count=without_count,
            rebase_multiplier=rebase_multiplier,
        )
        return self._request(request)

    def query_ledgers(
        self,
        id: str | list[str],
        trades: bool = False,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[QueryLedgersRequest, QueryLedgersResponse]:
        """Query ledgers.

        Retrieve information about specific ledger entries.

        Args:
            id: Ledger ID(s) to query info about (20 maximum, string or list)
            trades: Whether or not to include trades related to position in output
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.query_ledgers(
            ...     id="LQFCFM-ELBSU-CMH5EI"
            ... )
            >>> if response.is_success:
            ...     for ledger_id, ledger in response.success.ledger.items():
            ...         print(f"{ledger_id}: {ledger.amount}")
        """
        request = QueryLedgersRequest(id=id, trades=trades, rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def get_trade_volume(
        self,
        pair: str | list[str] | None = None,
        rebase_multiplier: REBASE_MULTIPLIER | None = None,
    ) -> Tuple[GetTradeVolumeRequest, GetTradeVolumeResponse]:
        """Get trade volume.

        Returns 30 day USD trading volume and resulting fee schedule for any asset
        pair(s) provided.

        Args:
            pair: Asset pair(s) to get fee info on (string or list)
            rebase_multiplier: Optional parameter for viewing xstocks data

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_trade_volume(
            ...     pair=["XXBTZUSD", "XETHZUSD"]
            ... )
            >>> if response.is_success:
            ...     print(f"Volume: {response.success.volume} {response.success.currency}")
            ...     for pair, fee_info in response.success.fees.items():
            ...         print(f"{pair}: {fee_info.fee}%")
        """
        request = GetTradeVolumeRequest(pair=pair, rebase_multiplier=rebase_multiplier)
        return self._request(request)

    def request_export(
        self,
        report: EXPORT_REPORT_TYPE,
        description: str,
        format: EXPORT_FORMAT = "CSV",
        fields: str | list[str] | None = None,
        starttm: int | None = None,
        endtm: int | None = None,
    ) -> Tuple[RequestExportRequest, RequestExportResponse]:
        """Request export report.

        Request export of trades or ledgers.

        Args:
            report: Type of data to export (trades or ledgers)
            description: Description for the export
            format: File format to export (CSV or TSV, default: CSV)
            fields: Fields to include (string or list)
            starttm: UNIX timestamp for report start time
            endtm: UNIX timestamp for report end time

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.request_export(
            ...     report="trades",
            ...     description="Q1 2023 trades",
            ...     format="CSV"
            ... )
            >>> if response.is_success:
            ...     print(f"Export ID: {response.success.id}")
        """
        request = RequestExportRequest(
            report=report,
            description=description,
            format=format,
            fields=fields,
            starttm=starttm,
            endtm=endtm,
        )
        return self._request(request)

    def get_export_status(
        self, report: EXPORT_REPORT_TYPE
    ) -> Tuple[GetExportStatusRequest, GetExportStatusResponse]:
        """Get export report status.

        Get status of requested data exports.

        Args:
            report: Type of reports to inquire about (trades or ledgers)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.get_export_status(report="trades")
            >>> if response.is_success:
            ...     for export in response.success.reports:
            ...         print(f"{export.id}: {export.status} - {export.descr}")
        """
        request = GetExportStatusRequest(report=report)
        return self._request(request)

    def retrieve_export(self, id: str) -> Tuple[RetrieveExportRequest, RetrieveExportResponse]:
        """Retrieve data export.

        Retrieve a processed data export.

        Args:
            id: Report ID to retrieve

        Returns:
            Tuple of request and response objects

        Note:
            This endpoint returns binary data (zip file). Access it via
            response.success.report which contains the raw bytes.

        Example:
            >>> request, response = client.account.retrieve_export(id="TCJA")
            >>> if response.is_success:
            ...     with open("export.zip", "wb") as f:
            ...         f.write(response.success.report)
        """
        request = RetrieveExportRequest(id=id)
        return self._request(request)

    def delete_export(
        self, id: str, type: EXPORT_DELETE_TYPE
    ) -> Tuple[DeleteExportRequest, DeleteExportResponse]:
        """Delete export report.

        Delete exported trades/ledgers report.

        Args:
            id: ID of report to delete or cancel
            type: 'delete' (for processed reports) or 'cancel' (for queued/processing reports)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.delete_export(
            ...     id="TCJA", type="delete"
            ... )
            >>> if response.is_success:
            ...     if response.success.delete:
            ...         print("Report deleted successfully")
            ...     if response.success.cancel:
            ...         print("Report cancelled successfully")
        """
        request = DeleteExportRequest(id=id, type=type)
        return self._request(request)

    def create_subaccount(
        self,
        username: str,
        email: str,
    ) -> Tuple[CreateSubaccountRequest, CreateSubaccountResponse]:
        """Create a trading subaccount.

        Args:
            username: Username for the subaccount
            email: Email address for the subaccount

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.create_subaccount(
            ...     username="subaccount1",
            ...     email="sub@example.com"
            ... )
            >>> if response.is_success:
            ...     print(f"Subaccount created: {response.success.result}")
        """
        request = CreateSubaccountRequest(username=username, email=email)
        return self._request(request)

    def account_transfer(
        self,
        asset: str,
        amount: str | float,
        from_account: str,
        to_account: str,
        asset_class: ASSET_CLASS = "currency",
    ) -> Tuple[AccountTransferRequest, AccountTransferResponse]:
        """Transfer funds between accounts.

        Transfer funds to and from master and subaccounts.

        Args:
            asset: Asset being transferred
            amount: Amount to transfer
            from_account: IBAN of the source account
            to_account: IBAN of the destination account
            asset_class: Asset class (default: currency)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.account.account_transfer(
            ...     asset="ZUSD",
            ...     amount="1000.00",
            ...     from_account="AB12-CD34-EF56-GH78",
            ...     to_account="IJ90-KL12-MN34-OP56"
            ... )
            >>> if response.is_success:
            ...     print(f"Transfer ID: {response.success.transfer.transfer_id}")
            ...     print(f"Status: {response.success.transfer.status}")
        """
        request = AccountTransferRequest(
            asset=asset,
            amount=str(amount),
            from_account=from_account,
            to_account=to_account,
            asset_class=asset_class,
        )
        return self._request(request)
