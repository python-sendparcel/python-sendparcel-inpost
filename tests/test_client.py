"""Tests for ShipXClient."""

import httpx
import pytest
import respx

from sendparcel_inpost.client import ShipXClient
from sendparcel_inpost.exceptions import (
    ShipXAPIError,
    ShipXAuthenticationError,
    ShipXValidationError,
)

SANDBOX_URL = "https://sandbox-api-shipx-pl.easypack24.net"
PROD_URL = "https://api-shipx-pl.easypack24.net"


class TestClientInit:
    def test_sandbox_url(self) -> None:
        client = ShipXClient(
            token="t",
            organization_id=1,
            sandbox=True,
        )
        assert client.base_url == SANDBOX_URL

    def test_production_url(self) -> None:
        client = ShipXClient(
            token="t",
            organization_id=1,
            sandbox=False,
        )
        assert client.base_url == PROD_URL

    def test_custom_base_url(self) -> None:
        client = ShipXClient(
            token="t",
            organization_id=1,
            base_url="https://custom.api.local",
        )
        assert client.base_url == "https://custom.api.local"

    def test_default_timeout(self) -> None:
        client = ShipXClient(token="t", organization_id=1)
        assert client.timeout == 30.0

    def test_custom_timeout(self) -> None:
        client = ShipXClient(
            token="t",
            organization_id=1,
            timeout=60.0,
        )
        assert client.timeout == 60.0


class TestCreateShipment:
    @respx.mock
    async def test_success(self, shipx_client: ShipXClient) -> None:
        route = respx.post(
            f"{SANDBOX_URL}/v1/organizations/12345/shipments",
        ).respond(
            json={
                "id": 999,
                "tracking_number": "TRACK123",
                "status": "created",
            },
        )
        result = await shipx_client.create_shipment(
            payload={
                "receiver": {"phone": "500100200", "email": "a@b.com"},
                "parcels": [{"template": "small"}],
                "service": "inpost_locker_standard",
                "custom_attributes": {"target_point": "KRA010"},
            },
        )
        assert result["id"] == 999
        assert result["tracking_number"] == "TRACK123"
        assert route.called
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer test-token-123"

    @respx.mock
    async def test_401_raises_auth_error(
        self,
        shipx_client: ShipXClient,
    ) -> None:
        respx.post(
            f"{SANDBOX_URL}/v1/organizations/12345/shipments",
        ).respond(
            status_code=401,
            json={"error": "unauthorized", "message": "Bad token"},
        )
        with pytest.raises(ShipXAuthenticationError):
            await shipx_client.create_shipment(payload={})

    @respx.mock
    async def test_422_raises_validation_error(
        self,
        shipx_client: ShipXClient,
    ) -> None:
        respx.post(
            f"{SANDBOX_URL}/v1/organizations/12345/shipments",
        ).respond(
            status_code=422,
            json={
                "error": "validation_failed",
                "message": "Validation failed",
                "details": [
                    {"field": "receiver.phone", "message": "is required"},
                ],
            },
        )
        with pytest.raises(ShipXValidationError) as exc_info:
            await shipx_client.create_shipment(payload={})
        assert exc_info.value.errors == [
            {"field": "receiver.phone", "message": "is required"},
        ]

    @respx.mock
    async def test_500_raises_api_error(
        self,
        shipx_client: ShipXClient,
    ) -> None:
        respx.post(
            f"{SANDBOX_URL}/v1/organizations/12345/shipments",
        ).respond(
            status_code=500,
            json={"error": "internal_error", "message": "Server error"},
        )
        with pytest.raises(ShipXAPIError) as exc_info:
            await shipx_client.create_shipment(payload={})
        assert exc_info.value.status_code == 500


class TestGetShipment:
    @respx.mock
    async def test_success(self, shipx_client: ShipXClient) -> None:
        respx.get(f"{SANDBOX_URL}/v1/shipments/999").respond(
            json={"id": 999, "status": "confirmed"},
        )
        result = await shipx_client.get_shipment(shipment_id=999)
        assert result["id"] == 999
        assert result["status"] == "confirmed"


class TestGetLabel:
    @respx.mock
    async def test_success(self, shipx_client: ShipXClient) -> None:
        pdf_bytes = b"%PDF-1.4 fake label"
        respx.get(f"{SANDBOX_URL}/v1/shipments/999/label").respond(
            content=pdf_bytes,
            headers={"content-type": "application/pdf"},
        )
        result = await shipx_client.get_label(shipment_id=999)
        assert result == pdf_bytes

    @respx.mock
    async def test_custom_format(self, shipx_client: ShipXClient) -> None:
        route = respx.get(f"{SANDBOX_URL}/v1/shipments/999/label").respond(
            content=b"ZPL data",
        )
        await shipx_client.get_label(
            shipment_id=999,
            label_format="Zpl",
            label_type="normal",
        )
        assert "format=Zpl" in str(route.calls[0].request.url)
        assert "type=normal" in str(route.calls[0].request.url)


class TestCancelShipment:
    @respx.mock
    async def test_success(self, shipx_client: ShipXClient) -> None:
        respx.delete(f"{SANDBOX_URL}/v1/shipments/999").respond(
            status_code=204,
        )
        await shipx_client.cancel_shipment(shipment_id=999)

    @respx.mock
    async def test_400_raises_api_error(
        self,
        shipx_client: ShipXClient,
    ) -> None:
        respx.delete(f"{SANDBOX_URL}/v1/shipments/999").respond(
            status_code=400,
            json={"error": "cannot_cancel", "message": "Already confirmed"},
        )
        with pytest.raises(ShipXAPIError):
            await shipx_client.cancel_shipment(shipment_id=999)


class TestGetTracking:
    @respx.mock
    async def test_success(self, shipx_client: ShipXClient) -> None:
        respx.get(f"{SANDBOX_URL}/v1/tracking/TRACK123").respond(
            json={
                "tracking_number": "TRACK123",
                "tracking_details": [
                    {
                        "status": "delivered",
                        "datetime": "2026-01-15T10:00:00",
                    },
                ],
            },
        )
        result = await shipx_client.get_tracking(
            tracking_number="TRACK123",
        )
        assert result["tracking_number"] == "TRACK123"
        assert len(result["tracking_details"]) == 1


class TestContextManager:
    async def test_async_context_manager(self) -> None:
        async with ShipXClient(
            token="t",
            organization_id=1,
            sandbox=True,
        ) as client:
            assert client is not None


class TestHTTPError:
    @respx.mock
    async def test_connection_error_propagates(
        self,
        shipx_client: ShipXClient,
    ) -> None:
        respx.get(f"{SANDBOX_URL}/v1/shipments/1").mock(
            side_effect=httpx.ConnectError("Connection refused"),
        )
        with pytest.raises(httpx.ConnectError):
            await shipx_client.get_shipment(shipment_id=1)
