"""Unit tests for Kraken REST API trading schemas"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from kraken.rest.schema.trading import (
    AddOrderBatchRequest,
    AddOrderBatchResponse,
    AddOrderBatchSuccess,
    AddOrderRequest,
    AddOrderResponse,
    AddOrderSuccess,
    AmendOrderRequest,
    AmendOrderResponse,
    AmendOrderSuccess,
    BatchOrderItem,
    BatchOrderResult,
    CancelAllOrdersAfterRequest,
    CancelAllOrdersAfterResponse,
    CancelAllOrdersAfterSuccess,
    CancelAllRequest,
    CancelAllResponse,
    CancelAllSuccess,
    CancelOrderBatchItem,
    CancelOrderBatchRequest,
    CancelOrderBatchResponse,
    CancelOrderBatchSuccess,
    CancelOrderRequest,
    CancelOrderResponse,
    CancelOrderSuccess,
    GetWebSocketsTokenRequest,
    GetWebSocketsTokenResponse,
    GetWebSocketsTokenSuccess,
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
        """Test the static compute_deadline() method (now in validators module)"""
        from kraken.rest.schema import validators

        deadline_str = validators.compute_deadline()

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
        with pytest.raises(ValidationError, match="(?i)limit orders require 'price'"):
            AddOrderRequest(
                ordertype="limit",
                type="buy",
                volume=1,
                pair="XBTUSD",
            )

    def test_field_dependency_validation_iceberg_order(self):
        """Test that iceberg orders require price field"""
        with pytest.raises(ValidationError, match="(?i)iceberg orders require 'price'"):
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
        assert response.failure is None
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
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

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
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EOrder:Insufficient funds" in response.failure.error

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


class TestAmendOrderRequest:
    """Tests for AmendOrderRequest schema"""

    def test_minimal_valid_amend_with_txid(self):
        """Test creating a minimal valid amend request with txid"""
        amend = AmendOrderRequest(
            txid="OUF4EM-FRGI2-MQMWZD",
            order_qty=2.5,
        )

        assert amend.txid == "OUF4EM-FRGI2-MQMWZD"
        assert amend.order_qty == "2.5"
        assert amend.cl_ord_id is None

    def test_minimal_valid_amend_with_cl_ord_id(self):
        """Test creating a minimal valid amend request with client order ID"""
        amend = AmendOrderRequest(
            cl_ord_id="my-order-123",
            limit_price="51000.50",
        )

        assert amend.cl_ord_id == "my-order-123"
        assert amend.limit_price == "51000.50"
        assert amend.txid is None

    def test_txid_cl_ord_id_mutually_exclusive(self):
        """Test that txid and cl_ord_id are mutually exclusive"""
        with pytest.raises(ValidationError, match="mutually exclusive"):
            AmendOrderRequest(
                txid="OUF4EM-FRGI2-MQMWZD",
                cl_ord_id="my-order-123",
                order_qty=1.0,
            )

    def test_at_least_one_identifier_required(self):
        """Test that either txid or cl_ord_id must be provided"""
        with pytest.raises(ValidationError, match="Either 'txid' or 'cl_ord_id' must be provided"):
            AmendOrderRequest(
                order_qty=1.5,
                limit_price="50000",
            )

    def test_order_qty_conversion_to_string(self):
        """Test that order_qty is converted to string"""
        # Integer order_qty
        amend1 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=3,
        )
        assert amend1.order_qty == "3"

        # Float order_qty
        amend2 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=2.75,
        )
        assert amend2.order_qty == "2.75"

        # String order_qty (unchanged)
        amend3 = AmendOrderRequest(
            txid="ABC-123",
            order_qty="1.5",
        )
        assert amend3.order_qty == "1.5"

        # None order_qty
        amend4 = AmendOrderRequest(
            txid="ABC-123",
            limit_price="50000",
        )
        assert amend4.order_qty is None

    def test_display_qty_floor_enforcement(self):
        """Test that display_qty is floored to 1/15 of order_qty"""
        # Display quantity too small - should be floored to order_qty/15
        amend1 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=15,
            display_qty=0.5,  # Less than 15/15 = 1
        )
        assert float(amend1.display_qty) == 1.0

        # Display quantity too large - should be capped at order_qty
        amend2 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=10,
            display_qty=20,  # More than order_qty
        )
        assert float(amend2.display_qty) == 10.0

        # Valid display quantity - should be unchanged
        amend3 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=15,
            display_qty=5,  # Between 1 and 15
        )
        assert float(amend3.display_qty) == 5.0

        # None display quantity - should remain None
        amend4 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=10,
        )
        assert amend4.display_qty is None

    def test_deadline_optional_when_not_provided(self):
        """Test that deadline is optional and remains None until REST client adds it"""
        amend = AmendOrderRequest(
            txid="ABC-123",
            order_qty=1.5,
        )

        # Deadline is NOT auto-generated to prevent race conditions
        assert amend.deadline is None

    def test_deadline_bounding(self):
        """Test that deadline is bounded between 2-60 seconds"""
        # Deadline too soon (< 2 seconds) - should be adjusted to 2 seconds
        now = datetime.now(timezone.utc)
        too_soon = (now + timedelta(seconds=1)).isoformat()
        amend1 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=1.5,
            deadline=too_soon,
        )
        deadline1 = datetime.fromisoformat(amend1.deadline)
        min_deadline = now + timedelta(seconds=2)
        # Allow small timing differences
        assert deadline1 >= min_deadline - timedelta(milliseconds=100)

        # Deadline too far (> 60 seconds) - should be adjusted to 60 seconds
        now2 = datetime.now(timezone.utc)
        too_far = (now2 + timedelta(seconds=120)).isoformat()
        amend2 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=1.5,
            deadline=too_far,
        )
        deadline2 = datetime.fromisoformat(amend2.deadline)
        max_deadline = now2 + timedelta(seconds=60)
        # Allow small timing differences
        assert deadline2 <= max_deadline + timedelta(milliseconds=100)

    def test_deadline_requires_timezone(self):
        """Test that deadline must include timezone information"""
        # Valid deadline with timezone
        valid_deadline = datetime.now(timezone.utc).isoformat()
        amend1 = AmendOrderRequest(
            txid="ABC-123",
            order_qty=1.5,
            deadline=valid_deadline,
        )
        assert amend1.deadline is not None

        # Invalid deadline without timezone - should raise error
        invalid_deadline = "2025-01-15T12:00:00"  # No timezone
        with pytest.raises(ValidationError, match="timezone information"):
            AmendOrderRequest(
                txid="ABC-123",
                order_qty=1.5,
                deadline=invalid_deadline,
            )

    def test_post_only_defaults_to_false(self):
        """Test that post_only defaults to False"""
        amend = AmendOrderRequest(
            txid="ABC-123",
            limit_price="50000",
        )
        assert amend.post_only is False

    def test_post_only_can_be_set_true(self):
        """Test that post_only can be set to True"""
        amend = AmendOrderRequest(
            txid="ABC-123",
            limit_price="50000",
            post_only=True,
        )
        assert amend.post_only is True

    def test_relative_pricing_strings(self):
        """Test that relative pricing strings are accepted"""
        # Positive offset
        amend1 = AmendOrderRequest(
            txid="ABC-123",
            limit_price="+100",
        )
        assert amend1.limit_price == "+100"

        # Negative offset
        amend2 = AmendOrderRequest(
            txid="ABC-123",
            trigger_price="-50",
        )
        assert amend2.trigger_price == "-50"

        # Percentage offset
        amend3 = AmendOrderRequest(
            txid="ABC-123",
            limit_price="+5%",
        )
        assert amend3.limit_price == "+5%"

        # Combined trigger and limit
        amend4 = AmendOrderRequest(
            txid="ABC-123",
            limit_price="+100",
            trigger_price="-50%",
        )
        assert amend4.limit_price == "+100"
        assert amend4.trigger_price == "-50%"

    def test_pair_for_xstocks(self):
        """Test that pair can be provided for non-crypto pairs"""
        amend = AmendOrderRequest(
            txid="ABC-123",
            order_qty=10,
            pair="TSLA/USD",
        )
        assert amend.pair == "TSLA/USD"

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        amend = AmendOrderRequest(
            txid="ABC-123",
            order_qty=1.5,
        )

        # Should not have a nonce attribute
        assert not hasattr(amend, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        amend = AmendOrderRequest(
            txid="OUF4EM-FRGI2-MQMWZD",
            order_qty=2.5,
            limit_price="51000",
        )

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = amend.to_api_dict()

        # None values should be excluded by default
        assert "deadline" not in data
        assert "pair" not in data
        assert "display_qty" not in data

        # Non-None values should be present
        assert data["txid"] == "OUF4EM-FRGI2-MQMWZD"
        assert data["order_qty"] == "2.5"
        assert data["limit_price"] == "51000"

        # Test exclude_none=False
        data_with_none = amend.to_api_dict(exclude_none=False)
        assert "deadline" in data_with_none
        assert data_with_none["deadline"] is None

    def test_compute_deadline_static_method(self):
        """Test the static compute_deadline() method (now in validators module)"""
        from kraken.rest.schema import validators

        deadline_str = validators.compute_deadline()

        # Should be a valid ISO format timestamp
        deadline = datetime.fromisoformat(deadline_str)
        assert deadline.tzinfo is not None

        # Should be between 2-60 seconds from now
        now = datetime.now(timezone.utc)
        time_diff = (deadline - now).total_seconds()
        assert 2 <= time_diff <= 60

    def test_all_fields_optional_except_identifier(self):
        """Test that all fields are optional except txid or cl_ord_id"""
        # Only txid provided
        amend1 = AmendOrderRequest(txid="ABC-123")
        assert amend1.txid == "ABC-123"

        # Only cl_ord_id provided
        amend2 = AmendOrderRequest(cl_ord_id="my-order")
        assert amend2.cl_ord_id == "my-order"

    def test_multiple_amendment_fields(self):
        """Test amend request with multiple fields being amended"""
        amend = AmendOrderRequest(
            txid="OUF4EM-FRGI2-MQMWZD",
            order_qty=5.0,
            limit_price="52000",
            trigger_price="51000",
            display_qty=2.0,
            pair="XBTUSD",
            post_only=True,
        )

        assert amend.order_qty == "5.0"
        assert amend.limit_price == "52000"
        assert amend.trigger_price == "51000"
        assert amend.display_qty == "2.0"
        assert amend.pair == "XBTUSD"
        assert amend.post_only is True


class TestAmendOrderResponse:
    """Tests for AmendOrder response schemas"""

    def test_success_response_parsing(self):
        """Test parsing a successful amend response"""
        kraken_response = {
            "error": [],
            "result": {
                "amend_id": "AMEND-123-456-789",
            },
        }

        response = AmendOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.amend_id == "AMEND-123-456-789"

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = AmendOrderResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EOrder:Order not found",
            ],
        }

        response = AmendOrderResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EOrder:Order not found" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "amend_id": "TEST-AMEND-ID",
                },
            }
        )

        response = AmendOrderResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.amend_id == "TEST-AMEND-ID"

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            AmendOrderResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating AmendOrderSuccess directly"""
        success = AmendOrderSuccess(amend_id="DIRECT-AMEND-123")

        assert success.amend_id == "DIRECT-AMEND-123"

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        error = ResponseErrorSchema(error=["EGeneral:Invalid arguments"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Invalid arguments"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating AmendOrderResponse wrapper directly"""
        success = AmendOrderSuccess(amend_id="WRAPPER-TEST")
        response = AmendOrderResponse(success=success)

        assert response.is_success is True
        assert response.success.amend_id == "WRAPPER-TEST"

        error = ResponseErrorSchema(error=["Test error"])
        response2 = AmendOrderResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"


class TestConcurrentAmendScenarios:
    """Tests for concurrent and async amend usage scenarios"""

    def test_multiple_amends_no_collision(self):
        """Test that creating multiple amend requests simultaneously doesn't cause issues"""
        # Create multiple amend requests in rapid succession
        amends = []
        for i in range(10):
            amend = AmendOrderRequest(
                txid=f"ORDER-{i}",
                order_qty=1 + i * 0.1,
            )
            amends.append(amend)

        # All amends should be valid
        assert len(amends) == 10

        # No nonce field should exist (nonce handled by REST client)
        for amend in amends:
            assert not hasattr(amend, "nonce")

        # Each should have unique txid
        txids = [a.txid for a in amends]
        assert len(set(txids)) == 10

    def test_deadline_validation_concurrent(self):
        """Test that deadline validation works in concurrent scenarios"""
        import concurrent.futures

        def create_amend(i):
            now = datetime.now(timezone.utc)
            deadline = (now + timedelta(seconds=10 + i)).isoformat()
            return AmendOrderRequest(
                txid=f"ORDER-{i}",
                order_qty=1,
                deadline=deadline,
            )

        # Create amend requests concurrently with deadlines
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            amends = list(executor.map(create_amend, range(20)))

        # All amends should have valid deadlines
        assert len(amends) == 20
        for amend in amends:
            assert amend.deadline is not None
            deadline = datetime.fromisoformat(amend.deadline)
            assert deadline.tzinfo is not None

    def test_mixed_identifier_types_concurrent(self):
        """Test concurrent creation with mixed identifier types"""
        import concurrent.futures

        def create_amend(i):
            if i % 2 == 0:
                return AmendOrderRequest(
                    txid=f"TXID-{i}",
                    order_qty=1.0 + i,
                )
            else:
                return AmendOrderRequest(
                    cl_ord_id=f"CLIENT-ORDER-{i}",
                    limit_price=f"{50000 + i * 100}",
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            amends = list(executor.map(create_amend, range(20)))

        assert len(amends) == 20

        # Check that txid and cl_ord_id are properly distributed
        txid_amends = [a for a in amends if a.txid is not None]
        cl_ord_id_amends = [a for a in amends if a.cl_ord_id is not None]

        assert len(txid_amends) == 10
        assert len(cl_ord_id_amends) == 10


class TestCancelOrderRequest:
    """Tests for CancelOrderRequest schema"""

    def test_minimal_valid_cancel_with_string_txid(self):
        """Test creating a minimal valid cancel request with string txid"""
        cancel = CancelOrderRequest(txid="OUF4EM-FRGI2-MQMWZD")

        assert cancel.txid == "OUF4EM-FRGI2-MQMWZD"
        assert cancel.cl_ord_id is None

    def test_minimal_valid_cancel_with_integer_txid(self):
        """Test creating a minimal valid cancel request with integer txid (userref)"""
        cancel = CancelOrderRequest(txid=12345)

        assert cancel.txid == 12345
        assert isinstance(cancel.txid, int)
        assert cancel.cl_ord_id is None

    def test_minimal_valid_cancel_with_cl_ord_id(self):
        """Test creating a minimal valid cancel request with client order ID"""
        cancel = CancelOrderRequest(cl_ord_id="my-order-123")

        assert cancel.cl_ord_id == "my-order-123"
        assert cancel.txid is None

    def test_txid_string_integer_conversion(self):
        """Test that numeric string txids are converted to integers"""
        # Numeric string should be converted to int (userref)
        cancel1 = CancelOrderRequest(txid="12345")
        assert cancel1.txid == 12345
        assert isinstance(cancel1.txid, int)

        # Alphanumeric string stays as string (txid)
        cancel2 = CancelOrderRequest(txid="OUF4EM-FRGI2-MQMWZD")
        assert cancel2.txid == "OUF4EM-FRGI2-MQMWZD"
        assert isinstance(cancel2.txid, str)

        # String with spaces should be stripped
        cancel3 = CancelOrderRequest(txid="  ABC-123-DEF  ")
        assert cancel3.txid == "ABC-123-DEF"

    def test_txid_cl_ord_id_mutually_exclusive(self):
        """Test that txid and cl_ord_id are mutually exclusive"""
        with pytest.raises(ValidationError, match="mutually exclusive"):
            CancelOrderRequest(
                txid="OUF4EM-FRGI2-MQMWZD",
                cl_ord_id="my-order-123",
            )

    def test_at_least_one_identifier_required(self):
        """Test that either txid or cl_ord_id must be provided"""
        with pytest.raises(ValidationError, match="Either 'txid' or 'cl_ord_id' must be provided"):
            CancelOrderRequest()

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        cancel = CancelOrderRequest(txid="OUF4EM-FRGI2-MQMWZD")

        # Should not have a nonce attribute
        assert not hasattr(cancel, "nonce")

    def test_to_api_dict_method_with_txid(self):
        """Test to_api_dict() serialization helper method with txid"""
        cancel = CancelOrderRequest(txid="OUF4EM-FRGI2-MQMWZD")

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = cancel.to_api_dict()

        # None values should be excluded by default
        assert "cl_ord_id" not in data

        # Non-None values should be present
        assert data["txid"] == "OUF4EM-FRGI2-MQMWZD"

        # Test exclude_none=False
        data_with_none = cancel.to_api_dict(exclude_none=False)
        assert "cl_ord_id" in data_with_none
        assert data_with_none["cl_ord_id"] is None

    def test_to_api_dict_method_with_integer_txid(self):
        """Test to_api_dict() serialization with integer txid (userref)"""
        cancel = CancelOrderRequest(txid=99999)

        data = cancel.to_api_dict()

        # Integer txid should be preserved
        assert data["txid"] == 99999
        assert isinstance(data["txid"], int)

    def test_to_api_dict_method_with_cl_ord_id(self):
        """Test to_api_dict() serialization helper method with cl_ord_id"""
        cancel = CancelOrderRequest(cl_ord_id="client-order-abc")

        data = cancel.to_api_dict()

        # None values should be excluded by default
        assert "txid" not in data

        # Non-None values should be present
        assert data["cl_ord_id"] == "client-order-abc"

    def test_various_txid_formats(self):
        """Test various transaction ID formats"""
        # Standard Kraken transaction ID format
        cancel1 = CancelOrderRequest(txid="OUF4EM-FRGI2-MQMWZD")
        assert cancel1.txid == "OUF4EM-FRGI2-MQMWZD"

        # Shorter ID
        cancel2 = CancelOrderRequest(txid="ABC123")
        assert cancel2.txid == "ABC123"

        # User reference as integer
        cancel3 = CancelOrderRequest(txid=555)
        assert cancel3.txid == 555

        # User reference as string
        cancel4 = CancelOrderRequest(txid="555")
        assert cancel4.txid == 555  # Should be converted to int

    def test_various_cl_ord_id_formats(self):
        """Test various client order ID formats"""
        # UUID-like format
        cancel1 = CancelOrderRequest(cl_ord_id="550e8400-e29b-41d4-a716-446655440000")
        assert cancel1.cl_ord_id == "550e8400-e29b-41d4-a716-446655440000"

        # Short alphanumeric
        cancel2 = CancelOrderRequest(cl_ord_id="order-123")
        assert cancel2.cl_ord_id == "order-123"

        # 18-character ASCII
        cancel3 = CancelOrderRequest(cl_ord_id="ABCDEF1234567890XY")
        assert cancel3.cl_ord_id == "ABCDEF1234567890XY"


class TestCancelOrderResponse:
    """Tests for CancelOrder response schemas"""

    def test_success_response_parsing_single_order(self):
        """Test parsing a successful single order cancellation response"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 1,
            },
        }

        response = CancelOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.count == 1
        assert response.success.pending is None

    def test_success_response_parsing_multiple_orders(self):
        """Test parsing a successful multiple order cancellation response"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 5,
            },
        }

        response = CancelOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 5

    def test_success_response_with_pending_true(self):
        """Test parsing a success response with pending cancellation"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 2,
                "pending": True,
            },
        }

        response = CancelOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 2
        assert response.success.pending is True

    def test_success_response_with_pending_false(self):
        """Test parsing a success response with pending = false"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 1,
                "pending": False,
            },
        }

        response = CancelOrderResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 1
        assert response.success.pending is False

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EOrder:Unknown order"],
        }

        response = CancelOrderResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EOrder:Unknown order" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EOrder:Unknown order",
            ],
        }

        response = CancelOrderResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EOrder:Unknown order" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "count": 3,
                    "pending": False,
                },
            }
        )

        response = CancelOrderResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.count == 3
        assert response.success.pending is False

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            CancelOrderResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating CancelOrderSuccess directly"""
        success = CancelOrderSuccess(count=10)

        assert success.count == 10
        assert success.pending is None

        success2 = CancelOrderSuccess(count=5, pending=True)

        assert success2.count == 5
        assert success2.pending is True

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        error = ResponseErrorSchema(error=["EOrder:Unknown order"])

        assert len(error.error) == 1
        assert error.error[0] == "EOrder:Unknown order"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating CancelOrderResponse wrapper directly"""
        success = CancelOrderSuccess(count=3, pending=False)
        response = CancelOrderResponse(success=success)

        assert response.is_success is True
        assert response.success.count == 3

        error = ResponseErrorSchema(error=["Test error"])
        response2 = CancelOrderResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_zero_count_response(self):
        """Test handling response with zero count (edge case)"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 0,
            },
        }

        response = CancelOrderResponse.from_response(kraken_response)

        # Even with zero count, it's still a successful response
        assert response.is_success is True
        assert response.success.count == 0


class TestConcurrentCancelScenarios:
    """Tests for concurrent and async cancel usage scenarios"""

    def test_multiple_cancels_no_collision(self):
        """Test that creating multiple cancel requests simultaneously doesn't cause issues"""
        # Create multiple cancel requests in rapid succession
        cancels = []
        for i in range(10):
            if i % 2 == 0:
                cancel = CancelOrderRequest(txid=f"ORDER-{i}")
            else:
                cancel = CancelOrderRequest(txid=10000 + i)
            cancels.append(cancel)

        # All cancels should be valid
        assert len(cancels) == 10

        # No nonce field should exist (nonce handled by REST client)
        for cancel in cancels:
            assert not hasattr(cancel, "nonce")

    def test_mixed_identifier_types_concurrent(self):
        """Test concurrent creation with mixed identifier types"""
        import concurrent.futures

        def create_cancel(i):
            if i % 3 == 0:
                return CancelOrderRequest(txid=f"TXID-{i}")
            elif i % 3 == 1:
                return CancelOrderRequest(txid=50000 + i)
            else:
                return CancelOrderRequest(cl_ord_id=f"CLIENT-ORDER-{i}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            cancels = list(executor.map(create_cancel, range(30)))

        assert len(cancels) == 30

        # Check that different identifier types are properly distributed
        string_txid_cancels = [
            c for c in cancels if isinstance(c.txid, str) and c.txid is not None
        ]
        int_txid_cancels = [c for c in cancels if isinstance(c.txid, int) and c.txid is not None]
        cl_ord_id_cancels = [c for c in cancels if c.cl_ord_id is not None]

        assert len(string_txid_cancels) == 10
        assert len(int_txid_cancels) == 10
        assert len(cl_ord_id_cancels) == 10

    def test_rapid_cancel_creation(self):
        """Test rapid creation of cancel requests"""
        cancels = []
        for i in range(100):
            cancel = CancelOrderRequest(txid=f"RAPID-{i}")
            cancels.append(cancel)

        # All should be valid
        assert len(cancels) == 100

        # All txids should be unique
        txids = [c.txid for c in cancels]
        assert len(set(txids)) == 100

    def test_concurrent_serialization(self):
        """Test concurrent serialization of cancel requests"""
        import concurrent.futures

        def create_and_serialize(i):
            cancel = CancelOrderRequest(txid=f"SERIAL-{i}")
            return cancel.to_api_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            dicts = list(executor.map(create_and_serialize, range(50)))

        assert len(dicts) == 50

        # All should have valid structure
        for d in dicts:
            assert "txid" in d
            assert d["txid"].startswith("SERIAL-")


class TestCancelAllRequest:
    """Tests for CancelAllRequest schema"""

    def test_minimal_valid_cancel_all(self):
        """Test creating a minimal valid cancel all request"""
        cancel_all = CancelAllRequest()

        # Should be valid with no required fields
        assert cancel_all is not None

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        cancel_all = CancelAllRequest()

        # Should not have a nonce attribute
        assert not hasattr(cancel_all, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        cancel_all = CancelAllRequest()

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = cancel_all.to_api_dict()

        # Should return an empty dict (no fields except nonce which is added by client)
        assert data == {}

        # Test exclude_none=False
        data_with_none = cancel_all.to_api_dict(exclude_none=False)
        assert data_with_none == {}

    def test_multiple_instances(self):
        """Test creating multiple CancelAllRequest instances"""
        requests = [CancelAllRequest() for _ in range(10)]

        # All should be valid
        assert len(requests) == 10
        for req in requests:
            assert req is not None


class TestCancelAllResponse:
    """Tests for CancelAll response schemas"""

    def test_success_response_parsing_single_order(self):
        """Test parsing a successful single order cancellation response"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 1,
            },
        }

        response = CancelAllResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.count == 1
        assert response.success.pending is None

    def test_success_response_parsing_multiple_orders(self):
        """Test parsing a successful multiple order cancellation response"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 15,
            },
        }

        response = CancelAllResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 15

    def test_success_response_with_pending_true(self):
        """Test parsing a success response with pending cancellation"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 8,
                "pending": True,
            },
        }

        response = CancelAllResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 8
        assert response.success.pending is True

    def test_success_response_with_pending_false(self):
        """Test parsing a success response with pending = false"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 3,
                "pending": False,
            },
        }

        response = CancelAllResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 3
        assert response.success.pending is False

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Permission denied"],
        }

        response = CancelAllResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Permission denied" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EGeneral:Permission denied",
            ],
        }

        response = CancelAllResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EGeneral:Permission denied" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "count": 7,
                    "pending": False,
                },
            }
        )

        response = CancelAllResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.count == 7
        assert response.success.pending is False

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            CancelAllResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating CancelAllSuccess directly"""
        success = CancelAllSuccess(count=20)

        assert success.count == 20
        assert success.pending is None

        success2 = CancelAllSuccess(count=10, pending=True)

        assert success2.count == 10
        assert success2.pending is True

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        error = ResponseErrorSchema(error=["EGeneral:Permission denied"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Permission denied"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating CancelAllResponse wrapper directly"""
        success = CancelAllSuccess(count=5, pending=False)
        response = CancelAllResponse(success=success)

        assert response.is_success is True
        assert response.success.count == 5

        error = ResponseErrorSchema(error=["Test error"])
        response2 = CancelAllResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_zero_count_response(self):
        """Test handling response with zero count (edge case - no open orders)"""
        kraken_response = {
            "error": [],
            "result": {
                "count": 0,
            },
        }

        response = CancelAllResponse.from_response(kraken_response)

        # Even with zero count, it's still a successful response
        assert response.is_success is True
        assert response.success.count == 0


class TestConcurrentCancelAllScenarios:
    """Tests for concurrent and async cancel all usage scenarios"""

    def test_multiple_cancel_all_no_collision(self):
        """Test that creating multiple cancel all requests simultaneously doesn't cause issues"""
        # Create multiple cancel all requests in rapid succession
        cancels = []
        for i in range(10):
            cancel = CancelAllRequest()
            cancels.append(cancel)

        # All cancels should be valid
        assert len(cancels) == 10

        # No nonce field should exist (nonce handled by REST client)
        for cancel in cancels:
            assert not hasattr(cancel, "nonce")

    def test_concurrent_serialization(self):
        """Test concurrent serialization of cancel all requests"""
        import concurrent.futures

        def create_and_serialize(i):
            cancel = CancelAllRequest()
            return cancel.to_api_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            dicts = list(executor.map(create_and_serialize, range(50)))

        assert len(dicts) == 50

        # All should have valid structure (empty dict)
        for d in dicts:
            assert d == {}


class TestCancelAllOrdersAfterRequest:
    """Tests for CancelAllOrdersAfterRequest schema"""

    def test_minimal_valid_request_with_timeout(self):
        """Test creating a minimal valid request with timeout"""
        cancel_after = CancelAllOrdersAfterRequest(timeout=60)

        assert cancel_after.timeout == 60

    def test_timeout_zero_to_disable(self):
        """Test setting timeout to zero to disable the timer"""
        cancel_after = CancelAllOrdersAfterRequest(timeout=0)

        assert cancel_after.timeout == 0

    def test_timeout_max_value(self):
        """Test setting timeout to maximum allowed value (24 hours)"""
        cancel_after = CancelAllOrdersAfterRequest(timeout=86400)

        assert cancel_after.timeout == 86400

    def test_timeout_string_conversion(self):
        """Test that timeout string is converted to integer"""
        cancel_after = CancelAllOrdersAfterRequest(timeout="120")

        assert cancel_after.timeout == 120
        assert isinstance(cancel_after.timeout, int)

    def test_timeout_negative_validation(self):
        """Test that negative timeout raises validation error"""
        with pytest.raises(ValidationError, match="between 0 and 86400"):
            CancelAllOrdersAfterRequest(timeout=-1)

    def test_timeout_too_large_validation(self):
        """Test that timeout exceeding maximum raises validation error"""
        with pytest.raises(ValidationError, match="between 0 and 86400"):
            CancelAllOrdersAfterRequest(timeout=86401)

    def test_timeout_way_too_large_validation(self):
        """Test that extremely large timeout raises validation error"""
        with pytest.raises(ValidationError, match="between 0 and 86400"):
            CancelAllOrdersAfterRequest(timeout=100000)

    def test_timeout_required(self):
        """Test that timeout field is required"""
        with pytest.raises(ValidationError):
            CancelAllOrdersAfterRequest()

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        cancel_after = CancelAllOrdersAfterRequest(timeout=60)

        # Should not have a nonce attribute
        assert not hasattr(cancel_after, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        cancel_after = CancelAllOrdersAfterRequest(timeout=120)

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = cancel_after.to_api_dict()

        # Should contain timeout field
        assert "timeout" in data
        assert data["timeout"] == 120

    def test_to_api_dict_with_zero_timeout(self):
        """Test to_api_dict() with timeout=0 to disable"""
        cancel_after = CancelAllOrdersAfterRequest(timeout=0)

        data = cancel_after.to_api_dict()

        # Zero should be included (not excluded as None)
        assert "timeout" in data
        assert data["timeout"] == 0

    def test_various_timeout_values(self):
        """Test various valid timeout values"""
        timeouts = [0, 15, 30, 60, 300, 600, 3600, 43200, 86400]

        for timeout_val in timeouts:
            cancel_after = CancelAllOrdersAfterRequest(timeout=timeout_val)
            assert cancel_after.timeout == timeout_val


class TestCancelAllOrdersAfterResponse:
    """Tests for CancelAllOrdersAfter response schemas"""

    def test_success_response_parsing(self):
        """Test parsing a successful response"""
        kraken_response = {
            "error": [],
            "result": {
                "currentTime": "2025-01-15T12:00:00Z",
                "triggerTime": "2025-01-15T12:01:00Z",
            },
        }

        response = CancelAllOrdersAfterResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.current_time == "2025-01-15T12:00:00Z"
        assert response.success.trigger_time == "2025-01-15T12:01:00Z"

    def test_success_response_with_zero_timeout(self):
        """Test parsing response when timer is disabled (timeout=0)"""
        kraken_response = {
            "error": [],
            "result": {
                "currentTime": "2025-01-15T12:00:00Z",
                "triggerTime": "0",
            },
        }

        response = CancelAllOrdersAfterResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.current_time == "2025-01-15T12:00:00Z"
        assert response.success.trigger_time == "0"

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Invalid arguments"],
        }

        response = CancelAllOrdersAfterResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EGeneral:Permission denied",
            ],
        }

        response = CancelAllOrdersAfterResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EGeneral:Permission denied" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "currentTime": "2025-01-15T14:30:00Z",
                    "triggerTime": "2025-01-15T14:31:00Z",
                },
            }
        )

        response = CancelAllOrdersAfterResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.current_time == "2025-01-15T14:30:00Z"
        assert response.success.trigger_time == "2025-01-15T14:31:00Z"

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            CancelAllOrdersAfterResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating CancelAllOrdersAfterSuccess directly"""
        success = CancelAllOrdersAfterSuccess(
            currentTime="2025-01-15T10:00:00Z", triggerTime="2025-01-15T10:01:00Z"
        )

        assert success.current_time == "2025-01-15T10:00:00Z"
        assert success.trigger_time == "2025-01-15T10:01:00Z"

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        error = ResponseErrorSchema(error=["EGeneral:Invalid timeout"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Invalid timeout"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating CancelAllOrdersAfterResponse wrapper directly"""
        success = CancelAllOrdersAfterSuccess(
            currentTime="2025-01-15T10:00:00Z", triggerTime="2025-01-15T10:01:00Z"
        )
        response = CancelAllOrdersAfterResponse(success=success)

        assert response.is_success is True
        assert response.success.current_time == "2025-01-15T10:00:00Z"

        error = ResponseErrorSchema(error=["Test error"])
        response2 = CancelAllOrdersAfterResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_rfc3339_timestamp_format(self):
        """Test that various RFC3339 timestamp formats are accepted"""
        # Different RFC3339 formats
        formats = [
            ("2025-01-15T12:00:00Z", "2025-01-15T12:01:00Z"),
            ("2025-01-15T12:00:00+00:00", "2025-01-15T12:01:00+00:00"),
            ("2025-01-15T12:00:00.123456Z", "2025-01-15T12:01:00.123456Z"),
            ("2025-01-15T08:00:00-04:00", "2025-01-15T08:01:00-04:00"),
        ]

        for current, trigger in formats:
            kraken_response = {
                "error": [],
                "result": {
                    "currentTime": current,
                    "triggerTime": trigger,
                },
            }

            response = CancelAllOrdersAfterResponse.from_response(kraken_response)

            assert response.is_success is True
            assert response.success.current_time == current
            assert response.success.trigger_time == trigger


class TestConcurrentCancelAllOrdersAfterScenarios:
    """Tests for concurrent and async cancel all orders after usage scenarios"""

    def test_multiple_requests_no_collision(self):
        """Test that creating multiple requests simultaneously doesn't cause issues"""
        # Create multiple requests in rapid succession
        requests = []
        for i in range(10):
            req = CancelAllOrdersAfterRequest(timeout=60 + i * 10)
            requests.append(req)

        # All requests should be valid
        assert len(requests) == 10

        # No nonce field should exist (nonce handled by REST client)
        for req in requests:
            assert not hasattr(req, "nonce")

        # Each should have unique timeout
        timeouts = [r.timeout for r in requests]
        assert len(set(timeouts)) == 10

    def test_concurrent_creation_with_validation(self):
        """Test concurrent creation with timeout validation"""
        import concurrent.futures

        def create_request(i):
            # Create with different valid timeouts
            timeout = (i % 10) * 100 + 60
            return CancelAllOrdersAfterRequest(timeout=timeout)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            requests = list(executor.map(create_request, range(50)))

        assert len(requests) == 50

        # All should have valid timeouts
        for req in requests:
            assert 0 <= req.timeout <= 86400

    def test_concurrent_serialization(self):
        """Test concurrent serialization of requests"""
        import concurrent.futures

        def create_and_serialize(i):
            req = CancelAllOrdersAfterRequest(timeout=60 + i)
            return req.to_api_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            dicts = list(executor.map(create_and_serialize, range(50)))

        assert len(dicts) == 50

        # All should have valid structure with timeout field
        for i, d in enumerate(dicts):
            assert "timeout" in d
            assert d["timeout"] == 60 + i

    def test_rapid_toggle_timer(self):
        """Test rapid toggling between enabling and disabling timer"""
        requests = []
        for i in range(100):
            if i % 2 == 0:
                req = CancelAllOrdersAfterRequest(timeout=60)
            else:
                req = CancelAllOrdersAfterRequest(timeout=0)
            requests.append(req)

        # All should be valid
        assert len(requests) == 100

        # Check alternating pattern
        for i, req in enumerate(requests):
            if i % 2 == 0:
                assert req.timeout == 60
            else:
                assert req.timeout == 0


class TestGetWebSocketsTokenRequest:
    """Tests for GetWebSocketsTokenRequest schema"""

    def test_minimal_valid_request(self):
        """Test creating a minimal valid request"""
        ws_token_request = GetWebSocketsTokenRequest()

        # Should be valid with no required fields
        assert ws_token_request is not None

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema (handled by REST client)"""
        ws_token_request = GetWebSocketsTokenRequest()

        # Should not have a nonce attribute
        assert not hasattr(ws_token_request, "nonce")

    def test_to_api_dict_method(self):
        """Test to_api_dict() serialization helper method"""
        ws_token_request = GetWebSocketsTokenRequest()

        # to_api_dict() should use by_alias=True and exclude_none=True
        data = ws_token_request.to_api_dict()

        # Should return an empty dict (no fields except nonce which is added by client)
        assert data == {}

        # Test exclude_none=False
        data_with_none = ws_token_request.to_api_dict(exclude_none=False)
        assert data_with_none == {}

    def test_multiple_instances(self):
        """Test creating multiple GetWebSocketsTokenRequest instances"""
        requests = [GetWebSocketsTokenRequest() for _ in range(10)]

        # All should be valid
        assert len(requests) == 10
        for req in requests:
            assert req is not None


class TestGetWebSocketsTokenResponse:
    """Tests for GetWebSocketsToken response schemas"""

    def test_success_response_parsing(self):
        """Test parsing a successful response"""
        kraken_response = {
            "error": [],
            "result": {
                "token": "1Dwc4lzSwNWOAwkMdqhssNNFhs1ed606d1WcF3XfEMw",
                "expires": 900,
            },
        }

        response = GetWebSocketsTokenResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success is not None
        assert response.failure is None
        assert response.success.token == "1Dwc4lzSwNWOAwkMdqhssNNFhs1ed606d1WcF3XfEMw"
        assert response.success.expires == 900

    def test_error_response_parsing(self):
        """Test parsing an error response"""
        kraken_response = {
            "error": ["EGeneral:Permission denied"],
        }

        response = GetWebSocketsTokenResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.success is None
        assert response.failure is not None
        assert "EGeneral:Permission denied" in response.failure.error

    def test_multiple_errors(self):
        """Test parsing response with multiple errors"""
        kraken_response = {
            "error": [
                "EGeneral:Invalid arguments",
                "EAPI:Invalid key",
            ],
        }

        response = GetWebSocketsTokenResponse.from_response(kraken_response)

        assert response.is_success is False
        assert len(response.failure.error) == 2
        assert "EGeneral:Invalid arguments" in response.failure.error
        assert "EAPI:Invalid key" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "token": "testTokenABC123xyz789",
                    "expires": 900,
                },
            }
        )

        response = GetWebSocketsTokenResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.token == "testTokenABC123xyz789"
        assert response.success.expires == 900

    def test_invalid_response_format(self):
        """Test that invalid response format raises appropriate error"""
        invalid_response = {"error": []}  # Missing 'result'

        with pytest.raises(ValueError, match="missing 'result'"):
            GetWebSocketsTokenResponse.from_response(invalid_response)

    def test_success_model_direct_instantiation(self):
        """Test creating GetWebSocketsTokenSuccess directly"""
        success = GetWebSocketsTokenSuccess(token="directTokenExample123", expires=900)

        assert success.token == "directTokenExample123"
        assert success.expires == 900

    def test_error_model_direct_instantiation(self):
        """Test creating error response directly"""
        error = ResponseErrorSchema(error=["EGeneral:Permission denied"])

        assert len(error.error) == 1
        assert error.error[0] == "EGeneral:Permission denied"

    def test_response_wrapper_direct_instantiation(self):
        """Test creating GetWebSocketsTokenResponse wrapper directly"""
        success = GetWebSocketsTokenSuccess(token="wrapperTest", expires=900)
        response = GetWebSocketsTokenResponse(success=success)

        assert response.is_success is True
        assert response.success.token == "wrapperTest"

        error = ResponseErrorSchema(error=["Test error"])
        response2 = GetWebSocketsTokenResponse(failure=error)

        assert response2.is_success is False
        assert response2.failure.error[0] == "Test error"

    def test_token_format(self):
        """Test that token is string format"""
        kraken_response = {
            "error": [],
            "result": {
                "token": "aBcDeF123456789",
                "expires": 900,
            },
        }

        response = GetWebSocketsTokenResponse.from_response(kraken_response)

        assert response.is_success is True
        assert isinstance(response.success.token, str)
        assert len(response.success.token) > 0

    def test_expires_value(self):
        """Test that expires is integer value (typically 900)"""
        kraken_response = {
            "error": [],
            "result": {
                "token": "tokenExample",
                "expires": 900,
            },
        }

        response = GetWebSocketsTokenResponse.from_response(kraken_response)

        assert response.is_success is True
        assert isinstance(response.success.expires, int)
        assert response.success.expires == 900

    def test_different_expires_values(self):
        """Test parsing with different expires values"""
        # While typically 900, test flexibility for other values
        test_expires = [300, 600, 900, 1800]

        for expires_val in test_expires:
            kraken_response = {
                "error": [],
                "result": {
                    "token": f"token_{expires_val}",
                    "expires": expires_val,
                },
            }

            response = GetWebSocketsTokenResponse.from_response(kraken_response)

            assert response.is_success is True
            assert response.success.expires == expires_val

    def test_long_token_string(self):
        """Test handling of long token strings"""
        long_token = "a" * 100  # Long token string
        kraken_response = {
            "error": [],
            "result": {
                "token": long_token,
                "expires": 900,
            },
        }

        response = GetWebSocketsTokenResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.token == long_token
        assert len(response.success.token) == 100


class TestConcurrentGetWebSocketsTokenScenarios:
    """Tests for concurrent and async GetWebSocketsToken usage scenarios"""

    def test_multiple_requests_no_collision(self):
        """Test that creating multiple requests simultaneously doesn't cause issues"""
        # Create multiple requests in rapid succession
        requests = []
        for i in range(10):
            req = GetWebSocketsTokenRequest()
            requests.append(req)

        # All requests should be valid
        assert len(requests) == 10

        # No nonce field should exist (nonce handled by REST client)
        for req in requests:
            assert not hasattr(req, "nonce")

    def test_concurrent_serialization(self):
        """Test concurrent serialization of requests"""
        import concurrent.futures

        def create_and_serialize(i):
            req = GetWebSocketsTokenRequest()
            return req.to_api_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            dicts = list(executor.map(create_and_serialize, range(50)))

        assert len(dicts) == 50

        # All should have valid structure (empty dict)
        for d in dicts:
            assert d == {}

    def test_rapid_request_creation(self):
        """Test rapid creation of WebSocket token requests"""
        requests = []
        for i in range(100):
            req = GetWebSocketsTokenRequest()
            requests.append(req)

        # All should be valid
        assert len(requests) == 100

        # All should serialize to empty dict
        for req in requests:
            assert req.to_api_dict() == {}

    def test_concurrent_response_parsing(self):
        """Test concurrent parsing of responses"""
        import concurrent.futures

        def parse_response(i):
            kraken_response = {
                "error": [],
                "result": {
                    "token": f"concurrent_token_{i}",
                    "expires": 900,
                },
            }
            return GetWebSocketsTokenResponse.from_response(kraken_response)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            responses = list(executor.map(parse_response, range(50)))

        assert len(responses) == 50

        # All should be successful
        for i, response in enumerate(responses):
            assert response.is_success is True
            assert response.success.token == f"concurrent_token_{i}"
            assert response.success.expires == 900


class TestBatchOrderItem:
    """Tests for BatchOrderItem schema"""

    def test_minimal_valid_item(self):
        """Test creating a minimal valid batch order item"""
        item = BatchOrderItem(
            ordertype="market",
            type="buy",
            volume=1.5,
        )

        assert item.ordertype == "market"
        assert item.type == "buy"
        assert item.volume == "1.5"

    def test_field_inheritance_from_add_order(self):
        """Test that validators work same as AddOrderRequest"""
        item = BatchOrderItem(
            ordertype="limit",
            type="sell",
            volume=2.0,
            price="50000",
        )

        assert item.ordertype == "limit"
        assert item.volume == "2.0"
        assert item.price == "50000"

    def test_volume_conversion(self):
        """Test that volume is converted to string"""
        # Integer volume
        item1 = BatchOrderItem(ordertype="market", type="buy", volume=3)
        assert item1.volume == "3"

        # Float volume
        item2 = BatchOrderItem(ordertype="market", type="buy", volume=1.25)
        assert item2.volume == "1.25"

    def test_ordertype_normalization(self):
        """Test that ordertype is normalized to lowercase"""
        item = BatchOrderItem(
            ordertype="LIMIT",
            type="buy",
            volume=1,
            price="50000",
        )
        assert item.ordertype == "limit"

    def test_field_dependency_validation(self):
        """Test that limit orders require price field"""
        with pytest.raises(ValidationError, match="(?i)limit orders require 'price'"):
            BatchOrderItem(
                ordertype="limit",
                type="buy",
                volume=1,
            )

    def test_stop_loss_limit_validation(self):
        """Test that stop-loss-limit requires both price and price2"""
        with pytest.raises(
            ValidationError, match="stop-loss-limit orders require both 'price' and 'price2'"
        ):
            BatchOrderItem(
                ordertype="stop-loss-limit",
                type="sell",
                volume=1,
                price="48000",
            )

    def test_iceberg_display_volume(self):
        """Test iceberg order display volume floor enforcement"""
        # Display volume too small
        item1 = BatchOrderItem(
            ordertype="iceberg",
            type="buy",
            volume=15,
            displayvol=0.5,
            price="50000",
        )
        assert float(item1.displayvol) == 1.0

    def test_userref_cl_ord_id_mutually_exclusive(self):
        """Test that userref and cl_ord_id cannot both be set"""
        with pytest.raises(ValidationError, match="mutually exclusive"):
            BatchOrderItem(
                ordertype="market",
                type="buy",
                volume=1,
                userref=123,
                cl_ord_id="order-abc",
            )


class TestAddOrderBatchRequest:
    """Tests for AddOrderBatchRequest schema"""

    def test_minimal_valid_batch(self):
        """Test creating a minimal valid batch with 2 orders"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="buy", volume=0.5),
            ],
            pair="XBTUSD",
        )

        assert len(batch.orders) == 2
        assert batch.pair == "XBTUSD"

    def test_maximum_batch_size(self):
        """Test batch with maximum 15 orders"""
        orders = [BatchOrderItem(ordertype="market", type="buy", volume=1.0) for _ in range(15)]
        batch = AddOrderBatchRequest(orders=orders, pair="XBTUSD")

        assert len(batch.orders) == 15

    def test_batch_size_too_small(self):
        """Test that batch with 1 order is rejected"""
        with pytest.raises(ValidationError, match="at least 2 orders"):
            AddOrderBatchRequest(
                orders=[BatchOrderItem(ordertype="market", type="buy", volume=1.0)],
                pair="XBTUSD",
            )

    def test_batch_size_too_large(self):
        """Test that batch with 16+ orders is rejected"""
        orders = [BatchOrderItem(ordertype="market", type="buy", volume=1.0) for _ in range(16)]
        with pytest.raises(ValidationError, match="at most 15 orders"):
            AddOrderBatchRequest(orders=orders, pair="XBTUSD")

    def test_single_pair_requirement(self):
        """Test that all orders are for a single pair"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="sell", volume=0.5),
            ],
            pair="ETHUSD",
        )

        assert batch.pair == "ETHUSD"

    def test_deadline_validation(self):
        """Test deadline RFC3339 format and timezone requirement"""
        now = datetime.now(timezone.utc)
        valid_deadline = (now + timedelta(seconds=10)).isoformat()

        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="buy", volume=0.5),
            ],
            pair="XBTUSD",
            deadline=valid_deadline,
        )

        assert batch.deadline is not None

    def test_deadline_bounding(self):
        """Test that deadline is bounded between 2-60 seconds"""
        now = datetime.now(timezone.utc)
        too_far = (now + timedelta(seconds=120)).isoformat()

        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="buy", volume=0.5),
            ],
            pair="XBTUSD",
            deadline=too_far,
        )

        deadline = datetime.fromisoformat(batch.deadline)
        max_deadline = now + timedelta(seconds=60)
        assert deadline <= max_deadline + timedelta(milliseconds=100)

    def test_validate_flag(self):
        """Test validation only mode"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="buy", volume=0.5),
            ],
            pair="XBTUSD",
            only_validate=True,
        )

        assert batch.only_validate is True

    def test_validate_flag_alias(self):
        """Test that 'validate' alias works for backward compatibility"""
        # Test that we can use the 'validate' alias when instantiating
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="buy", volume=0.5),
            ],
            pair="XBTUSD",
            validate=True,  # Using the alias
        )

        # The field name is 'only_validate'
        assert batch.only_validate is True

        # Verify it serializes as 'validate' to the API
        data = batch.to_api_dict()
        assert "validate" in data
        assert data["validate"] is True
        assert "only_validate" not in data

    def test_asset_class_for_xstocks(self):
        """Test asset_class parameter for tokenized assets"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=10),
                BatchOrderItem(ordertype="market", type="buy", volume=5),
            ],
            pair="TSLA/USD",
            asset_class="tokenized_asset",
        )

        assert batch.asset_class == "tokenized_asset"

    def test_to_api_dict_serialization(self):
        """Test to_api_dict() serialization"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="limit", type="buy", volume=1.0, price="50000"),
                BatchOrderItem(ordertype="limit", type="buy", volume=0.5, price="49000"),
            ],
            pair="XBTUSD",
        )

        data = batch.to_api_dict()

        assert "orders" in data
        assert "pair" in data
        assert data["pair"] == "XBTUSD"
        assert len(data["orders"]) == 2

    def test_mixed_order_types(self):
        """Test batch with mixed order types"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="limit", type="sell", volume=1.0, price="55000"),
                BatchOrderItem(ordertype="stop-loss", type="sell", volume=1.0, price="45000"),
            ],
            pair="XBTUSD",
        )

        assert batch.orders[0].ordertype == "market"
        assert batch.orders[1].ordertype == "limit"
        assert batch.orders[2].ordertype == "stop-loss"

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema"""
        batch = AddOrderBatchRequest(
            orders=[
                BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                BatchOrderItem(ordertype="market", type="buy", volume=0.5),
            ],
            pair="XBTUSD",
        )

        assert not hasattr(batch, "nonce")


class TestAddOrderBatchResponse:
    """Tests for AddOrderBatch response schemas"""

    def test_success_response_all_orders(self):
        """Test parsing response where all orders succeeded"""
        kraken_response = {
            "error": [],
            "result": {
                "orders": [
                    {"txid": "ORDER-1", "descr": {"order": "buy 1.0 XBTUSD @ market"}},
                    {"txid": "ORDER-2", "descr": {"order": "buy 0.5 XBTUSD @ market"}},
                ]
            },
        }

        response = AddOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.orders) == 2
        assert response.success.orders[0].txid == "ORDER-1"
        assert response.success.orders[1].txid == "ORDER-2"
        assert response.success.orders[0].is_success is True
        assert response.success.orders[1].is_success is True

    def test_partial_success_response(self):
        """Test parsing response where some orders failed"""
        kraken_response = {
            "error": [],
            "result": {
                "orders": [
                    {"txid": "ORDER-1", "descr": {"order": "buy 1.0 XBTUSD @ market"}},
                    {"error": "Insufficient funds"},
                ]
            },
        }

        response = AddOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is True
        assert len(response.success.orders) == 2
        assert response.success.orders[0].is_success is True
        assert response.success.orders[1].is_success is False
        assert response.success.orders[1].error == "Insufficient funds"

    def test_all_orders_failed_validation(self):
        """Test parsing response where whole batch rejected"""
        kraken_response = {"error": ["EGeneral:Invalid arguments"]}

        response = AddOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is False
        assert response.failure is not None
        assert "EGeneral:Invalid arguments" in response.failure.error

    def test_error_response_parsing(self):
        """Test parsing batch-level error response"""
        kraken_response = {"error": ["EOrder:Invalid pair"]}

        response = AddOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is False
        assert "EOrder:Invalid pair" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps(
            {
                "error": [],
                "result": {
                    "orders": [
                        {"txid": "TX-1", "descr": {"order": "buy"}},
                        {"txid": "TX-2", "descr": {"order": "sell"}},
                    ]
                },
            }
        )

        response = AddOrderBatchResponse.from_response(json_response)

        assert response.is_success is True
        assert len(response.success.orders) == 2

    def test_invalid_response_format(self):
        """Test that invalid response format raises error"""
        invalid_response = {"error": []}

        with pytest.raises(ValueError, match="missing 'result'"):
            AddOrderBatchResponse.from_response(invalid_response)

    def test_order_result_ordering(self):
        """Test that results match request order"""
        kraken_response = {
            "error": [],
            "result": {
                "orders": [
                    {"txid": "FIRST"},
                    {"txid": "SECOND"},
                    {"txid": "THIRD"},
                ]
            },
        }

        response = AddOrderBatchResponse.from_response(kraken_response)

        assert response.success.orders[0].txid == "FIRST"
        assert response.success.orders[1].txid == "SECOND"
        assert response.success.orders[2].txid == "THIRD"

    def test_individual_order_error(self):
        """Test individual order with error field"""
        kraken_response = {
            "error": [],
            "result": {"orders": [{"error": "EOrder:Rate limit exceeded"}]},
        }

        response = AddOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.orders[0].error == "EOrder:Rate limit exceeded"
        assert response.success.orders[0].txid is None

    def test_txid_and_descr_fields(self):
        """Test successful order with txid and descr fields"""
        kraken_response = {
            "error": [],
            "result": {
                "orders": [
                    {
                        "txid": "ABC-123",
                        "descr": {"order": "buy 1.5 XBTUSD @ limit 50000"},
                    }
                ]
            },
        }

        response = AddOrderBatchResponse.from_response(kraken_response)

        order_result = response.success.orders[0]
        assert order_result.txid == "ABC-123"
        assert order_result.descr["order"] == "buy 1.5 XBTUSD @ limit 50000"
        assert order_result.is_success is True

    def test_direct_instantiation(self):
        """Test creating models directly"""
        result1 = BatchOrderResult(txid="TX-1", descr={"order": "buy"}, error=None)
        result2 = BatchOrderResult(txid=None, descr=None, error="Failed")

        success = AddOrderBatchSuccess(orders=[result1, result2])
        response = AddOrderBatchResponse(success=success)

        assert response.is_success is True
        assert len(response.success.orders) == 2


class TestConcurrentAddOrderBatchScenarios:
    """Tests for concurrent AddOrderBatch usage scenarios"""

    def test_multiple_batches_no_collision(self):
        """Test creating multiple batches simultaneously"""
        batches = []
        for i in range(10):
            batch = AddOrderBatchRequest(
                orders=[
                    BatchOrderItem(ordertype="market", type="buy", volume=1.0 + i * 0.1),
                    BatchOrderItem(ordertype="market", type="sell", volume=0.5),
                ],
                pair="XBTUSD",
            )
            batches.append(batch)

        assert len(batches) == 10
        for batch in batches:
            assert not hasattr(batch, "nonce")

    def test_concurrent_batch_creation(self):
        """Test concurrent batch creation with ThreadPoolExecutor"""
        import concurrent.futures

        def create_batch(i):
            return AddOrderBatchRequest(
                orders=[
                    BatchOrderItem(ordertype="market", type="buy", volume=1.0),
                    BatchOrderItem(ordertype="market", type="buy", volume=0.5),
                ],
                pair="XBTUSD",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            batches = list(executor.map(create_batch, range(20)))

        assert len(batches) == 20

    def test_rapid_batch_serialization(self):
        """Test rapid serialization of batches"""
        import concurrent.futures

        def create_and_serialize(i):
            batch = AddOrderBatchRequest(
                orders=[
                    BatchOrderItem(ordertype="limit", type="buy", volume=1.0, price="50000"),
                    BatchOrderItem(ordertype="limit", type="buy", volume=0.5, price="49000"),
                ],
                pair="XBTUSD",
            )
            return batch.to_api_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            dicts = list(executor.map(create_and_serialize, range(50)))

        assert len(dicts) == 50
        for d in dicts:
            assert "orders" in d
            assert "pair" in d

    def test_large_batch_handling(self):
        """Test batch with maximum 15 orders"""
        orders = [
            BatchOrderItem(
                ordertype="limit", type="buy", volume=1.0 + i * 0.1, price=f"{50000 + i * 100}"
            )
            for i in range(15)
        ]
        batch = AddOrderBatchRequest(orders=orders, pair="XBTUSD")

        assert len(batch.orders) == 15

        data = batch.to_api_dict()
        assert len(data["orders"]) == 15


class TestCancelOrderBatchItem:
    """Tests for CancelOrderBatchItem schema"""

    def test_with_txid_string(self):
        """Test creating item with string transaction ID"""
        item = CancelOrderBatchItem(txid="OUF4EM-FRGI2-MQMWZD")

        assert item.txid == "OUF4EM-FRGI2-MQMWZD"
        assert item.cl_ord_id is None

    def test_with_txid_integer(self):
        """Test creating item with integer userref"""
        item = CancelOrderBatchItem(txid=12345)

        assert item.txid == 12345
        assert isinstance(item.txid, int)

    def test_with_cl_ord_id(self):
        """Test creating item with client order ID"""
        item = CancelOrderBatchItem(cl_ord_id="my-order-123")

        assert item.cl_ord_id == "my-order-123"
        assert item.txid is None

    def test_txid_normalization(self):
        """Test that numeric string txids are converted to int"""
        item = CancelOrderBatchItem(txid="67890")

        assert item.txid == 67890
        assert isinstance(item.txid, int)

    def test_mutual_exclusivity(self):
        """Test that txid and cl_ord_id cannot both be set"""
        with pytest.raises(ValidationError, match="mutually exclusive"):
            CancelOrderBatchItem(txid="ABC-123", cl_ord_id="order-xyz")

    def test_at_least_one_required(self):
        """Test that at least one identifier must be provided"""
        with pytest.raises(ValidationError, match="Either 'txid' or 'cl_ord_id' must be provided"):
            CancelOrderBatchItem()


class TestCancelOrderBatchRequest:
    """Tests for CancelOrderBatchRequest schema"""

    def test_with_orders_list(self):
        """Test cancel batch with orders list"""
        batch = CancelOrderBatchRequest(
            orders=[
                CancelOrderBatchItem(txid="ORDER-1"),
                CancelOrderBatchItem(txid="ORDER-2"),
            ]
        )

        assert len(batch.orders) == 2
        assert batch.cl_ord_ids is None

    def test_with_cl_ord_ids_list(self):
        """Test cancel batch with cl_ord_ids list"""
        batch = CancelOrderBatchRequest(cl_ord_ids=["order-1", "order-2", "order-3"])

        assert len(batch.cl_ord_ids) == 3
        assert batch.orders is None

    def test_maximum_50_items(self):
        """Test batch with maximum 50 items"""
        orders = [CancelOrderBatchItem(txid=f"ORDER-{i}") for i in range(50)]
        batch = CancelOrderBatchRequest(orders=orders)

        assert len(batch.orders) == 50

    def test_exceeds_50_items(self):
        """Test that batch with 51+ items is rejected"""
        orders = [CancelOrderBatchItem(txid=f"ORDER-{i}") for i in range(51)]

        with pytest.raises(ValidationError, match="at most 50 total items"):
            CancelOrderBatchRequest(orders=orders)

    def test_mixed_txid_types(self):
        """Test batch with string txids and integer userrefs"""
        batch = CancelOrderBatchRequest(
            orders=[
                CancelOrderBatchItem(txid="ABC-123"),
                CancelOrderBatchItem(txid=99999),
                CancelOrderBatchItem(txid="DEF-456"),
            ]
        )

        assert isinstance(batch.orders[0].txid, str)
        assert isinstance(batch.orders[1].txid, int)
        assert isinstance(batch.orders[2].txid, str)

    def test_at_least_one_field_required(self):
        """Test that orders or cl_ord_ids must be provided"""
        with pytest.raises(
            ValidationError, match="Either 'orders' or 'cl_ord_ids' must be provided"
        ):
            CancelOrderBatchRequest()

    def test_to_api_dict_with_orders(self):
        """Test serialization with orders list"""
        batch = CancelOrderBatchRequest(
            orders=[
                CancelOrderBatchItem(txid="ORDER-1"),
                CancelOrderBatchItem(txid="ORDER-2"),
            ]
        )

        data = batch.to_api_dict()

        assert "orders" in data
        assert len(data["orders"]) == 2

    def test_to_api_dict_with_cl_ord_ids(self):
        """Test serialization with cl_ord_ids"""
        batch = CancelOrderBatchRequest(cl_ord_ids=["order-1", "order-2"])

        data = batch.to_api_dict()

        assert "cl_ord_ids" in data
        assert len(data["cl_ord_ids"]) == 2

    def test_no_nonce_field(self):
        """Test that nonce is not present in schema"""
        batch = CancelOrderBatchRequest(orders=[CancelOrderBatchItem(txid="ORDER-1")])

        assert not hasattr(batch, "nonce")

    def test_combined_orders_and_cl_ord_ids(self):
        """Test batch with both orders and cl_ord_ids"""
        batch = CancelOrderBatchRequest(
            orders=[CancelOrderBatchItem(txid="ORDER-1")], cl_ord_ids=["client-order-1"]
        )

        assert len(batch.orders) == 1
        assert len(batch.cl_ord_ids) == 1

    def test_combined_exceeds_50(self):
        """Test that combined orders + cl_ord_ids cannot exceed 50"""
        orders = [CancelOrderBatchItem(txid=f"ORDER-{i}") for i in range(30)]
        cl_ord_ids = [f"client-{i}" for i in range(21)]

        with pytest.raises(ValidationError, match="at most 50 total items"):
            CancelOrderBatchRequest(orders=orders, cl_ord_ids=cl_ord_ids)


class TestCancelOrderBatchResponse:
    """Tests for CancelOrderBatch response schemas"""

    def test_success_response(self):
        """Test parsing successful response"""
        kraken_response = {"error": [], "result": {"count": 5}}

        response = CancelOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 5

    def test_error_response_parsing(self):
        """Test parsing error response"""
        kraken_response = {"error": ["EOrder:Unknown order"]}

        response = CancelOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is False
        assert "EOrder:Unknown order" in response.failure.error

    def test_from_json_string(self):
        """Test parsing from JSON string"""
        json_response = json.dumps({"error": [], "result": {"count": 10}})

        response = CancelOrderBatchResponse.from_response(json_response)

        assert response.is_success is True
        assert response.success.count == 10

    def test_invalid_response_format(self):
        """Test that invalid response format raises error"""
        invalid_response = {"error": []}

        with pytest.raises(ValueError, match="missing 'result'"):
            CancelOrderBatchResponse.from_response(invalid_response)

    def test_zero_count(self):
        """Test response with zero count"""
        kraken_response = {"error": [], "result": {"count": 0}}

        response = CancelOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 0

    def test_large_count(self):
        """Test response with maximum count"""
        kraken_response = {"error": [], "result": {"count": 50}}

        response = CancelOrderBatchResponse.from_response(kraken_response)

        assert response.is_success is True
        assert response.success.count == 50

    def test_direct_instantiation(self):
        """Test creating models directly"""
        success = CancelOrderBatchSuccess(count=25)
        response = CancelOrderBatchResponse(success=success)

        assert response.is_success is True
        assert response.success.count == 25


class TestConcurrentCancelOrderBatchScenarios:
    """Tests for concurrent CancelOrderBatch usage scenarios"""

    def test_multiple_cancel_batches(self):
        """Test creating multiple cancel batches simultaneously"""
        batches = []
        for i in range(10):
            batch = CancelOrderBatchRequest(
                orders=[
                    CancelOrderBatchItem(txid=f"ORDER-{i}-1"),
                    CancelOrderBatchItem(txid=f"ORDER-{i}-2"),
                ]
            )
            batches.append(batch)

        assert len(batches) == 10

    def test_concurrent_serialization(self):
        """Test concurrent serialization of cancel batches"""
        import concurrent.futures

        def create_and_serialize(i):
            batch = CancelOrderBatchRequest(
                orders=[
                    CancelOrderBatchItem(txid=f"ORDER-{i}"),
                ]
            )
            return batch.to_api_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            dicts = list(executor.map(create_and_serialize, range(50)))

        assert len(dicts) == 50

    def test_rapid_batch_creation(self):
        """Test rapid creation of cancel batches"""
        batches = []
        for i in range(100):
            batch = CancelOrderBatchRequest(cl_ord_ids=[f"order-{i}"])
            batches.append(batch)

        assert len(batches) == 100

    def test_maximum_size_batches(self):
        """Test batches with 50 items each"""
        batch1 = CancelOrderBatchRequest(
            orders=[CancelOrderBatchItem(txid=f"ORDER-{i}") for i in range(50)]
        )
        batch2 = CancelOrderBatchRequest(cl_ord_ids=[f"client-{i}" for i in range(50)])

        assert len(batch1.orders) == 50
        assert len(batch2.cl_ord_ids) == 50


