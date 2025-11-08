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


class AssetInfo(BaseSchema):
    """Individual asset information from Kraken API.

    Contains details about a specific asset including its classification,
    display name, and decimal precision for calculations and display.
    """

    aclass: Literal["currency", "tokenied_asset"] = Field(
        ...,
        description="Asset class.",
    )
    altname: str = Field(
        ...,
        description="Alternate/display name for the asset (e.g., 'BTC' for 'XXBT').",
    )
    decimals: int = Field(
        ...,
        description="Scaling decimal places for record keeping and calculations.",
    )
    display_decimals: int = Field(
        ...,
        description="Scaling decimal places for output display.",
    )
    status: Literal[
        "enabled", "deposit_only", "withdrawl_only", "funding_temporarily_disabled"
    ] = Field(..., description="Status of asset.")
    collateral_value: float | None = Field(
        None, description="Valuation as margin collateral, if applicable."
    )


class GetAssetInfoRequest(BaseRequestSchema):
    """Schema for Kraken GetAssetInfo API request.

    This schema validates and prepares data for submission to Kraken's
    GetAssetInfo (Assets) API endpoint, which retrieves information about
    assets available for deposit, withdrawal, trading, and earn activities.

    Important Notes:
        - This is a public endpoint that requires no authentication.
        - All parameters are optional.
        - The 'asset' parameter accepts both a comma-delimited string or a list of strings.
        - Use to_api_dict() to serialize for API submission.

    Usage Examples:
        Get all assets:
        >>> asset_info_request = GetAssetInfoRequest()
        >>> data = asset_info_request.to_api_dict()
        >>> response = client.request("Assets", data=data)

        Get specific assets (string format):
        >>> asset_info_request = GetAssetInfoRequest(asset="XBT,ETH,USD")
        >>> data = asset_info_request.to_api_dict()
        >>> response = client.request("Assets", data=data)

        Get specific assets (list format):
        >>> asset_info_request = GetAssetInfoRequest(asset=["XBT", "ETH", "USD"])
        >>> data = asset_info_request.to_api_dict()
        >>> # Result: {"asset": "XBT,ETH,USD"}

        Filter by asset class:
        >>> asset_info_request = GetAssetInfoRequest(aclass="currency")
        >>> response = client.request("Assets", data=asset_info_request.to_api_dict())

        Async usage:
        >>> asset_info_request = GetAssetInfoRequest(asset=["XBT", "ETH"])
        >>> response = await client.arequest("Assets", data=asset_info_request.to_api_dict())
    """

    asset: str | list[str] | None = Field(
        default=None,
        description="Comma-delimited string or list of assets to get info on (e.g., 'XBT,ETH,USD' or ['XBT', 'ETH', 'USD']).",
    )
    aclass: Literal["currency", "tokenized_asset"] = Field(
        default=None,
        description="Asset class filter (e.g., 'currency').",
    )

    @field_validator("asset", mode="before")
    @classmethod
    def normalize_asset_list(cls, value: str | list[str] | None) -> str | None:
        """Convert asset list to comma-delimited string format.

        Accepts either a string (returned as-is) or a list of strings
        (converted to comma-delimited format). Validates that list items
        are non-empty strings and removes duplicates while preserving order.

        Args:
            value: Either a comma-delimited string, a list of asset strings, or None

        Returns:
            Comma-delimited string or None

        Raises:
            ValueError: If list contains empty strings or non-string values
        """
        return validators.normalize_comma_separated_list(value)


class GetAssetInfoSuccess(BaseSchema):
    """Successful GetAssetInfo response from Kraken API.

    Contains a dictionary of assets keyed by asset name, with each value
    containing detailed information about that asset.
    """

    assets: dict[str, AssetInfo] = Field(
        default_factory=dict,
        description="Dictionary mapping asset names to their information.",
    )


class GetAssetInfoResponse(BaseResponseWrapper[GetAssetInfoSuccess]):
    """Combined response wrapper for GetAssetInfo API calls.

    This wrapper handles both success and error cases from the Kraken API.
    Use the `is_success` property to determine the outcome and access the
    appropriate `success` or `error` attribute.
    """

    @classmethod
    def from_response(cls, response: dict | str) -> "GetAssetInfoResponse":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            GetAssetInfoResponse with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)
        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(failure=error_data)
        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        assets = {asset_name: AssetInfo(**asset_data) for asset_name, asset_data in result.items()}
        success_data = GetAssetInfoSuccess(assets=assets)
        return cls(success=success_data)


class GetSystemStatusRequest(BaseRequestSchema):
    """Schema for Kraken GetSystemStatus API request.

    This schema validates and prepares data for submission to Kraken's
    GetSystemStatus API endpoint, which retrieves the current system status
    or trading mode. This endpoint is useful for checking if the exchange
    is online or in a restricted mode.

    Important Notes:
        - This is a public endpoint that requires no authentication.
        - No parameters are required for this endpoint.
        - Use to_api_dict() to serialize for API submission (though it will
          return an empty dict since no parameters are needed).

    Usage Examples:
        Get system status:
        >>> system_status_request = GetSystemStatusRequest()
        >>> data = system_status_request.to_api_dict()
        >>> response = client.request("SystemStatus", data=data)

        Async usage:
        >>> system_status_request = GetSystemStatusRequest()
        >>> response = await client.arequest("SystemStatus", data=system_status_request.to_api_dict())
    """

    pass


class GetSystemStatusSuccess(BaseSchema):
    """Successful GetSystemStatus response from Kraken API.

    Contains the current system status or trading mode and the timestamp
    when the status was generated.
    """

    status: Literal["online", "maintenance", "cancel_only", "post_only"] = Field(
        ...,
        description=(
            "Current system status. 'online': normal operation; "
            "'maintenance': offline for scheduled maintenance; "
            "'cancel_only': only cancellations allowed; "
            "'post_only': only post-only limit orders allowed."
        ),
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when the status was generated (e.g., '2021-03-22T17:18:03Z').",
    )


class GetSystemStatusResponse(BaseResponseWrapper[GetSystemStatusSuccess]):
    """Combined response wrapper for GetSystemStatus API calls.

    This wrapper handles both success and error cases from the Kraken API.
    Use the `is_success` property to determine the outcome and access the
    appropriate `success` or `error` attribute.
    """

    @classmethod
    def from_response(cls, response: dict | str) -> "GetSystemStatusResponse":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            GetSystemStatusResponse with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)
        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(failure=error_data)

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")
        success_data = GetSystemStatusSuccess(
            status=result["status"],
            timestamp=result["timestamp"],
        )
        return cls(success=success_data)


class GetServerTimeRequest(BaseRequestSchema):
    """Schema for Kraken GetServerTime API request.

    This schema validates and prepares data for submission to Kraken's
    GetServerTime API endpoint, which retrieves the server's current time.
    This endpoint is useful for approximating the skew time between the
    server and client.

    Important Notes:
        - This is a public endpoint that requires no authentication.
        - No parameters are required for this endpoint.
        - Use to_api_dict() to serialize for API submission (though it will
          return an empty dict since no parameters are needed).

    Usage Examples:
        Get server time:
        >>> server_time_request = GetServerTimeRequest()
        >>> data = server_time_request.to_api_dict()
        >>> response = client.request("Time", data=data)

        Async usage:
        >>> server_time_request = GetServerTimeRequest()
        >>> response = await client.arequest("Time", data=server_time_request.to_api_dict())
    """

    pass


class GetServerTimeSuccess(BaseSchema):
    """Successful GetServerTime response from Kraken API.

    Contains the server's current time in both Unix timestamp and RFC 1123 formats.
    """

    unixtime: int = Field(
        ...,
        description="Server time as Unix timestamp (seconds since epoch).",
    )
    rfc1123: str = Field(
        ...,
        description="Server time in RFC 1123 format (e.g., 'Tue, 29 Sep 2021 13:27:06 GMT').",
    )


class GetServerTimeResponse(BaseResponseWrapper[GetServerTimeSuccess]):
    """Combined response wrapper for GetServerTime API calls.

    This wrapper handles both success and error cases from the Kraken API.
    Use the `is_success` property to determine the outcome and access the
    appropriate `success` or `error` attribute.
    """

    @classmethod
    def from_response(cls, response: dict | str) -> "GetServerTimeResponse":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            GetServerTimeResponse with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)
        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(failure=error_data)

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")
        success_data = GetServerTimeSuccess(
            unixtime=result["unixtime"],
            rfc1123=result["rfc1123"],
        )
        return cls(success=success_data)


class AssetPairInfo(BaseSchema):
    """Individual asset pair information from Kraken API.

    Contains detailed information about a specific trading pair including
    its base and quote assets, decimal precision for various calculations,
    trading status, and minimum order requirements. Additional fields may
    be present depending on the 'info' parameter used in the request.
    """

    altname: str = Field(
        ...,
        description="Alternate pair name.",
    )
    wsname: str | None = Field(
        None,
        description="WebSocket pair name (if available).",
    )
    aclass_base: str = Field(
        ...,
        description="Asset class of base component.",
    )
    base: str = Field(
        ...,
        description="Asset ID of base component.",
    )
    aclass_quote: str = Field(
        ...,
        description="Asset class of quote component.",
    )
    quote: str = Field(
        ...,
        description="Asset ID of quote component.",
    )
    pair_decimals: int = Field(
        ...,
        description="Number of decimal places for prices in this pair.",
    )
    cost_decimals: int = Field(
        ...,
        description="Number of decimal places for cost of trades in pair (quote asset terms).",
    )
    lot_decimals: int = Field(
        ...,
        description="Number of decimal places for volume (base asset terms).",
    )
    lot_multiplier: int = Field(
        ...,
        description="Amount to multiply lot volume by to get currency volume.",
    )
    leverage_buy: list[int] | None = Field(
        None,
        description="Array of leverage amounts available when buying.",
    )
    leverage_sell: list[int] | None = Field(
        None,
        description="Array of leverage amounts available when selling.",
    )
    fees: list[list[int | float]] | None = Field(
        None,
        description="Fee schedule array in [<volume>, <percent fee>] tuples.",
    )
    fees_maker: list[list[int | float]] | None = Field(
        None,
        description="Maker fee schedule array in [<volume>, <percent fee>] tuples (if on maker/taker).",
    )
    fee_volume_currency: str | None = Field(
        None,
        description="Volume discount currency.",
    )
    margin_call: int | None = Field(
        None,
        description="Margin call level.",
    )
    margin_stop: int | None = Field(
        None,
        description="Stop-out/liquidation margin level.",
    )
    ordermin: str = Field(
        ...,
        description="Minimum order size (in terms of base currency).",
    )
    costmin: str = Field(
        ...,
        description="Minimum order cost (in terms of quote currency).",
    )
    tick_size: str = Field(
        ...,
        description="Minimum increment between valid price levels.",
    )
    status: Literal["online", "cancel_only", "post_only", "limit_only", "reduce_only"] = Field(
        ...,
        description="Status of asset. Possible values: online, cancel_only, post_only, limit_only, reduce_only.",
    )
    long_position_limit: int | None = Field(
        None,
        description="Maximum long margin position size (in terms of base currency).",
    )
    short_position_limit: int | None = Field(
        None,
        description="Maximum short margin position size (in terms of base currency).",
    )


class GetAssetPairsRequest(BaseRequestSchema):
    """Schema for Kraken GetAssetPairs API request.

    This schema validates and prepares data for submission to Kraken's
    GetAssetPairs (AssetPairs) API endpoint, which retrieves information
    about tradeable asset pairs available on the exchange.

    Important Notes:
        - This is a public endpoint that requires no authentication.
        - All parameters are optional.
        - The 'pair' parameter accepts both a comma-delimited string or a list of strings.
        - The 'info' parameter controls which fields appear in the response.
        - Use to_api_dict() to serialize for API submission.

    Usage Examples:
        Get all asset pairs:
        >>> pairs_request = GetAssetPairsRequest()
        >>> data = pairs_request.to_api_dict()
        >>> response = client.request("AssetPairs", data=data)

        Get specific pairs (string format):
        >>> pairs_request = GetAssetPairsRequest(pair="BTC/USD,ETH/BTC")
        >>> data = pairs_request.to_api_dict()
        >>> response = client.request("AssetPairs", data=data)

        Get specific pairs (list format):
        >>> pairs_request = GetAssetPairsRequest(pair=["BTC/USD", "ETH/BTC"])
        >>> data = pairs_request.to_api_dict()
        >>> # Result: {"pair": "BTC/USD,ETH/BTC"}

        Filter by asset class:
        >>> pairs_request = GetAssetPairsRequest(aclass_base="currency")
        >>> response = client.request("AssetPairs", data=pairs_request.to_api_dict())

        Get leverage information:
        >>> pairs_request = GetAssetPairsRequest(pair="BTC/USD", info="leverage")
        >>> response = client.request("AssetPairs", data=pairs_request.to_api_dict())

        Get fee information:
        >>> pairs_request = GetAssetPairsRequest(info="fees")
        >>> response = client.request("AssetPairs", data=pairs_request.to_api_dict())

        Filter by country:
        >>> pairs_request = GetAssetPairsRequest(country_code="GB")
        >>> response = client.request("AssetPairs", data=pairs_request.to_api_dict())

        Async usage:
        >>> pairs_request = GetAssetPairsRequest(pair=["BTC/USD", "ETH/BTC"])
        >>> response = await client.arequest("AssetPairs", data=pairs_request.to_api_dict())
    """

    pair: str | list[str] | None = Field(
        default=None,
        description="Asset pairs to get data for (e.g., 'BTC/USD,ETH/BTC' or ['BTC/USD', 'ETH/BTC']).",
    )
    aclass_base: Literal["currency", "tokenized_asset"] | None = Field(
        default=None,
        description="Filters the asset class to retrieve. 'currency' = spot currency pairs, 'tokenized_asset' = tokenized asset pairs (e.g., xstocks). Default: 'currency'.",
    )
    info: Literal["info", "leverage", "fees", "margin"] | None = Field(
        default=None,
        description="Info to retrieve: 'info' (all info, default), 'leverage' (leverage info), 'fees' (fee schedule), 'margin' (margin info).",
    )
    country_code: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code to filter pairs available in the provided country/region (e.g., 'GB').",
    )

    @field_validator("pair", mode="before")
    @classmethod
    def normalize_pair_list(cls, value: str | list[str] | None) -> str | None:
        """Convert pair list to comma-delimited string format.

        Accepts either a string (returned as-is) or a list of strings
        (converted to comma-delimited format). Validates that list items
        are non-empty strings and removes duplicates while preserving order.

        Args:
            value: Either a comma-delimited string, a list of pair strings, or None

        Returns:
            Comma-delimited string or None

        Raises:
            ValueError: If list contains empty strings or non-string values
        """
        return validators.normalize_comma_separated_list(value)


class GetAssetPairsSuccess(BaseSchema):
    """Successful GetAssetPairs response from Kraken API.

    Contains a dictionary of asset pairs keyed by pair name, with each value
    containing detailed information about that trading pair.
    """

    pairs: dict[str, AssetPairInfo] = Field(
        default_factory=dict,
        description="Dictionary mapping asset pair names to their information.",
    )


class GetAssetPairsResponse(BaseResponseWrapper[GetAssetPairsSuccess]):
    """Combined response wrapper for GetAssetPairs API calls.

    This wrapper handles both success and error cases from the Kraken API.
    Use the `is_success` property to determine the outcome and access the
    appropriate `success` or `error` attribute.
    """

    @classmethod
    def from_response(cls, response: dict | str) -> "GetAssetPairsResponse":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            GetAssetPairsResponse with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)
        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(failure=error_data)
        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        pairs = {pair_name: AssetPairInfo(**pair_data) for pair_name, pair_data in result.items()}
        success_data = GetAssetPairsSuccess(pairs=pairs)
        return cls(success=success_data)


class TickerInfo(BaseSchema):
    """Individual ticker information for a trading pair from Kraken API.

    Contains real-time market data including bid/ask prices, last trade,
    volume, price ranges, and trade counts. Prices start at midnight UTC
    and statistics are provided for both 'today' and 'last 24 hours'.
    """

    a: list[str] = Field(
        ...,
        description="Ask array [price, whole lot volume, lot volume]. Price and volumes as strings for precision.",
    )
    b: list[str] = Field(
        ...,
        description="Bid array [price, whole lot volume, lot volume]. Price and volumes as strings for precision.",
    )
    c: list[str] = Field(
        ...,
        description="Last trade closed array [price, lot volume]. Price and volume as strings for precision.",
    )
    v: list[str] = Field(
        ...,
        description="Volume array [today, last 24 hours]. Volumes as strings for precision.",
    )
    p: list[str] = Field(
        ...,
        description="Volume weighted average price array [today, last 24 hours]. Prices as strings for precision.",
    )
    t: list[int] = Field(
        ...,
        description="Number of trades array [today, last 24 hours].",
    )
    l: list[str] = Field(
        ...,
        description="Low price array [today, last 24 hours]. Prices as strings for precision.",
    )
    h: list[str] = Field(
        ...,
        description="High price array [today, last 24 hours]. Prices as strings for precision.",
    )
    o: str = Field(
        ...,
        description="Today's opening price. Price as string for precision.",
    )


class GetTickerInformationRequest(BaseRequestSchema):
    """Schema for Kraken GetTickerInformation API request.

    This schema validates and prepares data for submission to Kraken's
    GetTickerInformation (Ticker) API endpoint, which retrieves ticker
    information for all or requested markets.

    Important Notes:
        - This is a public endpoint that requires no authentication.
        - All parameters are optional.
        - Today's prices start at midnight UTC.
        - Leaving the 'pair' parameter blank will return tickers for all tradeable assets on Kraken.
        - The 'pair' parameter accepts both a comma-delimited string or a list of strings.
        - The 'asset_class' parameter is required for tokenized pairs (e.g., xstocks).
        - Use to_api_dict() to serialize for API submission.

    Usage Examples:
        Get all tickers:
        >>> ticker_request = GetTickerInformationRequest()
        >>> data = ticker_request.to_api_dict()
        >>> response = client.request("Ticker", data=data)

        Get specific pairs (string format):
        >>> ticker_request = GetTickerInformationRequest(pair="XBTUSD,ETHUSD")
        >>> data = ticker_request.to_api_dict()
        >>> response = client.request("Ticker", data=data)

        Get specific pairs (list format):
        >>> ticker_request = GetTickerInformationRequest(pair=["XBTUSD", "ETHUSD"])
        >>> data = ticker_request.to_api_dict()
        >>> # Result: {"pair": "XBTUSD,ETHUSD"}

        Filter by asset class (tokenized assets):
        >>> ticker_request = GetTickerInformationRequest(asset_class="tokenized_asset")
        >>> response = client.request("Ticker", data=ticker_request.to_api_dict())

        Get specific tokenized pair:
        >>> ticker_request = GetTickerInformationRequest(
        ...     pair="TSLA/USD",
        ...     asset_class="tokenized_asset"
        ... )
        >>> response = client.request("Ticker", data=ticker_request.to_api_dict())

        Async usage:
        >>> ticker_request = GetTickerInformationRequest(pair=["XBTUSD", "ETHUSD"])
        >>> response = await client.arequest("Ticker", data=ticker_request.to_api_dict())
    """

    pair: str | list[str] | None = Field(
        default=None,
        description="Comma-delimited string or list of asset pairs to get data for (e.g., 'XBTUSD,ETHUSD' or ['XBTUSD', 'ETHUSD']). Default: all tradeable pairs.",
    )
    asset_class: Literal["tokenized_asset", "forex"] | None = Field(
        default=None,
        description="Asset class filter. Required for tokenized pairs (e.g., xstocks). If asset_class is provided without pair, all pairs for that asset class will be returned. Default: 'forex'.",
    )

    @field_validator("pair", mode="before")
    @classmethod
    def normalize_pair_list(cls, value: str | list[str] | None) -> str | None:
        """Convert pair list to comma-delimited string format.

        Accepts either a string (returned as-is) or a list of strings
        (converted to comma-delimited format). Validates that list items
        are non-empty strings and removes duplicates while preserving order.

        Args:
            value: Either a comma-delimited string, a list of pair strings, or None

        Returns:
            Comma-delimited string or None

        Raises:
            ValueError: If list contains empty strings or non-string values
        """
        return validators.normalize_comma_separated_list(value)


class GetTickerInformationSuccess(BaseSchema):
    """Successful GetTickerInformation response from Kraken API.

    Contains a dictionary of tickers keyed by pair name, with each value
    containing real-time market data for that trading pair.
    """

    tickers: dict[str, TickerInfo] = Field(
        default_factory=dict,
        description="Dictionary mapping asset pair names to their ticker information.",
    )


class GetTickerInformationResponse(BaseResponseWrapper[GetTickerInformationSuccess]):
    """Combined response wrapper for GetTickerInformation API calls.

    This wrapper handles both success and error cases from the Kraken API.
    Use the `is_success` property to determine the outcome and access the
    appropriate `success` or `error` attribute.
    """

    @classmethod
    def from_response(cls, response: dict | str) -> "GetTickerInformationResponse":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            GetTickerInformationResponse with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)
        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(failure=error_data)
        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        tickers = {
            pair_name: TickerInfo(**ticker_data) for pair_name, ticker_data in result.items()
        }
        success_data = GetTickerInformationSuccess(tickers=tickers)
        return cls(success=success_data)


class OHLCData(BaseSchema):
    """Individual OHLC (Open, High, Low, Close) candle data from Kraken API.

    Represents a single time period's trading data including open/high/low/close prices,
    volume-weighted average price (VWAP), trading volume, and number of trades.
    All price values are returned as strings for precision.
    """

    time: int = Field(
        ...,
        description="Unix timestamp for the start of the interval.",
    )
    open: str = Field(
        ...,
        description="Opening price for the interval. Price as string for precision.",
    )
    high: str = Field(
        ...,
        description="Highest price during the interval. Price as string for precision.",
    )
    low: str = Field(
        ...,
        description="Lowest price during the interval. Price as string for precision.",
    )
    close: str = Field(
        ...,
        description="Closing price for the interval. Price as string for precision.",
    )
    vwap: str = Field(
        ...,
        description="Volume-weighted average price for the interval. Price as string for precision.",
    )
    volume: str = Field(
        ...,
        description="Trading volume for the interval. Volume as string for precision.",
    )
    count: int = Field(
        ...,
        description="Number of trades executed during the interval.",
    )

    @classmethod
    def from_array(cls, data: list) -> "OHLCData":
        """Parse OHLC data from Kraken's array format.

        Args:
            data: Array in format [time, open, high, low, close, vwap, volume, count]

        Returns:
            OHLCData instance

        Raises:
            ValueError: If array doesn't have exactly 8 elements
        """
        if len(data) != 8:
            raise ValueError(f"OHLC data array must have exactly 8 elements, got {len(data)}")

        return cls(
            time=data[0],
            open=data[1],
            high=data[2],
            low=data[3],
            close=data[4],
            vwap=data[5],
            volume=data[6],
            count=data[7],
        )


class GetOHLCDataRequest(BaseRequestSchema):
    """Schema for Kraken GetOHLCData API request.

    This schema validates and prepares data for submission to Kraken's
    GetOHLCData (OHLC) API endpoint, which retrieves OHLC (Open, High, Low, Close)
    market data. The last entry in the OHLC array is for the current, not-yet-committed
    time frame and will always be present, regardless of the value of 'since'.

    Important Notes:
        - This is a public endpoint that requires no authentication.
        - The 'pair' parameter is required.
        - The 'pair' parameter accepts both a comma-delimited string or a list of strings.
        - The 'interval' parameter controls the time frame in minutes (default: 1).
        - The 'since' parameter is for incremental updates - returns committed OHLC data since the given ID.
        - The 'asset_class' parameter is required for non-crypto pairs (e.g., tokenized assets).
        - Use to_api_dict() to serialize for API submission.

    Usage Examples:
        Get OHLC data for a single pair:
        >>> ohlc_request = GetOHLCDataRequest(pair="XBTUSD")
        >>> data = ohlc_request.to_api_dict()
        >>> response = client.request("OHLC", data=data)

        Get OHLC data with specific interval (60 minutes):
        >>> ohlc_request = GetOHLCDataRequest(pair="XBTUSD", interval=60)
        >>> data = ohlc_request.to_api_dict()
        >>> response = client.request("OHLC", data=data)

        Get OHLC data for multiple pairs (list format):
        >>> ohlc_request = GetOHLCDataRequest(pair=["XBTUSD", "ETHUSD"], interval=15)
        >>> data = ohlc_request.to_api_dict()
        >>> # Result: {"pair": "XBTUSD,ETHUSD", "interval": 15}

        Get incremental updates since a timestamp:
        >>> ohlc_request = GetOHLCDataRequest(pair="XBTUSD", since=1688671200)
        >>> data = ohlc_request.to_api_dict()
        >>> response = client.request("OHLC", data=data)

        Get data for tokenized asset:
        >>> ohlc_request = GetOHLCDataRequest(
        ...     pair="TSLA/USD",
        ...     asset_class="tokenized_asset",
        ...     interval=1440
        ... )
        >>> response = client.request("OHLC", data=ohlc_request.to_api_dict())

        Async usage:
        >>> ohlc_request = GetOHLCDataRequest(pair="XBTUSD", interval=5)
        >>> response = await client.arequest("OHLC", data=ohlc_request.to_api_dict())
    """

    pair: str | list[str] = Field(
        ...,
        description="Comma-delimited string or list of asset pairs to get data for (e.g., 'XBTUSD' or ['XBTUSD', 'ETHUSD']).",
    )
    interval: int | None = Field(
        default=None,
        description="Time frame interval in minutes. Possible values: [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]. Default: 1.",
    )
    since: int | None = Field(
        default=None,
        description="Return OHLC entries since the given timestamp (intended for incremental updates). Unix timestamp.",
    )
    asset_class: Literal["tokenized_asset"] | None = Field(
        default=None,
        description="Asset class filter. Required for tokenized pairs (e.g., xstocks).",
    )

    @field_validator("pair", mode="before")
    @classmethod
    def normalize_pair_list(cls, value: str | list[str]) -> str:
        """Convert pair list to comma-delimited string format.

        Accepts either a string (returned as-is) or a list of strings
        (converted to comma-delimited format). Validates that list items
        are non-empty strings and removes duplicates while preserving order.

        Args:
            value: Either a comma-delimited string or a list of pair strings

        Returns:
            Comma-delimited string

        Raises:
            ValueError: If list contains empty strings or non-string values
        """
        return validators.normalize_comma_separated_list(value)

    @field_validator("interval", mode="before")
    @classmethod
    def validate_interval(cls, value: int | None) -> int | None:
        """Validate interval is within allowed values.

        Args:
            value: Interval value in minutes

        Returns:
            Validated interval as integer, or None if input is None

        Raises:
            ValueError: If interval is not in allowed set [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
        """
        return validators.validate_ohlc_interval(value)


class GetOHLCDataSuccess(BaseSchema):
    """Successful GetOHLCData response from Kraken API.

    Contains a dictionary of OHLC data keyed by pair name, with each value
    containing an array of OHLC candles for that trading pair. Also includes
    the 'last' timestamp for incremental polling.
    """

    ohlc_data: dict[str, list[OHLCData]] = Field(
        default_factory=dict,
        description="Dictionary mapping asset pair names to their OHLC data arrays.",
    )
    last: int = Field(
        ...,
        description="ID to be used as 'since' when polling for new, committed OHLC data.",
    )


class GetOHLCDataResponse(BaseResponseWrapper[GetOHLCDataSuccess]):
    """Combined response wrapper for GetOHLCData API calls.

    This wrapper handles both success and error cases from the Kraken API.
    Use the `is_success` property to determine the outcome and access the
    appropriate `success` or `error` attribute.
    """

    @classmethod
    def from_response(cls, response: dict | str) -> "GetOHLCDataResponse":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            GetOHLCDataResponse with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)
        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(failure=error_data)
        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        # Extract 'last' field
        last = result.get("last")
        if last is None:
            raise ValueError("Response result missing 'last' field")

        # Parse OHLC data for each pair (all keys except 'last')
        ohlc_data = {}
        for pair_name, pair_data in result.items():
            if pair_name == "last":
                continue
            # Parse array of OHLC arrays into list of OHLCData objects
            ohlc_data[pair_name] = [OHLCData.from_array(candle) for candle in pair_data]

        success_data = GetOHLCDataSuccess(ohlc_data=ohlc_data, last=last)
        return cls(success=success_data)
