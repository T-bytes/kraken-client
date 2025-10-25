import json
from datetime import datetime, timedelta
from typing import Annotated, Literal
from uuid import uuid4 as randuuid

from pydantic import BaseModel as BaseSchema
from pydantic import Field, field_validator

from kraken.constants import LATENCY_TOLERANCE, SANDBOX_TRADING
from kraken.utilities import get_nonce, utc_now

ORDER_TYPE = Literal[
    "market",
    "limit",
    "iceberg",
    "stop-loss",
    "take-profit",
    "stop-loss-limit",
    "take-profit-limit",
    "trailing-stop",
    "trailing-stop-limit",
    "settle-position",
]
ORDER_DIRECTION = Literal["buy", "sell"]
ORDER_FLAG_SET = set(["post", "fcib", "fciq", "viqc"])
TRIGGER_TYPE = Literal["index", "last"]
STP_TYPE = Literal["cancel-newest", "cancel-oldest", "cancel-both"]
TIME_IN_FORCE = Literal["GTC", "IOC", "GTD"]


class AddOrderRequest(BaseSchema):
    nonce: int = Field(
        default_factory=lambda: get_nonce(),
        description="Nonce used in construction of `API-Sign` header",
    )
    userref: int | None = Field(
        default=None,
        description="This is an optional non-unique, numeric identifier for user metadata tracking. This field is mutually exclusive with `cl_ord_id` parameter.",
    )
    cl_ord_id: str | None = Field(
        default=None,
        description="Adds an alphanumeric client order identifier which uniquely identifies an open order for each client (long/short UUID or 18-ascii char). This field is mutually exclusive with `userref` parameter.",
    )
    ordertype: ORDER_TYPE = Field(..., description="The execution model of the order.")
    type: ORDER_DIRECTION = Field(..., description="Order direction (buy/sell).")
    volume: str | float | int = Field(
        ...,
        description="Order quantity in terms of the base asset; can be specified as 0 for closing margin orders to automatically fill the requisite quantity.",
    )
    displayvol: str | float | int | None = Field(
        default=None,
        description="For 'iceberg' orders only, it defines the quantity to show in the book while the rest of order quantity remains hidden. Minimum value is 1/15 of volume.",
    )
    pair: str = Field(..., description="Asset pair `id` or `altname`.")
    asset_class: str | None = Field(
        None, description="Required to be set as 'tokenized_asset' for non-crypto pairs (xstocks)."
    )
    price: str | None = Field(
        default=None,
        description="Limit price for 'limit' and 'iceberg' orders; trigger price for 'stop-loss', 'stop-loss-limit', 'take-profit', 'take-profit-limit', 'trailing-stop' and 'trailing-stop-limit' orders.",
    )
    price2: str | None = Field(
        default=None,
        description="Limit price for 'stop-loss-limit', 'take-profit-limit' and 'trailing-stop-limit' orders.",
    )
    trigger: TRIGGER_TYPE | None = Field(
        default=None,
        description="Price signal used to trigger 'stop-loss', 'stop-loss-limit', 'take-profit', 'take-profit-limit', 'trailing-stop' and 'trailing-stop-limit' orders.",
    )
    leverage: str | int | None = Field(None, description="Amount of desired leverage.")
    reduce_only: bool | None = Field(
        default=False,
        description="If `True`, order will only reduce a currently open position, not increase it or open a new position.",
    )
    stptype: STP_TYPE | None = Field(
        default="cancel-newest",
        description="Self Trade Prevention (STP) prevents users from inadvertently or deliberately trading against themselves.",
    )
    oflags: str | list[str] | set[str] | None = Field(
        default=None,
        description="Comma delimited list of order flags: 'post', 'fcib', 'fciq', 'viqc'.",
    )
    timeinforce: TIME_IN_FORCE | None = Field(
        default="GTC",
        description="Time-in-force of the order to specify how long it should remain in the order book before being cancelled.",
    )
    starttm: str | None = Field(
        default="0",
        description="Scheduled start time, can be specified as an absolute timestamp or as a number of seconds in the future.",
    )
    expiretm: str | None = Field(
        default="0",
        description="Expiry time on GTD orders can be set up to one month in future, it is specified as an absolute timestamp or as a number of seconds from now.",
    )
    deadline: str | None = Field(
        default=None,
        description="RFC3339 timestamp after which the matching engine should reject the new order request, in presence of latency or order queueing.",
    )
    validate: bool | None = Field(
        default=SANDBOX_TRADING,
        description="If set to `True` the order will be validated only, it will not trade in the matching engine.",
    )

    @field_validator("ordertype", mode="before")
    @classmethod
    def lowercase_order(cls, value: str) -> str:
        return value.lower().strip()

    @field_validator("volume", mode="before")
    @classmethod
    def string_volume(cls, value: str | float | int) -> str:
        return str(value)

    @field_validator("displayvol", mode="before")
    @classmethod
    def floor_display_volume(cls, value: str | float | int | None, info) -> str | None:
        if value == None:
            return None
        order_volume = float(info.data.get("volume"))
        floor_volume = order_volume / 15.0
        if float(value) > order_volume:
            return str(order_volume)
        elif float(value) < floor_volume:
            return str(floor_volume)
        else:
            return str(value)

    @field_validator("leverage", mode="before")
    @classmethod
    def string_leverage(cls, value: str | float | None) -> str | None:
        if value == None:
            return None
        return str(value)

    @field_validator("oflags", mode="before")
    @classmethod
    def concat_order_flags(cls, value: str | list[str] | set[str] | None) -> str | None:
        if value == None:
            return None
        if isinstance(value, str):
            splits = value.split(",")
            if len(splits) > 1:
                value = set(splits)
            else:
                value = {value}
        elif isinstance(value, list):
            value = set(value)
        value = ORDER_FLAG_SET.intersection(value)
        return ",".join(value) if len(value) > 0 else None

    @field_validator("timeinforce", mode="before")
    @classmethod
    def capitalize_time_in_force(cls, value: str) -> str:
        return value.upper().strip()

    @field_validator("deadline", mode="after")
    @classmethod
    def bound_deadline(cls, value: str | None, latency_tolerance: int = LATENCY_TOLERANCE) -> str:
        now = utc_now()
        min_t, max_t = now + timedelta(seconds=2), now + timedelta(seconds=60)
        if value == None:
            deadline = now + timedelta(seconds=latency_tolerance)
        else:
            deadline = datetime.fromisoformat(value)
            if deadline < min_t:
                deadline = min_t
            elif deadline > max_t:
                deadline = max_t
        return deadline.isoformat()


class AddOrderResponse(BaseSchema):
    order: str = Field(
        ...,
        description="Order description (e.g., 'buy 2.12340000 XBTUSD @ limit 25000.1 with 2:1 leverage').",
    )
    close: str | None = Field(
        default=None,
        description="Conditional close order description, if applicable (e.g., 'close position @ stop loss 22000.0 -> limit 21000.0').",
    )
    txid: list[str] | None = Field(
        default=None,
        description="18-character transaction IDs for order, if order was added successfully.",
    )
    error: list[object] = Field(
        default_factory=lambda: [], description="Any errors, if applicable."
    )

    @classmethod
    def from_response(cls, response: dict | str) -> "AddOrderResponse":
        try:
            if isinstance(response, str):
                response = json.loads(response)
            fields = {
                "error": response["error"],
                "txid": response["result"]["txid"],
                "order": response["result"]["descr"]["order"],
                "close": response["result"]["descr"]["close"],
            }
        except Exception as e:
            fields = {
                "error": [str(e)],
                "txid": None,
                "order": None,
                "close": None,
            }
        return cls.model_construct(**fields)
