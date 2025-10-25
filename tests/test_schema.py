"""Unit tests for Kraken REST API schemas"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from kraken.rest.schema.trading import (
    AddOrderRequest,
    AddOrderResponse,
    AddOrderSuccess,
    ResponseErrorSchema,
)


class TestAddOrderRequest:
    """Tests for AddOrderRequest schema"""

    def test_minimal_valid_order(self):
        """Test creating a minimal valid market order"""
        order = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1.5,
            pair="XBTUSD",
        )

        assert order.ordertype == "market"
        assert order.type == "buy"
        assert order.volume == "1.5"
        assert order.pair == "XBTUSD"
        assert order.only_validate is False  # Default

    def test_limit_order_with_price(self):
        """Test creating a limit order with price"""
        order = AddOrderRequest(
            ordertype="limit",
            type="sell",
            volume=0.5,
            pair="ETHUSD",
            price="2000.50",
        )

        assert order.ordertype == "limit"
        assert order.price == "2000.50"

    def test_ordertype_normalization(self):
        """Test that order type is normalized to lowercase"""
        order = AddOrderRequest(
            ordertype="MARKET",
            type="buy",
            volume=1,
            pair="XBTUSD",
        )

        assert order.ordertype == "market"

        order2 = AddOrderRequest(
            ordertype="  Stop-Loss  ",
            type="sell",
            volume=1,
            pair="XBTUSD",
            price="48000",  # stop-loss orders require price
        )

        assert order2.ordertype == "stop-loss"

    def test_volume_conversion_to_string(self):
        """Test that volume is converted to string"""
        # Integer volume
        order1 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=2,
            pair="XBTUSD",
        )
        assert order1.volume == "2"

        # Float volume
        order2 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1.25,
            pair="XBTUSD",
        )
        assert order2.volume == "1.25"

        # String volume (unchanged)
        order3 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume="0.001",
            pair="XBTUSD",
        )
        assert order3.volume == "0.001"

    def test_displayvol_floor_enforcement(self):
        """Test that displayvol is floored to 1/15 of volume for iceberg orders"""
        # Display volume too small - should be floored to volume/15
        order1 = AddOrderRequest(
            ordertype="iceberg",
            type="buy",
            volume=15,
            displayvol=0.5,  # Less than 15/15 = 1
            pair="XBTUSD",
            price="50000",
        )
        assert float(order1.displayvol) == 1.0

        # Display volume too large - should be capped at volume
        order2 = AddOrderRequest(
            ordertype="iceberg",
            type="buy",
            volume=10,
            displayvol=20,  # More than volume
            pair="XBTUSD",
            price="50000",
        )
        assert float(order2.displayvol) == 10.0

        # Valid display volume - should be unchanged
        order3 = AddOrderRequest(
            ordertype="iceberg",
            type="buy",
            volume=15,
            displayvol=5,  # Between 1 and 15
            pair="XBTUSD",
            price="50000",
        )
        assert float(order3.displayvol) == 5.0

        # None display volume - should remain None
        order4 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=10,
            pair="XBTUSD",
        )
        assert order4.displayvol is None

    def test_leverage_conversion(self):
        """Test that leverage is converted to string"""
        order1 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            leverage=5,
        )
        assert order1.leverage == "5"

        order2 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            leverage="2",
        )
        assert order2.leverage == "2"

        order3 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
        )
        assert order3.leverage is None

    def test_oflags_normalization(self):
        """Test order flags normalization and validation"""
        # String with single flag
        order1 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            oflags="post",
        )
        assert order1.oflags == "post"

        # String with multiple flags
        order2 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            oflags="post,fcib",
        )
        assert set(order2.oflags.split(",")) == {"post", "fcib"}

        # List of flags
        order3 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            oflags=["fciq", "viqc"],
        )
        assert set(order3.oflags.split(",")) == {"fciq", "viqc"}

        # Set of flags
        order4 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            oflags={"post", "fcib"},
        )
        assert set(order4.oflags.split(",")) == {"post", "fcib"}

        # Invalid flags filtered out
        order5 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            oflags="post,invalid,fcib",
        )
        assert "invalid" not in order5.oflags
        assert set(order5.oflags.split(",")) == {"post", "fcib"}

    def test_timeinforce_normalization(self):
        """Test that time-in-force is normalized to uppercase"""
        order1 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            timeinforce="ioc",
        )
        assert order1.timeinforce == "IOC"

        order2 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            timeinforce="  gtd  ",
            expiretm="60",  # GTD orders require expiretm
        )
        assert order2.timeinforce == "GTD"

        # Test new PO (post-only) option
        order3 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            timeinforce="po",
        )
        assert order3.timeinforce == "PO"

    def test_deadline_optional_when_not_provided(self):
        """Test that deadline is optional and remains None until REST client adds it"""
        order = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
        )

        # Deadline is NOT auto-generated to prevent race conditions
        # The REST client will generate it at request signing time
        assert order.deadline is None

    def test_deadline_bounding(self):
        """Test that deadline is bounded between 2-60 seconds"""
        # Deadline too soon (< 2 seconds) - should be adjusted to 2 seconds
        now = datetime.now(timezone.utc)
        too_soon = (now + timedelta(seconds=1)).isoformat()
        order1 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            deadline=too_soon,
        )
        deadline1 = datetime.fromisoformat(order1.deadline)
        min_deadline = now + timedelta(seconds=2)
        # Allow small timing differences
        assert deadline1 >= min_deadline - timedelta(milliseconds=100)

        # Deadline too far (> 60 seconds) - should be adjusted to 60 seconds
        now2 = datetime.now(timezone.utc)
        too_far = (now2 + timedelta(seconds=120)).isoformat()
        order2 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            deadline=too_far,
        )
        deadline2 = datetime.fromisoformat(order2.deadline)
        max_deadline = now2 + timedelta(seconds=60)
        # Allow small timing differences
        assert deadline2 <= max_deadline + timedelta(milliseconds=100)

    def test_deadline_requires_timezone(self):
        """Test that deadline must include timezone information"""
        # Valid deadline with timezone
        valid_deadline = datetime.now(timezone.utc).isoformat()
        order1 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            deadline=valid_deadline,
        )
        assert order1.deadline is not None

        # Invalid deadline without timezone - should raise error
        invalid_deadline = "2025-01-15T12:00:00"  # No timezone
        with pytest.raises(ValidationError, match="timezone information"):
            AddOrderRequest(
                ordertype="market",
                type="buy",
                volume=1,
                pair="XBTUSD",
                deadline=invalid_deadline,
            )

    def test_validate_defaults_to_false(self):
        """Test that validate defaults to False for real order execution"""
        order = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
        )
        assert order.only_validate is False

    def test_stptype_defaults_to_none(self):
        """Test that STP type defaults to None (uses Kraken's default)"""
        order = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
        )
        assert order.stptype is None

    def test_conditional_close_order_parameters(self):
        """Test conditional close order (OCO) parameters"""
        order = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            close_ordertype="stop-loss",
            close_price="48000",
        )

        assert order.close_ordertype == "stop-loss"
        assert order.close_price == "48000"
        assert order.close_price2 is None

        # With secondary price for stop-loss-limit
        order2 = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            close_ordertype="stop-loss-limit",
            close_price="48000",
            close_price2="47500",
        )

        assert order2.close_ordertype == "stop-loss-limit"
        assert order2.close_price == "48000"
        assert order2.close_price2 == "47500"

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        order = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
        )

        # Should not have a nonce attribute
        assert not hasattr(order, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        order = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1.5,
            pair="XBTUSD",
            price="50000",
            only_validate=True,
        )

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = order.to_api_dict()

        # Field aliasing: only_validate -> validate
        assert "validate" in data
        assert "only_validate" not in data
        assert data["validate"] is True

        # None values should be excluded by default
        assert "deadline" not in data
        assert "leverage" not in data

        # Test exclude_none=False
        data_with_none = order.to_api_dict(exclude_none=False)
        assert "deadline" in data_with_none
        assert data_with_none["deadline"] is None

    def test_compute_deadline_static_method(self):
        """Test the static compute_deadline() method"""
        deadline_str = AddOrderRequest.compute_deadline()

        # Should be a valid ISO format timestamp
        deadline = datetime.fromisoformat(deadline_str)
        assert deadline.tzinfo is not None

        # Should be between 2-60 seconds from now
        now = datetime.now(timezone.utc)
        time_diff = (deadline - now).total_seconds()
        assert 2 <= time_diff <= 60

    def test_field_dependency_validation_limit_order(self):
        """Test that limit orders require price field"""
        # Valid limit order with price
        order = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
        )
        assert order.price == "50000"

        # Invalid limit order without price
        with pytest.raises(ValidationError, match="Limit orders require 'price'"):
            AddOrderRequest(
                ordertype="limit",
                type="buy",
                volume=1,
                pair="XBTUSD",
            )

    def test_field_dependency_validation_iceberg_order(self):
        """Test that iceberg orders require price field"""
        with pytest.raises(ValidationError, match="Iceberg orders require 'price'"):
            AddOrderRequest(
                ordertype="iceberg",
                type="buy",
                volume=10,
                pair="XBTUSD",
            )

    def test_field_dependency_validation_stop_loss_limit(self):
        """Test that stop-loss-limit orders require both price and price2"""
        # Missing both
        with pytest.raises(
            ValidationError, match="stop-loss-limit orders require both 'price' and 'price2'"
        ):
            AddOrderRequest(
                ordertype="stop-loss-limit",
                type="sell",
                volume=1,
                pair="XBTUSD",
            )

        # Missing price2
        with pytest.raises(
            ValidationError, match="stop-loss-limit orders require both 'price' and 'price2'"
        ):
            AddOrderRequest(
                ordertype="stop-loss-limit",
                type="sell",
                volume=1,
                pair="XBTUSD",
                price="48000",
            )

        # Valid with both
        order = AddOrderRequest(
            ordertype="stop-loss-limit",
            type="sell",
            volume=1,
            pair="XBTUSD",
            price="48000",
            price2="47500",
        )
        assert order.price == "48000"
        assert order.price2 == "47500"

    def test_field_dependency_validation_gtd_order(self):
        """Test that GTD orders require expiretm field"""
        with pytest.raises(ValidationError, match="GTD .* orders require 'expiretm'"):
            AddOrderRequest(
                ordertype="limit",
                type="buy",
                volume=1,
                pair="XBTUSD",
                price="50000",
                timeinforce="GTD",
            )

        # Valid GTD with expiretm
        order = AddOrderRequest(
            ordertype="limit",
            type="buy",
            volume=1,
            pair="XBTUSD",
            price="50000",
            timeinforce="GTD",
            expiretm="60",
        )
        assert order.expiretm == "60"

    def test_field_dependency_validation_mutually_exclusive(self):
        """Test that userref and cl_ord_id are mutually exclusive"""
        # Both set - should fail
        with pytest.raises(ValidationError, match="mutually exclusive"):
            AddOrderRequest(
                ordertype="market",
                type="buy",
                volume=1,
                pair="XBTUSD",
                userref=12345,
                cl_ord_id="my-order-id",
            )

        # Only userref - should succeed
        order1 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            userref=12345,
        )
        assert order1.userref == 12345

        # Only cl_ord_id - should succeed
        order2 = AddOrderRequest(
            ordertype="market",
            type="buy",
            volume=1,
            pair="XBTUSD",
            cl_ord_id="my-order-id",
        )
        assert order2.cl_ord_id == "my-order-id"


class TestAddOrderResponse:
    """Tests for AddOrder response schemas"""

    def test_success_response_parsing(self):
        """Test parsing a successful order response"""
        kraken_response = {
            "error": [],
            "result": {
                "txid": ["OUF4EM-FRGI2-MQMWZD"],
                "descr": {
                    "order": "buy 1.00000000 XBTUSD @ market",
                    "close": None,
                },
            },
        }

        response = AddOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.error is None
        assert response.success.txid == ["OUF4EM-FRGI2-MQMWZD"]
        assert "buy 1.00000000 XBTUSD" in response.success.order_description

    def test_success_response_with_conditional_close(self):
        """Test parsing a success response with conditional close order"""
        kraken_response = {
            "error": [],
            "result": {
                "txid": ["ABC123-DEF456-GHI789"],
                "descr": {
                    "order": "buy 0.50000000 ETHUSD @ limit 2000.00",
                    "close": "close position @ stop loss 1800.00",
                },
            },
        }

        response = AddOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.close_description == "close position @ stop loss 1800.00"

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = AddOrderResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.error is not None
        assert "EGeneral:Invalid arguments" in response.error.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EOrder:Insufficient funds",
            ],
        }

        response = AddOrderResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.error.error) == 2
        assert "EGeneral:Invalid arguments" in response.error.error
        assert "EOrder:Insufficient funds" in response.error.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "txid": ["TEST-TX-ID"],
                    "descr": {
                        "order": "sell 1.00000000 XBTUSD @ market",
                        "close": None,
                    },
                },
            }
        )

        response = AddOrderResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.txid == ["TEST-TX-ID"]

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            AddOrderResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating AddOrderSuccess directly"""
        success = AddOrderSuccess(
            txid=["TX-123"],
            descr={
                "order": "buy 1.0 XBTUSD @ limit 50000",
                "close": None,
            },
        )

        assert success.txid == ["TX-123"]
        assert success.order_description == "buy 1.0 XBTUSD @ limit 50000"
        assert success.close_description is None

    def test_error_model_direct_instantiation(self):
        """Test creating AddOrderError directly"""
        error = ResponseErrorSchema(error=["EGeneral:Invalid arguments"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Invalid arguments"


class TestConcurrentScenarios:
    """Tests for concurrent and async usage scenarios"""

    def test_multiple_orders_no_nonce_collision(self):
        """Test that creating multiple orders simultaneously doesn't cause nonce collisions"""
        # Create multiple orders in rapid succession
        orders = []
        for i in range(10):
            order = AddOrderRequest(
                ordertype="market",
                type="buy" if i % 2 == 0 else "sell",
                volume=1 + i * 0.1,
                pair="XBTUSD",
            )
            orders.append(order)

        # All orders should be valid
        assert len(orders) == 10

        # No nonce field should exist (nonce handled by REST client)
        for order in orders:
            assert not hasattr(order, "nonce")

    def test_deadline_validation_concurrent(self):
        """Test that deadline validation works in concurrent scenarios"""
        import concurrent.futures

        def create_order(i):
            now = datetime.now(timezone.utc)
            deadline = (now + timedelta(seconds=10 + i)).isoformat()
            return AddOrderRequest(
                ordertype="market",
                type="buy",
                volume=1,
                pair="XBTUSD",
                deadline=deadline,
            )

        # Create orders concurrently with deadlines
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            orders = list(executor.map(create_order, range(20)))

        # All orders should have valid deadlines
        assert len(orders) == 20
        for order in orders:
            assert order.deadline is not None
            deadline = datetime.fromisoformat(order.deadline)
            assert deadline.tzinfo is not None
