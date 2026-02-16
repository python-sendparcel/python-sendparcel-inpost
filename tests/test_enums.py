"""Tests for ShipX enums."""

from sendparcel_inpost.enums import ShipXParcelTemplate, ShipXService


class TestShipXService:
    def test_locker_standard(self) -> None:
        assert ShipXService.INPOST_LOCKER_STANDARD == "inpost_locker_standard"

    def test_inpost_courier_standard(self) -> None:
        assert ShipXService.INPOST_COURIER_STANDARD == "inpost_courier_standard"

    def test_is_str_enum(self) -> None:
        assert isinstance(ShipXService.INPOST_LOCKER_STANDARD, str)


class TestShipXParcelTemplate:
    def test_small(self) -> None:
        assert ShipXParcelTemplate.SMALL == "small"

    def test_medium(self) -> None:
        assert ShipXParcelTemplate.MEDIUM == "medium"

    def test_large(self) -> None:
        assert ShipXParcelTemplate.LARGE == "large"
