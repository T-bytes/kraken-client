"""Unit tests for Kraken REST API schemas"""

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
    TickerInfo,
)
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
