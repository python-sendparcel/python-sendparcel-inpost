"""ShipX API async HTTP client."""

from typing import Any
from types import TracebackType

import httpx

from sendparcel_inpost.exceptions import (
    ShipXAPIError,
    ShipXAuthenticationError,
    ShipXValidationError,
)

PRODUCTION_BASE_URL = "https://api-shipx-pl.easypack24.net"
SANDBOX_BASE_URL = "https://sandbox-api-shipx-pl.easypack24.net"

DEFAULT_TIMEOUT = 30.0


class ShipXClient:
    """Async HTTP client for InPost ShipX API.

    Can be used standalone (independent of sendparcel providers).

    Usage::

        async with ShipXClient(token="...", organization_id=123) as client:
            result = await client.create_shipment(payload={...})
    """

    def __init__(
        self,
        token: str,
        organization_id: int,
        *,
        sandbox: bool = False,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if base_url is not None:
            self.base_url = base_url
        elif sandbox:
            self.base_url = SANDBOX_BASE_URL
        else:
            self.base_url = PRODUCTION_BASE_URL
        self.organization_id = organization_id
        self.timeout = timeout
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def __aenter__(self) -> "ShipXClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def create_shipment(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a shipment via simplified flow.

        POST /v1/organizations/{org_id}/shipments
        """
        url = f"/v1/organizations/{self.organization_id}/shipments"
        response = await self._http.post(url, json=payload)
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    async def get_shipment(self, shipment_id: int) -> dict[str, Any]:
        """Fetch shipment details.

        GET /v1/shipments/{shipment_id}
        """
        response = await self._http.get(f"/v1/shipments/{shipment_id}")
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    async def get_label(
        self,
        shipment_id: int,
        *,
        label_format: str = "Pdf",
        label_type: str = "normal",
    ) -> bytes:
        """Fetch shipping label as binary content.

        GET /v1/shipments/{shipment_id}/label?format=...&type=...
        """
        response = await self._http.get(
            f"/v1/shipments/{shipment_id}/label",
            params={"format": label_format, "type": label_type},
        )
        self._raise_for_status(response)
        return response.content

    async def cancel_shipment(self, shipment_id: int) -> None:
        """Cancel a shipment.

        DELETE /v1/shipments/{shipment_id}
        """
        response = await self._http.delete(f"/v1/shipments/{shipment_id}")
        self._raise_for_status(response)

    async def get_tracking(self, tracking_number: str) -> dict[str, Any]:
        """Fetch public tracking data (no auth required).

        GET /v1/tracking/{tracking_number}
        """
        response = await self._http.get(f"/v1/tracking/{tracking_number}")
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    async def get_statuses(self, lang: str = "pl") -> list[dict[str, Any]]:
        """Fetch list of all ShipX statuses.

        GET /v1/statuses
        """
        response = await self._http.get(
            "/v1/statuses",
            params={"lang": lang},
        )
        self._raise_for_status(response)
        result: list[dict[str, Any]] = response.json()
        return result

    async def get_services(self) -> list[dict[str, Any]]:
        """Fetch list of all ShipX services.

        GET /v1/services
        """
        response = await self._http.get("/v1/services")
        self._raise_for_status(response)
        result: list[dict[str, Any]] = response.json()
        return result

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise ShipXAPIError subclasses for non-2xx responses."""
        if response.is_success:
            return

        try:
            body = response.json()
        except Exception:
            body = {}

        detail = body.get("message") or body.get("error") or response.text
        errors = body.get("details", [])
        status_code = response.status_code

        if status_code == 401:
            raise ShipXAuthenticationError(detail=str(detail))
        if status_code == 422:
            raise ShipXValidationError(
                detail=str(detail),
                errors=errors,
            )
        raise ShipXAPIError(
            status_code=status_code,
            detail=str(detail),
            errors=errors,
        )
