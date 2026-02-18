"""InPost Locker (Paczkomat) provider."""

import base64
import ipaddress
import logging
from typing import Any, ClassVar

from sendparcel.enums import ConfirmationMethod, LabelFormat
from sendparcel.exceptions import InvalidCallbackError
from sendparcel.provider import (
    BaseProvider,
    CancellableProvider,
    LabelProvider,
    PullStatusProvider,
    PushCallbackProvider,
)
from sendparcel.types import (
    AddressInfo,
    LabelInfo,
    ParcelInfo,
    ShipmentCreateResult,
    ShipmentStatusResponse,
)

from sendparcel_inpost.client import ShipXClient
from sendparcel_inpost.exceptions import ShipXAPIError
from sendparcel_inpost.status_mapping import map_shipx_status
from sendparcel_inpost.types import ShipXAddress, ShipXPeer

logger = logging.getLogger(__name__)

INPOST_WEBHOOK_NETWORK = ipaddress.ip_network("91.216.25.0/24")


class InPostLockerProvider(
    BaseProvider,
    LabelProvider,
    PushCallbackProvider,
    PullStatusProvider,
    CancellableProvider,
):
    """InPost Paczkomat locker delivery provider."""

    slug: ClassVar[str] = "inpost_locker"
    display_name: ClassVar[str] = "InPost Paczkomat"
    supported_countries: ClassVar[list[str]] = ["PL"]
    supported_services: ClassVar[list[str]] = [
        "inpost_locker_standard",
    ]
    confirmation_method: ClassVar[ConfirmationMethod] = ConfirmationMethod.PUSH
    user_selectable: ClassVar[bool] = True
    config_schema: ClassVar[dict[str, Any]] = {
        "token": {
            "type": "str",
            "required": True,
            "secret": True,
            "description": "ShipX API bearer token",
        },
        "organization_id": {
            "type": "int",
            "required": True,
            "secret": False,
            "description": "ShipX organization ID",
        },
        "sandbox": {
            "type": "bool",
            "required": False,
            "secret": False,
            "description": "Use sandbox environment",
            "default": False,
        },
        "base_url": {
            "type": "str",
            "required": False,
            "secret": False,
            "description": "Custom API base URL (overrides sandbox flag)",
        },
        "timeout": {
            "type": "float",
            "required": False,
            "secret": False,
            "description": "HTTP request timeout in seconds",
            "default": 30.0,
        },
    }

    def _get_client(self) -> ShipXClient:
        """Build a ShipXClient from provider config."""
        return ShipXClient(
            token=self.get_setting("token", ""),
            organization_id=self.get_setting("organization_id", 0),
            sandbox=self.get_setting("sandbox", False),
            base_url=self.get_setting("base_url"),
            timeout=self.get_setting("timeout", 30.0),
        )

    def _address_to_peer(self, addr: AddressInfo) -> ShipXPeer:
        """Convert sendparcel AddressInfo to ShipX peer dict."""
        first_name = addr.get("first_name", "")
        last_name = addr.get("last_name", "")

        if not first_name and not last_name:
            name = addr.get("name", "")
            parts = name.split(None, 1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""

        peer: ShipXPeer = {}
        if first_name:
            peer["first_name"] = first_name
        if last_name:
            peer["last_name"] = last_name

        company = addr.get("company", "")
        if company:
            peer["company_name"] = company

        phone = addr.get("phone", "")
        if phone:
            peer["phone"] = phone

        email = addr.get("email", "")
        if email:
            peer["email"] = email

        street = addr.get("street", "") or addr.get("line1", "")
        building_number = addr.get("building_number", "")
        city = addr.get("city", "")
        postal_code = addr.get("postal_code", "")
        country_code = addr.get("country_code", "")

        if street or city:
            shipx_addr: ShipXAddress = {}
            if street:
                shipx_addr["street"] = street
            if building_number:
                shipx_addr["building_number"] = building_number
            flat_number = addr.get("flat_number", "")
            if flat_number:
                shipx_addr["flat_number"] = flat_number
            if city:
                shipx_addr["city"] = city
            if postal_code:
                shipx_addr["post_code"] = postal_code
            if country_code:
                shipx_addr["country_code"] = country_code
            peer["address"] = shipx_addr

        return peer

    def _parcel_template_from_parcels(self, parcels: list[ParcelInfo]) -> str:
        """Determine locker parcel template from parcels.

        For locker shipments, defaults to 'small' if dimensions
        don't clearly indicate a larger size.
        """
        if not parcels:
            return "small"

        parcel = parcels[0]
        height_cm = float(parcel.get("height_cm", 0))

        if height_cm > 19:
            return "large"
        if height_cm > 8:
            return "medium"
        return "small"

    async def create_shipment(
        self,
        *,
        sender_address: AddressInfo,
        receiver_address: AddressInfo,
        parcels: list[ParcelInfo],
        **kwargs: Any,
    ) -> ShipmentCreateResult:
        """Create an InPost locker shipment.

        Required kwargs:
            target_point: Locker machine ID (e.g. "KRA010")

        Optional kwargs:
            sending_method: How to dispatch (default "dispatch_order")
            parcel_template: Override parcel size ("small"/"medium"/"large")
        """
        target_point = kwargs.get("target_point")
        if not target_point:
            raise ValueError("target_point is required for locker shipments")

        sending_method = kwargs.get("sending_method", "dispatch_order")
        template = kwargs.get(
            "parcel_template",
            self._parcel_template_from_parcels(parcels),
        )

        receiver_peer = self._address_to_peer(receiver_address)

        payload = {
            "receiver": dict(receiver_peer),
            "parcels": [{"template": template}],
            "service": "inpost_locker_standard",
            "custom_attributes": {
                "target_point": target_point,
                "sending_method": sending_method,
            },
        }

        sender_peer = self._address_to_peer(sender_address)
        if sender_peer:
            payload["sender"] = dict(sender_peer)

        client = self._get_client()
        try:
            response = await client.create_shipment(payload=payload)
        finally:
            await client.close()

        return ShipmentCreateResult(
            external_id=str(response["id"]),
            tracking_number=response.get("tracking_number", ""),
        )

    async def create_label(self, **kwargs: Any) -> LabelInfo:
        """Fetch label PDF for the shipment."""
        shipment_id = int(self.shipment.external_id)
        label_format = kwargs.get("label_format", "Pdf")

        client = self._get_client()
        try:
            content = await client.get_label(
                shipment_id=shipment_id,
                label_format=label_format,
            )
        finally:
            await client.close()

        format_value: LabelFormat = (
            LabelFormat.PDF
            if label_format == "Pdf"
            else LabelFormat(label_format)
        )
        return LabelInfo(
            format=format_value,
            content_base64=base64.b64encode(content).decode("ascii"),
        )

    async def verify_callback(
        self,
        data: dict[str, Any],
        headers: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Verify InPost webhook by source IP."""
        ip_str = headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip_str:
            raise InvalidCallbackError("Missing source IP in webhook request")
        try:
            ip_addr = ipaddress.ip_address(ip_str)
        except ValueError as exc:
            raise InvalidCallbackError(f"Invalid source IP: {ip_str}") from exc

        if ip_addr not in INPOST_WEBHOOK_NETWORK:
            raise InvalidCallbackError(
                f"Source IP {ip_str} not in InPost webhook range"
            )

    async def handle_callback(
        self,
        data: dict[str, Any],
        headers: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Process InPost webhook payload.

        The actual FSM transition is handled by ShipmentFlow.
        This method extracts and normalizes the status.
        """
        payload = data.get("payload", {})
        shipx_status = payload.get("status", "")
        sendparcel_status = map_shipx_status(shipx_status)
        if sendparcel_status:
            logger.info(
                "InPost webhook: %s -> %s (shipment %s)",
                shipx_status,
                sendparcel_status,
                payload.get("shipment_id"),
            )

    async def fetch_shipment_status(
        self,
        **kwargs: Any,
    ) -> ShipmentStatusResponse:
        """Fetch current status from ShipX API."""
        shipment_id = int(self.shipment.external_id)

        client = self._get_client()
        try:
            response = await client.get_shipment(shipment_id=shipment_id)
        finally:
            await client.close()

        shipx_status = response.get("status", "")
        sendparcel_status = map_shipx_status(shipx_status)

        return ShipmentStatusResponse(
            status=sendparcel_status.value if sendparcel_status else None,
        )

    async def cancel_shipment(self, **kwargs: Any) -> bool:
        """Cancel shipment via ShipX API."""
        shipment_id = int(self.shipment.external_id)

        client = self._get_client()
        try:
            await client.cancel_shipment(shipment_id=shipment_id)
            return True
        except ShipXAPIError:
            return False
        finally:
            await client.close()
