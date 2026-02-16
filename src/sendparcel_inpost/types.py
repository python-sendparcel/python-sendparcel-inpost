"""ShipX-specific type definitions."""

from typing import TypedDict


class ShipXAddress(TypedDict, total=False):
    """ShipX address structure."""

    street: str
    building_number: str
    flat_number: str
    city: str
    post_code: str
    country_code: str


class ShipXPeer(TypedDict, total=False):
    """ShipX sender/receiver peer."""

    first_name: str
    last_name: str
    company_name: str
    phone: str
    email: str
    address: ShipXAddress


class _ShipXDimensions(TypedDict, total=False):
    """Parcel dimensions."""

    length: float
    width: float
    height: float
    unit: str


class _ShipXWeight(TypedDict, total=False):
    """Parcel weight."""

    amount: float
    unit: str


class ShipXParcel(TypedDict, total=False):
    """ShipX parcel definition."""

    template: str
    dimensions: _ShipXDimensions
    weight: _ShipXWeight


class _ShipXCustomAttributes(TypedDict, total=False):
    """ShipX shipment custom attributes."""

    target_point: str
    sending_method: str
    dropoff_point: str


class ShipXShipmentPayload(TypedDict, total=False):
    """Payload for ShipX create shipment endpoint."""

    receiver: ShipXPeer
    sender: ShipXPeer
    parcels: list[ShipXParcel]
    service: str
    custom_attributes: _ShipXCustomAttributes
    reference: str
    comments: str
    insurance: dict
    cod: dict
    additional_services: list[str]
