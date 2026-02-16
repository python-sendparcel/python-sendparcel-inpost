"""ShipX-specific enumerations."""

from enum import StrEnum


class ShipXService(StrEnum):
    """ShipX shipment service types."""

    INPOST_LOCKER_STANDARD = "inpost_locker_standard"
    INPOST_COURIER_STANDARD = "inpost_courier_standard"


class ShipXParcelTemplate(StrEnum):
    """Locker parcel size templates."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
