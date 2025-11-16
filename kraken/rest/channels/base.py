from abc import ABC
from enum import StrEnum
from typing import Tuple, TypeVar

from kraken.rest.client import KrakenRESTClient
from kraken.rest.schema.base import BaseRequestSchema, BaseResponseWrapper

TRequest = TypeVar("TRequest", bound=BaseRequestSchema)
TResponse = TypeVar("TResponse", bound=BaseResponseWrapper)
TClient = TypeVar("TClient", bound=KrakenRESTClient)


class ChannelInterface(ABC):
    def __init__(self, client: TClient, channel: str, private: bool):
        self.client = client
        self.channel = channel
        self.private = private

    def _request(self, schema: TRequest, **kwargs) -> Tuple[TRequest, TResponse]:
        return schema, self.client.request(schema, **kwargs)

    @property
    def path(self):
        return f"/0/{'private' if self.private else 'public'}/"
