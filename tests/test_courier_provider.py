"""Tests for InPostCourierProvider."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from sendparcel.enums import ConfirmationMethod, ShipmentStatus
from sendparcel.types import AddressInfo, ParcelInfo

from sendparcel_inpost.providers.courier import InPostCourierProvider

SENDER_ADDRESS: AddressInfo = {
    "first_name": "Jan",
    "last_name": "Nadawca",
    "phone": "500100200",
    "email": "sender@example.com",
    "street": "Nadawcza",
    "building_number": "1",
    "city": "Warszawa",
    "postal_code": "00-001",
    "country_code": "PL",
}

RECEIVER_ADDRESS: AddressInfo = {
    "first_name": "Anna",
    "last_name": "Odbiorca",
    "phone": "600200300",
    "email": "receiver@example.com",
    "street": "Odbiorcza",
    "building_number": "5",
    "flat_number": "10",
    "city": "Krakow",
    "postal_code": "30-001",
    "country_code": "PL",
}

PARCELS: list[ParcelInfo] = [
    {
        "weight_kg": Decimal("2.5"),
        "length_cm": Decimal("30"),
        "width_cm": Decimal("20"),
        "height_cm": Decimal("15"),
    },
]


@dataclass
class _FakeShipment:
    id: str = "ship-2"
    status: str = "new"
    provider: str = "inpost_courier"
    external_id: str = ""
    tracking_number: str = ""
    label_url: str = ""


class TestCourierProviderClassVars:
    def test_slug(self) -> None:
        assert InPostCourierProvider.slug == "inpost_courier"

    def test_display_name(self) -> None:
        assert InPostCourierProvider.display_name == "InPost Kurier"

    def test_supported_countries(self) -> None:
        assert "PL" in InPostCourierProvider.supported_countries

    def test_supported_services(self) -> None:
        assert (
            "inpost_courier_standard"
            in InPostCourierProvider.supported_services
        )

    def test_confirmation_method(self) -> None:
        assert (
            InPostCourierProvider.confirmation_method == ConfirmationMethod.PUSH
        )


class TestCourierCreateShipment:
    async def test_creates_shipment_with_dimensions(self) -> None:
        shipment = _FakeShipment()
        config = {
            "token": "test-token",
            "organization_id": 12345,
            "sandbox": True,
        }
        provider = InPostCourierProvider(shipment, config=config)

        mock_response = {
            "id": 888,
            "tracking_number": "TRACK888",
            "status": "created",
        }

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.create_shipment = AsyncMock(
                return_value=mock_response,
            )
            mock_client.close = AsyncMock()

            result = await provider.create_shipment(
                sender_address=SENDER_ADDRESS,
                receiver_address=RECEIVER_ADDRESS,
                parcels=PARCELS,
            )

        assert result["external_id"] == "888"
        assert result["tracking_number"] == "TRACK888"

        call_kwargs = mock_client.create_shipment.call_args
        payload = call_kwargs.kwargs["payload"]
        assert payload["service"] == "inpost_courier_standard"
        # Courier uses dimensions, not template
        parcel = payload["parcels"][0]
        assert "dimensions" in parcel
        assert "weight" in parcel
        assert "template" not in parcel

    async def test_includes_receiver_address(self) -> None:
        shipment = _FakeShipment()
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostCourierProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.create_shipment = AsyncMock(
                return_value={"id": 1, "tracking_number": "T1"},
            )
            mock_client.close = AsyncMock()

            await provider.create_shipment(
                sender_address=SENDER_ADDRESS,
                receiver_address=RECEIVER_ADDRESS,
                parcels=PARCELS,
            )

        call_kwargs = mock_client.create_shipment.call_args
        payload = call_kwargs.kwargs["payload"]
        receiver = payload["receiver"]
        assert receiver["first_name"] == "Anna"
        assert receiver["address"]["street"] == "Odbiorcza"
        assert receiver["address"]["flat_number"] == "10"


class TestCourierCreateLabel:
    async def test_returns_label_info(self) -> None:
        shipment = _FakeShipment(external_id="888")
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostCourierProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.get_label = AsyncMock(
                return_value=b"%PDF-1.4 courier label",
            )
            mock_client.close = AsyncMock()

            label = await provider.create_label()

        assert label["format"] == "PDF"


class TestCourierFetchStatus:
    async def test_maps_shipx_status(self) -> None:
        shipment = _FakeShipment(external_id="888")
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostCourierProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.get_shipment = AsyncMock(
                return_value={
                    "id": 888,
                    "status": "taken_by_courier",
                },
            )
            mock_client.close = AsyncMock()

            result = await provider.fetch_shipment_status()

        assert result["status"] == ShipmentStatus.IN_TRANSIT
