import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel as BaseSchema
from pydantic import Field

TSuccess = TypeVar("TSuccess", bound=BaseSchema)


class ResponseErrorSchema(BaseSchema):
    """Error response from Kraken API.

    Contains error messages when order placement fails.
    """

    error: list[str] = Field(
        ...,
        description="List of error messages from the API.",
    )


class BaseRequestSchema(BaseSchema):
    """Base class for all trading request schemas.

    Provides common to_api_dict() method for API serialization.
    """

    def to_api_dict(self, **kwargs) -> dict[str, Any]:
        """Serialize request to dict for Kraken API submission.

        This method handles proper field aliasing and exclusion of None values
        for API compatibility. Use this method when passing requests to the REST client.

        Args:
            by_alias: Use field aliases in output (default True)
            exclude_none: Remove fields with None values (default True)
            **kwargs: Additional arguments passed to model_dump()

        Returns:
            Dictionary suitable for Kraken API endpoints
        """
        return self.model_dump(
            by_alias=kwargs.pop("by_alias", True),
            exclude_none=kwargs.pop("exclude_none", True),
            **kwargs,
        )


class BaseResponseWrapper(BaseSchema, Generic[TSuccess]):
    """Generic base class for all trading response wrappers.

    Handles both success and failure cases from the Kraken API.
    Use the `is_success` property to determine the outcome.
    """

    success: TSuccess | None = Field(
        default=None,
        description="Success response data, present when request succeeds.",
    )
    failure: ResponseErrorSchema | None = Field(
        default=None,
        description="Error response data, present when request fails.",
    )

    @property
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.success is not None

    @classmethod
    def from_response(cls, response: dict | str) -> "BaseResponseWrapper":
        """Parse a Kraken API response into the appropriate response model.

        Args:
            response: Either a JSON string or dict containing the API response

        Returns:
            Response wrapper with either success or error data populated

        Raises:
            ValueError: If the response format is invalid
        """
        if isinstance(response, str):
            response = json.loads(response)

        errors = response.get("error", [])
        if errors:
            error_data = ResponseErrorSchema(error=errors)
            return cls(error=error_data)

        result = response.get("result")
        if not result:
            raise ValueError("Response missing 'result' field")

        # Subclasses must override to construct their specific success type
        raise NotImplementedError("Subclasses must implement from_response()")
