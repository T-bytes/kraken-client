"""Earn channel for staking and earning operations."""

from typing import Tuple

from kraken.rest.schema.earn import *

from .base import ChannelInterface


class EarningChannel(ChannelInterface):
    """Channel for Earn endpoints.

    Provides access to staking and earning operations.
    All endpoints in this channel are private and require API key authentication.
    """

    def __init__(self, client):
        super().__init__(client, "earn", True)

    def list_strategies(
        self,
        ascending: bool | None = None,
        asset: str | None = None,
        cursor: str | bool | None = None,
        limit: int | None = None,
        lock_type: list[str] | None = None,
    ) -> Tuple[ListEarnStrategiesRequest, ListEarnStrategiesResponse]:
        """List earn strategies.

        List earn strategies along with their parameters.

        Args:
            ascending: Whether to sort ascending or descending by asset name
            asset: Filter strategies by asset name
            cursor: Enable/disable pagination or cursor for next page
            limit: Number of results to include per page
            lock_type: Filter strategies by lock type (flex, bonded, timed, instant)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.earn.list_strategies(asset="XBT", limit=10)
            >>> if response.is_success:
            ...     for strategy in response.success.items:
            ...         print(f"{strategy.id}: {strategy.asset} - {strategy.lock_type}")
        """
        request = ListEarnStrategiesRequest(
            ascending=ascending,
            asset=asset,
            cursor=cursor,
            limit=limit,
            lock_type=lock_type,
        )
        return self._request(request)

    def list_allocations(
        self,
        ascending: bool | None = None,
        asset: str | None = None,
        converted_asset: str | None = None,
        cursor: str | bool | None = None,
        hide_zero_allocations: bool | None = None,
    ) -> Tuple[ListEarnAllocationsRequest, ListEarnAllocationsResponse]:
        """List earn allocations.

        List all allocations for the user.

        Args:
            ascending: Whether to sort ascending or descending
            asset: Filter allocations by asset name
            converted_asset: Currency to convert amounts into
            cursor: Enable/disable pagination or cursor for next page
            hide_zero_allocations: Whether to include zero allocations

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.earn.list_allocations(
            ...     asset="XBT", hide_zero_allocations=True
            ... )
            >>> if response.is_success:
            ...     print(f"Total allocated: {response.success.total_allocated}")
            ...     for allocation in response.success.items:
            ...         print(f"{allocation.strategy_id}: {allocation.amount_allocated}")
        """
        request = ListEarnAllocationsRequest(
            ascending=ascending,
            asset=asset,
            converted_asset=converted_asset,
            cursor=cursor,
            hide_zero_allocations=hide_zero_allocations,
        )
        return self._request(request)

    def allocate_funds(
        self,
        amount: str | float,
        strategy_id: str,
    ) -> Tuple[AllocateEarnFundsRequest, AllocateEarnFundsResponse]:
        """Allocate earn funds.

        Allocate funds to a strategy.

        Args:
            amount: The amount to allocate
            strategy_id: A unique identifier per earn strategy

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.earn.allocate_funds(
            ...     amount="4.3", strategy_id="ESRFUO3-Q62XD-WIOIL7"
            ... )
            >>> if response.is_success:
            ...     if response.success.result:
            ...         print("Funds allocated successfully")
        """
        request = AllocateEarnFundsRequest(
            amount=str(amount),
            strategy_id=strategy_id,
        )
        return self._request(request)

    def deallocate_funds(
        self,
        amount: str | float,
        strategy_id: str,
    ) -> Tuple[DeallocateEarnFundsRequest, DeallocateEarnFundsResponse]:
        """Deallocate earn funds.

        Deallocate funds from a strategy.

        Args:
            amount: The amount to deallocate (required)
            strategy_id: A unique identifier per earn strategy

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.earn.deallocate_funds(
            ...     amount="4.3", strategy_id="ESRFUO3-Q62XD-WIOIL7"
            ... )
            >>> if response.is_success:
            ...     if response.success.result:
            ...         print("Funds deallocated successfully")
        """
        request = DeallocateEarnFundsRequest(
            amount=str(amount),
            strategy_id=strategy_id,
        )
        return self._request(request)

    def get_allocation_status(
        self,
        strategy_id: str,
    ) -> Tuple[GetAllocationStatusRequest, GetAllocationStatusResponse]:
        """Get allocation status.

        Get the status of the last allocation request.

        Args:
            strategy_id: ID of the earn strategy

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.earn.get_allocation_status(
            ...     strategy_id="ESRFUO3-Q62XD-WIOIL7"
            ... )
            >>> if response.is_success:
            ...     if response.success.pending:
            ...         print("Allocation still in progress")
            ...     else:
            ...         print("No pending allocation")
        """
        request = GetAllocationStatusRequest(strategy_id=strategy_id)
        return self._request(request)

    def get_deallocation_status(
        self,
        strategy_id: str,
    ) -> Tuple[GetDeallocationStatusRequest, GetDeallocationStatusResponse]:
        """Get deallocation status.

        Get the status of the last deallocation request.

        Args:
            strategy_id: ID of the earn strategy

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.earn.get_deallocation_status(
            ...     strategy_id="ESRFUO3-Q62XD-WIOIL7"
            ... )
            >>> if response.is_success:
            ...     if response.success.pending:
            ...         print("Deallocation still in progress")
            ...     else:
            ...         print("No pending deallocation")
        """
        request = GetDeallocationStatusRequest(strategy_id=strategy_id)
        return self._request(request)
