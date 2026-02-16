"""Tests for ShipX type definitions."""

from sendparcel_inpost.types import (
    ShipXAddress,
    ShipXParcel,
    ShipXPeer,
    ShipXShipmentPayload,
)


class TestShipXPeer:
    def test_minimal_peer(self) -> None:
        peer: ShipXPeer = {
            "phone": "500100200",
            "email": "jan@example.com",
        }
        assert peer["phone"] == "500100200"

    def test_full_peer(self) -> None:
        peer: ShipXPeer = {
            "first_name": "Jan",
            "last_name": "Kowalski",
            "company_name": "Firma Sp. z o.o.",
            "phone": "500100200",
            "email": "jan@example.com",
            "address": {
                "street": "Marszalkowska",
                "building_number": "1",
                "city": "Warszawa",
                "post_code": "00-001",
                "country_code": "PL",
            },
        }
        assert peer["first_name"] == "Jan"
        assert peer["address"]["street"] == "Marszalkowska"


class TestShipXAddress:
    def test_address_fields(self) -> None:
        addr: ShipXAddress = {
            "street": "Marszalkowska",
            "building_number": "1",
            "city": "Warszawa",
            "post_code": "00-001",
            "country_code": "PL",
        }
        assert addr["post_code"] == "00-001"

    def test_optional_flat_number(self) -> None:
        addr: ShipXAddress = {
            "street": "Marszalkowska",
            "building_number": "1",
            "city": "Warszawa",
            "post_code": "00-001",
            "country_code": "PL",
            "flat_number": "10",
        }
        assert addr["flat_number"] == "10"


class TestShipXParcel:
    def test_template_parcel(self) -> None:
        parcel: ShipXParcel = {"template": "small"}
        assert parcel["template"] == "small"

    def test_dimensioned_parcel(self) -> None:
        parcel: ShipXParcel = {
            "dimensions": {
                "length": 200,
                "width": 300,
                "height": 150,
                "unit": "mm",
            },
            "weight": {"amount": 5.0, "unit": "kg"},
        }
        assert parcel["dimensions"]["length"] == 200


class TestShipXShipmentPayload:
    def test_locker_payload(self) -> None:
        payload: ShipXShipmentPayload = {
            "receiver": {
                "phone": "500100200",
                "email": "jan@example.com",
            },
            "parcels": [{"template": "small"}],
            "service": "inpost_locker_standard",
            "custom_attributes": {
                "target_point": "KRA010",
                "sending_method": "dispatch_order",
            },
        }
        assert payload["service"] == "inpost_locker_standard"
        assert payload["custom_attributes"]["target_point"] == "KRA010"
