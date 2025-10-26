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
