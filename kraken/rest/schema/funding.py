"""Funding REST API schema definitions for deposits, withdrawals, and wallet transfers."""

import json
from typing import Literal

from pydantic import AliasChoices, Field, field_validator

from kraken.rest.schema.base import (
    BaseRequestSchema,
    BaseResponseWrapper,
    BaseSchema,
    ResponseErrorSchema,
)

ASSET_CLASS = Literal["currency", "tokenized_asset"]
REBASE_MULTIPLIER = Literal["rebased", "base"]
DEPOSIT_STATUS = Literal["Initial", "Pending", "Settled", "Success", "Failure"]
WITHDRAWAL_STATUS = Literal["Initial", "Pending", "Settled", "Success", "Failure"]
WITHDRAWAL_STATUS_PROP = Literal["cancel-pending", "canceled", "cancel-denied", "return", "onhold"]
WALLET_TYPE = Literal["Spot Wallet", "Futures Wallet"]


class GetDepositMethodsRequest(BaseRequestSchema):
    """Request schema for Get Deposit Methods endpoint.

    Retrieve methods available for depositing a particular asset.

    API Key Permissions Required:
        Funds permissions - Query AND Funds permissions - Deposit

    Usage Example:
        >>> request = GetDepositMethodsRequest(asset="XBT")
        >>> request = GetDepositMethodsRequest(asset="XBT", aclass="currency")
    """

    asset: str = Field(..., description="Asset being deposited.")
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Asset class being deposited (default: currency).",
    )


class DepositMethod(BaseSchema):
    """Information about a single deposit method."""

    method: str = Field(..., description="Name of deposit method.")
    limit: str | bool = Field(
        ...,
        description="Maximum net amount that can be deposited right now, or false if no limit.",
    )
    fee: str | None = Field(default=None, description="Amount of fees that will be paid.")
    address_setup_fee: str | None = Field(
        default=None,
        serialization_alias="address-setup-fee",
        description="Whether or not method has an address setup fee.",
    )
    gen_address: bool | None = Field(
        default=None,
        serialization_alias="gen-address",
        description="Whether new addresses can be generated for this method.",
    )
    minimum: str | None = Field(
        default=None, description="Minimum net amount that can be deposited right now."
    )


class GetDepositMethodsSuccess(BaseSchema):
    """Successful response from Get Deposit Methods endpoint."""

    methods: list[DepositMethod] = Field(
        default_factory=list, description="List of available deposit methods."
    )


class GetDepositMethodsResponse(BaseResponseWrapper[GetDepositMethodsSuccess]):
    """Combined response wrapper for Get Deposit Methods API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetDepositMethodsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        methods = [DepositMethod(**method_data) for method_data in result]
        success_data = GetDepositMethodsSuccess(methods=methods)
        return cls(success=success_data)


class GetDepositAddressesRequest(BaseRequestSchema):
    """Request schema for Get Deposit Addresses endpoint.

    Retrieve (or generate a new) deposit addresses for a particular asset and method.

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = GetDepositAddressesRequest(asset="XBT", method="Bitcoin")
        >>> request = GetDepositAddressesRequest(asset="XBT", method="Bitcoin", new=True)
    """

    asset: str = Field(..., description="Asset being deposited.")
    method: str = Field(..., description="Name of the deposit method.")
    new: bool = Field(default=False, description="Whether or not to generate a new address.")
    amount: str | None = Field(
        default=None,
        description="Amount you wish to deposit (only required for method='Bitcoin Lightning').",
    )
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Asset class being deposited (default: currency).",
    )


class DepositAddress(BaseSchema):
    """Information about a single deposit address."""

    address: str = Field(..., description="Deposit Address.")
    expiretm: str | None = Field(
        default=None,
        description="Expiration time in unix timestamp, or 0 if not expiring.",
    )
    new: bool | None = Field(
        default=None, description="Whether or not address has ever been used."
    )
    tag: str | None = Field(
        default=None,
        description="Contains tags for XRP deposit addresses and memos for STX, XLM, and EOS deposit addresses.",
    )


class GetDepositAddressesSuccess(BaseSchema):
    """Successful response from Get Deposit Addresses endpoint."""

    addresses: list[DepositAddress] = Field(
        default_factory=list, description="List of deposit addresses."
    )


class GetDepositAddressesResponse(BaseResponseWrapper[GetDepositAddressesSuccess]):
    """Combined response wrapper for Get Deposit Addresses API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetDepositAddressesResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        addresses = [DepositAddress(**addr_data) for addr_data in result]
        success_data = GetDepositAddressesSuccess(addresses=addresses)
        return cls(success=success_data)


class GetDepositStatusRequest(BaseRequestSchema):
    """Request schema for Get Status of Recent Deposits endpoint.

    Retrieve information about recent deposits. Results are sorted by recency.

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = GetDepositStatusRequest()
        >>> request = GetDepositStatusRequest(asset="XBT", method="Bitcoin")
    """

    asset: str | None = Field(
        default=None, description="Filter for specific asset being deposited."
    )
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Filter for specific asset class being deposited (default: currency).",
    )
    method: str | None = Field(
        default=None, description="Filter for specific name of deposit method."
    )
    start: str | None = Field(
        default=None,
        description="Start timestamp, deposits created strictly before will not be included in the response.",
    )
    end: str | None = Field(
        default=None,
        description="End timestamp, deposits created strictly after will not be included in the response.",
    )
    cursor: str | bool | None = Field(
        default=None,
        description="true/false to enable/disable paginated response (boolean) or cursor for next page of results (string).",
    )
    limit: int | None = Field(
        default=None, description="Number of results to include per page (default: 25)."
    )


class DepositStatusInfo(BaseSchema):
    """Information about a single deposit."""

    method: str = Field(..., description="Name of deposit method.")
    aclass: str = Field(..., description="Asset class.")
    asset: str = Field(..., description="Asset.")
    refid: str = Field(..., description="Reference ID.")
    txid: str | None = Field(default=None, description="Method transaction ID.")
    info: str | None = Field(default=None, description="Method transaction information.")
    amount: str = Field(..., description="Amount deposited.")
    fee: str | None = Field(default=None, description="Fees paid.")
    time: int = Field(..., description="Unix timestamp when request was made.")
    status: str = Field(..., description="Status of deposit.")
    status_prop: str | None = Field(
        default=None,
        serialization_alias="status-prop",
        description="Additional status properties (return, onhold).",
    )
    originators: list[str] | None = Field(
        default=None,
        description="Client sending transaction id(s) for deposits that credit with a sweeping transaction.",
    )


class GetDepositStatusSuccess(BaseSchema):
    """Successful response from Get Status of Recent Deposits endpoint."""

    deposits: list[DepositStatusInfo] = Field(
        default_factory=list, description="List of recent deposits."
    )
    next_cursor: str | None = Field(default=None, description="Cursor for next page of results.")


class GetDepositStatusResponse(BaseResponseWrapper[GetDepositStatusSuccess]):
    """Combined response wrapper for Get Status of Recent Deposits API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetDepositStatusResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        # Handle both paginated and non-paginated responses
        if isinstance(result, list):
            deposits = [DepositStatusInfo(**deposit_data) for deposit_data in result]
            success_data = GetDepositStatusSuccess(deposits=deposits)
        else:
            deposits = [
                DepositStatusInfo(**deposit_data)
                for deposit_data in result.get("deposit", result.get("deposits", []))
            ]
            next_cursor = result.get("next_cursor")
            success_data = GetDepositStatusSuccess(deposits=deposits, next_cursor=next_cursor)

        return cls(success=success_data)


class GetWithdrawalMethodsRequest(BaseRequestSchema):
    """Request schema for Get Withdrawal Methods endpoint.

    Retrieve a list of withdrawal methods available for the user.

    API Key Permissions Required:
        Funds permissions - Query AND Funds permissions - Withdraw

    Usage Example:
        >>> request = GetWithdrawalMethodsRequest()
        >>> request = GetWithdrawalMethodsRequest(asset="XBT", network="Bitcoin")
    """

    asset: str | None = Field(default=None, description="Filter methods for specific asset.")
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Filter methods for specific asset class (default: currency).",
    )
    network: str | None = Field(default=None, description="Filter methods for specific network.")


class WithdrawalMethod(BaseSchema):
    """Information about a single withdrawal method."""

    asset: str = Field(..., description="Name of asset being withdrawn.")
    method: str = Field(..., description="Name of the withdrawal method.")
    network: str | None = Field(
        default=None, description="Name of the blockchain or network being withdrawn on."
    )
    minimum: str = Field(..., description="Minimum net amount that can be withdrawn right now.")


class GetWithdrawalMethodsSuccess(BaseSchema):
    """Successful response from Get Withdrawal Methods endpoint."""

    methods: list[WithdrawalMethod] = Field(
        default_factory=list, description="List of available withdrawal methods."
    )


class GetWithdrawalMethodsResponse(BaseResponseWrapper[GetWithdrawalMethodsSuccess]):
    """Combined response wrapper for Get Withdrawal Methods API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetWithdrawalMethodsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        methods = [WithdrawalMethod(**method_data) for method_data in result]
        success_data = GetWithdrawalMethodsSuccess(methods=methods)
        return cls(success=success_data)


class GetWithdrawalAddressesRequest(BaseRequestSchema):
    """Request schema for Get Withdrawal Addresses endpoint.

    Retrieve a list of withdrawal addresses available for the user.

    API Key Permissions Required:
        Funds permissions - Query AND Funds permissions - Withdraw

    Usage Example:
        >>> request = GetWithdrawalAddressesRequest()
        >>> request = GetWithdrawalAddressesRequest(asset="XBT", method="Bitcoin", verified=True)
    """

    asset: str | None = Field(default=None, description="Filter addresses for specific asset.")
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Filter addresses for specific asset class (default: currency).",
    )
    method: str | None = Field(default=None, description="Filter addresses for specific method.")
    key: str | None = Field(
        default=None,
        description="Find address for by withdrawal key name, as set up on your account.",
    )
    verified: bool | None = Field(
        default=None,
        description="Filter by verification status of the withdrawal address.",
    )


class WithdrawalAddress(BaseSchema):
    """Information about a single withdrawal address."""

    address: str = Field(..., description="Withdrawal address.")
    asset: str = Field(..., description="Name of asset being withdrawn.")
    method: str = Field(..., description="Name of the withdrawal method.")
    key: str = Field(..., description="Withdrawal key name, as set up on your account.")
    tag: str | None = Field(
        default=None,
        description="Contains tags for XRP deposit addresses and memos for STX, XLM, and EOS deposit addresses.",
    )
    verified: bool = Field(..., description="Verification status of withdrawal address.")


class GetWithdrawalAddressesSuccess(BaseSchema):
    """Successful response from Get Withdrawal Addresses endpoint."""

    addresses: list[WithdrawalAddress] = Field(
        default_factory=list, description="List of withdrawal addresses."
    )


class GetWithdrawalAddressesResponse(BaseResponseWrapper[GetWithdrawalAddressesSuccess]):
    """Combined response wrapper for Get Withdrawal Addresses API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetWithdrawalAddressesResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        addresses = [WithdrawalAddress(**addr_data) for addr_data in result]
        success_data = GetWithdrawalAddressesSuccess(addresses=addresses)
        return cls(success=success_data)


class GetWithdrawalInfoRequest(BaseRequestSchema):
    """Request schema for Get Withdrawal Information endpoint.

    Retrieve fee information about potential withdrawals for a particular asset, key and amount.

    API Key Permissions Required:
        Funds permissions - Query AND Funds permissions - Withdraw

    Usage Example:
        >>> request = GetWithdrawalInfoRequest(asset="XBT", key="btc_testnet", amount="0.725")
    """

    asset: str = Field(..., description="Asset being withdrawn.")
    key: str = Field(..., description="Withdrawal key name, as set up on your account.")
    amount: str = Field(..., description="Amount to be withdrawn.")


class GetWithdrawalInfoSuccess(BaseSchema):
    """Successful response from Get Withdrawal Information endpoint."""

    method: str = Field(..., description="Name of the withdrawal method that will be used.")
    limit: str = Field(..., description="Maximum net amount that can be withdrawn right now.")
    amount: str = Field(..., description="Net amount that will be sent, after fees.")
    fee: str = Field(..., description="Amount of fees that will be paid.")


class GetWithdrawalInfoResponse(BaseResponseWrapper[GetWithdrawalInfoSuccess]):
    """Combined response wrapper for Get Withdrawal Information API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetWithdrawalInfoResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = GetWithdrawalInfoSuccess(**result)
        return cls(success=success_data)


class WithdrawFundsRequest(BaseRequestSchema):
    """Request schema for Withdraw Funds endpoint.

    Make a withdrawal request.

    API Key Permissions Required:
        Funds permissions - Withdraw

    Usage Example:
        >>> request = WithdrawFundsRequest(asset="XBT", key="btc_2709", amount="0.725")
        >>> request = WithdrawFundsRequest(
        ...     asset="XBT",
        ...     key="btc_2709",
        ...     amount="0.725",
        ...     address="bc1kar0ssrr7xf3vy5l6d3lydnwkre5og2z3f51dq"
        ... )
    """

    asset: str = Field(..., description="Asset being withdrawn.")
    key: str = Field(..., description="Withdrawal key name, as set up on your account.")
    amount: str = Field(..., description="Amount to be withdrawn.")
    address: str | None = Field(
        default=None,
        description="Optional, crypto address that can be used to confirm address matches key (will return Invalid withdrawal_address error if different).",
    )
    max_fee: str | None = Field(
        default=None,
        description="Optional, if the processed withdrawal fee is higher than max_fee, withdrawal will fail with EFunding:Max fee exceeded.",
    )
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Specify the asset class of the asset being withdrawn (default: currency).",
    )

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, value) -> str:
        """Normalize amount to string."""
        return str(value)

    @field_validator("max_fee", mode="before")
    @classmethod
    def normalize_max_fee(cls, value) -> str | None:
        """Normalize max_fee to string."""
        if value is None:
            return None
        return str(value)


class WithdrawFundsSuccess(BaseSchema):
    """Successful response from Withdraw Funds endpoint."""

    refid: str = Field(..., description="Reference ID.")


class WithdrawFundsResponse(BaseResponseWrapper[WithdrawFundsSuccess]):
    """Combined response wrapper for Withdraw Funds API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "WithdrawFundsResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = WithdrawFundsSuccess(**result)
        return cls(success=success_data)


class GetWithdrawalStatusRequest(BaseRequestSchema):
    """Request schema for Get Status of Recent Withdrawals endpoint.

    Retrieve information about recent withdrawals. Results are sorted by recency.

    API Key Permissions Required:
        Funds permissions - Withdraw OR Data - Query ledger entries

    Usage Example:
        >>> request = GetWithdrawalStatusRequest()
        >>> request = GetWithdrawalStatusRequest(asset="XBT", method="Bitcoin")
    """

    asset: str | None = Field(
        default=None, description="Filter for specific asset being withdrawn."
    )
    aclass: ASSET_CLASS | None = Field(
        default=None,
        description="Filter for specific asset class being withdrawn (default: currency).",
    )
    method: str | None = Field(
        default=None, description="Filter for specific name of withdrawal method."
    )
    start: str | None = Field(
        default=None,
        description="Start timestamp, withdrawals created strictly before will not be included in the response.",
    )
    end: str | None = Field(
        default=None,
        description="End timestamp, withdrawals created strictly after will not be included in the response.",
    )
    cursor: str | bool | None = Field(
        default=None,
        description="true/false to enable/disable paginated response (boolean) or cursor for next page of results (string).",
    )
    limit: int | None = Field(
        default=None, description="Number of results to include per page (default: 500)."
    )


class WithdrawalStatusInfo(BaseSchema):
    """Information about a single withdrawal."""

    method: str = Field(..., description="Name of withdrawal method.")
    network: str | None = Field(
        default=None, description="Network name based on the funding method used."
    )
    aclass: str = Field(..., description="Asset class.")
    asset: str = Field(..., description="Asset.")
    refid: str = Field(..., description="Reference ID.")
    txid: str | None = Field(default=None, description="Method transaction ID.")
    info: str | None = Field(default=None, description="Method transaction information.")
    amount: str = Field(..., description="Amount withdrawn.")
    fee: str | None = Field(default=None, description="Fees paid.")
    time: int = Field(..., description="Unix timestamp when request was made.")
    status: str = Field(..., description="Status of withdrawal.")
    status_prop: str | None = Field(
        default=None,
        serialization_alias="status-prop",
        description="Additional status properties (cancel-pending, canceled, cancel-denied, return, onhold).",
    )
    key: str | None = Field(
        default=None, description="Withdrawal key name, as set up on your account."
    )


class GetWithdrawalStatusSuccess(BaseSchema):
    """Successful response from Get Status of Recent Withdrawals endpoint."""

    withdrawals: list[WithdrawalStatusInfo] = Field(
        default_factory=list, description="List of recent withdrawals."
    )
    next_cursor: str | None = Field(default=None, description="Cursor for next page of results.")


class GetWithdrawalStatusResponse(BaseResponseWrapper[GetWithdrawalStatusSuccess]):
    """Combined response wrapper for Get Status of Recent Withdrawals API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "GetWithdrawalStatusResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        # Handle both paginated and non-paginated responses
        if isinstance(result, list):
            withdrawals = [WithdrawalStatusInfo(**withdrawal_data) for withdrawal_data in result]
            success_data = GetWithdrawalStatusSuccess(withdrawals=withdrawals)
        else:
            withdrawals = [
                WithdrawalStatusInfo(**withdrawal_data)
                for withdrawal_data in result.get("withdrawal", result.get("withdrawals", []))
            ]
            next_cursor = result.get("next_cursor")
            success_data = GetWithdrawalStatusSuccess(
                withdrawals=withdrawals, next_cursor=next_cursor
            )

        return cls(success=success_data)


class RequestWithdrawalCancellationRequest(BaseRequestSchema):
    """Request schema for Request Withdrawal Cancellation endpoint.

    Cancel a recently requested withdrawal, if it has not already been successfully processed.

    API Key Permissions Required:
        Funds permissions - Withdraw, unless withdrawal is a WalletTransfer, then no permissions are required.

    Usage Example:
        >>> request = RequestWithdrawalCancellationRequest(asset="XBT", refid="FTQcuak-V6Za8qrWnhzTx67yYHz8Tg")
    """

    asset: str = Field(..., description="Asset being withdrawn.")
    refid: str = Field(..., description="Withdrawal reference ID.")


class RequestWithdrawalCancellationSuccess(BaseSchema):
    """Successful response from Request Withdrawal Cancellation endpoint."""

    result: bool = Field(..., description="Whether cancellation was successful or not.")


class WithdrawCancelResponse(BaseResponseWrapper[RequestWithdrawalCancellationSuccess]):
    """Combined response wrapper for Request Withdrawal Cancellation API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "WithdrawCancelResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if result is None:
            raise ValueError("Response missing 'result' field")

        success_data = RequestWithdrawalCancellationSuccess(result=result)
        return cls(success=success_data)


class RequestWalletTransferRequest(BaseRequestSchema):
    """Request schema for Request Wallet Transfer endpoint.

    Transfer from a Kraken spot wallet to a Kraken Futures wallet.
    Note that a transfer in the other direction must be requested via the
    Kraken Futures API endpoint for withdrawals to Spot wallets.

    API Key Permissions Required:
        Funds permissions - Query

    Usage Example:
        >>> request = RequestWalletTransferRequest(
        ...     asset="XBT",
        ...     from_wallet="Spot Wallet",
        ...     to_wallet="Futures Wallet",
        ...     amount="2.54"
        ... )
    """

    asset: str = Field(..., description="Asset to transfer (asset ID or altname).")
    from_wallet: str = Field(
        ...,
        validation_alias=AliasChoices("from_wallet", "from"),
        serialization_alias="from",
        description="Source wallet (Spot Wallet).",
    )
    to_wallet: str = Field(
        ...,
        validation_alias=AliasChoices("to_wallet", "to"),
        serialization_alias="to",
        description="Destination wallet (Futures Wallet).",
    )
    amount: str = Field(..., description="Amount to transfer.")

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_amount(cls, value) -> str:
        """Normalize amount to string."""
        return str(value)


class RequestWalletTransferSuccess(BaseSchema):
    """Successful response from Request Wallet Transfer endpoint."""

    refid: str = Field(..., description="Reference ID.")


class RequestWalletTransferResponse(BaseResponseWrapper[RequestWalletTransferSuccess]):
    """Combined response wrapper for Request Wallet Transfer API calls."""

    @classmethod
    def from_response(cls, response: dict | str) -> "RequestWalletTransferResponse":
        """Parse Kraken API response into the appropriate response model."""
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            return cls(failure=ResponseErrorSchema(error=errors))

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        success_data = RequestWalletTransferSuccess(**result)
        return cls(success=success_data)
