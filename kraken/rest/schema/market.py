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
