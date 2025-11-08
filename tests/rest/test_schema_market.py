"""Unit tests for Kraken REST API market data schemas"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from kraken.rest.schema.market import (
    AssetInfo,
    AssetPairInfo,
    GetAssetInfoRequest,
    GetAssetInfoResponse,
    GetAssetInfoSuccess,
    GetAssetPairsRequest,
    GetAssetPairsResponse,
    GetAssetPairsSuccess,
    GetOHLCDataRequest,
    GetOHLCDataResponse,
    GetOHLCDataSuccess,
    GetOrderBookRequest,
    GetOrderBookResponse,
    GetOrderBookSuccess,
    GetRecentSpreadsRequest,
    GetRecentSpreadsResponse,
    GetRecentSpreadsSuccess,
    GetRecentTradesRequest,
    GetRecentTradesResponse,
    GetRecentTradesSuccess,
    GetServerTimeRequest,
    GetServerTimeResponse,
    GetServerTimeSuccess,
    GetSystemStatusRequest,
    GetSystemStatusResponse,
    GetSystemStatusSuccess,
    GetTickerInformationRequest,
    GetTickerInformationResponse,
    GetTickerInformationSuccess,
    OHLCData,
    OrderBook,
    OrderBookEntry,
    RecentTradeEntry,
    SpreadEntry,
    TickerInfo,
)
from kraken.rest.schema.base import ResponseErrorSchema


class TestGetServerTimeRequest:
    """Tests for GetServerTimeRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request"""
        server_time_request = GetServerTimeRequest()

        # Should be valid with no required fields
        assert server_time_request is not None

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        server_time_request = GetServerTimeRequest()

        # Should not have a nonce attribute
        assert not hasattr(server_time_request, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        server_time_request = GetServerTimeRequest()

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = server_time_request.to_api_dict()

        # Should return an empty dict (no fields except nonce which is added by client)
        assert data == {}

        # Test exclude_none=False
        data_with_none = server_time_request.to_api_dict(exclude_none=False)
        assert data_with_none == {}

    def test_multiple_instances(self):
        """Test creating multiple GetServerTimeRequest instances"""
        requests = [GetServerTimeRequest() for _ in range(10)]

        # All should be valid
        assert len(requests) == 10
        for req in requests:
            assert req is not None

    def test_concurrent_creation(self):
        """Test concurrent creation of multiple requests"""
        import concurrent.futures

        def create_request(i):
            return GetServerTimeRequest()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            requests = list(executor.map(create_request, range(20)))

        assert len(requests) == 20
        for req in requests:
            assert req is not None


class TestGetServerTimeResponse:
    """Tests for GetServerTime response schemas"""

    def test_success_response_parsing(self):
        """Test parsing a successful response"""
        kraken_response = {
            "error": [],
            "result": {
                "unixtime": 1632931626,
                "rfc1123": "Tue, 29 Sep 2021 13:27:06 GMT",
            },
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.unixtime == 1632931626
        assert response.success.rfc1123 == "Tue, 29 Sep 2021 13:27:06 GMT"

    def test_success_response_various_timestamps(self):
        """Test parsing responses with various timestamp values"""
        # Recent timestamp (2025)
        kraken_response = {
            "error": [],
            "result": {
                "unixtime": 1735689600,
                "rfc1123": "Wed, 01 Jan 2025 00:00:00 GMT",
            },
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.unixtime == 1735689600
        assert response.success.rfc1123 == "Wed, 01 Jan 2025 00:00:00 GMT"

        # Earlier timestamp (2020)
        kraken_response2 = {
            "error": [],
            "result": {
                "unixtime": 1577836800,
                "rfc1123": "Wed, 01 Jan 2020 00:00:00 GMT",
            },
        }

        response2 = GetServerTimeResponse.from_response(kraken_response2)

        assert response2.is_success is True
        assert response2.success.unixtime == 1577836800
        assert response2.success.rfc1123 == "Wed, 01 Jan 2020 00:00:00 GMT"

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Internal error"],
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Internal error" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Internal error",
                "EAPI:Rate limit exceeded",
            ],
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Internal error" in response.failure.error
        assert "EAPI:Rate limit exceeded" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "unixtime": 1700000000,
                    "rfc1123": "Tue, 14 Nov 2023 22:13:20 GMT",
                },
            }
        )

        response = GetServerTimeResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.unixtime == 1700000000
        assert response.success.rfc1123 == "Tue, 14 Nov 2023 22:13:20 GMT"

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetServerTimeResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetServerTimeSuccess directly"""
        success = GetServerTimeSuccess(
            unixtime=1609459200,
            rfc1123="Fri, 01 Jan 2021 00:00:00 GMT",
        )

        assert success.unixtime == 1609459200
        assert success.rfc1123 == "Fri, 01 Jan 2021 00:00:00 GMT"

    def test_success_model_field_types(self):
        """Test that field types are enforced"""
        # Valid types
        success = GetServerTimeSuccess(
            unixtime=1234567890,
            rfc1123="Fri, 13 Feb 2009 23:31:30 GMT",
        )

        assert isinstance(success.unixtime, int)
        assert isinstance(success.rfc1123, str)

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        from kraken.rest.schema.base import ResponseErrorSchema

        error = ResponseErrorSchema(error=["EGeneral:Internal error"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Internal error"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetServerTimeResponse wrapper directly"""
        success = GetServerTimeSuccess(
            unixtime=1600000000,
            rfc1123="Sun, 13 Sep 2020 12:26:40 GMT",
        )
        response = GetServerTimeResponse(success=success)

        assert response.is_success is True
        assert response.success.unixtime == 1600000000

        from kraken.rest.schema.base import ResponseErrorSchema

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetServerTimeResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_rfc1123_format_validation(self):
        """Test that various RFC 1123 formats are accepted"""
        # Standard format
        success1 = GetServerTimeSuccess(
            unixtime=1632931626,
            rfc1123="Tue, 29 Sep 2021 13:27:06 GMT",
        )
        assert success1.rfc1123 == "Tue, 29 Sep 2021 13:27:06 GMT"

        # Different day/month
        success2 = GetServerTimeSuccess(
            unixtime=1609459200,
            rfc1123="Fri, 01 Jan 2021 00:00:00 GMT",
        )
        assert success2.rfc1123 == "Fri, 01 Jan 2021 00:00:00 GMT"

    def test_concurrent_response_parsing(self):
        """Test concurrent parsing of multiple responses"""
        import concurrent.futures

        def parse_response(i):
            kraken_response = {
                "error": [],
                "result": {
                    "unixtime": 1632931626 + i,
                    "rfc1123": "Tue, 29 Sep 2021 13:27:06 GMT",
                },
            }
            return GetServerTimeResponse.from_response(kraken_response)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(executor.map(parse_response, range(20)))

        assert len(responses) == 20
        for i, resp in enumerate(responses):
            assert resp.is_success is True
            assert resp.success.unixtime == 1632931626 + i

    def test_response_immutability(self):
        """Test that response objects maintain their data correctly"""
        kraken_response = {
            "error": [],
            "result": {
                "unixtime": 1632931626,
                "rfc1123": "Tue, 29 Sep 2021 13:27:06 GMT",
            },
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        # Store original values
        original_unixtime = response.success.unixtime
        original_rfc1123 = response.success.rfc1123

        # Values should remain unchanged
        assert response.success.unixtime == original_unixtime
        assert response.success.rfc1123 == original_rfc1123

    def test_zero_unixtime_edge_case(self):
        """Test handling of zero unixtime (Unix epoch)"""
        kraken_response = {
            "error": [],
            "result": {
                "unixtime": 0,
                "rfc1123": "Thu, 01 Jan 1970 00:00:00 GMT",
            },
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.unixtime == 0
        assert response.success.rfc1123 == "Thu, 01 Jan 1970 00:00:00 GMT"

    def test_large_unixtime_future_date(self):
        """Test handling of large unixtime values (far future)"""
        kraken_response = {
            "error": [],
            "result": {
                "unixtime": 2147483647,  # Year 2038 problem boundary
                "rfc1123": "Tue, 19 Jan 2038 03:14:07 GMT",
            },
        }

        response = GetServerTimeResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.unixtime == 2147483647
        assert response.success.rfc1123 == "Tue, 19 Jan 2038 03:14:07 GMT"


class TestGetSystemStatusRequest:
    """Tests for GetSystemStatusRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request"""
        system_status_request = GetSystemStatusRequest()

        # Should be valid with no required fields
        assert system_status_request is not None

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        system_status_request = GetSystemStatusRequest()

        # Should not have a nonce attribute
        assert not hasattr(system_status_request, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        system_status_request = GetSystemStatusRequest()

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = system_status_request.to_api_dict()

        # Should return an empty dict (no fields)
        assert data == {}

        # Test exclude_none=False
        data_with_none = system_status_request.to_api_dict(exclude_none=False)
        assert data_with_none == {}

    def test_multiple_instances(self):
        """Test creating multiple GetSystemStatusRequest instances"""
        requests = [GetSystemStatusRequest() for _ in range(10)]

        # All should be valid
        assert len(requests) == 10
        for req in requests:
            assert req is not None

    def test_concurrent_creation(self):
        """Test concurrent creation of multiple requests"""
        import concurrent.futures

        def create_request(i):
            return GetSystemStatusRequest()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            requests = list(executor.map(create_request, range(20)))

        assert len(requests) == 20
        for req in requests:
            assert req is not None


class TestGetSystemStatusResponse:
    """Tests for GetSystemStatus response schemas"""

    def test_success_response_parsing_online(self):
        """Test parsing a successful response with 'online' status"""
        kraken_response = {
            "error": [],
            "result": {
                "status": "online",
                "timestamp": "2021-03-22T17:18:03Z",
            },
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.status == "online"
        assert response.success.timestamp == "2021-03-22T17:18:03Z"

    def test_success_response_parsing_maintenance(self):
        """Test parsing a successful response with 'maintenance' status"""
        kraken_response = {
            "error": [],
            "result": {
                "status": "maintenance",
                "timestamp": "2023-10-15T12:00:00Z",
            },
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.status == "maintenance"
        assert response.success.timestamp == "2023-10-15T12:00:00Z"

    def test_success_response_parsing_cancel_only(self):
        """Test parsing a successful response with 'cancel_only' status"""
        kraken_response = {
            "error": [],
            "result": {
                "status": "cancel_only",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.status == "cancel_only"
        assert response.success.timestamp == "2024-01-01T00:00:00Z"

    def test_success_response_parsing_post_only(self):
        """Test parsing a successful response with 'post_only' status"""
        kraken_response = {
            "error": [],
            "result": {
                "status": "post_only",
                "timestamp": "2024-06-15T18:30:45Z",
            },
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.status == "post_only"
        assert response.success.timestamp == "2024-06-15T18:30:45Z"

    def test_invalid_status_validation(self):
        """Test that invalid status values are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetSystemStatusSuccess(
                status="invalid_status",
                timestamp="2021-03-22T17:18:03Z",
            )

        # Should contain validation error about status literal
        assert "status" in str(exc_info.value).lower()

    def test_various_timestamp_formats(self):
        """Test parsing responses with various ISO 8601 timestamp formats"""
        # Standard format
        kraken_response1 = {
            "error": [],
            "result": {
                "status": "online",
                "timestamp": "2025-01-15T10:30:00Z",
            },
        }

        response1 = GetSystemStatusResponse.from_response(kraken_response1)
        assert response1.is_success is True
        assert response1.success.timestamp == "2025-01-15T10:30:00Z"

        # With milliseconds
        kraken_response2 = {
            "error": [],
            "result": {
                "status": "online",
                "timestamp": "2025-01-15T10:30:00.123Z",
            },
        }

        response2 = GetSystemStatusResponse.from_response(kraken_response2)
        assert response2.is_success is True
        assert response2.success.timestamp == "2025-01-15T10:30:00.123Z"

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Internal error"],
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Internal error" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Internal error",
                "EAPI:Rate limit exceeded",
            ],
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Internal error" in response.failure.error
        assert "EAPI:Rate limit exceeded" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "status": "online",
                    "timestamp": "2021-03-22T17:18:03Z",
                },
            }
        )

        response = GetSystemStatusResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.status == "online"
        assert response.success.timestamp == "2021-03-22T17:18:03Z"

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetSystemStatusResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetSystemStatusSuccess directly with all status types"""
        # Online status
        success1 = GetSystemStatusSuccess(
            status="online",
            timestamp="2021-03-22T17:18:03Z",
        )
        assert success1.status == "online"
        assert success1.timestamp == "2021-03-22T17:18:03Z"

        # Maintenance status
        success2 = GetSystemStatusSuccess(
            status="maintenance",
            timestamp="2023-10-15T12:00:00Z",
        )
        assert success2.status == "maintenance"

        # Cancel only status
        success3 = GetSystemStatusSuccess(
            status="cancel_only",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert success3.status == "cancel_only"

        # Post only status
        success4 = GetSystemStatusSuccess(
            status="post_only",
            timestamp="2024-06-15T18:30:45Z",
        )
        assert success4.status == "post_only"

    def test_success_model_field_types(self):
        """Test that field types are enforced"""
        # Valid types
        success = GetSystemStatusSuccess(
            status="online",
            timestamp="2021-03-22T17:18:03Z",
        )

        assert isinstance(success.status, str)
        assert isinstance(success.timestamp, str)
        assert success.status in ["online", "maintenance", "cancel_only", "post_only"]

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        from kraken.rest.schema.base import ResponseErrorSchema

        error = ResponseErrorSchema(error=["EGeneral:Internal error"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Internal error"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetSystemStatusResponse wrapper directly"""
        success = GetSystemStatusSuccess(
            status="online",
            timestamp="2021-03-22T17:18:03Z",
        )
        response = GetSystemStatusResponse(success=success)

        assert response.is_success is True
        assert response.success.status == "online"

        from kraken.rest.schema.base import ResponseErrorSchema

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetSystemStatusResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_concurrent_response_parsing(self):
        """Test concurrent parsing of multiple responses"""
        import concurrent.futures

        statuses = ["online", "maintenance", "cancel_only", "post_only"]

        def parse_response(i):
            kraken_response = {
                "error": [],
                "result": {
                    "status": statuses[i % len(statuses)],
                    "timestamp": f"2021-03-22T17:18:{i:02d}Z",
                },
            }
            return GetSystemStatusResponse.from_response(kraken_response)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(executor.map(parse_response, range(20)))

        assert len(responses) == 20
        for i, resp in enumerate(responses):
            assert resp.is_success is True
            assert resp.success.status == statuses[i % len(statuses)]

    def test_response_immutability(self):
        """Test that response objects maintain their data correctly"""
        kraken_response = {
            "error": [],
            "result": {
                "status": "online",
                "timestamp": "2021-03-22T17:18:03Z",
            },
        }

        response = GetSystemStatusResponse.from_response(kraken_response)

        # Store original values
        original_status = response.success.status
        original_timestamp = response.success.timestamp

        # Values should remain unchanged
        assert response.success.status == original_status
        assert response.success.timestamp == original_timestamp

    def test_all_status_literals(self):
        """Test that all documented status literals work correctly"""
        statuses = ["online", "maintenance", "cancel_only", "post_only"]

        for status in statuses:
            kraken_response = {
                "error": [],
                "result": {
                    "status": status,
                    "timestamp": "2021-03-22T17:18:03Z",
                },
            }

            response = GetSystemStatusResponse.from_response(kraken_response)

            assert response.is_success is True
            assert response.success.status == status
            assert response.success.timestamp == "2021-03-22T17:18:03Z"

    def test_status_field_validation_rejects_typos(self):
        """Test that common typos in status field are rejected"""
        invalid_statuses = [
            "Online",  # Wrong case
            "ONLINE",  # Wrong case
            "on-line",  # Wrong format
            "cancelonly",  # Missing underscore
            "cancel-only",  # Wrong separator
            "postonly",  # Missing underscore
            "post-only",  # Wrong separator
        ]

        for invalid_status in invalid_statuses:
            with pytest.raises(ValidationError):
                GetSystemStatusSuccess(
                    status=invalid_status,
                    timestamp="2021-03-22T17:18:03Z",
                )


class TestGetAssetInfoRequest:
    """Tests for GetAssetInfoRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request with no parameters"""
        asset_info_request = GetAssetInfoRequest()

        # Should be valid with all fields None
        assert asset_info_request is not None
        assert asset_info_request.asset is None
        assert asset_info_request.aclass is None

    def test_single_asset_parameter(self):
        """Test request with single asset"""
        asset_info_request = GetAssetInfoRequest(asset="XBT")

        assert asset_info_request.asset == "XBT"
        assert asset_info_request.aclass is None

    def test_multiple_assets_parameter(self):
        """Test request with multiple comma-delimited assets"""
        asset_info_request = GetAssetInfoRequest(asset="XBT,ETH,USD")

        assert asset_info_request.asset == "XBT,ETH,USD"

    def test_with_aclass_parameter(self):
        """Test request with asset class filter"""
        asset_info_request = GetAssetInfoRequest(aclass="currency")

        assert asset_info_request.aclass == "currency"
        assert asset_info_request.asset is None

    def test_with_aclass_parameter(self):
        """Test request with aclass parameter"""
        asset_info_request = GetAssetInfoRequest(aclass="currency")

        assert asset_info_request.aclass == "currency"
        assert asset_info_request.asset is None

    def test_all_parameters_combined(self):
        """Test request with all parameters specified"""
        asset_info_request = GetAssetInfoRequest(asset="XBT,ETH", aclass="currency")

        assert asset_info_request.asset == "XBT,ETH"
        assert asset_info_request.aclass == "currency"

    def test_to_api_dict_method_no_params(self):
        """Test to_api_dict() serialization with no parameters"""
        asset_info_request = GetAssetInfoRequest()

        # to_api_dict() should exclude None values by default
        data = asset_info_request.to_api_dict()

        # Should return empty dict (all None values excluded)
        assert data == {}

    def test_to_api_dict_method_with_params(self):
        """Test to_api_dict() serialization with parameters"""
        asset_info_request = GetAssetInfoRequest(asset="XBT,ETH", aclass="currency")

        data = asset_info_request.to_api_dict()

        assert data["asset"] == "XBT,ETH"
        assert data["aclass"] == "currency"
        assert "info" not in data  # None value excluded

    def test_to_api_dict_exclude_none_false(self):
        """Test to_api_dict() with exclude_none=False"""
        asset_info_request = GetAssetInfoRequest(asset="XBT")

        data = asset_info_request.to_api_dict(exclude_none=False)

        assert data["asset"] == "XBT"
        assert data["aclass"] is None

    def test_multiple_instances(self):
        """Test creating multiple GetAssetInfoRequest instances"""
        requests = [
            GetAssetInfoRequest(),
            GetAssetInfoRequest(asset="XBT"),
            GetAssetInfoRequest(aclass="currency"),
            GetAssetInfoRequest(asset="ETH", aclass="currency"),
        ]

        assert len(requests) == 4
        for req in requests:
            assert req is not None

    def test_various_asset_combinations(self):
        """Test various asset parameter combinations"""
        test_cases = [
            "XBT",
            "XBT,ETH",
            "XBT,ETH,USD",
            "XXBT,ZUSD",
            "ADA,ATOM,DOT",
        ]

        for assets in test_cases:
            request = GetAssetInfoRequest(asset=assets)
            assert request.asset == assets
            data = request.to_api_dict()
            assert data["asset"] == assets

    def test_asset_list_input_single_item(self):
        """Test asset parameter as list with single item"""
        request = GetAssetInfoRequest(asset=["XBT"])

        assert request.asset == "XBT"
        data = request.to_api_dict()
        assert data["asset"] == "XBT"

    def test_asset_list_input_multiple_items(self):
        """Test asset parameter as list with multiple items"""
        request = GetAssetInfoRequest(asset=["XBT", "ETH", "USD"])

        assert request.asset == "XBT,ETH,USD"
        data = request.to_api_dict()
        assert data["asset"] == "XBT,ETH,USD"

    def test_asset_list_with_whitespace(self):
        """Test that list items with whitespace are trimmed"""
        request = GetAssetInfoRequest(asset=[" XBT ", "  ETH", "USD  "])

        assert request.asset == "XBT,ETH,USD"

    def test_asset_list_duplicate_removal(self):
        """Test that duplicate assets are removed while preserving order"""
        request = GetAssetInfoRequest(asset=["XBT", "ETH", "XBT", "USD", "ETH"])

        # Should keep first occurrence only
        assert request.asset == "XBT,ETH,USD"

    def test_asset_list_with_duplicates_case_sensitive(self):
        """Test that duplicate removal is case-sensitive"""
        request = GetAssetInfoRequest(asset=["XBT", "xbt", "ETH"])

        # Different cases are treated as different assets
        assert request.asset == "XBT,xbt,ETH"

    def test_asset_string_vs_list_equivalence(self):
        """Test that string and list inputs produce equivalent results"""
        request_string = GetAssetInfoRequest(asset="XBT,ETH,USD")
        request_list = GetAssetInfoRequest(asset=["XBT", "ETH", "USD"])

        assert request_string.asset == request_list.asset
        assert request_string.to_api_dict() == request_list.to_api_dict()

    def test_asset_list_empty_validation(self):
        """Test that empty list is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetInfoRequest(asset=[])

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_asset_list_empty_string_validation(self):
        """Test that list with empty strings is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetInfoRequest(asset=["XBT", "", "ETH"])

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_asset_list_whitespace_only_validation(self):
        """Test that list with whitespace-only strings is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetInfoRequest(asset=["XBT", "   ", "ETH"])

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_asset_list_non_string_validation(self):
        """Test that list with non-string items is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetInfoRequest(asset=["XBT", 123, "ETH"])

        assert "string" in str(exc_info.value).lower()

    def test_asset_string_empty_validation(self):
        """Test that empty string is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetInfoRequest(asset="")

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_asset_string_whitespace_validation(self):
        """Test that whitespace-only string is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetInfoRequest(asset="   ")

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_asset_string_with_whitespace_trimmed(self):
        """Test that string with leading/trailing whitespace is trimmed"""
        request = GetAssetInfoRequest(asset="  XBT,ETH,USD  ")

        assert request.asset == "XBT,ETH,USD"

    def test_asset_invalid_type_validation(self):
        """Test that invalid types are rejected"""
        invalid_values = [123, 45.67, True, {"XBT": "BTC"}, (("XBT", "ETH"))]

        for invalid_value in invalid_values:
            with pytest.raises(ValidationError):
                GetAssetInfoRequest(asset=invalid_value)

    def test_asset_list_many_items(self):
        """Test list with many asset items"""
        assets = [f"ASSET{i}" for i in range(20)]
        request = GetAssetInfoRequest(asset=assets)

        expected = ",".join(assets)
        assert request.asset == expected

    def test_asset_list_with_common_assets(self):
        """Test list with realistic asset names"""
        common_assets = ["BTC", "ETH", "USDT", "USDC", "XRP", "ADA", "SOL", "DOT"]
        request = GetAssetInfoRequest(asset=common_assets)

        assert request.asset == "BTC,ETH,USDT,USDC,XRP,ADA,SOL,DOT"

    def test_asset_list_order_preservation(self):
        """Test that list order is preserved in conversion"""
        request = GetAssetInfoRequest(asset=["USD", "XBT", "ETH", "ADA"])

        # Order should be preserved
        assert request.asset == "USD,XBT,ETH,ADA"

    def test_combined_list_with_other_params(self):
        """Test asset list combined with other parameters"""
        request = GetAssetInfoRequest(asset=["XBT", "ETH"], aclass="currency")

        assert request.asset == "XBT,ETH"
        assert request.aclass == "currency"

        data = request.to_api_dict()
        assert data["asset"] == "XBT,ETH"
        assert data["aclass"] == "currency"


class TestGetAssetInfoResponse:
    """Tests for GetAssetInfo response schemas"""

    def test_asset_info_model_direct_instantiation(self):
        """Test creating AssetInfo model directly"""
        asset_info = AssetInfo(
            aclass="currency", altname="BTC", decimals=10, display_decimals=5, status="enabled"
        )

        assert asset_info.aclass == "currency"
        assert asset_info.altname == "BTC"
        assert asset_info.decimals == 10
        assert asset_info.display_decimals == 5

    def test_success_response_single_asset(self):
        """Test parsing a successful response with single asset"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBT": {
                    "aclass": "currency",
                    "altname": "XBT",
                    "decimals": 10,
                    "display_decimals": 5,
                    "status": "enabled",
                }
            },
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert "XXBT" in response.success.assets
        assert response.success.assets["XXBT"].altname == "XBT"
        assert response.success.assets["XXBT"].decimals == 10
        assert response.success.assets["XXBT"].display_decimals == 5

    def test_success_response_multiple_assets(self):
        """Test parsing a successful response with multiple assets"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBT": {
                    "aclass": "currency",
                    "altname": "XBT",
                    "decimals": 10,
                    "display_decimals": 5,
                    "status": "enabled",
                },
                "ZUSD": {
                    "aclass": "currency",
                    "altname": "USD",
                    "decimals": 4,
                    "display_decimals": 2,
                    "status": "enabled",
                },
                "XETH": {
                    "aclass": "currency",
                    "altname": "ETH",
                    "decimals": 10,
                    "display_decimals": 5,
                    "status": "enabled",
                },
            },
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.assets) == 3
        assert "XXBT" in response.success.assets
        assert "ZUSD" in response.success.assets
        assert "XETH" in response.success.assets

        # Check XXBT
        assert response.success.assets["XXBT"].altname == "XBT"
        assert response.success.assets["XXBT"].decimals == 10

        # Check ZUSD
        assert response.success.assets["ZUSD"].altname == "USD"
        assert response.success.assets["ZUSD"].decimals == 4
        assert response.success.assets["ZUSD"].display_decimals == 2

        # Check XETH
        assert response.success.assets["XETH"].altname == "ETH"

    def test_empty_result_response(self):
        """Test parsing response with no assets (valid but empty)"""
        kraken_response = {"error": [], "result": {}}

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.assets) == 0
        assert response.success.assets == {}

    def test_various_decimal_values(self):
        """Test assets with different decimal precision values"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBT": {
                    "aclass": "currency",
                    "altname": "XBT",
                    "decimals": 10,
                    "display_decimals": 5,
                    "status": "enabled",
                },
                "ZUSD": {
                    "aclass": "currency",
                    "altname": "USD",
                    "decimals": 4,
                    "display_decimals": 2,
                    "status": "enabled",
                },
                "ADA": {
                    "aclass": "currency",
                    "altname": "ADA",
                    "decimals": 8,
                    "display_decimals": 6,
                    "status": "enabled",
                },
            },
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.assets["XXBT"].decimals == 10
        assert response.success.assets["ZUSD"].decimals == 4
        assert response.success.assets["ADA"].decimals == 8

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Internal error"],
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Internal error" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Internal error",
                "EAPI:Rate limit exceeded",
            ],
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Internal error" in response.failure.error
        assert "EAPI:Rate limit exceeded" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBT": {
                        "aclass": "currency",
                        "altname": "XBT",
                        "decimals": 10,
                        "display_decimals": 5,
                        "status": "enabled",
                    }
                },
            }
        )

        response = GetAssetInfoResponse.from_response(json_response)

        assert response.is_success is True
        assert "XXBT" in response.success.assets
        assert response.success.assets["XXBT"].altname == "XBT"

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetAssetInfoResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetAssetInfoSuccess directly"""
        asset1 = AssetInfo(
            aclass="currency", altname="BTC", decimals=10, display_decimals=5, status="enabled"
        )
        asset2 = AssetInfo(
            aclass="currency", altname="USD", decimals=4, display_decimals=2, status="enabled"
        )

        success = GetAssetInfoSuccess(assets={"XXBT": asset1, "ZUSD": asset2})

        assert len(success.assets) == 2
        assert success.assets["XXBT"].altname == "BTC"
        assert success.assets["ZUSD"].altname == "USD"

    def test_asset_info_field_types(self):
        """Test that AssetInfo field types are enforced"""
        asset_info = AssetInfo(
            aclass="currency", altname="BTC", decimals=10, display_decimals=5, status="enabled"
        )

        assert isinstance(asset_info.aclass, str)
        assert isinstance(asset_info.altname, str)
        assert isinstance(asset_info.decimals, int)
        assert isinstance(asset_info.display_decimals, int)

    def test_asset_info_missing_fields_validation(self):
        """Test that AssetInfo validates required fields"""
        with pytest.raises(ValidationError):
            AssetInfo(aclass="currency", altname="BTC")  # Missing decimals fields

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetAssetInfoResponse wrapper directly"""
        asset = AssetInfo(
            aclass="currency", altname="BTC", decimals=10, display_decimals=5, status="enabled"
        )
        success = GetAssetInfoSuccess(assets={"XXBT": asset})
        response = GetAssetInfoResponse(success=success)

        assert response.is_success is True
        assert "XXBT" in response.success.assets

        from kraken.rest.schema.base import ResponseErrorSchema

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetAssetInfoResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_dictionary_access_patterns(self):
        """Test various dictionary access patterns on assets"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBT": {
                    "aclass": "currency",
                    "altname": "XBT",
                    "decimals": 10,
                    "display_decimals": 5,
                    "status": "enabled",
                },
                "ZUSD": {
                    "aclass": "currency",
                    "altname": "USD",
                    "decimals": 4,
                    "display_decimals": 2,
                    "status": "enabled",
                },
            },
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        # Test dict access
        assert "XXBT" in response.success.assets
        assert "ZUSD" in response.success.assets
        assert "INVALID" not in response.success.assets

        # Test iteration
        asset_names = list(response.success.assets.keys())
        assert "XXBT" in asset_names
        assert "ZUSD" in asset_names

        # Test values
        for asset_info in response.success.assets.values():
            assert isinstance(asset_info, AssetInfo)

    def test_concurrent_response_parsing(self):
        """Test concurrent parsing of multiple responses"""
        import concurrent.futures

        def parse_response(i):
            kraken_response = {
                "error": [],
                "result": {
                    f"ASSET{i}": {
                        "aclass": "currency",
                        "altname": f"A{i}",
                        "decimals": 10,
                        "display_decimals": 5,
                        "status": "enabled",
                    }
                },
            }
            return GetAssetInfoResponse.from_response(kraken_response)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(executor.map(parse_response, range(20)))

        assert len(responses) == 20
        for i, resp in enumerate(responses):
            assert resp.is_success is True
            assert f"ASSET{i}" in resp.success.assets

    def test_response_immutability(self):
        """Test that response objects maintain their data correctly"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBT": {
                    "aclass": "currency",
                    "altname": "XBT",
                    "decimals": 10,
                    "display_decimals": 5,
                    "status": "enabled",
                }
            },
        }

        response = GetAssetInfoResponse.from_response(kraken_response)

        # Store original values
        original_asset_count = len(response.success.assets)
        original_altname = response.success.assets["XXBT"].altname

        # Values should remain unchanged
        assert len(response.success.assets) == original_asset_count
        assert response.success.assets["XXBT"].altname == original_altname

    def test_many_assets_response(self):
        """Test response with many assets (simulating full asset list)"""
        # Create a response with 50 different assets
        result = {}
        for i in range(50):
            result[f"ASSET{i}"] = {
                "aclass": "currency",
                "altname": f"A{i}",
                "decimals": 8 + (i % 3),
                "display_decimals": 4 + (i % 3),
                "status": "enabled",
            }

        kraken_response = {"error": [], "result": result}

        response = GetAssetInfoResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.assets) == 50

        # Verify some random assets (0 % 3 = 0, 10 % 3 = 1, 24 % 3 = 0)
        assert response.success.assets["ASSET0"].decimals == 8
        assert response.success.assets["ASSET10"].decimals == 9
        assert response.success.assets["ASSET24"].decimals == 8

    def test_asset_info_decimal_precision_values(self):
        """Test that various decimal precision values are handled correctly"""
        test_cases = [
            {"decimals": 0, "display_decimals": 0},
            {"decimals": 2, "display_decimals": 2},
            {"decimals": 4, "display_decimals": 2},
            {"decimals": 8, "display_decimals": 6},
            {"decimals": 10, "display_decimals": 5},
            {"decimals": 18, "display_decimals": 8},
        ]

        for i, precision in enumerate(test_cases):
            asset_info = AssetInfo(
                aclass="currency",
                altname=f"TEST{i}",
                decimals=precision["decimals"],
                display_decimals=precision["display_decimals"],
                status="enabled",
            )

            assert asset_info.decimals == precision["decimals"]
            assert asset_info.display_decimals == precision["display_decimals"]

    def test_altname_variations(self):
        """Test that various altname formats are accepted"""
        altnames = ["BTC", "ETH", "USD", "EUR", "ADA", "DOT", "SOL", "MATIC"]

        for i, altname in enumerate(altnames):
            asset_info = AssetInfo(
                aclass="currency",
                altname=altname,
                decimals=10,
                display_decimals=5,
                status="enabled",
            )

            assert asset_info.altname == altname


class TestNormalizeCommaSeperatedListValidator:
    """Tests for normalize_comma_separated_list validator function"""

    def test_none_input(self):
        """Test that None input returns None"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(None)
        assert result is None

    def test_single_string(self):
        """Test single string input is returned as-is after stripping"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list("BTC")
        assert result == "BTC"

    def test_string_with_whitespace(self):
        """Test that string whitespace is stripped"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list("  BTC  ")
        assert result == "BTC"

    def test_comma_separated_string(self):
        """Test comma-separated string is returned after stripping"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list("BTC,ETH")
        assert result == "BTC,ETH"

    def test_comma_separated_string_with_spaces(self):
        """Test comma-separated string with extra spaces"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list("  BTC,ETH,USD  ")
        assert result == "BTC,ETH,USD"

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="String cannot be empty or whitespace"):
            validators.normalize_comma_separated_list("")

    def test_whitespace_only_string_raises_error(self):
        """Test that whitespace-only string raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="String cannot be empty or whitespace"):
            validators.normalize_comma_separated_list("   ")

    def test_list_with_single_item(self):
        """Test list with single item is converted to string"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["BTC"])
        assert result == "BTC"

    def test_list_with_multiple_items(self):
        """Test list with multiple items is converted to comma-separated string"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["BTC", "ETH"])
        assert result == "BTC,ETH"

    def test_list_with_three_items(self):
        """Test list with three items"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["BTC", "ETH", "USD"])
        assert result == "BTC,ETH,USD"

    def test_list_items_with_whitespace(self):
        """Test that list items are stripped of whitespace"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["  BTC  ", "  ETH  "])
        assert result == "BTC,ETH"

    def test_list_with_duplicates_removes_duplicates(self):
        """Test that duplicate items are removed while preserving order"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["BTC", "ETH", "BTC"])
        assert result == "BTC,ETH"

    def test_list_with_multiple_duplicates(self):
        """Test removal of multiple duplicate items"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(
            ["BTC", "ETH", "BTC", "USD", "ETH", "BTC"]
        )
        assert result == "BTC,ETH,USD"

    def test_list_duplicate_removal_preserves_order(self):
        """Test that first occurrence order is preserved when removing duplicates"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["ETH", "BTC", "USD", "BTC", "ETH"])
        assert result == "ETH,BTC,USD"

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="List cannot be empty"):
            validators.normalize_comma_separated_list([])

    def test_list_with_non_string_raises_error(self):
        """Test that list with non-string item raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="All list items must be strings, got int"):
            validators.normalize_comma_separated_list(["BTC", 123])

    def test_list_with_float_raises_error(self):
        """Test that list with float item raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="All list items must be strings, got float"):
            validators.normalize_comma_separated_list(["BTC", 3.14])

    def test_list_with_empty_string_raises_error(self):
        """Test that list with empty string raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(
            ValueError, match="List cannot contain empty or whitespace-only strings"
        ):
            validators.normalize_comma_separated_list(["BTC", ""])

    def test_list_with_whitespace_only_string_raises_error(self):
        """Test that list with whitespace-only string raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(
            ValueError, match="List cannot contain empty or whitespace-only strings"
        ):
            validators.normalize_comma_separated_list(["BTC", "   "])

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="Must be a string, list, or None, got int"):
            validators.normalize_comma_separated_list(123)

    def test_dict_raises_error(self):
        """Test that dict type raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="Must be a string, list, or None, got dict"):
            validators.normalize_comma_separated_list({"BTC": "Bitcoin"})

    def test_tuple_raises_error(self):
        """Test that tuple type raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="Must be a string, list, or None, got tuple"):
            validators.normalize_comma_separated_list(("BTC", "ETH"))

    def test_set_raises_error(self):
        """Test that set type raises ValueError"""
        from kraken.rest.schema import validators

        with pytest.raises(ValueError, match="Must be a string, list, or None, got set"):
            validators.normalize_comma_separated_list({"BTC", "ETH"})

    def test_various_asset_names(self):
        """Test with various realistic asset names"""
        from kraken.rest.schema import validators

        test_cases = [
            (["XBT", "ETH", "USD"], "XBT,ETH,USD"),
            (["XXBT", "XETH", "ZUSD"], "XXBT,XETH,ZUSD"),
            (["BTC", "ETH", "ADA", "DOT"], "BTC,ETH,ADA,DOT"),
        ]

        for input_list, expected in test_cases:
            result = validators.normalize_comma_separated_list(input_list)
            assert result == expected

    def test_case_sensitivity_preserved(self):
        """Test that case sensitivity is preserved"""
        from kraken.rest.schema import validators

        result = validators.normalize_comma_separated_list(["btc", "BTC", "Btc"])
        # All three are different strings, so all should be preserved
        assert result == "btc,BTC,Btc"

    def test_long_list(self):
        """Test with a longer list of items"""
        from kraken.rest.schema import validators

        items = [f"ASSET{i}" for i in range(20)]
        result = validators.normalize_comma_separated_list(items)
        expected = ",".join(items)
        assert result == expected

    def test_integration_with_get_asset_info_request(self):
        """Test integration with GetAssetInfoRequest schema"""
        # Test with string
        request1 = GetAssetInfoRequest(asset="BTC")
        assert request1.asset == "BTC"

        # Test with comma-separated string
        request2 = GetAssetInfoRequest(asset="BTC,ETH")
        assert request2.asset == "BTC,ETH"

        # Test with list
        request3 = GetAssetInfoRequest(asset=["BTC", "ETH"])
        assert request3.asset == "BTC,ETH"

        # Test with None
        request4 = GetAssetInfoRequest(asset=None)
        assert request4.asset is None

        # Test with list containing duplicates
        request5 = GetAssetInfoRequest(asset=["BTC", "ETH", "BTC"])
        assert request5.asset == "BTC,ETH"

    def test_integration_empty_string_error(self):
        """Test that GetAssetInfoRequest raises error for empty string"""
        with pytest.raises(ValidationError, match="String cannot be empty or whitespace"):
            GetAssetInfoRequest(asset="")

    def test_integration_empty_list_error(self):
        """Test that GetAssetInfoRequest raises error for empty list"""
        with pytest.raises(ValidationError, match="List cannot be empty"):
            GetAssetInfoRequest(asset=[])

    def test_integration_list_with_non_string_error(self):
        """Test that GetAssetInfoRequest raises error for list with non-string"""
        with pytest.raises(ValidationError, match="All list items must be strings"):
            GetAssetInfoRequest(asset=["BTC", 123])


class TestGetAssetPairsRequest:
    """Tests for GetAssetPairsRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request with no parameters"""
        pairs_request = GetAssetPairsRequest()

        # Should be valid with all fields None
        assert pairs_request is not None
        assert pairs_request.pair is None
        assert pairs_request.aclass_base is None
        assert pairs_request.info is None
        assert pairs_request.country_code is None

    def test_single_pair_parameter(self):
        """Test request with single pair"""
        pairs_request = GetAssetPairsRequest(pair="BTC/USD")

        assert pairs_request.pair == "BTC/USD"
        assert pairs_request.aclass_base is None
        assert pairs_request.info is None
        assert pairs_request.country_code is None

    def test_multiple_pairs_parameter(self):
        """Test request with multiple comma-delimited pairs"""
        pairs_request = GetAssetPairsRequest(pair="BTC/USD,ETH/BTC,XRP/USD")

        assert pairs_request.pair == "BTC/USD,ETH/BTC,XRP/USD"

    def test_with_aclass_base_currency(self):
        """Test request with aclass_base filter set to currency"""
        pairs_request = GetAssetPairsRequest(aclass_base="currency")

        assert pairs_request.aclass_base == "currency"
        assert pairs_request.pair is None

    def test_with_aclass_base_tokenized_asset(self):
        """Test request with aclass_base filter set to tokenized_asset"""
        pairs_request = GetAssetPairsRequest(aclass_base="tokenized_asset")

        assert pairs_request.aclass_base == "tokenized_asset"
        assert pairs_request.pair is None

    def test_with_info_parameter_info(self):
        """Test request with info parameter set to 'info'"""
        pairs_request = GetAssetPairsRequest(info="info")

        assert pairs_request.info == "info"

    def test_with_info_parameter_leverage(self):
        """Test request with info parameter set to 'leverage'"""
        pairs_request = GetAssetPairsRequest(info="leverage")

        assert pairs_request.info == "leverage"

    def test_with_info_parameter_fees(self):
        """Test request with info parameter set to 'fees'"""
        pairs_request = GetAssetPairsRequest(info="fees")

        assert pairs_request.info == "fees"

    def test_with_info_parameter_margin(self):
        """Test request with info parameter set to 'margin'"""
        pairs_request = GetAssetPairsRequest(info="margin")

        assert pairs_request.info == "margin"

    def test_with_country_code_parameter(self):
        """Test request with country_code parameter"""
        pairs_request = GetAssetPairsRequest(country_code="GB")

        assert pairs_request.country_code == "GB"
        assert pairs_request.pair is None

    def test_all_parameters_combined(self):
        """Test request with all parameters specified"""
        pairs_request = GetAssetPairsRequest(
            pair="BTC/USD,ETH/BTC", aclass_base="currency", info="fees", country_code="US"
        )

        assert pairs_request.pair == "BTC/USD,ETH/BTC"
        assert pairs_request.aclass_base == "currency"
        assert pairs_request.info == "fees"
        assert pairs_request.country_code == "US"

    def test_to_api_dict_method_no_params(self):
        """Test to_api_dict() serialization with no parameters"""
        pairs_request = GetAssetPairsRequest()

        data = pairs_request.to_api_dict()

        # Should return empty dict (all None values excluded)
        assert data == {}

    def test_to_api_dict_method_with_params(self):
        """Test to_api_dict() serialization with parameters"""
        pairs_request = GetAssetPairsRequest(pair="BTC/USD", info="leverage")

        data = pairs_request.to_api_dict()

        assert data["pair"] == "BTC/USD"
        assert data["info"] == "leverage"
        assert "aclass_base" not in data  # None value excluded
        assert "country_code" not in data  # None value excluded

    def test_to_api_dict_exclude_none_false(self):
        """Test to_api_dict() with exclude_none=False"""
        pairs_request = GetAssetPairsRequest(pair="BTC/USD")

        data = pairs_request.to_api_dict(exclude_none=False)

        assert data["pair"] == "BTC/USD"
        assert data["aclass_base"] is None
        assert data["info"] is None
        assert data["country_code"] is None

    def test_pair_list_input_single_item(self):
        """Test pair parameter as list with single item"""
        request = GetAssetPairsRequest(pair=["BTC/USD"])

        assert request.pair == "BTC/USD"
        data = request.to_api_dict()
        assert data["pair"] == "BTC/USD"

    def test_pair_list_input_multiple_items(self):
        """Test pair parameter as list with multiple items"""
        request = GetAssetPairsRequest(pair=["BTC/USD", "ETH/BTC", "XRP/USD"])

        assert request.pair == "BTC/USD,ETH/BTC,XRP/USD"
        data = request.to_api_dict()
        assert data["pair"] == "BTC/USD,ETH/BTC,XRP/USD"

    def test_pair_list_with_whitespace(self):
        """Test that list items with whitespace are trimmed"""
        request = GetAssetPairsRequest(pair=[" BTC/USD ", "  ETH/BTC", "XRP/USD  "])

        assert request.pair == "BTC/USD,ETH/BTC,XRP/USD"

    def test_pair_list_duplicate_removal(self):
        """Test that duplicate pairs are removed while preserving order"""
        request = GetAssetPairsRequest(
            pair=["BTC/USD", "ETH/BTC", "BTC/USD", "XRP/USD", "ETH/BTC"]
        )

        # Should keep first occurrence only
        assert request.pair == "BTC/USD,ETH/BTC,XRP/USD"

    def test_pair_string_vs_list_equivalence(self):
        """Test that string and list inputs produce equivalent results"""
        request_string = GetAssetPairsRequest(pair="BTC/USD,ETH/BTC,XRP/USD")
        request_list = GetAssetPairsRequest(pair=["BTC/USD", "ETH/BTC", "XRP/USD"])

        assert request_string.pair == request_list.pair
        assert request_string.to_api_dict() == request_list.to_api_dict()

    def test_pair_list_empty_validation(self):
        """Test that empty list is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetPairsRequest(pair=[])

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_pair_list_empty_string_validation(self):
        """Test that list with empty strings is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetPairsRequest(pair=["BTC/USD", "", "ETH/BTC"])

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_pair_string_empty_validation(self):
        """Test that empty string is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetPairsRequest(pair="")

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_pair_string_whitespace_validation(self):
        """Test that whitespace-only string is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetAssetPairsRequest(pair="   ")

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_invalid_info_parameter(self):
        """Test that invalid info value is rejected"""
        with pytest.raises(ValidationError):
            GetAssetPairsRequest(info="invalid")

    def test_invalid_aclass_base_parameter(self):
        """Test that invalid aclass_base value is rejected"""
        with pytest.raises(ValidationError):
            GetAssetPairsRequest(aclass_base="invalid")

    def test_multiple_instances(self):
        """Test creating multiple GetAssetPairsRequest instances"""
        requests = [
            GetAssetPairsRequest(),
            GetAssetPairsRequest(pair="BTC/USD"),
            GetAssetPairsRequest(aclass_base="currency"),
            GetAssetPairsRequest(info="leverage"),
            GetAssetPairsRequest(country_code="GB"),
        ]

        assert len(requests) == 5
        for req in requests:
            assert req is not None

    def test_various_pair_combinations(self):
        """Test various pair parameter combinations"""
        test_cases = [
            "BTC/USD",
            "BTC/USD,ETH/BTC",
            "BTC/USD,ETH/BTC,XRP/USD",
            "XXBT/ZUSD,XETH/ZUSD",
            "ADA/USD,ATOM/USD,DOT/USD",
        ]

        for pairs in test_cases:
            request = GetAssetPairsRequest(pair=pairs)
            assert request.pair == pairs
            data = request.to_api_dict()
            assert data["pair"] == pairs

    def test_various_country_codes(self):
        """Test various country code values"""
        test_cases = ["US", "GB", "DE", "JP", "AU", "CA", "FR"]

        for code in test_cases:
            request = GetAssetPairsRequest(country_code=code)
            assert request.country_code == code
            data = request.to_api_dict()
            assert data["country_code"] == code

    def test_combined_list_with_other_params(self):
        """Test pair list combined with other parameters"""
        request = GetAssetPairsRequest(
            pair=["BTC/USD", "ETH/BTC"], aclass_base="currency", info="fees", country_code="US"
        )

        assert request.pair == "BTC/USD,ETH/BTC"
        assert request.aclass_base == "currency"
        assert request.info == "fees"
        assert request.country_code == "US"

        data = request.to_api_dict()
        assert data["pair"] == "BTC/USD,ETH/BTC"
        assert data["aclass_base"] == "currency"
        assert data["info"] == "fees"
        assert data["country_code"] == "US"


class TestGetAssetPairsResponse:
    """Tests for GetAssetPairs response schemas"""

    def test_asset_pair_info_model_direct_instantiation(self):
        """Test creating AssetPairInfo model directly"""
        pair_info = AssetPairInfo(
            altname="XBTUSDT",
            wsname="BTC/USDT",
            aclass_base="currency",
            base="XXBT",
            aclass_quote="currency",
            quote="USDT",
            pair_decimals=1,
            cost_decimals=5,
            lot_decimals=8,
            lot_multiplier=1,
            ordermin="0.0001",
            costmin="0.5",
            tick_size="0.1",
            status="online",
        )

        assert pair_info.altname == "XBTUSDT"
        assert pair_info.wsname == "BTC/USDT"
        assert pair_info.aclass_base == "currency"
        assert pair_info.base == "XXBT"
        assert pair_info.pair_decimals == 1
        assert pair_info.status == "online"

    def test_success_response_single_pair(self):
        """Test parsing a successful response with single pair"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                }
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert "XXBTZUSD" in response.success.pairs
        assert response.success.pairs["XXBTZUSD"].altname == "XBTUSDT"
        assert response.success.pairs["XXBTZUSD"].pair_decimals == 1
        assert response.success.pairs["XXBTZUSD"].status == "online"

    def test_success_response_multiple_pairs(self):
        """Test parsing a successful response with multiple pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                },
                "XETHZUSD": {
                    "altname": "ETHUSDT",
                    "wsname": "ETH/USD",
                    "aclass_base": "currency",
                    "base": "XETH",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 2,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "ordermin": "0.001",
                    "costmin": "0.5",
                    "tick_size": "0.01",
                    "status": "online",
                },
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.pairs) == 2
        assert "XXBTZUSD" in response.success.pairs
        assert "XETHZUSD" in response.success.pairs

        # Check XXBTZUSD
        assert response.success.pairs["XXBTZUSD"].altname == "XBTUSDT"
        assert response.success.pairs["XXBTZUSD"].pair_decimals == 1

        # Check XETHZUSD
        assert response.success.pairs["XETHZUSD"].altname == "ETHUSDT"
        assert response.success.pairs["XETHZUSD"].pair_decimals == 2

    def test_empty_result_response(self):
        """Test parsing response with no pairs (valid but empty)"""
        kraken_response = {"error": [], "result": {}}

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.pairs) == 0
        assert response.success.pairs == {}

    def test_response_with_leverage_info(self):
        """Test parsing response with leverage information"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "leverage_buy": [2, 3, 4, 5],
                    "leverage_sell": [2, 3, 4, 5],
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                }
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.pairs["XXBTZUSD"].leverage_buy == [2, 3, 4, 5]
        assert response.success.pairs["XXBTZUSD"].leverage_sell == [2, 3, 4, 5]

    def test_response_with_fee_info(self):
        """Test parsing response with fee information"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "fees": [[0, 0.26], [50000, 0.24], [100000, 0.22]],
                    "fees_maker": [[0, 0.16], [50000, 0.14], [100000, 0.12]],
                    "fee_volume_currency": "ZUSD",
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                }
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.pairs["XXBTZUSD"].fees == [
            [0, 0.26],
            [50000, 0.24],
            [100000, 0.22],
        ]
        assert response.success.pairs["XXBTZUSD"].fees_maker == [
            [0, 0.16],
            [50000, 0.14],
            [100000, 0.12],
        ]
        assert response.success.pairs["XXBTZUSD"].fee_volume_currency == "ZUSD"

    def test_response_with_margin_info(self):
        """Test parsing response with margin information"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "margin_call": 80,
                    "margin_stop": 40,
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                }
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.pairs["XXBTZUSD"].margin_call == 80
        assert response.success.pairs["XXBTZUSD"].margin_stop == 40

    def test_response_with_position_limits(self):
        """Test parsing response with position limits"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "wsname": "BTC/USD",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "long_position_limit": 500,
                    "short_position_limit": 250,
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                }
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.pairs["XXBTZUSD"].long_position_limit == 500
        assert response.success.pairs["XXBTZUSD"].short_position_limit == 250

    def test_various_status_values(self):
        """Test pairs with different status values"""
        statuses = ["online", "cancel_only", "post_only", "limit_only", "reduce_only"]

        for status in statuses:
            kraken_response = {
                "error": [],
                "result": {
                    "TESTPAIR": {
                        "altname": "TEST",
                        "aclass_base": "currency",
                        "base": "TEST",
                        "aclass_quote": "currency",
                        "quote": "USD",
                        "pair_decimals": 2,
                        "cost_decimals": 5,
                        "lot_decimals": 8,
                        "lot_multiplier": 1,
                        "ordermin": "0.01",
                        "costmin": "1.0",
                        "tick_size": "0.01",
                        "status": status,
                    }
                },
            }

            response = GetAssetPairsResponse.from_response(kraken_response)
            assert response.is_success is True
            assert response.success.pairs["TESTPAIR"].status == status

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Internal error"],
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Internal error" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Internal error",
                "EAPI:Rate limit exceeded",
            ],
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Internal error" in response.failure.error
        assert "EAPI:Rate limit exceeded" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBTZUSD": {
                        "altname": "XBTUSDT",
                        "wsname": "BTC/USD",
                        "aclass_base": "currency",
                        "base": "XXBT",
                        "aclass_quote": "currency",
                        "quote": "ZUSD",
                        "pair_decimals": 1,
                        "cost_decimals": 5,
                        "lot_decimals": 8,
                        "lot_multiplier": 1,
                        "ordermin": "0.0001",
                        "costmin": "0.5",
                        "tick_size": "0.1",
                        "status": "online",
                    }
                },
            }
        )

        response = GetAssetPairsResponse.from_response(json_response)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.pairs
        assert response.success.pairs["XXBTZUSD"].altname == "XBTUSDT"

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetAssetPairsResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetAssetPairsSuccess directly"""
        pair1 = AssetPairInfo(
            altname="XBTUSDT",
            aclass_base="currency",
            base="XXBT",
            aclass_quote="currency",
            quote="ZUSD",
            pair_decimals=1,
            cost_decimals=5,
            lot_decimals=8,
            lot_multiplier=1,
            ordermin="0.0001",
            costmin="0.5",
            tick_size="0.1",
            status="online",
        )
        pair2 = AssetPairInfo(
            altname="ETHUSDT",
            aclass_base="currency",
            base="XETH",
            aclass_quote="currency",
            quote="ZUSD",
            pair_decimals=2,
            cost_decimals=5,
            lot_decimals=8,
            lot_multiplier=1,
            ordermin="0.001",
            costmin="0.5",
            tick_size="0.01",
            status="online",
        )

        success = GetAssetPairsSuccess(pairs={"XXBTZUSD": pair1, "XETHZUSD": pair2})

        assert len(success.pairs) == 2
        assert success.pairs["XXBTZUSD"].altname == "XBTUSDT"
        assert success.pairs["XETHZUSD"].altname == "ETHUSDT"

    def test_asset_pair_info_missing_fields_validation(self):
        """Test that AssetPairInfo validates required fields"""
        with pytest.raises(ValidationError):
            AssetPairInfo(altname="TEST", base="TEST")  # Missing many required fields

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetAssetPairsResponse wrapper directly"""
        pair = AssetPairInfo(
            altname="XBTUSDT",
            aclass_base="currency",
            base="XXBT",
            aclass_quote="currency",
            quote="ZUSD",
            pair_decimals=1,
            cost_decimals=5,
            lot_decimals=8,
            lot_multiplier=1,
            ordermin="0.0001",
            costmin="0.5",
            tick_size="0.1",
            status="online",
        )
        success = GetAssetPairsSuccess(pairs={"XXBTZUSD": pair})
        response = GetAssetPairsResponse(success=success)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.pairs

        from kraken.rest.schema.base import ResponseErrorSchema

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetAssetPairsResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_dictionary_access_patterns(self):
        """Test various dictionary access patterns on pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "altname": "XBTUSDT",
                    "aclass_base": "currency",
                    "base": "XXBT",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 1,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "ordermin": "0.0001",
                    "costmin": "0.5",
                    "tick_size": "0.1",
                    "status": "online",
                },
                "XETHZUSD": {
                    "altname": "ETHUSDT",
                    "aclass_base": "currency",
                    "base": "XETH",
                    "aclass_quote": "currency",
                    "quote": "ZUSD",
                    "pair_decimals": 2,
                    "cost_decimals": 5,
                    "lot_decimals": 8,
                    "lot_multiplier": 1,
                    "ordermin": "0.001",
                    "costmin": "0.5",
                    "tick_size": "0.01",
                    "status": "online",
                },
            },
        }

        response = GetAssetPairsResponse.from_response(kraken_response)

        # Test dict access
        assert "XXBTZUSD" in response.success.pairs
        assert "XETHZUSD" in response.success.pairs
        assert "INVALID" not in response.success.pairs

        # Test iteration
        pair_names = list(response.success.pairs.keys())
        assert "XXBTZUSD" in pair_names
        assert "XETHZUSD" in pair_names

        # Test values
        for pair_info in response.success.pairs.values():
            assert isinstance(pair_info, AssetPairInfo)

    def test_many_pairs_response(self):
        """Test response with many pairs (simulating full pair list)"""
        # Create a response with 50 different pairs
        result = {}
        for i in range(50):
            result[f"PAIR{i}"] = {
                "altname": f"P{i}",
                "aclass_base": "currency",
                "base": f"BASE{i}",
                "aclass_quote": "currency",
                "quote": "USD",
                "pair_decimals": 1 + (i % 3),
                "cost_decimals": 4 + (i % 3),
                "lot_decimals": 8,
                "lot_multiplier": 1,
                "ordermin": "0.001",
                "costmin": "0.5",
                "tick_size": "0.01",
                "status": "online",
            }

        kraken_response = {"error": [], "result": result}

        response = GetAssetPairsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.pairs) == 50

        # Verify a few samples
        assert response.success.pairs["PAIR0"].altname == "P0"
        assert response.success.pairs["PAIR25"].altname == "P25"
        assert response.success.pairs["PAIR49"].altname == "P49"


class TestGetTickerInformationRequest:
    """Tests for GetTickerInformationRequest schema"""

    def test_minimal_valid_request_no_params(self):
        """Test creating a minimal valid request with no parameters"""
        ticker_request = GetTickerInformationRequest()

        assert ticker_request.pair is None
        assert ticker_request.asset_class is None

    def test_request_with_single_pair_string(self):
        """Test request with single pair as string"""
        ticker_request = GetTickerInformationRequest(pair="XBTUSD")

        assert ticker_request.pair == "XBTUSD"
        assert ticker_request.asset_class is None

    def test_request_with_multiple_pairs_string(self):
        """Test request with multiple pairs as comma-delimited string"""
        ticker_request = GetTickerInformationRequest(pair="XBTUSD,ETHUSD,ADAUSD")

        assert ticker_request.pair == "XBTUSD,ETHUSD,ADAUSD"

    def test_request_with_single_pair_list(self):
        """Test request with single pair as list"""
        ticker_request = GetTickerInformationRequest(pair=["XBTUSD"])

        assert ticker_request.pair == "XBTUSD"

    def test_request_with_multiple_pairs_list(self):
        """Test request with multiple pairs as list"""
        ticker_request = GetTickerInformationRequest(pair=["XBTUSD", "ETHUSD", "ADAUSD"])

        assert ticker_request.pair == "XBTUSD,ETHUSD,ADAUSD"

    def test_pair_normalization_whitespace(self):
        """Test that pair list with whitespace is normalized"""
        ticker_request = GetTickerInformationRequest(pair=[" XBTUSD ", "  ETHUSD", "ADAUSD  "])

        assert ticker_request.pair == "XBTUSD,ETHUSD,ADAUSD"

    def test_pair_normalization_duplicates(self):
        """Test that duplicate pairs are removed while preserving order"""
        ticker_request = GetTickerInformationRequest(
            pair=["XBTUSD", "ETHUSD", "XBTUSD", "ADAUSD", "ETHUSD"]
        )

        # Should keep first occurrence only
        assert ticker_request.pair == "XBTUSD,ETHUSD,ADAUSD"

    def test_request_with_asset_class(self):
        """Test request with asset_class parameter"""
        ticker_request = GetTickerInformationRequest(asset_class="tokenized_asset")

        assert ticker_request.asset_class == "tokenized_asset"
        assert ticker_request.pair is None

    def test_request_with_both_pair_and_asset_class(self):
        """Test request with both pair and asset_class"""
        ticker_request = GetTickerInformationRequest(
            pair="TSLA/USD", asset_class="tokenized_asset"
        )

        assert ticker_request.pair == "TSLA/USD"
        assert ticker_request.asset_class == "tokenized_asset"

    def test_empty_list_validation(self):
        """Test that empty list is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetTickerInformationRequest(pair=[])

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_empty_string_validation(self):
        """Test that empty string is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            GetTickerInformationRequest(pair="")

        assert (
            "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()
        )

    def test_to_api_dict_no_params(self):
        """Test to_api_dict() serialization with no parameters"""
        ticker_request = GetTickerInformationRequest()

        data = ticker_request.to_api_dict()

        # Should return empty dict with no parameters
        assert data == {}

    def test_to_api_dict_with_params(self):
        """Test to_api_dict() serialization excludes None by default"""
        ticker_request = GetTickerInformationRequest(pair="XBTUSD,ETHUSD")

        data = ticker_request.to_api_dict()

        # Should include pair but not asset_class (None)
        assert "pair" in data
        assert data["pair"] == "XBTUSD,ETHUSD"
        assert "asset_class" not in data

    def test_to_api_dict_exclude_none_false(self):
        """Test to_api_dict() with exclude_none=False includes None values"""
        ticker_request = GetTickerInformationRequest(pair="XBTUSD")

        data = ticker_request.to_api_dict(exclude_none=False)

        # Should include both pair and asset_class (None)
        assert "pair" in data
        assert "asset_class" in data
        assert data["pair"] == "XBTUSD"
        assert data["asset_class"] is None

    def test_list_to_string_conversion(self):
        """Test that list is properly converted to comma-delimited string"""
        ticker_request = GetTickerInformationRequest(pair=["XBTUSD", "ETHUSD"])

        data = ticker_request.to_api_dict()

        # Should be converted to string
        assert isinstance(data["pair"], str)
        assert data["pair"] == "XBTUSD,ETHUSD"

    def test_string_vs_list_equivalence(self):
        """Test that string and list inputs produce equivalent results"""
        request_string = GetTickerInformationRequest(pair="XBTUSD,ETHUSD,ADAUSD")
        request_list = GetTickerInformationRequest(pair=["XBTUSD", "ETHUSD", "ADAUSD"])

        assert request_string.pair == request_list.pair
        assert request_string.to_api_dict() == request_list.to_api_dict()

    def test_multiple_instances(self):
        """Test creating multiple GetTickerInformationRequest instances"""
        requests = [
            GetTickerInformationRequest(),
            GetTickerInformationRequest(pair="XBTUSD"),
            GetTickerInformationRequest(asset_class="forex"),
            GetTickerInformationRequest(pair="ETHUSD", asset_class="forex"),
        ]

        assert len(requests) == 4
        for req in requests:
            assert req is not None


class TestGetTickerInformationResponse:
    """Tests for GetTickerInformation response schemas"""

    def test_ticker_info_direct_instantiation(self):
        """Test creating TickerInfo directly"""
        ticker = TickerInfo(
            a=["50000.00000", "1", "1.000"],
            b=["49999.90000", "2", "2.000"],
            c=["50000.00000", "0.00100000"],
            v=["1234.56789012", "2345.67890123"],
            p=["49500.12345", "49600.23456"],
            t=[1000, 2000],
            l=["49000.00000", "48900.00000"],
            h=["50500.00000", "50600.00000"],
            o="49800.00000",
        )

        assert ticker.a == ["50000.00000", "1", "1.000"]
        assert ticker.b == ["49999.90000", "2", "2.000"]
        assert ticker.c == ["50000.00000", "0.00100000"]
        assert ticker.v == ["1234.56789012", "2345.67890123"]
        assert ticker.p == ["49500.12345", "49600.23456"]
        assert ticker.t == [1000, 2000]
        assert ticker.l == ["49000.00000", "48900.00000"]
        assert ticker.h == ["50500.00000", "50600.00000"]
        assert ticker.o == "49800.00000"

    def test_success_response_single_pair(self):
        """Test parsing a successful response with single pair"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "a": ["50000.00000", "1", "1.000"],
                    "b": ["49999.90000", "2", "2.000"],
                    "c": ["50000.00000", "0.00100000"],
                    "v": ["1234.56789012", "2345.67890123"],
                    "p": ["49500.12345", "49600.23456"],
                    "t": [1000, 2000],
                    "l": ["49000.00000", "48900.00000"],
                    "h": ["50500.00000", "50600.00000"],
                    "o": "49800.00000",
                }
            },
        }

        response = GetTickerInformationResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert len(response.success.tickers) == 1
        assert "XXBTZUSD" in response.success.tickers

        ticker = response.success.tickers["XXBTZUSD"]
        assert ticker.a == ["50000.00000", "1", "1.000"]
        assert ticker.o == "49800.00000"

    def test_success_response_multiple_pairs(self):
        """Test parsing a successful response with multiple pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "a": ["50000.00000", "1", "1.000"],
                    "b": ["49999.90000", "2", "2.000"],
                    "c": ["50000.00000", "0.00100000"],
                    "v": ["1234.56789012", "2345.67890123"],
                    "p": ["49500.12345", "49600.23456"],
                    "t": [1000, 2000],
                    "l": ["49000.00000", "48900.00000"],
                    "h": ["50500.00000", "50600.00000"],
                    "o": "49800.00000",
                },
                "XETHZUSD": {
                    "a": ["3000.00000", "10", "10.000"],
                    "b": ["2999.90000", "20", "20.000"],
                    "c": ["3000.00000", "1.50000000"],
                    "v": ["5000.12345678", "6000.23456789"],
                    "p": ["2950.12345", "2960.23456"],
                    "t": [500, 1000],
                    "l": ["2900.00000", "2890.00000"],
                    "h": ["3050.00000", "3060.00000"],
                    "o": "2980.00000",
                },
                "XADAZUSD": {
                    "a": ["0.50000", "1000", "1000.000"],
                    "b": ["0.49900", "2000", "2000.000"],
                    "c": ["0.50000", "500.00000000"],
                    "v": ["100000.12345678", "200000.23456789"],
                    "p": ["0.49500", "0.49600"],
                    "t": [2000, 4000],
                    "l": ["0.48000", "0.47000"],
                    "h": ["0.51000", "0.52000"],
                    "o": "0.49000",
                },
            },
        }

        response = GetTickerInformationResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.tickers) == 3
        assert "XXBTZUSD" in response.success.tickers
        assert "XETHZUSD" in response.success.tickers
        assert "XADAZUSD" in response.success.tickers

        # Verify ticker instances
        for ticker_info in response.success.tickers.values():
            assert isinstance(ticker_info, TickerInfo)

    def test_success_response_many_pairs(self):
        """Test response with many pairs (simulating full ticker list)"""
        # Create a response with 50 different pairs
        result = {}
        for i in range(50):
            result[f"PAIR{i}USD"] = {
                "a": [f"{1000 + i}.00000", "1", "1.000"],
                "b": [f"{999 + i}.90000", "2", "2.000"],
                "c": [f"{1000 + i}.00000", "0.00100000"],
                "v": [f"{1234 + i}.56789012", f"{2345 + i}.67890123"],
                "p": [f"{995 + i}.12345", f"{996 + i}.23456"],
                "t": [1000 + i, 2000 + i],
                "l": [f"{990 + i}.00000", f"{989 + i}.00000"],
                "h": [f"{1005 + i}.00000", f"{1006 + i}.00000"],
                "o": f"{998 + i}.00000",
            }

        kraken_response = {"error": [], "result": result}

        response = GetTickerInformationResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.tickers) == 50

        # Verify a few samples
        assert response.success.tickers["PAIR0USD"].o == "998.00000"
        assert response.success.tickers["PAIR25USD"].o == "1023.00000"
        assert response.success.tickers["PAIR49USD"].o == "1047.00000"

    def test_parse_from_dict(self):
        """Test parsing from dict"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "a": ["50000.00000", "1", "1.000"],
                    "b": ["49999.90000", "2", "2.000"],
                    "c": ["50000.00000", "0.00100000"],
                    "v": ["1234.56789012", "2345.67890123"],
                    "p": ["49500.12345", "49600.23456"],
                    "t": [1000, 2000],
                    "l": ["49000.00000", "48900.00000"],
                    "h": ["50500.00000", "50600.00000"],
                    "o": "49800.00000",
                }
            },
        }

        response = GetTickerInformationResponse.from_response(kraken_response)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.tickers

    def test_parse_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBTZUSD": {
                        "a": ["50000.00000", "1", "1.000"],
                        "b": ["49999.90000", "2", "2.000"],
                        "c": ["50000.00000", "0.00100000"],
                        "v": ["1234.56789012", "2345.67890123"],
                        "p": ["49500.12345", "49600.23456"],
                        "t": [1000, 2000],
                        "l": ["49000.00000", "48900.00000"],
                        "h": ["50500.00000", "50600.00000"],
                        "o": "49800.00000",
                    }
                },
            }
        )

        response = GetTickerInformationResponse.from_response(json_response)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.tickers

    def test_error_response_single_error(self):
        """Test parsing an error response with single error"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = GetTickerInformationResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_error_response_multiple_errors(self):
        """Test parsing an error response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EQuery:Unknown asset pair",
            ],
        }

        response = GetTickerInformationResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EQuery:Unknown asset pair" in response.failure.error

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetTickerInformationResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetTickerInformationSuccess directly"""
        ticker = TickerInfo(
            a=["50000.00000", "1", "1.000"],
            b=["49999.90000", "2", "2.000"],
            c=["50000.00000", "0.00100000"],
            v=["1234.56789012", "2345.67890123"],
            p=["49500.12345", "49600.23456"],
            t=[1000, 2000],
            l=["49000.00000", "48900.00000"],
            h=["50500.00000", "50600.00000"],
            o="49800.00000",
        )

        success = GetTickerInformationSuccess(tickers={"XXBTZUSD": ticker})

        assert len(success.tickers) == 1
        assert "XXBTZUSD" in success.tickers
        assert success.tickers["XXBTZUSD"].o == "49800.00000"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetTickerInformationResponse wrapper directly"""
        ticker = TickerInfo(
            a=["50000.00000", "1", "1.000"],
            b=["49999.90000", "2", "2.000"],
            c=["50000.00000", "0.00100000"],
            v=["1234.56789012", "2345.67890123"],
            p=["49500.12345", "49600.23456"],
            t=[1000, 2000],
            l=["49000.00000", "48900.00000"],
            h=["50500.00000", "50600.00000"],
            o="49800.00000",
        )
        success = GetTickerInformationSuccess(tickers={"XXBTZUSD": ticker})
        response = GetTickerInformationResponse(success=success)

        assert response.is_success is True
        assert response.success.tickers["XXBTZUSD"].o == "49800.00000"

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetTickerInformationResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_is_success_property(self):
        """Test is_success property verification"""
        # Success case
        ticker = TickerInfo(
            a=["50000.00000", "1", "1.000"],
            b=["49999.90000", "2", "2.000"],
            c=["50000.00000", "0.00100000"],
            v=["1234.56789012", "2345.67890123"],
            p=["49500.12345", "49600.23456"],
            t=[1000, 2000],
            l=["49000.00000", "48900.00000"],
            h=["50500.00000", "50600.00000"],
            o="49800.00000",
        )
        success = GetTickerInformationSuccess(tickers={"XXBTZUSD": ticker})
        response_success = GetTickerInformationResponse(success=success)

        assert response_success.is_success is True

        # Failure case
        error = ResponseErrorSchema(error=["Test error"])
        response_failure = GetTickerInformationResponse(failure=error)

        assert response_failure.is_success is False


class TestGetOHLCDataRequest:
    """Tests for GetOHLCDataRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid OHLC request with required pair"""
        request = GetOHLCDataRequest(pair="XBTUSD")

        assert request.pair == "XBTUSD"
        assert request.interval is None
        assert request.since is None
        assert request.asset_class is None

    def test_request_with_all_parameters(self):
        """Test creating request with all parameters"""
        request = GetOHLCDataRequest(
            pair="XBTUSD",
            interval=60,
            since=1688671200,
            asset_class="tokenized_asset",
        )

        assert request.pair == "XBTUSD"
        assert request.interval == 60
        assert request.since == 1688671200
        assert request.asset_class == "tokenized_asset"

    def test_pair_list_normalization(self):
        """Test that pair list is normalized to comma-separated string"""
        # List input
        request1 = GetOHLCDataRequest(pair=["XBTUSD", "ETHUSD"])
        assert request1.pair == "XBTUSD,ETHUSD"

        # String input (unchanged)
        request2 = GetOHLCDataRequest(pair="XBTUSD,ETHUSD")
        assert request2.pair == "XBTUSD,ETHUSD"

        # Single item list
        request3 = GetOHLCDataRequest(pair=["XBTUSD"])
        assert request3.pair == "XBTUSD"

    def test_pair_list_deduplication(self):
        """Test that duplicate pairs are removed"""
        request = GetOHLCDataRequest(pair=["XBTUSD", "ETHUSD", "XBTUSD"])
        assert request.pair == "XBTUSD,ETHUSD"

    def test_interval_validation_valid_values(self):
        """Test that valid interval values are accepted"""
        valid_intervals = [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]

        for interval in valid_intervals:
            request = GetOHLCDataRequest(pair="XBTUSD", interval=interval)
            assert request.interval == interval

    def test_interval_validation_invalid_value(self):
        """Test that invalid interval values are rejected"""
        with pytest.raises(ValidationError, match="Interval must be one of"):
            GetOHLCDataRequest(pair="XBTUSD", interval=10)

        with pytest.raises(ValidationError, match="Interval must be one of"):
            GetOHLCDataRequest(pair="XBTUSD", interval=999)

        with pytest.raises(ValidationError, match="Interval must be one of"):
            GetOHLCDataRequest(pair="XBTUSD", interval=0)

    def test_interval_none_is_valid(self):
        """Test that None interval is valid (uses API default)"""
        request = GetOHLCDataRequest(pair="XBTUSD", interval=None)
        assert request.interval is None

    def test_since_parameter(self):
        """Test since parameter for incremental updates"""
        request = GetOHLCDataRequest(pair="XBTUSD", since=1688671200)
        assert request.since == 1688671200

    def test_asset_class_tokenized(self):
        """Test asset_class parameter for tokenized assets"""
        request = GetOHLCDataRequest(
            pair="TSLA/USD",
            asset_class="tokenized_asset",
        )
        assert request.asset_class == "tokenized_asset"

    def test_to_api_dict_minimal(self):
        """Test to_api_dict() with minimal parameters"""
        request = GetOHLCDataRequest(pair="XBTUSD")
        data = request.to_api_dict()

        assert "pair" in data
        assert data["pair"] == "XBTUSD"
        # None values should be excluded
        assert "interval" not in data
        assert "since" not in data
        assert "asset_class" not in data

    def test_to_api_dict_all_parameters(self):
        """Test to_api_dict() with all parameters"""
        request = GetOHLCDataRequest(
            pair="XBTUSD",
            interval=60,
            since=1688671200,
            asset_class="tokenized_asset",
        )
        data = request.to_api_dict()

        assert data["pair"] == "XBTUSD"
        assert data["interval"] == 60
        assert data["since"] == 1688671200
        assert data["asset_class"] == "tokenized_asset"

    def test_to_api_dict_exclude_none_false(self):
        """Test to_api_dict() with exclude_none=False"""
        request = GetOHLCDataRequest(pair="XBTUSD")
        data = request.to_api_dict(exclude_none=False)

        assert "pair" in data
        assert "interval" in data
        assert data["interval"] is None


class TestGetOHLCDataResponse:
    """Tests for GetOHLCData response schemas"""

    def test_ohlc_data_from_array(self):
        """Test creating OHLCData from array format"""
        candle_array = [
            1688671200,
            "50000.0",
            "50500.0",
            "49500.0",
            "50200.0",
            "50100.0",
            "123.456",
            100,
        ]

        ohlc = OHLCData.from_array(candle_array)

        assert ohlc.time == 1688671200
        assert ohlc.open == "50000.0"
        assert ohlc.high == "50500.0"
        assert ohlc.low == "49500.0"
        assert ohlc.close == "50200.0"
        assert ohlc.vwap == "50100.0"
        assert ohlc.volume == "123.456"
        assert ohlc.count == 100

    def test_ohlc_data_from_array_invalid_length(self):
        """Test that invalid array length raises error"""
        # Too few elements
        with pytest.raises(ValueError, match="must have exactly 8 elements"):
            OHLCData.from_array([1688671200, "50000.0", "50500.0"])

        # Too many elements
        with pytest.raises(ValueError, match="must have exactly 8 elements"):
            OHLCData.from_array(
                [
                    1688671200,
                    "50000.0",
                    "50500.0",
                    "49500.0",
                    "50200.0",
                    "50100.0",
                    "123.456",
                    100,
                    "extra",
                ]
            )

    def test_ohlc_data_direct_instantiation(self):
        """Test creating OHLCData directly"""
        ohlc = OHLCData(
            time=1688671200,
            open="50000.0",
            high="50500.0",
            low="49500.0",
            close="50200.0",
            vwap="50100.0",
            volume="123.456",
            count=100,
        )

        assert ohlc.time == 1688671200
        assert ohlc.open == "50000.0"
        assert ohlc.high == "50500.0"
        assert ohlc.low == "49500.0"
        assert ohlc.close == "50200.0"
        assert ohlc.vwap == "50100.0"
        assert ohlc.volume == "123.456"
        assert ohlc.count == 100

    def test_success_response_single_pair(self):
        """Test parsing a successful response with single pair"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [
                        1688671200,
                        "50000.0",
                        "50500.0",
                        "49500.0",
                        "50200.0",
                        "50100.0",
                        "123.456",
                        100,
                    ],
                    [
                        1688671260,
                        "50200.0",
                        "50600.0",
                        "50000.0",
                        "50400.0",
                        "50300.0",
                        "150.789",
                        120,
                    ],
                ],
                "last": 1688671260,
            },
        }

        response = GetOHLCDataResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.last == 1688671260
        assert len(response.success.ohlc_data) == 1
        assert "XXBTZUSD" in response.success.ohlc_data

        ohlc_array = response.success.ohlc_data["XXBTZUSD"]
        assert len(ohlc_array) == 2
        assert ohlc_array[0].time == 1688671200
        assert ohlc_array[0].open == "50000.0"
        assert ohlc_array[1].time == 1688671260
        assert ohlc_array[1].close == "50400.0"

    def test_success_response_multiple_pairs(self):
        """Test parsing a successful response with multiple pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [
                        1688671200,
                        "50000.0",
                        "50500.0",
                        "49500.0",
                        "50200.0",
                        "50100.0",
                        "123.456",
                        100,
                    ],
                ],
                "XETHZUSD": [
                    [1688671200, "3000.0", "3050.0", "2950.0", "3020.0", "3010.0", "500.123", 200],
                    [1688671260, "3020.0", "3060.0", "3000.0", "3040.0", "3030.0", "550.456", 210],
                ],
                "last": 1688671260,
            },
        }

        response = GetOHLCDataResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.last == 1688671260
        assert len(response.success.ohlc_data) == 2
        assert "XXBTZUSD" in response.success.ohlc_data
        assert "XETHZUSD" in response.success.ohlc_data

        # Verify XXBTZUSD has 1 candle
        assert len(response.success.ohlc_data["XXBTZUSD"]) == 1

        # Verify XETHZUSD has 2 candles
        assert len(response.success.ohlc_data["XETHZUSD"]) == 2
        assert response.success.ohlc_data["XETHZUSD"][1].close == "3040.0"

    def test_success_response_many_candles(self):
        """Test response with many OHLC candles"""
        # Create a response with 100 candles
        candles = []
        for i in range(100):
            candles.append(
                [
                    1688671200 + i * 60,
                    f"{50000 + i}.0",
                    f"{50100 + i}.0",
                    f"{49900 + i}.0",
                    f"{50050 + i}.0",
                    f"{50025 + i}.0",
                    f"{100 + i}.456",
                    100 + i,
                ]
            )

        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": candles,
                "last": 1688677140,
            },
        }

        response = GetOHLCDataResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.ohlc_data["XXBTZUSD"]) == 100
        assert response.success.ohlc_data["XXBTZUSD"][0].time == 1688671200
        assert response.success.ohlc_data["XXBTZUSD"][99].time == 1688677140
        assert response.success.ohlc_data["XXBTZUSD"][99].count == 199

    def test_parse_from_dict(self):
        """Test parsing from dict"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [
                        1688671200,
                        "50000.0",
                        "50500.0",
                        "49500.0",
                        "50200.0",
                        "50100.0",
                        "123.456",
                        100,
                    ],
                ],
                "last": 1688671200,
            },
        }

        response = GetOHLCDataResponse.from_response(kraken_response)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.ohlc_data

    def test_parse_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBTZUSD": [
                        [
                            1688671200,
                            "50000.0",
                            "50500.0",
                            "49500.0",
                            "50200.0",
                            "50100.0",
                            "123.456",
                            100,
                        ],
                    ],
                    "last": 1688671200,
                },
            }
        )

        response = GetOHLCDataResponse.from_response(json_response)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.ohlc_data

    def test_error_response_single_error(self):
        """Test parsing an error response with single error"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = GetOHLCDataResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_error_response_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EQuery:Unknown asset pair",
            ],
        }

        response = GetOHLCDataResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EQuery:Unknown asset pair" in response.failure.error

    def test_invalid_response_format_missing_result(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetOHLCDataResponse.from_response(invalid_response)

    def test_invalid_response_format_missing_last(self):
        """Test that response missing 'last' field raises error"""
        invalid_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [
                        1688671200,
                        "50000.0",
                        "50500.0",
                        "49500.0",
                        "50200.0",
                        "50100.0",
                        "123.456",
                        100,
                    ],
                ],
                # Missing 'last' field
            },
        }

        with pytest.raises(ValueError, match="missing 'last'"):
            GetOHLCDataResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetOHLCDataSuccess directly"""
        ohlc = OHLCData(
            time=1688671200,
            open="50000.0",
            high="50500.0",
            low="49500.0",
            close="50200.0",
            vwap="50100.0",
            volume="123.456",
            count=100,
        )

        success = GetOHLCDataSuccess(
            ohlc_data={"XXBTZUSD": [ohlc]},
            last=1688671200,
        )

        assert len(success.ohlc_data) == 1
        assert "XXBTZUSD" in success.ohlc_data
        assert success.ohlc_data["XXBTZUSD"][0].time == 1688671200
        assert success.last == 1688671200

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetOHLCDataResponse wrapper directly"""
        ohlc = OHLCData(
            time=1688671200,
            open="50000.0",
            high="50500.0",
            low="49500.0",
            close="50200.0",
            vwap="50100.0",
            volume="123.456",
            count=100,
        )
        success = GetOHLCDataSuccess(
            ohlc_data={"XXBTZUSD": [ohlc]},
            last=1688671200,
        )
        response = GetOHLCDataResponse(success=success)

        assert response.is_success is True
        assert response.success.ohlc_data["XXBTZUSD"][0].time == 1688671200

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetOHLCDataResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_is_success_property(self):
        """Test is_success property verification"""
        # Success case
        ohlc = OHLCData(
            time=1688671200,
            open="50000.0",
            high="50500.0",
            low="49500.0",
            close="50200.0",
            vwap="50100.0",
            volume="123.456",
            count=100,
        )
        success = GetOHLCDataSuccess(
            ohlc_data={"XXBTZUSD": [ohlc]},
            last=1688671200,
        )
        response_success = GetOHLCDataResponse(success=success)

        assert response_success.is_success is True

        # Failure case
        error = ResponseErrorSchema(error=["Test error"])
        response_failure = GetOHLCDataResponse(failure=error)

        assert response_failure.is_success is False


class TestOrderBookEntry:
    """Tests for OrderBookEntry schema"""

    def test_valid_order_book_entry(self):
        """Test creating a valid order book entry"""
        entry = OrderBookEntry(
            price="50000.00",
            volume="1.5",
            timestamp=1688671200,
        )

        assert entry.price == "50000.00"
        assert entry.volume == "1.5"
        assert entry.timestamp == 1688671200

    def test_from_array_valid(self):
        """Test parsing order book entry from array"""
        data = ["50000.00", "1.5", 1688671200]
        entry = OrderBookEntry.from_array(data)

        assert entry.price == "50000.00"
        assert entry.volume == "1.5"
        assert entry.timestamp == 1688671200

    def test_from_array_invalid_length(self):
        """Test that invalid array length raises error"""
        # Too few elements
        with pytest.raises(ValueError, match="exactly 3 elements"):
            OrderBookEntry.from_array(["50000.00", "1.5"])

        # Too many elements
        with pytest.raises(ValueError, match="exactly 3 elements"):
            OrderBookEntry.from_array(["50000.00", "1.5", 1688671200, "extra"])

    def test_price_volume_as_strings(self):
        """Test that prices and volumes are stored as strings for precision"""
        entry = OrderBookEntry(
            price="50000.123456789",
            volume="1.123456789012345",
            timestamp=1688671200,
        )

        assert isinstance(entry.price, str)
        assert isinstance(entry.volume, str)
        assert entry.price == "50000.123456789"
        assert entry.volume == "1.123456789012345"


class TestOrderBook:
    """Tests for OrderBook schema"""

    def test_empty_order_book(self):
        """Test creating an empty order book"""
        book = OrderBook()

        assert book.asks == []
        assert book.bids == []

    def test_order_book_with_entries(self):
        """Test creating an order book with asks and bids"""
        asks = [
            OrderBookEntry(price="50100.00", volume="1.0", timestamp=1688671200),
            OrderBookEntry(price="50200.00", volume="2.0", timestamp=1688671201),
        ]
        bids = [
            OrderBookEntry(price="50000.00", volume="1.5", timestamp=1688671200),
            OrderBookEntry(price="49900.00", volume="2.5", timestamp=1688671201),
        ]

        book = OrderBook(asks=asks, bids=bids)

        assert len(book.asks) == 2
        assert len(book.bids) == 2
        assert book.asks[0].price == "50100.00"
        assert book.bids[0].price == "50000.00"

    def test_order_book_only_asks(self):
        """Test order book with only asks"""
        asks = [
            OrderBookEntry(price="50100.00", volume="1.0", timestamp=1688671200),
        ]

        book = OrderBook(asks=asks)

        assert len(book.asks) == 1
        assert book.bids == []

    def test_order_book_only_bids(self):
        """Test order book with only bids"""
        bids = [
            OrderBookEntry(price="50000.00", volume="1.5", timestamp=1688671200),
        ]

        book = OrderBook(bids=bids)

        assert book.asks == []
        assert len(book.bids) == 1


class TestGetOrderBookRequest:
    """Tests for GetOrderBookRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid order book request"""
        request = GetOrderBookRequest(pair="XBTUSD")

        assert request.pair == "XBTUSD"
        assert request.count is None
        assert request.asset_class is None

    def test_request_with_count(self):
        """Test creating request with specific count"""
        request = GetOrderBookRequest(pair="XBTUSD", count=10)

        assert request.pair == "XBTUSD"
        assert request.count == 10

    def test_request_with_max_count(self):
        """Test creating request with maximum count"""
        request = GetOrderBookRequest(pair="XBTUSD", count=500)

        assert request.count == 500

    def test_request_with_min_count(self):
        """Test creating request with minimum count"""
        request = GetOrderBookRequest(pair="XBTUSD", count=1)

        assert request.count == 1

    def test_count_validation_too_small(self):
        """Test that count below minimum raises error"""
        with pytest.raises(ValidationError, match="between 1 and 500"):
            GetOrderBookRequest(pair="XBTUSD", count=0)

        with pytest.raises(ValidationError, match="between 1 and 500"):
            GetOrderBookRequest(pair="XBTUSD", count=-1)

    def test_count_validation_too_large(self):
        """Test that count above maximum raises error"""
        with pytest.raises(ValidationError, match="between 1 and 500"):
            GetOrderBookRequest(pair="XBTUSD", count=501)

        with pytest.raises(ValidationError, match="between 1 and 500"):
            GetOrderBookRequest(pair="XBTUSD", count=1000)

    def test_request_with_tokenized_asset(self):
        """Test creating request for tokenized asset"""
        request = GetOrderBookRequest(
            pair="TSLA/USD",
            asset_class="tokenized_asset",
            count=50,
        )

        assert request.pair == "TSLA/USD"
        assert request.asset_class == "tokenized_asset"
        assert request.count == 50

    def test_to_api_dict_minimal(self):
        """Test to_api_dict() with minimal request"""
        request = GetOrderBookRequest(pair="XBTUSD")
        data = request.to_api_dict()

        assert data["pair"] == "XBTUSD"
        assert "count" not in data
        assert "asset_class" not in data

    def test_to_api_dict_with_count(self):
        """Test to_api_dict() with count"""
        request = GetOrderBookRequest(pair="XBTUSD", count=25)
        data = request.to_api_dict()

        assert data["pair"] == "XBTUSD"
        assert data["count"] == 25

    def test_to_api_dict_with_all_fields(self):
        """Test to_api_dict() with all fields"""
        request = GetOrderBookRequest(
            pair="TSLA/USD",
            count=100,
            asset_class="tokenized_asset",
        )
        data = request.to_api_dict()

        assert data["pair"] == "TSLA/USD"
        assert data["count"] == 100
        assert data["asset_class"] == "tokenized_asset"

    def test_various_pair_formats(self):
        """Test various pair format strings"""
        # Standard crypto pair
        request1 = GetOrderBookRequest(pair="XBTUSD")
        assert request1.pair == "XBTUSD"

        # Pair with slash
        request2 = GetOrderBookRequest(pair="BTC/USD")
        assert request2.pair == "BTC/USD"

        # Tokenized asset
        request3 = GetOrderBookRequest(pair="TSLA/USD")
        assert request3.pair == "TSLA/USD"

        # Alternate format
        request4 = GetOrderBookRequest(pair="XXBTZUSD")
        assert request4.pair == "XXBTZUSD"


class TestGetOrderBookResponse:
    """Tests for GetOrderBook response schemas"""

    def test_success_response_parsing(self):
        """Test parsing a successful order book response"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": [
                        ["50100.00000", "1.000", 1688671200],
                        ["50200.00000", "2.000", 1688671201],
                        ["50300.00000", "1.500", 1688671202],
                    ],
                    "bids": [
                        ["50000.00000", "1.500", 1688671200],
                        ["49900.00000", "2.500", 1688671201],
                        ["49800.00000", "3.000", 1688671202],
                    ],
                }
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert "XXBTZUSD" in response.success.order_books

        book = response.success.order_books["XXBTZUSD"]
        assert len(book.asks) == 3
        assert len(book.bids) == 3
        assert book.asks[0].price == "50100.00000"
        assert book.asks[0].volume == "1.000"
        assert book.asks[0].timestamp == 1688671200
        assert book.bids[0].price == "50000.00000"
        assert book.bids[0].volume == "1.500"
        assert book.bids[0].timestamp == 1688671200

    def test_success_response_multiple_pairs(self):
        """Test parsing response with multiple trading pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": [["50100.00", "1.0", 1688671200]],
                    "bids": [["50000.00", "1.5", 1688671200]],
                },
                "XETHZUSD": {
                    "asks": [["2100.00", "10.0", 1688671200]],
                    "bids": [["2090.00", "15.0", 1688671200]],
                },
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.order_books) == 2
        assert "XXBTZUSD" in response.success.order_books
        assert "XETHZUSD" in response.success.order_books

        btc_book = response.success.order_books["XXBTZUSD"]
        assert len(btc_book.asks) == 1
        assert len(btc_book.bids) == 1

        eth_book = response.success.order_books["XETHZUSD"]
        assert len(eth_book.asks) == 1
        assert len(eth_book.bids) == 1

    def test_success_response_empty_order_book(self):
        """Test parsing response with empty order book"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": [],
                    "bids": [],
                }
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is True
        book = response.success.order_books["XXBTZUSD"]
        assert book.asks == []
        assert book.bids == []

    def test_success_response_only_asks(self):
        """Test parsing response with only asks"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": [["50100.00", "1.0", 1688671200]],
                    "bids": [],
                }
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is True
        book = response.success.order_books["XXBTZUSD"]
        assert len(book.asks) == 1
        assert book.bids == []

    def test_success_response_only_bids(self):
        """Test parsing response with only bids"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": [],
                    "bids": [["50000.00", "1.5", 1688671200]],
                }
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is True
        book = response.success.order_books["XXBTZUSD"]
        assert book.asks == []
        assert len(book.bids) == 1

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EQuery:Unknown asset pair"],
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EQuery:Unknown asset pair" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EQuery:Unknown asset pair",
            ],
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EQuery:Unknown asset pair" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBTZUSD": {
                        "asks": [["50100.00", "1.0", 1688671200]],
                        "bids": [["50000.00", "1.5", 1688671200]],
                    }
                },
            }
        )

        response = GetOrderBookResponse.from_response(json_response)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.order_books

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetOrderBookResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetOrderBookSuccess directly"""
        asks = [OrderBookEntry(price="50100.00", volume="1.0", timestamp=1688671200)]
        bids = [OrderBookEntry(price="50000.00", volume="1.5", timestamp=1688671200)]
        book = OrderBook(asks=asks, bids=bids)

        success = GetOrderBookSuccess(order_books={"XXBTZUSD": book})

        assert "XXBTZUSD" in success.order_books
        assert len(success.order_books["XXBTZUSD"].asks) == 1
        assert len(success.order_books["XXBTZUSD"].bids) == 1

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        error = ResponseErrorSchema(error=["EQuery:Unknown asset pair"])

        assert len(error.error) == 1
        assert error.error[0] == "EQuery:Unknown asset pair"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetOrderBookResponse wrapper directly"""
        asks = [OrderBookEntry(price="50100.00", volume="1.0", timestamp=1688671200)]
        bids = [OrderBookEntry(price="50000.00", volume="1.5", timestamp=1688671200)]
        book = OrderBook(asks=asks, bids=bids)
        success = GetOrderBookSuccess(order_books={"XXBTZUSD": book})
        response = GetOrderBookResponse(success=success)

        assert response.is_success is True
        assert "XXBTZUSD" in response.success.order_books

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetOrderBookResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_large_order_book(self):
        """Test parsing response with maximum order book depth"""
        # Create 500 asks and 500 bids (maximum allowed)
        asks = [[f"{50000 + i}.00", "1.0", 1688671200 + i] for i in range(500)]
        bids = [[f"{50000 - i}.00", "1.0", 1688671200 + i] for i in range(500)]

        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": asks,
                    "bids": bids,
                }
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        assert response.is_success is True
        book = response.success.order_books["XXBTZUSD"]
        assert len(book.asks) == 500
        assert len(book.bids) == 500
        assert book.asks[0].price == "50000.00"
        assert book.bids[0].price == "50000.00"

    def test_precision_preservation(self):
        """Test that price/volume precision is preserved"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": {
                    "asks": [["50123.456789012345", "1.123456789012345", 1688671200]],
                    "bids": [["50000.987654321098", "2.987654321098765", 1688671200]],
                }
            },
        }

        response = GetOrderBookResponse.from_response(kraken_response)

        book = response.success.order_books["XXBTZUSD"]
        assert book.asks[0].price == "50123.456789012345"
        assert book.asks[0].volume == "1.123456789012345"
        assert book.bids[0].price == "50000.987654321098"
        assert book.bids[0].volume == "2.987654321098765"


class TestRecentTradeEntry:
    """Tests for RecentTradeEntry schema"""

    def test_from_array_valid(self):
        """Test parsing valid trade entry from array"""
        trade_array = ["50000.50", "1.5", 1616663618.1234, "b", "m", "", 123456]

        entry = RecentTradeEntry.from_array(trade_array)

        assert entry.price == "50000.50"
        assert entry.volume == "1.5"
        assert entry.time == 1616663618.1234
        assert entry.buy_sell == "b"
        assert entry.market_limit == "m"
        assert entry.miscellaneous == ""
        assert entry.trade_id == 123456

    def test_from_array_with_none_trade_id(self):
        """Test parsing trade entry with null trade_id"""
        trade_array = ["49500.00", "0.25", 1616663618.5678, "s", "l", "misc", None]

        entry = RecentTradeEntry.from_array(trade_array)

        assert entry.price == "49500.00"
        assert entry.volume == "0.25"
        assert entry.time == 1616663618.5678
        assert entry.buy_sell == "s"
        assert entry.market_limit == "l"
        assert entry.miscellaneous == "misc"
        assert entry.trade_id is None

    def test_from_array_with_empty_trade_id(self):
        """Test parsing trade entry with empty string trade_id (treated as None)"""
        trade_array = ["50100.00", "2.0", 1616663619.0, "b", "l", "", ""]

        entry = RecentTradeEntry.from_array(trade_array)

        assert entry.trade_id is None

    def test_from_array_invalid_length_too_short(self):
        """Test that array with too few elements raises error"""
        trade_array = ["50000.50", "1.5", 1616663618.0, "b", "m", ""]

        with pytest.raises(ValueError, match="exactly 7 elements"):
            RecentTradeEntry.from_array(trade_array)

    def test_from_array_invalid_length_too_long(self):
        """Test that array with too many elements raises error"""
        trade_array = ["50000.50", "1.5", 1616663618.0, "b", "m", "", 123, "extra"]

        with pytest.raises(ValueError, match="exactly 7 elements"):
            RecentTradeEntry.from_array(trade_array)

    def test_direct_instantiation(self):
        """Test creating RecentTradeEntry directly"""
        entry = RecentTradeEntry(
            price="51000.25",
            volume="3.5",
            time=1616663620.9876,
            buy_sell="s",
            market_limit="m",
            miscellaneous="test",
            trade_id=789012,
        )

        assert entry.price == "51000.25"
        assert entry.volume == "3.5"
        assert entry.time == 1616663620.9876
        assert entry.buy_sell == "s"
        assert entry.market_limit == "m"
        assert entry.miscellaneous == "test"
        assert entry.trade_id == 789012

    def test_precision_preservation(self):
        """Test that price/volume precision is preserved as strings"""
        trade_array = ["50123.123456789012345", "1.987654321098765", 1616663618.0, "b", "l", "", 1]

        entry = RecentTradeEntry.from_array(trade_array)

        assert entry.price == "50123.123456789012345"
        assert entry.volume == "1.987654321098765"


class TestGetRecentTradesRequest:
    """Tests for GetRecentTradesRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request with pair only"""
        request = GetRecentTradesRequest(pair="XBTUSD")

        assert request.pair == "XBTUSD"
        assert request.since is None
        assert request.count is None
        assert request.asset_class is None

    def test_request_with_all_parameters(self):
        """Test creating request with all optional parameters"""
        request = GetRecentTradesRequest(
            pair="ETHUSD",
            since="1616663618",
            count=500,
            asset_class="tokenized_asset",
        )

        assert request.pair == "ETHUSD"
        assert request.since == "1616663618"
        assert request.count == 500
        assert request.asset_class == "tokenized_asset"

    def test_count_validation_min(self):
        """Test count minimum validation (must be >= 1)"""
        request = GetRecentTradesRequest(pair="XBTUSD", count=1)
        assert request.count == 1

    def test_count_validation_max(self):
        """Test count maximum validation (must be <= 1000)"""
        request = GetRecentTradesRequest(pair="XBTUSD", count=1000)
        assert request.count == 1000

    def test_count_validation_too_small(self):
        """Test that count less than 1 raises error"""
        with pytest.raises(ValidationError, match="between 1 and 1000"):
            GetRecentTradesRequest(pair="XBTUSD", count=0)

    def test_count_validation_negative(self):
        """Test that negative count raises error"""
        with pytest.raises(ValidationError, match="between 1 and 1000"):
            GetRecentTradesRequest(pair="XBTUSD", count=-1)

    def test_count_validation_too_large(self):
        """Test that count greater than 1000 raises error"""
        with pytest.raises(ValidationError, match="between 1 and 1000"):
            GetRecentTradesRequest(pair="XBTUSD", count=1001)

    def test_count_validation_way_too_large(self):
        """Test that extremely large count raises error"""
        with pytest.raises(ValidationError, match="between 1 and 1000"):
            GetRecentTradesRequest(pair="XBTUSD", count=10000)

    def test_to_api_dict_minimal(self):
        """Test to_api_dict() with minimal parameters"""
        request = GetRecentTradesRequest(pair="XBTUSD")
        data = request.to_api_dict()

        assert "pair" in data
        assert data["pair"] == "XBTUSD"
        # None values should be excluded
        assert "since" not in data
        assert "count" not in data
        assert "asset_class" not in data

    def test_to_api_dict_with_all_params(self):
        """Test to_api_dict() with all parameters"""
        request = GetRecentTradesRequest(
            pair="ETHUSD",
            since="1616663618",
            count=250,
            asset_class="tokenized_asset",
        )
        data = request.to_api_dict()

        assert data["pair"] == "ETHUSD"
        assert data["since"] == "1616663618"
        assert data["count"] == 250
        assert data["asset_class"] == "tokenized_asset"

    def test_to_api_dict_exclude_none_false(self):
        """Test to_api_dict() with exclude_none=False"""
        request = GetRecentTradesRequest(pair="XBTUSD")
        data = request.to_api_dict(exclude_none=False)

        assert "since" in data
        assert data["since"] is None
        assert "count" in data
        assert data["count"] is None

    def test_tokenized_asset_request(self):
        """Test request for tokenized asset"""
        request = GetRecentTradesRequest(
            pair="TSLA/USD",
            asset_class="tokenized_asset",
            count=100,
        )

        assert request.pair == "TSLA/USD"
        assert request.asset_class == "tokenized_asset"
        assert request.count == 100


class TestGetRecentTradesResponse:
    """Tests for GetRecentTrades response schemas"""

    def test_success_response_single_pair(self):
        """Test parsing successful response for single pair"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    ["50000.00", "1.5", 1616663618.1234, "b", "m", "", 123456],
                    ["50001.00", "0.5", 1616663619.5678, "s", "l", "", 123457],
                ],
                "last": "1616663619567800000",
            },
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.last == "1616663619567800000"
        assert "XXBTZUSD" in response.success.trades

        trades = response.success.trades["XXBTZUSD"]
        assert len(trades) == 2
        assert trades[0].price == "50000.00"
        assert trades[0].volume == "1.5"
        assert trades[0].buy_sell == "b"
        assert trades[1].price == "50001.00"
        assert trades[1].volume == "0.5"
        assert trades[1].buy_sell == "s"

    def test_success_response_multiple_pairs(self):
        """Test parsing successful response with multiple pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    ["50000.00", "1.0", 1616663618.0, "b", "m", "", 123456],
                ],
                "XETHZUSD": [
                    ["2000.00", "5.0", 1616663620.0, "s", "l", "", 123458],
                ],
                "last": "1616663620000000000",
            },
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.trades) == 2
        assert "XXBTZUSD" in response.success.trades
        assert "XETHZUSD" in response.success.trades
        assert response.success.last == "1616663620000000000"

    def test_success_response_many_trades(self):
        """Test parsing response with many trades"""
        # Create 100 trade entries
        trades_array = []
        for i in range(100):
            trades_array.append([f"{50000 + i}.00", "1.0", 1616663618.0 + i, "b", "m", "", i])

        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": trades_array,
                "last": "1616663718000000000",
            },
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.trades["XXBTZUSD"]) == 100
        assert response.success.trades["XXBTZUSD"][0].price == "50000.00"
        assert response.success.trades["XXBTZUSD"][99].price == "50099.00"

    def test_success_response_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBTZUSD": [
                        ["50000.00", "1.0", 1616663618.0, "b", "m", "", 123456],
                    ],
                    "last": "1616663618000000000",
                },
            }
        )

        response = GetRecentTradesResponse.from_response(json_response)

        assert response.is_success is True
        assert len(response.success.trades["XXBTZUSD"]) == 1

    def test_success_response_with_none_trade_ids(self):
        """Test parsing response with null trade IDs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    ["50000.00", "1.0", 1616663618.0, "b", "m", "", None],
                    ["50001.00", "0.5", 1616663619.0, "s", "l", "misc", None],
                ],
                "last": "1616663619000000000",
            },
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is True
        trades = response.success.trades["XXBTZUSD"]
        assert trades[0].trade_id is None
        assert trades[1].trade_id is None

    def test_error_response_single_error(self):
        """Test parsing error response with single error"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_error_response_multiple_errors(self):
        """Test parsing error response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EQuery:Unknown asset pair",
            ],
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EQuery:Unknown asset pair" in response.failure.error

    def test_invalid_response_missing_result(self):
        """Test that response missing 'result' raises error"""
        invalid_response = {"error": []}

        with pytest.raises(ValueError, match="missing 'result'"):
            GetRecentTradesResponse.from_response(invalid_response)

    def test_invalid_response_missing_last(self):
        """Test that response missing 'last' field raises error"""
        invalid_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    ["50000.00", "1.0", 1616663618.0, "b", "m", "", 123456],
                ],
            },
        }

        with pytest.raises(ValueError, match="missing 'last'"):
            GetRecentTradesResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetRecentTradesSuccess directly"""
        trade = RecentTradeEntry(
            price="50000.00",
            volume="1.0",
            time=1616663618.0,
            buy_sell="b",
            market_limit="m",
            miscellaneous="",
            trade_id=123456,
        )

        success = GetRecentTradesSuccess(
            trades={"XXBTZUSD": [trade]},
            last="1616663618000000000",
        )

        assert len(success.trades["XXBTZUSD"]) == 1
        assert success.last == "1616663618000000000"
        assert success.trades["XXBTZUSD"][0].price == "50000.00"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetRecentTradesResponse wrapper directly"""
        from kraken.rest.schema.trading import ResponseErrorSchema

        success = GetRecentTradesSuccess(
            trades={},
            last="1616663618000000000",
        )
        response = GetRecentTradesResponse(success=success)

        assert response.is_success is True
        assert response.success.last == "1616663618000000000"

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetRecentTradesResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_precision_preservation(self):
        """Test that price/volume precision is preserved"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [
                        "50123.123456789012345",
                        "1.987654321098765",
                        1616663618.123456,
                        "b",
                        "l",
                        "",
                        1,
                    ],
                ],
                "last": "1616663618123456000",
            },
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        trade = response.success.trades["XXBTZUSD"][0]
        assert trade.price == "50123.123456789012345"
        assert trade.volume == "1.987654321098765"
        assert trade.time == 1616663618.123456

    def test_empty_trades_array(self):
        """Test parsing response with empty trades array"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [],
                "last": "1616663618000000000",
            },
        }

        response = GetRecentTradesResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.trades["XXBTZUSD"]) == 0
        assert response.success.last == "1616663618000000000"


class TestSpreadEntry:
    """Tests for SpreadEntry schema"""

    def test_from_array_valid(self):
        """Test parsing valid spread entry from array"""
        spread_array = [1616663618, "50000.00", "50001.00"]

        entry = SpreadEntry.from_array(spread_array)

        assert entry.time == 1616663618
        assert entry.bid == "50000.00"
        assert entry.ask == "50001.00"

    def test_from_array_with_high_precision(self):
        """Test parsing spread entry with high precision prices"""
        spread_array = [1616663618, "50123.123456789", "50124.987654321"]

        entry = SpreadEntry.from_array(spread_array)

        assert entry.time == 1616663618
        assert entry.bid == "50123.123456789"
        assert entry.ask == "50124.987654321"

    def test_from_array_invalid_length_too_short(self):
        """Test that array with too few elements raises error"""
        spread_array = [1616663618, "50000.00"]

        with pytest.raises(ValueError, match="exactly 3 elements"):
            SpreadEntry.from_array(spread_array)

    def test_from_array_invalid_length_too_long(self):
        """Test that array with too many elements raises error"""
        spread_array = [1616663618, "50000.00", "50001.00", "extra"]

        with pytest.raises(ValueError, match="exactly 3 elements"):
            SpreadEntry.from_array(spread_array)

    def test_direct_instantiation(self):
        """Test creating SpreadEntry directly"""
        entry = SpreadEntry(
            time=1616663618,
            bid="49999.50",
            ask="50000.50",
        )

        assert entry.time == 1616663618
        assert entry.bid == "49999.50"
        assert entry.ask == "50000.50"

    def test_precision_preservation(self):
        """Test that price precision is preserved as strings"""
        spread_array = [1616663618, "50123.123456789012345", "50124.987654321098765"]

        entry = SpreadEntry.from_array(spread_array)

        assert entry.bid == "50123.123456789012345"
        assert entry.ask == "50124.987654321098765"


class TestGetRecentSpreadsRequest:
    """Tests for GetRecentSpreadsRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request with pair only"""
        request = GetRecentSpreadsRequest(pair="XBTUSD")

        assert request.pair == "XBTUSD"
        assert request.since is None
        assert request.asset_class is None

    def test_request_with_all_parameters(self):
        """Test creating request with all optional parameters"""
        request = GetRecentSpreadsRequest(
            pair="ETHUSD",
            since=1678219570,
            asset_class="tokenized_asset",
        )

        assert request.pair == "ETHUSD"
        assert request.since == 1678219570
        assert request.asset_class == "tokenized_asset"

    def test_to_api_dict_minimal(self):
        """Test to_api_dict() with minimal parameters"""
        request = GetRecentSpreadsRequest(pair="XBTUSD")
        data = request.to_api_dict()

        assert "pair" in data
        assert data["pair"] == "XBTUSD"
        # None values should be excluded
        assert "since" not in data
        assert "asset_class" not in data

    def test_to_api_dict_with_all_params(self):
        """Test to_api_dict() with all parameters"""
        request = GetRecentSpreadsRequest(
            pair="ETHUSD",
            since=1678219570,
            asset_class="tokenized_asset",
        )
        data = request.to_api_dict()

        assert data["pair"] == "ETHUSD"
        assert data["since"] == 1678219570
        assert data["asset_class"] == "tokenized_asset"

    def test_to_api_dict_exclude_none_false(self):
        """Test to_api_dict() with exclude_none=False"""
        request = GetRecentSpreadsRequest(pair="XBTUSD")
        data = request.to_api_dict(exclude_none=False)

        assert "since" in data
        assert data["since"] is None
        assert "asset_class" in data
        assert data["asset_class"] is None

    def test_tokenized_asset_request(self):
        """Test request for tokenized asset"""
        request = GetRecentSpreadsRequest(
            pair="TSLA/USD",
            asset_class="tokenized_asset",
        )

        assert request.pair == "TSLA/USD"
        assert request.asset_class == "tokenized_asset"

    def test_incremental_update_request(self):
        """Test request for incremental updates with since parameter"""
        request = GetRecentSpreadsRequest(
            pair="XBTUSD",
            since=1678219570,
        )

        assert request.pair == "XBTUSD"
        assert request.since == 1678219570


class TestGetRecentSpreadsResponse:
    """Tests for GetRecentSpreads response schemas"""

    def test_success_response_single_pair(self):
        """Test parsing successful response for single pair"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [1616663618, "50000.00", "50001.00"],
                    [1616663619, "50002.00", "50003.00"],
                ],
                "last": 1616663619,
            },
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.last == 1616663619
        assert "XXBTZUSD" in response.success.spreads

        spreads = response.success.spreads["XXBTZUSD"]
        assert len(spreads) == 2
        assert spreads[0].time == 1616663618
        assert spreads[0].bid == "50000.00"
        assert spreads[0].ask == "50001.00"
        assert spreads[1].time == 1616663619
        assert spreads[1].bid == "50002.00"
        assert spreads[1].ask == "50003.00"

    def test_success_response_multiple_pairs(self):
        """Test parsing successful response with multiple pairs"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [1616663618, "50000.00", "50001.00"],
                ],
                "XETHZUSD": [
                    [1616663620, "2000.00", "2001.00"],
                ],
                "last": 1616663620,
            },
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.spreads) == 2
        assert "XXBTZUSD" in response.success.spreads
        assert "XETHZUSD" in response.success.spreads
        assert response.success.last == 1616663620

    def test_success_response_many_spreads(self):
        """Test parsing response with many spread entries"""
        # Create 100 spread entries
        spreads_array = []
        for i in range(100):
            spreads_array.append([1616663618 + i, f"{50000 + i}.00", f"{50001 + i}.00"])

        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": spreads_array,
                "last": 1616663718,
            },
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.spreads["XXBTZUSD"]) == 100
        assert response.success.spreads["XXBTZUSD"][0].bid == "50000.00"
        assert response.success.spreads["XXBTZUSD"][99].bid == "50099.00"

    def test_success_response_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "XXBTZUSD": [
                        [1616663618, "50000.00", "50001.00"],
                    ],
                    "last": 1616663618,
                },
            }
        )

        response = GetRecentSpreadsResponse.from_response(json_response)

        assert response.is_success is True
        assert len(response.success.spreads["XXBTZUSD"]) == 1

    def test_error_response_single_error(self):
        """Test parsing error response with single error"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_error_response_multiple_errors(self):
        """Test parsing error response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EQuery:Unknown asset pair",
            ],
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EQuery:Unknown asset pair" in response.failure.error

    def test_invalid_response_missing_result(self):
        """Test that response missing 'result' raises error"""
        invalid_response = {"error": []}

        with pytest.raises(ValueError, match="missing 'result'"):
            GetRecentSpreadsResponse.from_response(invalid_response)

    def test_invalid_response_missing_last(self):
        """Test that response missing 'last' field raises error"""
        invalid_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [1616663618, "50000.00", "50001.00"],
                ],
            },
        }

        with pytest.raises(ValueError, match="missing 'last'"):
            GetRecentSpreadsResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetRecentSpreadsSuccess directly"""
        spread = SpreadEntry(
            time=1616663618,
            bid="50000.00",
            ask="50001.00",
        )

        success = GetRecentSpreadsSuccess(
            spreads={"XXBTZUSD": [spread]},
            last=1616663618,
        )

        assert len(success.spreads["XXBTZUSD"]) == 1
        assert success.last == 1616663618
        assert success.spreads["XXBTZUSD"][0].bid == "50000.00"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetRecentSpreadsResponse wrapper directly"""
        from kraken.rest.schema.trading import ResponseErrorSchema

        success = GetRecentSpreadsSuccess(
            spreads={},
            last=1616663618,
        )
        response = GetRecentSpreadsResponse(success=success)

        assert response.is_success is True
        assert response.success.last == 1616663618

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetRecentSpreadsResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_precision_preservation(self):
        """Test that price precision is preserved"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [
                    [
                        1616663618,
                        "50123.123456789012345",
                        "50124.987654321098765",
                    ],
                ],
                "last": 1616663618,
            },
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        spread = response.success.spreads["XXBTZUSD"][0]
        assert spread.bid == "50123.123456789012345"
        assert spread.ask == "50124.987654321098765"
        assert spread.time == 1616663618

    def test_empty_spreads_array(self):
        """Test parsing response with empty spreads array"""
        kraken_response = {
            "error": [],
            "result": {
                "XXBTZUSD": [],
                "last": 1616663618,
            },
        }

        response = GetRecentSpreadsResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.spreads["XXBTZUSD"]) == 0
        assert response.success.last == 1616663618
