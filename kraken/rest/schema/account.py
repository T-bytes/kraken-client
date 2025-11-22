import json
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator

from kraken.rest.schema import validators
from kraken.rest.schema.base import (
    BaseRequestSchema,
    BaseResponseWrapper,
    BaseSchema,
    ResponseErrorSchema,
)

REBASE_MULTIPLIER = Literal["rebased", "base"]
ORDER_STATUS = Literal["pending", "open", "closed", "canceled", "expired"]
LEDGER_TYPE = Literal[
    "all",
    "trade",
    "deposit",
    "withdrawal",
    "transfer",
    "margin",
    "adjustment",
    "rollover",
    "spend",
    "receive",
    "settled",
    "staking",
    "reward",
    "dividend",
    "sale",
    "conversion",
    "nfttrade",
    "nftcreatorFee",
    "nftrebate",
    "custodytransfer",
]
EXPORT_REPORT_TYPE = Literal["trades", "ledgers"]
EXPORT_FORMAT = Literal["CSV", "TSV"]
EXPORT_DELETE_TYPE = Literal["cancel", "delete"]
AMEND_TYPE = Literal["original", "user", "restated"]
EXPORT_STATUS = Literal["Queued", "Processing", "Processed"]
CLOSETIME_TYPE = Literal["open", "close", "both"]


class GetBalanceRequest(BaseRequestSchema):
    """Request schema for Get Account Balance endpoint.

    Retrieve all cash balances, net of pending withdrawals.

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = GetBalanceRequest()
        >>> request = GetBalanceRequest(rebase_multiplier="base")
    """

    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class GetBalanceSuccess(BaseSchema):
    """Successful response from Get Account Balance endpoint.

    Contains all cash balances keyed by asset name.
    """

    balances: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping asset names to balance strings.",
    )


class GetBalanceResponse(BaseResponseWrapper[GetBalanceSuccess]):
    """Combined response wrapper for Get Account Balance API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetBalanceResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = GetBalanceSuccess(balances=result)
        return cls(success=success_data)


class GetExtendedBalanceRequest(BaseRequestSchema):
    """Request schema for Get Extended Balance endpoint.

    Retrieve all extended account balances, including credits and held amounts.
    Balance available for trading is calculated as:
    available_balance = balance + credit - credit_used - hold_trade

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = GetExtendedBalanceRequest()
    """

    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class ExtendedBalanceAsset(BaseSchema):
    """Extended balance information for a single asset."""

    balance: str = Field(..., description="Total balance amount for the asset.")
    credit: str = Field(
        ...,
        description="Total credit amount (only applicable if account has a credit line).",
    )
    credit_used: str = Field(
        ...,
        description="Used credit amount (only applicable if account has a credit line).",
    )
    hold_trade: str = Field(..., description="Total held amount for the asset.")


class GetExtendedBalanceSuccess(BaseSchema):
    """Successful response from Get Extended Balance endpoint."""

    assets: dict[str, ExtendedBalanceAsset] = Field(
        default_factory=dict,
        description="Dictionary mapping asset names to extended balance information.",
    )


class GetExtendedBalanceResponse(BaseResponseWrapper[GetExtendedBalanceSuccess]):
    """Combined response wrapper for Get Extended Balance API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetExtendedBalanceResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        assets = {
            asset_name: ExtendedBalanceAsset(**asset_data)
            for asset_name, asset_data in result.items()
        }
        success_data = GetExtendedBalanceSuccess(assets=assets)
        return cls(success=success_data)


class GetCreditLinesRequest(BaseRequestSchema):
    """Request schema for Get Credit Lines endpoint.

    Retrieve all credit line details for VIPs with this functionality.

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = GetCreditLinesRequest()
    """

    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class CreditLineAssetDetails(BaseSchema):
    """Credit line details for a single asset."""

    balance: str = Field(..., description="Current balance for the asset.")
    credit_limit: str = Field(..., description="Maximum credit limit for the asset.")
    credit_used: str = Field(..., description="Amount of credit currently used.")
    available_credit: str = Field(..., description="Available credit remaining.")


class CreditLineLimitsMonitor(BaseSchema):
    """Overall credit limits monitoring information."""

    total_credit_usd: str = Field(..., description="Total credit limit in USD.")
    total_credit_used_usd: str = Field(..., description="Total credit used in USD.")
    total_collateral_value_usd: str = Field(..., description="Total collateral value in USD.")
    equity_usd: str = Field(..., description="Account equity in USD.")
    ongoing_balance: str = Field(..., description="Ongoing balance amount.")
    debt_to_equity: str = Field(..., description="Debt to equity ratio.")


class GetCreditLinesSuccess(BaseSchema):
    """Successful response from Get Credit Lines endpoint."""

    asset_details: dict[str, CreditLineAssetDetails] = Field(
        default_factory=dict,
        description="Dictionary mapping asset names to credit line details.",
    )
    limits_monitor: CreditLineLimitsMonitor | None = Field(
        default=None, description="Overall credit limits monitoring information."
    )


class GetCreditLinesResponse(BaseResponseWrapper[GetCreditLinesSuccess]):
    """Combined response wrapper for Get Credit Lines API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetCreditLinesResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        asset_details = {
            asset_name: CreditLineAssetDetails(**asset_data)
            for asset_name, asset_data in result.get("asset_details", {}).items()
        }

        limits_monitor = None
        if "limits_monitor" in result:
            limits_monitor = CreditLineLimitsMonitor(**result["limits_monitor"])

        success_data = GetCreditLinesSuccess(
            asset_details=asset_details, limits_monitor=limits_monitor
        )
        return cls(success=success_data)


class GetTradeBalanceRequest(BaseRequestSchema):
    """Request schema for Get Trade Balance endpoint.

    Retrieve a summary of collateral balances, margin position valuations,
    equity and margin level.

    API Key Permissions Required:
        Orders and Trades - Query open orders & trades

    Usage Example:
        >>> request = GetTradeBalanceRequest()
        >>> request = GetTradeBalanceRequest(asset="ZUSD")
    """

    asset: str | None = Field(
        default=None,
        description="Base asset used to determine balance (Default: ZUSD).",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class GetTradeBalanceSuccess(BaseSchema):
    """Successful response from Get Trade Balance endpoint."""

    eb: str = Field(..., description="Equivalent balance (combined balance of all currencies).")
    tb: str = Field(..., description="Trade balance (combined balance of all equity currencies).")
    m: str = Field(..., description="Margin amount of open positions.")
    n: str = Field(..., description="Unrealized net profit/loss of open positions.")
    c: str = Field(..., description="Cost basis of open positions.")
    v: str = Field(..., description="Current floating valuation of open positions.")
    e: str = Field(..., description="Equity (trade balance + unrealized net profit/loss).")
    mf: str = Field(
        ...,
        description="Free margin (equity - initial margin, maximum margin available to open new positions).",
    )
    ml: str | None = Field(
        default=None, description="Margin level ((equity / initial margin) * 100)."
    )
    uv: str | None = Field(
        default=None,
        description="Unexecuted value (value of unfilled and partially filled orders).",
    )


class GetTradeBalanceResponse(BaseResponseWrapper[GetTradeBalanceSuccess]):
    """Combined response wrapper for Get Trade Balance API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetTradeBalanceResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = GetTradeBalanceSuccess(**result)
        return cls(success=success_data)


class GetOpenOrdersRequest(BaseRequestSchema):
    """Request schema for Get Open Orders endpoint.

    Retrieve information about currently open orders.

    API Key Permissions Required:
        Orders and Trades - Query open orders & trades

    Usage Example:
        >>> request = GetOpenOrdersRequest()
        >>> request = GetOpenOrdersRequest(trades=True, userref=12345)
    """

    trades: bool = Field(
        default=False,
        description="Whether or not to include trades related to position in output.",
    )
    userref: int | None = Field(
        default=None, description="Restrict results to given user reference id."
    )
    cl_ord_id: str | None = Field(
        default=None, description="Comma delimited list of client order IDs to limit output to."
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("cl_ord_id", mode="before")
    @classmethod
    def normalize_cl_ord_id(cls, value: str | list[str] | None) -> str | None:
        """Normalize cl_ord_id to comma-separated string."""
        if value is None:
            return None
        if isinstance(value, list):
            return ",".join(value)
        return value


class OrderDescription(BaseSchema):
    """Order description details."""

    pair: str = Field(..., description="Asset pair.")
    type: str = Field(..., description="Order type (buy/sell).")
    ordertype: str = Field(..., description="Order type (limit, market, etc).")
    price: str = Field(..., description="Primary price.")
    price2: str = Field(..., description="Secondary price.")
    leverage: str = Field(..., description="Amount of leverage.")
    order: str = Field(..., description="Order description.")
    close: str | None = Field(default=None, description="Conditional close order description.")


class OrderInfo(BaseSchema):
    """Information about a single order."""

    refid: str | None = Field(default=None, description="Referral order transaction ID.")
    userref: int | None = Field(default=None, description="User reference ID.")
    status: ORDER_STATUS = Field(..., description="Status of order.")
    opentm: float = Field(..., description="Unix timestamp of when order was placed.")
    starttm: int | None = Field(
        default=None, description="Unix timestamp of order start time (or 0 if not set)."
    )
    expiretm: int | None = Field(
        default=None, description="Unix timestamp of order end time (or 0 if not set)."
    )
    descr: OrderDescription = Field(..., description="Order description info.")
    vol: str = Field(..., description="Volume of order (base currency unless viqc set in oflags).")
    vol_exec: str = Field(
        ..., description="Volume executed (base currency unless viqc set in oflags)."
    )
    cost: str = Field(
        ..., description="Total cost (quote currency unless unless viqc set in oflags)."
    )
    fee: str = Field(..., description="Total fee (quote currency).")
    price: str = Field(
        ..., description="Average price (quote currency unless viqc set in oflags)."
    )
    stopprice: str | None = Field(
        default=None, description="Stop price (quote currency, for trailing stops)."
    )
    limitprice: str | None = Field(
        default=None,
        description="Triggered limit price (quote currency, when limit based order type triggered).",
    )
    misc: str = Field(..., description="Miscellaneous comma delimited list of order info.")
    oflags: str = Field(..., description="Comma delimited list of order flags.")
    trigger: str | None = Field(default=None, description="Trigger type.")
    trades: list[str] | None = Field(
        default=None,
        description="Array of trade IDs related to order (if trades info requested and data available).",
    )


class GetOpenOrdersSuccess(BaseSchema):
    """Successful response from Get Open Orders endpoint."""

    open: dict[str, OrderInfo] = Field(
        default_factory=dict,
        description="Dictionary of open orders keyed by order transaction ID.",
    )


class GetOpenOrdersResponse(BaseResponseWrapper[GetOpenOrdersSuccess]):
    """Combined response wrapper for Get Open Orders API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetOpenOrdersResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        open_orders = {}
        for order_id, order_data in result.get("open", {}).items():
            if "descr" in order_data:
                order_data["descr"] = OrderDescription(**order_data["descr"])
            open_orders[order_id] = OrderInfo(**order_data)

        success_data = GetOpenOrdersSuccess(open=open_orders)
        return cls(success=success_data)


class GetClosedOrdersRequest(BaseRequestSchema):
    """Request schema for Get Closed Orders endpoint.

    Retrieve information about orders that have been closed (filled or cancelled).
    50 results are returned at a time, the most recent by default.

    API Key Permissions Required:
        Orders and Trades - Query closed orders & trades

    Usage Example:
        >>> request = GetClosedOrdersRequest()
        >>> request = GetClosedOrdersRequest(userref=12345, start=1609459200)
    """

    trades: bool = Field(
        default=False,
        description="Whether or not to include trades related to position in output.",
    )
    userref: int | None = Field(
        default=None, description="Restrict results to given user reference id."
    )
    start: int | None = Field(
        default=None,
        description="Starting unix timestamp or order tx ID of results (exclusive).",
    )
    end: int | None = Field(
        default=None,
        description="Ending unix timestamp or order tx ID of results (inclusive).",
    )
    ofs: int | None = Field(default=None, description="Result offset for pagination.")
    closetime: CLOSETIME_TYPE | None = Field(
        default=None, description="Which time to use for filtering."
    )
    consolidate_taker: bool = Field(
        default=False,
        description="Whether or not to consolidate trades by individual taker trades.",
    )
    without_count: bool = Field(
        default=False,
        description="Whether or not to include the count of order matching criteria in output.",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class GetClosedOrdersSuccess(BaseSchema):
    """Successful response from Get Closed Orders endpoint."""

    closed: dict[str, OrderInfo] = Field(
        default_factory=dict,
        description="Dictionary of closed orders keyed by order transaction ID.",
    )
    count: int | None = Field(
        default=None, description="Amount of available order info matching criteria."
    )


class GetClosedOrdersResponse(BaseResponseWrapper[GetClosedOrdersSuccess]):
    """Combined response wrapper for Get Closed Orders API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetClosedOrdersResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        closed_orders = {}
        for order_id, order_data in result.get("closed", {}).items():
            if "descr" in order_data:
                order_data["descr"] = OrderDescription(**order_data["descr"])
            closed_orders[order_id] = OrderInfo(**order_data)

        success_data = GetClosedOrdersSuccess(closed=closed_orders, count=result.get("count"))
        return cls(success=success_data)


class QueryOrdersRequest(BaseRequestSchema):
    """Request schema for Query Orders Info endpoint.

    Retrieve information about specific orders.

    API Key Permissions Required:
        Orders and Trades - Query open orders & trades or Query closed orders & trades

    Usage Example:
        >>> request = QueryOrdersRequest(txid="OQCLML-BW3P3-BUCMWZ")
        >>> request = QueryOrdersRequest(txid="OQCLML-BW3P3-BUCMWZ,OQCLML-BW3P3-BUCMW1")
    """

    txid: str | None = Field(
        default=None,
        description="Comma delimited list of transaction IDs to query info about (50 maximum).",
    )
    trades: bool = Field(
        default=False,
        description="Whether or not to include trades related to position in output.",
    )
    userref: int | None = Field(
        default=None, description="Restrict results to given user reference id."
    )
    consolidate_taker: bool = Field(
        default=False,
        description="Whether or not to consolidate trades by individual taker trades.",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("txid", mode="before")
    @classmethod
    def normalize_txid(cls, value: str | list[str] | None) -> str | None:
        """Normalize txid to comma-separated string."""
        if value is None:
            return None
        if isinstance(value, list):
            return ",".join(value)
        return value


class QueryOrdersSuccess(BaseSchema):
    """Successful response from Query Orders Info endpoint."""

    orders: dict[str, OrderInfo] = Field(
        default_factory=dict,
        description="Dictionary of orders keyed by order transaction ID.",
    )


class QueryOrdersResponse(BaseResponseWrapper[QueryOrdersSuccess]):
    """Combined response wrapper for Query Orders Info API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "QueryOrdersResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        orders = {}
        for order_id, order_data in result.items():
            if "descr" in order_data:
                order_data["descr"] = OrderDescription(**order_data["descr"])
            orders[order_id] = OrderInfo(**order_data)

        success_data = QueryOrdersSuccess(orders=orders)
        return cls(success=success_data)


class GetOrderAmendsRequest(BaseRequestSchema):
    """Request schema for Get Order Amends endpoint.

    Retrieves an audit trail of amend transactions on the specified order.
    The list is ordered by ascending amend timestamp.

    API Key Permissions Required:
        Orders and Trades - Query open orders & trades or Query closed orders & trades

    Usage Example:
        >>> request = GetOrderAmendsRequest(order_id="OQCLML-BW3P3-BUCMWZ")
    """

    order_id: str = Field(..., description="The Kraken order identifier for the amended order.")
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class AmendInfo(BaseSchema):
    """Information about a single order amendment."""

    amend_id: str = Field(..., description="Unique identifier for the amendment.")
    amend_type: AMEND_TYPE = Field(..., description="Type of amendment.")
    order_qty: str | None = Field(default=None, description="Updated order quantity.")
    display_qty: str | None = Field(default=None, description="Updated display quantity.")
    remaining_qty: str | None = Field(default=None, description="Remaining quantity.")
    limit_price: str | None = Field(default=None, description="Updated limit price.")
    trigger_price: str | None = Field(default=None, description="Updated trigger price.")
    reason: str | None = Field(default=None, description="Reason for the amendment.")
    post_only: bool | None = Field(default=None, description="Post-only flag.")
    timestamp: int = Field(..., description="Unix timestamp of the amendment.")


class GetOrderAmendsSuccess(BaseSchema):
    """Successful response from Get Order Amends endpoint."""

    count: int = Field(..., description="Number of amendments.")
    amends: list[AmendInfo] = Field(default_factory=list, description="List of amendment records.")


class GetOrderAmendsResponse(BaseResponseWrapper[GetOrderAmendsSuccess]):
    """Combined response wrapper for Get Order Amends API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetOrderAmendsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        amends = [AmendInfo(**amend_data) for amend_data in result.get("amends", [])]
        success_data = GetOrderAmendsSuccess(count=result["count"], amends=amends)
        return cls(success=success_data)


class GetTradesHistoryRequest(BaseRequestSchema):
    """Request schema for Get Trades History endpoint.

    Retrieve information about trades/fills. 50 results are returned at a time,
    the most recent by default.

    API Key Permissions Required:
        Orders and Trades - Query closed orders & trades

    Usage Example:
        >>> request = GetTradesHistoryRequest()
        >>> request = GetTradesHistoryRequest(type="all", start=1609459200)
    """

    type: str | None = Field(
        default=None,
        description="Type of trade (all/any position/no position/closing position/closed position).",
    )
    trades: bool = Field(
        default=False,
        description="Whether or not to include trades related to position in output.",
    )
    start: int | None = Field(
        default=None,
        description="Starting unix timestamp or trade tx ID of results (exclusive).",
    )
    end: int | None = Field(
        default=None,
        description="Ending unix timestamp or trade tx ID of results (inclusive).",
    )
    ofs: int | None = Field(default=None, description="Result offset for pagination.")
    consolidation_type: str | None = Field(default=None, description="Type of consolidation.")
    ledgers: bool = Field(
        default=False, description="Whether or not to include related ledgers in output."
    )
    without_count: bool = Field(
        default=False,
        description="Whether or not to include the count of orders and trades that satisfy the input filter.",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )


class TradeInfo(BaseSchema):
    """Information about a single trade."""

    ordertxid: str = Field(..., description="Order responsible for execution of trade.")
    postxid: str | None = Field(default=None, description="Position ID (if applicable).")
    pair: str = Field(..., description="Asset pair.")
    time: float = Field(..., description="Unix timestamp of trade.")
    type: str = Field(..., description="Type of order (buy/sell).")
    ordertype: str = Field(..., description="Order type.")
    price: str = Field(..., description="Average price order was executed at (quote currency).")
    cost: str = Field(..., description="Total cost of order (quote currency).")
    fee: str = Field(..., description="Total fee (quote currency).")
    vol: str = Field(..., description="Volume (base currency).")
    margin: str = Field(..., description="Initial margin (quote currency).")
    leverage: str | None = Field(default=None, description="Leverage amount.")
    misc: str = Field(..., description="Comma delimited list of miscellaneous info.")
    ledgers: list[str] | None = Field(default=None, description="Related ledger transaction IDs.")
    trade_id: int | None = Field(default=None, description="Numeric trade ID.")
    maker: bool | None = Field(default=None, description="Whether trade was maker or taker.")
    posstatus: str | None = Field(default=None, description="Position status (if applicable).")
    cprice: float | None = Field(
        default=None, description="Average close price of position (if applicable)."
    )
    ccost: str | None = Field(
        default=None, description="Total close cost of position (if applicable)."
    )
    cfee: float | None = Field(
        default=None, description="Total close fee of position (if applicable)."
    )
    cvol: str | None = Field(
        default=None, description="Total close volume of position (if applicable)."
    )
    cmargin: float | None = Field(
        default=None, description="Total close margin of position (if applicable)."
    )
    net: float | None = Field(default=None, description="Total P&L of position (if applicable).")
    trades: list[str] | None = Field(
        default=None, description="List of closing trades for position (if applicable)."
    )


class GetTradesHistorySuccess(BaseSchema):
    """Successful response from Get Trades History endpoint."""

    trades: dict[str, TradeInfo] = Field(
        default_factory=dict,
        description="Dictionary of trades keyed by trade transaction ID.",
    )
    count: int | None = Field(
        default=None, description="Amount of available trades info matching criteria."
    )


class GetTradesHistoryResponse(BaseResponseWrapper[GetTradesHistorySuccess]):
    """Combined response wrapper for Get Trades History API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetTradesHistoryResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        trades = {
            trade_id: TradeInfo(**trade_data)
            for trade_id, trade_data in result.get("trades", {}).items()
        }

        success_data = GetTradesHistorySuccess(trades=trades, count=result.get("count"))
        return cls(success=success_data)


class QueryTradesRequest(BaseRequestSchema):
    """Request schema for Query Trades Info endpoint.

    Retrieve information about specific trades/fills.

    API Key Permissions Required:
        Orders and Trades - Query closed orders & trades

    Usage Example:
        >>> request = QueryTradesRequest(txid="THVRQM-33VKH-UCI7BS")
    """

    txid: str = Field(
        ...,
        description="Comma delimited list of transaction IDs to query info about (20 maximum).",
    )
    trades: bool = Field(
        default=False,
        description="Whether or not to include trades related to position in output.",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("txid", mode="before")
    @classmethod
    def normalize_txid(cls, value: str | list[str]) -> str:
        """Normalize txid to comma-separated string."""
        if isinstance(value, list):
            return ",".join(value)
        return value


class QueryTradesSuccess(BaseSchema):
    """Successful response from Query Trades Info endpoint."""

    trades: dict[str, TradeInfo] = Field(
        default_factory=dict,
        description="Dictionary of trades keyed by trade transaction ID.",
    )


class QueryTradesResponse(BaseResponseWrapper[QueryTradesSuccess]):
    """Combined response wrapper for Query Trades Info API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "QueryTradesResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        trades = {trade_id: TradeInfo(**trade_data) for trade_id, trade_data in result.items()}

        success_data = QueryTradesSuccess(trades=trades)
        return cls(success=success_data)


class GetOpenPositionsRequest(BaseRequestSchema):
    """Request schema for Get Open Positions endpoint.

    Get information about open margin positions.

    API Key Permissions Required:
        Orders and Trades - Query open orders & trades

    Usage Example:
        >>> request = GetOpenPositionsRequest()
        >>> request = GetOpenPositionsRequest(docalcs=True)
    """

    txid: str | None = Field(
        default=None, description="Comma delimited list of txids to limit output to."
    )
    docalcs: bool = Field(default=False, description="Whether to include P&L calculations.")
    consolidation: Literal["market"] | None = Field(
        default=None, description="Consolidate positions by market/pair."
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("txid", mode="before")
    @classmethod
    def normalize_txid(cls, value: str | list[str] | None) -> str | None:
        """Normalize txid to comma-separated string."""
        if value is None:
            return None
        if isinstance(value, list):
            return ",".join(value)
        return value


class PositionInfo(BaseSchema):
    """Information about a single open position."""

    ordertxid: str = Field(..., description="Order ID responsible for the position.")
    posstatus: Literal["open"] = Field(..., description="Position status.")
    pair: str = Field(..., description="Asset pair.")
    time: float = Field(..., description="Unix timestamp of trade.")
    type: str = Field(..., description="Type of order used to open position (buy/sell).")
    ordertype: str = Field(..., description="Order type used to open the position.")
    cost: str = Field(
        ..., description="Opening cost of position (quote currency unless viqc set in oflags)."
    )
    fee: str = Field(..., description="Opening fee of position (quote currency).")
    vol: str = Field(..., description="Position volume (base currency unless viqc set in oflags).")
    vol_closed: str = Field(
        ..., description="Position volume closed (base currency unless viqc set in oflags)."
    )
    margin: str = Field(..., description="Initial margin (quote currency).")
    value: str | None = Field(
        default=None, description="Current value of remaining position (if docalcs requested)."
    )
    net: str | None = Field(
        default=None, description="Unrealized P&L of remaining position (if docalcs requested)."
    )
    terms: str | None = Field(default=None, description="Funding cost and term of position.")
    rollovertm: str | None = Field(
        default=None, description="Unix timestamp of next margin rollover fee."
    )
    misc: str = Field(..., description="Comma delimited list of miscellaneous info.")
    oflags: str = Field(..., description="Comma delimited list of order flags.")


class GetOpenPositionsSuccess(BaseSchema):
    """Successful response from Get Open Positions endpoint."""

    positions: dict[str, PositionInfo] = Field(
        default_factory=dict,
        description="Dictionary of positions keyed by position transaction ID.",
    )


class GetOpenPositionsResponse(BaseResponseWrapper[GetOpenPositionsSuccess]):
    """Combined response wrapper for Get Open Positions API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetOpenPositionsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        positions = {pos_id: PositionInfo(**pos_data) for pos_id, pos_data in result.items()}

        success_data = GetOpenPositionsSuccess(positions=positions)
        return cls(success=success_data)


class GetLedgersRequest(BaseRequestSchema):
    """Request schema for Get Ledgers Info endpoint.

    Retrieve information about ledger entries. 50 results are returned at a time,
    the most recent by default.

    API Key Permissions Required:
        Data - Query ledger entries

    Usage Example:
        >>> request = GetLedgersRequest()
        >>> request = GetLedgersRequest(asset="XXBT", type="deposit")
    """

    asset: str | None = Field(
        default=None,
        description="Filter output by asset or comma delimited list of assets.",
    )
    aclass: str | None = Field(
        default=None, description="Filter output by asset class (Default: currency)."
    )
    type: LEDGER_TYPE | None = Field(default=None, description="Type of ledger to retrieve.")
    start: int | None = Field(
        default=None,
        description="Starting unix timestamp or ledger ID of results (exclusive).",
    )
    end: int | None = Field(
        default=None,
        description="Ending unix timestamp or ledger ID of results (inclusive).",
    )
    ofs: int | None = Field(default=None, description="Result offset for pagination.")
    without_count: bool = Field(
        default=False,
        description="If true, does not retrieve count of ledger entries.",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("asset", mode="before")
    @classmethod
    def normalize_asset(cls, value: str | list[str] | None) -> str | None:
        """Normalize asset to comma-separated string."""
        if value is None:
            return None
        if isinstance(value, list):
            return ",".join(value)
        return value


class LedgerInfo(BaseSchema):
    """Information about a single ledger entry."""

    refid: str = Field(..., description="Reference ID.")
    time: float = Field(..., description="Unix timestamp of ledger entry.")
    type: str = Field(..., description="Type of ledger entry.")
    subtype: str | None = Field(
        default=None, description="Additional information about the type of ledger entry."
    )
    aclass: str = Field(..., description="Asset class.")
    asset: str = Field(..., description="Asset.")
    amount: str = Field(..., description="Transaction amount.")
    fee: str = Field(..., description="Transaction fee.")
    balance: str = Field(..., description="Resulting balance.")


class GetLedgersSuccess(BaseSchema):
    """Successful response from Get Ledgers Info endpoint."""

    ledger: dict[str, LedgerInfo] = Field(
        default_factory=dict,
        description="Dictionary of ledgers keyed by ledger ID.",
    )
    count: int | None = Field(
        default=None, description="Amount of available ledger info matching criteria."
    )


class GetLedgersResponse(BaseResponseWrapper[GetLedgersSuccess]):
    """Combined response wrapper for Get Ledgers Info API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetLedgersResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        # Handle both "Ledger" and "ledger" keys
        ledger_data = result.get("Ledger", result.get("ledger", {}))
        ledger = {
            ledger_id: LedgerInfo(**ledger_info) for ledger_id, ledger_info in ledger_data.items()
        }

        success_data = GetLedgersSuccess(ledger=ledger, count=result.get("count"))
        return cls(success=success_data)


class QueryLedgersRequest(BaseRequestSchema):
    """Request schema for Query Ledgers endpoint.

    Retrieve information about specific ledger entries.

    API Key Permissions Required:
        Data - Query ledger entries

    Usage Example:
        >>> request = QueryLedgersRequest(id="LQFCFM-ELBSU-CMH5EI")
    """

    id: str = Field(
        ...,
        description="Comma delimited list of ledger IDs to query info about (20 maximum).",
    )
    trades: bool = Field(
        default=False,
        description="Whether or not to include trades related to position in output.",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: str | list[str]) -> str:
        """Normalize id to comma-separated string."""
        if isinstance(value, list):
            return ",".join(value)
        return value


class QueryLedgersSuccess(BaseSchema):
    """Successful response from Query Ledgers endpoint."""

    ledger: dict[str, LedgerInfo] = Field(
        default_factory=dict,
        description="Dictionary of ledgers keyed by ledger ID.",
    )


class QueryLedgersResponse(BaseResponseWrapper[QueryLedgersSuccess]):
    """Combined response wrapper for Query Ledgers API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "QueryLedgersResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        ledger = {
            ledger_id: LedgerInfo(**ledger_info) for ledger_id, ledger_info in result.items()
        }

        success_data = QueryLedgersSuccess(ledger=ledger)
        return cls(success=success_data)


class GetTradeVolumeRequest(BaseRequestSchema):
    """Request schema for Get Trade Volume endpoint.

    Returns 30 day USD trading volume and resulting fee schedule for any asset
    pair(s) provided. Fees are included in the output for all pairs, whether or
    not specified.

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = GetTradeVolumeRequest()
        >>> request = GetTradeVolumeRequest(pair="XXBTZUSD,XETHZUSD")
    """

    pair: str | None = Field(
        default=None,
        description="Comma delimited list of asset pairs to get fee info on (optional).",
    )
    rebase_multiplier: REBASE_MULTIPLIER | None = Field(
        default=None,
        description="Optional parameter for viewing xstocks data (rebased or base).",
    )

    @field_validator("pair", mode="before")
    @classmethod
    def normalize_pair(cls, value: str | list[str] | None) -> str | None:
        """Normalize pair to comma-separated string."""
        if value is None:
            return None
        if isinstance(value, list):
            return ",".join(value)
        return value


class FeeInfo(BaseSchema):
    """Fee information for a trading pair."""

    fee: str = Field(..., description="Current fee in percent.")
    min_fee: str = Field(..., description="Minimum fee for pair (if not fixed fee).")
    max_fee: str = Field(..., description="Maximum fee for pair (if not fixed fee).")
    next_fee: str = Field(..., description="Next tier's fee for pair (if not fixed fee).")
    tier_volume: str = Field(..., description="Volume level of current tier (if not fixed fee).")
    next_volume: str = Field(..., description="Volume level of next tier (if not fixed fee).")


class GetTradeVolumeSuccess(BaseSchema):
    """Successful response from Get Trade Volume endpoint."""

    currency: str = Field(..., description="Fee volume currency (will always be USD).")
    volume: str = Field(..., description="Current fee discount volume in USD.")
    fees: dict[str, FeeInfo] = Field(
        default_factory=dict, description="Dictionary of fee information for trading pairs."
    )
    fees_maker: dict[str, FeeInfo] = Field(
        default_factory=dict,
        description="Dictionary of maker fee information for trading pairs.",
    )


class GetTradeVolumeResponse(BaseResponseWrapper[GetTradeVolumeSuccess]):
    """Combined response wrapper for Get Trade Volume API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetTradeVolumeResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        fees = {pair: FeeInfo(**fee_data) for pair, fee_data in result.get("fees", {}).items()}
        fees_maker = {
            pair: FeeInfo(**fee_data) for pair, fee_data in result.get("fees_maker", {}).items()
        }

        success_data = GetTradeVolumeSuccess(
            currency=result["currency"],
            volume=result["volume"],
            fees=fees,
            fees_maker=fees_maker,
        )
        return cls(success=success_data)


class RequestExportRequest(BaseRequestSchema):
    """Request schema for Request Export Report endpoint.

    Request export of trades or ledgers.

    API Key Permissions Required:
        Data - Export data

    Usage Example:
        >>> request = RequestExportRequest(
        ...     report="trades",
        ...     description="Q1 2023 trades"
        ... )
    """

    report: EXPORT_REPORT_TYPE = Field(
        ..., description="Type of data to export (trades or ledgers)."
    )
    format: EXPORT_FORMAT = Field(default="CSV", description="File format to export (CSV or TSV).")
    description: str = Field(..., description="Description for the export.")
    fields: str | None = Field(
        default=None, description="Comma-delimited list of fields to include."
    )
    starttm: int | None = Field(
        default=None,
        description="UNIX timestamp for report start time (default 1st of the current month).",
    )
    endtm: int | None = Field(
        default=None,
        description="UNIX timestamp for report end time (default now).",
    )

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, value: str | list[str] | None) -> str | None:
        """Normalize fields to comma-separated string."""
        if value is None:
            return None
        if isinstance(value, list):
            return ",".join(value)
        return value


class RequestExportSuccess(BaseSchema):
    """Successful response from Request Export Report endpoint."""

    id: str = Field(..., description="Report ID.")


class RequestExportResponse(BaseResponseWrapper[RequestExportSuccess]):
    """Combined response wrapper for Request Export Report API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "RequestExportResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = RequestExportSuccess(id=result["id"])
        return cls(success=success_data)


class GetExportStatusRequest(BaseRequestSchema):
    """Request schema for Get Export Report Status endpoint.

    Get status of requested data exports.

    API Key Permissions Required:
        Data - Export data

    Usage Example:
        >>> request = GetExportStatusRequest(report="trades")
    """

    report: EXPORT_REPORT_TYPE = Field(
        ..., description="Type of reports to inquire about (trades or ledgers)."
    )


class ExportStatusItem(BaseSchema):
    """Status information for a single export report."""

    id: str = Field(..., description="Report ID.")
    descr: str = Field(..., description="Report description.")
    format: str = Field(..., description="Report format (CSV or TSV).")
    report: str = Field(..., description="Report type (trades or ledgers).")
    subtype: str | None = Field(default=None, description="Report subtype.")
    status: EXPORT_STATUS = Field(..., description="Report status.")
    flags: str | None = Field(default=None, description="Report flags.")
    fields: str | None = Field(default=None, description="Comma-delimited list of fields.")
    createdtm: str = Field(..., description="Unix timestamp of report creation.")
    expirestm: str | None = Field(default=None, description="Unix timestamp of report expiration.")
    starttm: str | None = Field(default=None, description="Report start time.")
    completedtm: str | None = Field(default=None, description="Report completion time.")
    datastarttm: str | None = Field(default=None, description="Report data start time.")
    dataendtm: str | None = Field(default=None, description="Report data end time.")
    aclass: str | None = Field(default=None, description="Asset class.")
    asset: str | None = Field(default=None, description="Asset name.")


class GetExportStatusSuccess(BaseSchema):
    """Successful response from Get Export Report Status endpoint."""

    reports: list[ExportStatusItem] = Field(
        default_factory=list, description="List of export report status items."
    )


class GetExportStatusResponse(BaseResponseWrapper[GetExportStatusSuccess]):
    """Combined response wrapper for Get Export Report Status API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetExportStatusResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        reports = [ExportStatusItem(**item) for item in result]
        success_data = GetExportStatusSuccess(reports=reports)
        return cls(success=success_data)


class RetrieveExportRequest(BaseRequestSchema):
    """Request schema for Retrieve Data Export endpoint.

    Retrieve a processed data export.

    API Key Permissions Required:
        Data - Export data

    Usage Example:
        >>> request = RetrieveExportRequest(id="TCJA")
    """

    id: str = Field(..., description="Report ID to retrieve.")


class RetrieveExportSuccess(BaseSchema):
    """Successful response from Retrieve Data Export endpoint."""

    report: bytes = Field(..., description="Binary zip archive containing the report.")


class RetrieveExportResponse(BaseResponseWrapper[RetrieveExportSuccess]):
    """Combined response wrapper for Retrieve Data Export API calls.

    Note: This endpoint returns binary data (zip file), not JSON.
    """

    @classmethod
    def from_response(cls, response: bytes | dict | str) -> "RetrieveExportResponse":
        """Parse Kraken API response into the appropriate response model.

        Note: For binary responses, the response will be raw bytes.
        For error responses, it will be a JSON dict/str.
        """
        # If response is bytes, it's the successful binary report
        if isinstance(response, bytes):
            success_data = RetrieveExportSuccess(report=response)
            return cls(success=success_data)

        # Otherwise, parse as potential error response
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        # If we get here, it's an unexpected format
        raise ValueError("Unexpected response format for RetrieveExport")


class DeleteExportRequest(BaseRequestSchema):
    """Request schema for Delete Export Report endpoint.

    Delete exported trades/ledgers report.

    API Key Permissions Required:
        Data - Export data

    Usage Example:
        >>> request = DeleteExportRequest(id="TCJA", type="delete")
    """

    id: str = Field(..., description="ID of report to delete or cancel.")
    type: EXPORT_DELETE_TYPE = Field(
        ...,
        description="'delete' (can only be used for reports that have already been processed) or 'cancel' (for queued or processing reports).",
    )


class DeleteExportSuccess(BaseSchema):
    """Successful response from Delete Export Report endpoint."""

    delete: bool | None = Field(default=None, description="Whether deletion was successful.")
    cancel: bool | None = Field(default=None, description="Whether cancellation was successful.")


class DeleteExportResponse(BaseResponseWrapper[DeleteExportSuccess]):
    """Combined response wrapper for Delete Export Report API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "DeleteExportResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = DeleteExportSuccess(
            delete=result.get("delete"), cancel=result.get("cancel")
        )
        return cls(success=success_data)


ASSET_CLASS = Literal["currency", "tokenized_asset"]
TRANSFER_STATUS = Literal["pending", "complete"]


class CreateSubaccountRequest(BaseRequestSchema):
    """Request schema for Create Subaccount endpoint.

    API Key Permissions Required:
        Funds permissions - Withdraw

    Usage Example:
        >>> request = CreateSubaccountRequest(
        ...     username="subaccount1",
        ...     email="sub@example.com"
        ... )
    """

    username: str = Field(..., description="Username for the subaccount.")
    email: str = Field(..., description="Email address for the subaccount.")


class CreateSubaccountSuccess(BaseSchema):
    """Successful response from Create Subaccount endpoint."""

    result: bool = Field(
        ...,
        description="Whether subaccount creation was successful or not.",
    )


class CreateSubaccountResponse(BaseResponseWrapper[CreateSubaccountSuccess]):
    """Combined response wrapper for Create Subaccount API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "CreateSubaccountResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        success_data = CreateSubaccountSuccess(result=result)
        return cls(success=success_data)


class AccountTransferRequest(BaseRequestSchema):
    """Request schema for Account Transfer endpoint.

    API Key Permissions Required:
        Funds permissions - Withdraw

    Usage Example:
        >>> request = AccountTransferRequest(
        ...     asset="XBT",
        ...     amount="2.54",
        ...     from_account="ABCD 1234 EFGH 5678",
        ...     to_account="IJKL 0987 MNOP 6543"
        ... )
    """

    asset: str = Field(..., description="Asset being transferred.")
    asset_class: ASSET_CLASS = Field(
        default="currency",
        description="Specify the asset class of the asset being transferred.",
    )
    amount: str = Field(..., description="Amount of asset to transfer.")
    from_account: str = Field(
        ...,
        validation_alias=AliasChoices("from_account", "from"),
        serialization_alias="from",
        description="IBAN of the source account.",
    )
    to_account: str = Field(
        ...,
        validation_alias=AliasChoices("to_account", "to"),
        serialization_alias="to",
        description="IBAN of the destination account.",
    )


class TransferResult(BaseSchema):
    """Transfer result details."""

    transfer_id: str = Field(..., description="Transfer ID.")
    status: TRANSFER_STATUS = Field(
        ...,
        description="Transfer status, either 'pending' or 'complete'.",
    )


class AccountTransferSuccess(BaseSchema):
    """Successful response from Account Transfer endpoint."""

    transfer: TransferResult = Field(
        ...,
        description="Transfer result information.",
    )


class AccountTransferResponse(BaseResponseWrapper[AccountTransferSuccess]):
    """Combined response wrapper for Account Transfer API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "AccountTransferResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        transfer_result = TransferResult(**result)
        success_data = AccountTransferSuccess(transfer=transfer_result)
        return cls(success=success_data)
