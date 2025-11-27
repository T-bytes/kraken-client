"""Base interface for all channel implementations.

This module provides the abstract base class that all channel interfaces extend.
The ChannelInterface defines the contract for channel implementations and provides
shared functionality for request delegation and path construction.
"""

from abc import ABC
from typing import Tuple, TypeVar

from kraken.rest.schema.base import BaseRequestSchema, BaseResponseWrapper

TRequest = TypeVar("TRequest", bound=BaseRequestSchema)
TResponse = TypeVar("TResponse", bound=BaseResponseWrapper)
TClient = TypeVar("TClient")


class ChannelInterface(ABC):
    """Abstract base class for all REST API channel interfaces.

    This class provides the foundation for domain-specific channel implementations.
    Each channel groups related API endpoints and provides convenience methods that
    wrap schema-based requests while maintaining type safety.
    """

    def __init__(self, client: TClient, channel: str, private: bool):
        """Initialize the channel interface.

        Args:
            client: The REST client instance that handles HTTP requests.
            channel: The channel name identifier (e.g., 'market', 'trading').
            private: Whether this channel's endpoints require authentication.
        """
        self.client = client
        self.channel = channel
        self.private = private

    def _request(self, schema: TRequest, **kwargs) -> Tuple[TRequest, TResponse]:
        """Delegate a request to the client and return both request and response.

        This is the core method that all channel methods use to execute API requests.
        It delegates to the client's request handler while preserving type information.

        Args:
            schema: The request schema instance containing validated parameters.
            **kwargs: Additional keyword arguments passed to the client's request method.

        Returns:
            A tuple of (request_schema, response_object) where:
            - request_schema: The same request object that was passed in.
            - response_object: The parsed and validated response from the API.
        """
        return schema, self.client.request(schema, **kwargs)

    @property
    def path(self):
        """Get the API path prefix for this channel.

        Returns:
            The path prefix string, either '/0/public/' for public endpoints
            or '/0/private/' for authenticated endpoints.
        """
        return f"/0/{'private' if self.private else 'public'}/"
