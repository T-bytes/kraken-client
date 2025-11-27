"""Earn REST API schema definitions for staking and earning operations."""

import json
from typing import Literal

from pydantic import AliasChoices, Field, field_validator

from kraken.rest.schema.base import (
    BaseRequestSchema,
    BaseResponseWrapper,
    BaseSchema,
    ResponseErrorSchema,
)

LOCK_TYPE = Literal["flex", "bonded", "timed", "instant"]


class ListEarnStrategiesRequest(BaseRequestSchema):
    """Request schema for List Earn Strategies endpoint.

    List earn strategies along with their parameters.

    API Key Permissions Required:
        Earn Funds OR Query Funds

    Usage Example:
        >>> request = ListEarnStrategiesRequest()
        >>> request = ListEarnStrategiesRequest(asset="XBT", limit=10)
    """

    ascending: bool | None = Field(
        default=None,
        description="Whether to sort ascending or descending by asset name.",
    )
    asset: str | None = Field(
        default=None,
        description="Filter strategies by asset name.",
    )
    cursor: str | bool | None = Field(
        default=None,
        description="true/false to enable/disable paginated response (boolean) or cursor for next page of results (string).",
    )
    limit: int | None = Field(
        default=None,
        description="Number of results to include per page.",
    )
    lock_type: list[LOCK_TYPE] | None = Field(
        default=None,
        description="Filter strategies by lock type (flex, bonded, timed, instant).",
    )


class EarnStrategy(BaseSchema):
    """Information about a single earn strategy."""

    id: str = Field(..., description="The unique identifier per strategy.")
    asset: str = Field(..., description="Asset class.")
    lock_type: str = Field(
        ...,
        description="Type of the strategy (flex, bonded, timed, instant).",
    )
    apr_estimate: dict | None = Field(
        default=None,
        description="Fee applied when allocating to this strategy. Optional field, not always present.",
    )
    user_min_allocation: str | None = Field(
        default=None,
        description="Minimum amount to allocate for a user.",
    )
    allocation_fee: str | None = Field(
        default=None,
        description="Fee applied when allocating to this strategy.",
    )
    deallocation_fee: str | None = Field(
        default=None,
        description="Fee applied when deallocating from this strategy.",
    )
    auto_compound: dict | None = Field(
        default=None,
        description="Auto compound choices for this strategy.",
    )
    yield_source: dict | None = Field(
        default=None,
        description="Yield generation mechanism for this strategy.",
    )
    can_allocate: bool | None = Field(
        default=None,
        description="Is allocation available for this strategy.",
    )
    can_deallocate: bool | None = Field(
        default=None,
        description="Is deallocation available for this strategy.",
    )
    allocation_restriction_info: list[str] | None = Field(
        default=None,
        description="Reasons as to why the user is not allowed to allocate to a given strategy.",
    )
    user_cap: str | None = Field(
        default=None,
        description="Maximum amount user can allocate to this strategy.",
    )


class ListEarnStrategiesSuccess(BaseSchema):
    """Successful response from List Earn Strategies endpoint."""

    items: list[EarnStrategy] = Field(
        default_factory=list,
        description="Array of strategy objects.",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for next page of results.",
    )


class ListEarnStrategiesResponse(BaseResponseWrapper[ListEarnStrategiesSuccess]):
    """Combined response wrapper for List Earn Strategies API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "ListEarnStrategiesResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        items = [EarnStrategy(**item_data) for item_data in result.get("items", [])]
        next_cursor = result.get("next_cursor")
        success_data = ListEarnStrategiesSuccess(items=items, next_cursor=next_cursor)
        return cls(success=success_data)


class ListEarnAllocationsRequest(BaseRequestSchema):
    """Request schema for List Earn Allocations endpoint.

    List all allocations for the user.

    API Key Permissions Required:
        Earn Funds OR Query Funds

    Usage Example:
        >>> request = ListEarnAllocationsRequest()
        >>> request = ListEarnAllocationsRequest(asset="XBT", hide_zero_allocations=True)
    """

    ascending: bool | None = Field(
        default=None,
        description="Whether to sort ascending or descending.",
    )
    asset: str | None = Field(
        default=None,
        description="Filter allocations by asset name.",
    )
    converted_asset: str | None = Field(
        default=None,
        description="Currency to convert amounts into.",
    )
    cursor: str | bool | None = Field(
        default=None,
        description="true/false to enable/disable paginated response (boolean) or cursor for next page of results (string).",
    )
    hide_zero_allocations: bool | None = Field(
        default=None,
        description="Whether to include zero allocations.",
    )


class EarnAllocation(BaseSchema):
    """Information about a single earn allocation."""

    native_asset: str = Field(..., description="Native asset name.")
    amount_allocated: dict = Field(
        ...,
        description="Amount allocated to the strategy, with native and converted amounts.",
    )
    total_rewarded: dict = Field(
        ...,
        description="Total rewards received to date.",
    )
    payout: dict | None = Field(
        default=None,
        description="Details about payout for this allocation.",
    )
    strategy_id: str = Field(..., description="The unique identifier of the strategy.")
    amount_allocated: dict | None = Field(
        default=None,
        description="Allocation amounts from the latest allocation request.",
    )


class ListEarnAllocationsSuccess(BaseSchema):
    """Successful response from List Earn Allocations endpoint."""

    converted_asset: str = Field(..., description="Currency that amounts were converted to.")
    total_allocated: str = Field(..., description="Total amount of all allocations.")
    total_rewarded: str = Field(..., description="Total rewards from all allocations.")
    items: list[EarnAllocation] = Field(
        default_factory=list,
        description="Array of allocation objects.",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor for next page of results.",
    )


class ListEarnAllocationsResponse(BaseResponseWrapper[ListEarnAllocationsSuccess]):
    """Combined response wrapper for List Earn Allocations API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "ListEarnAllocationsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        converted_asset = result.get("converted_asset", "")
        total_allocated = result.get("total_allocated", "0")
        total_rewarded = result.get("total_rewarded", "0")
        items = [EarnAllocation(**item_data) for item_data in result.get("items", [])]
        next_cursor = result.get("next_cursor")

        success_data = ListEarnAllocationsSuccess(
            converted_asset=converted_asset,
            total_allocated=total_allocated,
            total_rewarded=total_rewarded,
            items=items,
            next_cursor=next_cursor,
        )
        return cls(success=success_data)


class AllocateEarnFundsRequest(BaseRequestSchema):
    """Request schema for Allocate Earn Funds endpoint.

    Allocate funds to the Strategy.

    API Key Permissions Required:
        Earn Funds

    Usage Example:
        >>> request = AllocateEarnFundsRequest(
        ...     amount="4.3",
        ...     strategy_id="ESRFUO3-Q62XD-WIOIL7"
        ... )
    """

    amount: str = Field(..., description="The amount to allocate.")
    strategy_id: str = Field(..., description="A unique identifier per earn strategy.")

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, value) -> str:
        """Normalize amount to string."""
        return str(value)


class AllocateEarnFundsSuccess(BaseSchema):
    """Successful response from Allocate Earn Funds endpoint."""

    result: bool = Field(
        ...,
        description="Will return true when the operation is successful, null when an error occurred.",
    )


class AllocateEarnFundsResponse(BaseResponseWrapper[AllocateEarnFundsSuccess]):
    """Combined response wrapper for Allocate Earn Funds API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "AllocateEarnFundsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        success_data = AllocateEarnFundsSuccess(result=result)
        return cls(success=success_data)


class DeallocateEarnFundsRequest(BaseRequestSchema):
    """Request schema for Deallocate Earn Funds endpoint.

    Deallocate funds from a strategy.

    API Key Permissions Required:
        Earn Funds

    Usage Example:
        >>> request = DeallocateEarnFundsRequest(
        ...     amount="4.3",
        ...     strategy_id="ESRFUO3-Q62XD-WIOIL7"
        ... )
    """

    amount: str = Field(..., description="The amount to deallocate. This field is required.")
    strategy_id: str = Field(..., description="A unique identifier per earn strategy.")

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, value) -> str:
        """Normalize amount to string."""
        return str(value)


class DeallocateEarnFundsSuccess(BaseSchema):
    """Successful response from Deallocate Earn Funds endpoint."""

    result: bool = Field(
        ...,
        description="Will return true when the operation is successful, null when an error occurred.",
    )


class DeallocateEarnFundsResponse(BaseResponseWrapper[DeallocateEarnFundsSuccess]):
    """Combined response wrapper for Deallocate Earn Funds API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "DeallocateEarnFundsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        success_data = DeallocateEarnFundsSuccess(result=result)
        return cls(success=success_data)


class GetAllocationStatusRequest(BaseRequestSchema):
    """Request schema for Get Allocation Status endpoint.

    Get the status of the last allocation request.

    API Key Permissions Required:
        Earn Funds OR Query Funds

    Usage Example:
        >>> request = GetAllocationStatusRequest(strategy_id="ESRFUO3-Q62XD-WIOIL7")
    """

    strategy_id: str = Field(..., description="ID of the earn strategy.")


class GetAllocationStatusSuccess(BaseSchema):
    """Successful response from Get Allocation Status endpoint."""

    pending: bool = Field(
        ...,
        description="true if an operation is still in progress on the same strategy.",
    )


class GetAllocationStatusResponse(BaseResponseWrapper[GetAllocationStatusSuccess]):
    """Combined response wrapper for Get Allocation Status API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetAllocationStatusResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        success_data = GetAllocationStatusSuccess(pending=result.get("pending", False))
        return cls(success=success_data)


class GetDeallocationStatusRequest(BaseRequestSchema):
    """Request schema for Get Deallocation Status endpoint.

    Get the status of the last deallocation request.

    API Key Permissions Required:
        Earn Funds OR Query Funds

    Usage Example:
        >>> request = GetDeallocationStatusRequest(strategy_id="ESRFUO3-Q62XD-WIOIL7")
    """

    strategy_id: str = Field(..., description="ID of the earn strategy.")


class GetDeallocationStatusSuccess(BaseSchema):
    """Successful response from Get Deallocation Status endpoint."""

    pending: bool = Field(
        ...,
        description="true if an operation is still in progress on the same strategy.",
    )


class GetDeallocationStatusResponse(BaseResponseWrapper[GetDeallocationStatusSuccess]):
    """Combined response wrapper for Get Deallocation Status API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetDeallocationStatusResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        success_data = GetDeallocationStatusSuccess(pending=result.get("pending", False))
        return cls(success=success_data)
