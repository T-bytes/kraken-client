"""Funding channel for deposit, withdrawal, and wallet transfer operations."""

from typing import Tuple

from kraken.rest.schema.funding import *

from .base import ChannelInterface


class FundingChannel(ChannelInterface):
    """Channel for Funding endpoints.

    Provides access to deposit, withdrawal, and wallet transfer operations.
    All endpoints in this channel are private and require API key authentication.
    """

    def __init__(self, client):
        super().__init__(client, "funding", True)

    def get_deposit_methods(
        self,
        asset: str,
        aclass: ASSET_CLASS | None = None,
    ) -> Tuple[GetDepositMethodsRequest, GetDepositMethodsResponse]:
        """Get deposit methods.

        Retrieve methods available for depositing a particular asset.

        Args:
            asset: Asset being deposited
            aclass: Asset class being deposited (default: currency)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_deposit_methods(asset="XBT")
            >>> if response.is_success:
            ...     for method in response.success.methods:
            ...         print(f"{method.method}: min={method.minimum}")
        """
        request = GetDepositMethodsRequest(asset=asset, aclass=aclass)
        return self._request(request)

    def get_deposit_addresses(
        self,
        asset: str,
        method: str,
        new: bool = False,
        amount: str | None = None,
        aclass: ASSET_CLASS | None = None,
    ) -> Tuple[GetDepositAddressesRequest, GetDepositAddressesResponse]:
        """Get deposit addresses.

        Retrieve (or generate new) deposit addresses for a particular asset and method.

        Args:
            asset: Asset being deposited
            method: Name of the deposit method
            new: Whether or not to generate a new address (default: False)
            amount: Amount you wish to deposit (only required for Bitcoin Lightning)
            aclass: Asset class being deposited (default: currency)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_deposit_addresses(
            ...     asset="XBT", method="Bitcoin"
            ... )
            >>> if response.is_success:
            ...     for addr in response.success.addresses:
            ...         print(f"Address: {addr.address}")
        """
        request = GetDepositAddressesRequest(
            asset=asset,
            method=method,
            new=new,
            amount=amount,
            aclass=aclass,
        )
        return self._request(request)

    def get_deposit_status(
        self,
        asset: str | None = None,
        aclass: ASSET_CLASS | None = None,
        method: str | None = None,
        start: str | None = None,
        end: str | None = None,
        cursor: str | bool | None = None,
        limit: int | None = None,
    ) -> Tuple[GetDepositStatusRequest, GetDepositStatusResponse]:
        """Get status of recent deposits.

        Retrieve information about recent deposits. Results are sorted by recency.

        Args:
            asset: Filter for specific asset being deposited
            aclass: Filter for specific asset class (default: currency)
            method: Filter for specific name of deposit method
            start: Start timestamp, deposits before will not be included
            end: End timestamp, deposits after will not be included
            cursor: Enable/disable pagination or cursor for next page
            limit: Number of results to include per page (default: 25)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_deposit_status(asset="XBT")
            >>> if response.is_success:
            ...     for deposit in response.success.deposits:
            ...         print(f"{deposit.refid}: {deposit.amount} {deposit.asset} - {deposit.status}")
        """
        request = GetDepositStatusRequest(
            asset=asset,
            aclass=aclass,
            method=method,
            start=start,
            end=end,
            cursor=cursor,
            limit=limit,
        )
        return self._request(request)

    def get_withdrawal_methods(
        self,
        asset: str | None = None,
        aclass: ASSET_CLASS | None = None,
        network: str | None = None,
    ) -> Tuple[GetWithdrawalMethodsRequest, GetWithdrawalMethodsResponse]:
        """Get withdrawal methods.

        Retrieve a list of withdrawal methods available for the user.

        Args:
            asset: Filter methods for specific asset
            aclass: Filter methods for specific asset class (default: currency)
            network: Filter methods for specific network

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_withdrawal_methods(asset="XBT")
            >>> if response.is_success:
            ...     for method in response.success.methods:
            ...         print(f"{method.method}: min={method.minimum}")
        """
        request = GetWithdrawalMethodsRequest(
            asset=asset,
            aclass=aclass,
            network=network,
        )
        return self._request(request)

    def get_withdrawal_addresses(
        self,
        asset: str | None = None,
        aclass: ASSET_CLASS | None = None,
        method: str | None = None,
        key: str | None = None,
        verified: bool | None = None,
    ) -> Tuple[GetWithdrawalAddressesRequest, GetWithdrawalAddressesResponse]:
        """Get withdrawal addresses.

        Retrieve a list of withdrawal addresses available for the user.

        Args:
            asset: Filter addresses for specific asset
            aclass: Filter addresses for specific asset class (default: currency)
            method: Filter addresses for specific method
            key: Find address by withdrawal key name
            verified: Filter by verification status of the withdrawal address

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_withdrawal_addresses(
            ...     asset="XBT", verified=True
            ... )
            >>> if response.is_success:
            ...     for addr in response.success.addresses:
            ...         print(f"{addr.key}: {addr.address}")
        """
        request = GetWithdrawalAddressesRequest(
            asset=asset,
            aclass=aclass,
            method=method,
            key=key,
            verified=verified,
        )
        return self._request(request)

    def get_withdrawal_info(
        self,
        asset: str,
        key: str,
        amount: str | float,
    ) -> Tuple[GetWithdrawalInfoRequest, GetWithdrawalInfoResponse]:
        """Get withdrawal information.

        Retrieve fee information about potential withdrawals for a particular
        asset, key and amount.

        Args:
            asset: Asset being withdrawn
            key: Withdrawal key name, as set up on your account
            amount: Amount to be withdrawn

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_withdrawal_info(
            ...     asset="XBT", key="btc_testnet", amount="0.725"
            ... )
            >>> if response.is_success:
            ...     print(f"Fee: {response.success.fee}")
            ...     print(f"Amount after fee: {response.success.amount}")
        """
        request = GetWithdrawalInfoRequest(
            asset=asset,
            key=key,
            amount=str(amount),
        )
        return self._request(request)

    def withdraw_funds(
        self,
        asset: str,
        key: str,
        amount: str | float,
        address: str | None = None,
        max_fee: str | float | None = None,
        aclass: ASSET_CLASS | None = None,
    ) -> Tuple[WithdrawFundsRequest, WithdrawFundsResponse]:
        """Withdraw funds.

        Make a withdrawal request.

        Args:
            asset: Asset being withdrawn
            key: Withdrawal key name, as set up on your account
            amount: Amount to be withdrawn
            address: Optional, crypto address to confirm it matches key
            max_fee: Optional, if processed fee exceeds this, withdrawal fails
            aclass: Asset class of the asset being withdrawn (default: currency)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.withdraw_funds(
            ...     asset="XBT", key="btc_2709", amount="0.725"
            ... )
            >>> if response.is_success:
            ...     print(f"Withdrawal reference ID: {response.success.refid}")
        """
        request = WithdrawFundsRequest(
            asset=asset,
            key=key,
            amount=str(amount),
            address=address,
            max_fee=str(max_fee) if max_fee is not None else None,
            aclass=aclass,
        )
        return self._request(request)

    def get_withdrawal_status(
        self,
        asset: str | None = None,
        aclass: ASSET_CLASS | None = None,
        method: str | None = None,
        start: str | None = None,
        end: str | None = None,
        cursor: str | bool | None = None,
        limit: int | None = None,
    ) -> Tuple[GetWithdrawalStatusRequest, GetWithdrawalStatusResponse]:
        """Get status of recent withdrawals.

        Retrieve information about recent withdrawals. Results are sorted by recency.

        Args:
            asset: Filter for specific asset being withdrawn
            aclass: Filter for specific asset class (default: currency)
            method: Filter for specific name of withdrawal method
            start: Start timestamp, withdrawals before will not be included
            end: End timestamp, withdrawals after will not be included
            cursor: Enable/disable pagination or cursor for next page
            limit: Number of results to include per page (default: 500)

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.get_withdrawal_status(asset="XBT")
            >>> if response.is_success:
            ...     for withdrawal in response.success.withdrawals:
            ...         print(f"{withdrawal.refid}: {withdrawal.amount} {withdrawal.asset} - {withdrawal.status}")
        """
        request = GetWithdrawalStatusRequest(
            asset=asset,
            aclass=aclass,
            method=method,
            start=start,
            end=end,
            cursor=cursor,
            limit=limit,
        )
        return self._request(request)

    def request_withdrawal_cancellation(
        self,
        asset: str,
        refid: str,
    ) -> Tuple[RequestWithdrawalCancellationRequest, WithdrawCancelResponse]:
        """Request withdrawal cancellation.

        Cancel a recently requested withdrawal, if it has not already been
        successfully processed.

        Args:
            asset: Asset being withdrawn
            refid: Withdrawal reference ID

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.request_withdrawal_cancellation(
            ...     asset="XBT", refid="FTQcuak-V6Za8qrWnhzTx67yYHz8Tg"
            ... )
            >>> if response.is_success:
            ...     if response.success.result:
            ...         print("Withdrawal cancelled successfully")
        """
        request = RequestWithdrawalCancellationRequest(
            asset=asset,
            refid=refid,
        )
        return self._request(request)

    def request_wallet_transfer(
        self,
        asset: str,
        from_wallet: str,
        to_wallet: str,
        amount: str | float,
    ) -> Tuple[RequestWalletTransferRequest, RequestWalletTransferResponse]:
        """Request wallet transfer.

        Transfer from a Kraken spot wallet to a Kraken Futures wallet.
        Note that a transfer in the other direction must be requested via the
        Kraken Futures API endpoint for withdrawals to Spot wallets.

        Args:
            asset: Asset to transfer (asset ID or altname)
            from_wallet: Source wallet (e.g., "Spot Wallet")
            to_wallet: Destination wallet (e.g., "Futures Wallet")
            amount: Amount to transfer

        Returns:
            Tuple of request and response objects

        Example:
            >>> request, response = client.funding.request_wallet_transfer(
            ...     asset="XBT",
            ...     from_wallet="Spot Wallet",
            ...     to_wallet="Futures Wallet",
            ...     amount="2.54"
            ... )
            >>> if response.is_success:
            ...     print(f"Transfer reference ID: {response.success.refid}")
        """
        request = RequestWalletTransferRequest(
            asset=asset,
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            amount=str(amount),
        )
        return self._request(request)
