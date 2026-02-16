"""Tests for InPostLockerProvider."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sendparcel.enums import ConfirmationMethod, ShipmentStatus
from sendparcel.types import AddressInfo, ParcelInfo

from sendparcel_inpost.providers.locker import InPostLockerProvider


@dataclass
class _FakeOrder:
    weight: Decimal = Decimal("1.0")

    def get_total_weight(self) -> Decimal:
        return self.weight

    def get_parcels(self) -> list[ParcelInfo]:
        return [ParcelInfo(weight_kg=self.weight)]

    def get_sender_address(self) -> AddressInfo:
        return {
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

    def get_receiver_address(self) -> AddressInfo:
        return {
            "first_name": "Anna",
            "last_name": "Odbiorca",
            "phone": "600200300",
            "email": "receiver@example.com",
        }


@dataclass
class _FakeShipment:
    id: str = "ship-1"
    order: _FakeOrder = field(default_factory=_FakeOrder)
    status: str = "new"
    provider: str = "inpost_locker"
    external_id: str = ""
    tracking_number: str = ""
    label_url: str = ""


class TestLockerProviderClassVars:
    def test_slug(self) -> None:
        assert InPostLockerProvider.slug == "inpost_locker"

    def test_display_name(self) -> None:
        assert InPostLockerProvider.display_name == "InPost Paczkomat"

    def test_supported_countries(self) -> None:
        assert "PL" in InPostLockerProvider.supported_countries

    def test_supported_services(self) -> None:
        assert (
            "inpost_locker_standard" in InPostLockerProvider.supported_services
        )

    def test_confirmation_method(self) -> None:
        assert (
            InPostLockerProvider.confirmation_method == ConfirmationMethod.PUSH
        )


class TestLockerCreateShipment:
    async def test_creates_shipment_and_returns_result(self) -> None:
        shipment = _FakeShipment()
        config = {
            "token": "test-token",
            "organization_id": 12345,
            "sandbox": True,
        }
        provider = InPostLockerProvider(shipment, config=config)

        mock_response = {
            "id": 999,
            "tracking_number": "TRACK999",
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
                target_point="KRA010",
                sending_method="dispatch_order",
            )

        assert result["external_id"] == "999"
        assert result["tracking_number"] == "TRACK999"

        # Verify the payload sent to client
        call_kwargs = mock_client.create_shipment.call_args
        payload = call_kwargs.kwargs["payload"]
        assert payload["service"] == "inpost_locker_standard"
        assert payload["custom_attributes"]["target_point"] == "KRA010"
        assert payload["parcels"][0]["template"] == "small"

    async def test_target_point_is_required(self) -> None:
        shipment = _FakeShipment()
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostLockerProvider(shipment, config=config)
        with pytest.raises(ValueError, match="target_point"):
            await provider.create_shipment()


class TestLockerCreateLabel:
    async def test_returns_label_info(self) -> None:
        shipment = _FakeShipment(external_id="999")
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostLockerProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.get_label = AsyncMock(
                return_value=b"%PDF-1.4 data",
            )
            mock_client.close = AsyncMock()

            label = await provider.create_label()

        assert label["format"] == "PDF"
        assert label["content_base64"]  # non-empty base64 string


class TestLockerFetchStatus:
    async def test_maps_shipx_status(self) -> None:
        shipment = _FakeShipment(external_id="999")
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostLockerProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.get_shipment = AsyncMock(
                return_value={"id": 999, "status": "confirmed"},
            )
            mock_client.close = AsyncMock()

            result = await provider.fetch_shipment_status()

        assert result["status"] == ShipmentStatus.LABEL_READY


class TestLockerCancelShipment:
    async def test_returns_true_on_success(self) -> None:
        shipment = _FakeShipment(external_id="999")
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostLockerProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.cancel_shipment = AsyncMock(return_value=None)
            mock_client.close = AsyncMock()

            result = await provider.cancel_shipment()

        assert result is True

    async def test_returns_false_on_api_error(self) -> None:
        from sendparcel_inpost.exceptions import ShipXAPIError

        shipment = _FakeShipment(external_id="999")
        config = {
            "token": "t",
            "organization_id": 1,
            "sandbox": True,
        }
        provider = InPostLockerProvider(shipment, config=config)

        with patch.object(
            provider,
            "_get_client",
            return_value=AsyncMock(),
        ) as mock_get_client:
            mock_client = mock_get_client.return_value
            mock_client.cancel_shipment = AsyncMock(
                side_effect=ShipXAPIError(
                    status_code=400,
                    detail="Cannot cancel",
                ),
            )
            mock_client.close = AsyncMock()

            result = await provider.cancel_shipment()

        assert result is False


class TestLockerVerifyCallback:
    async def test_valid_ip_passes(self) -> None:
        shipment = _FakeShipment()
        provider = InPostLockerProvider(shipment, config={})
        await provider.verify_callback(
            data={},
            headers={"x-forwarded-for": "91.216.25.10"},
        )

    async def test_invalid_ip_raises(self) -> None:
        from sendparcel.exceptions import InvalidCallbackError

        shipment = _FakeShipment()
        provider = InPostLockerProvider(shipment, config={})
        with pytest.raises(InvalidCallbackError):
            await provider.verify_callback(
                data={},
                headers={"x-forwarded-for": "1.2.3.4"},
            )

    async def test_missing_ip_raises(self) -> None:
        from sendparcel.exceptions import InvalidCallbackError

        shipment = _FakeShipment()
        provider = InPostLockerProvider(shipment, config={})
        with pytest.raises(InvalidCallbackError):
            await provider.verify_callback(data={}, headers={})


class TestLockerHandleCallback:
    async def test_extracts_status(self) -> None:
        shipment = _FakeShipment()
        provider = InPostLockerProvider(shipment, config={})
        await provider.handle_callback(
            data={
                "payload": {
                    "shipment_id": 999,
                    "status": "confirmed",
                    "tracking_number": "TRACK999",
                },
            },
            headers={},
        )
        # handle_callback should not raise; status resolution
        # is the flow's responsibility


class TestLockerAddressConversion:
    def test_converts_address_info_to_shipx_peer(self) -> None:
        shipment = _FakeShipment()
        provider = InPostLockerProvider(shipment, config={})
        addr: AddressInfo = {
            "first_name": "Jan",
            "last_name": "Kowalski",
            "phone": "500100200",
            "email": "jan@example.com",
            "street": "Marszalkowska",
            "building_number": "1",
            "city": "Warszawa",
            "postal_code": "00-001",
            "country_code": "PL",
        }
        peer = provider._address_to_peer(addr)
        assert peer["first_name"] == "Jan"
        assert peer["last_name"] == "Kowalski"
        assert peer["phone"] == "500100200"
        assert peer["address"]["street"] == "Marszalkowska"
        assert peer["address"]["post_code"] == "00-001"

    def test_converts_legacy_name_to_first_last(self) -> None:
        shipment = _FakeShipment()
        provider = InPostLockerProvider(shipment, config={})
        addr: AddressInfo = {
            "name": "Jan Kowalski",
            "phone": "500100200",
            "email": "jan@example.com",
            "line1": "Marszalkowska 1",
            "city": "Warszawa",
            "postal_code": "00-001",
            "country_code": "PL",
        }
        peer = provider._address_to_peer(addr)
        assert peer["first_name"] == "Jan"
        assert peer["last_name"] == "Kowalski"
        assert peer["address"]["street"] == "Marszalkowska 1"
