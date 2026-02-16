"""ShipX provider exceptions."""

from sendparcel.exceptions import CommunicationError


class ShipXAPIError(CommunicationError):
    """ShipX API returned an error response."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        errors: list[dict] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.errors = errors or []
        super().__init__(
            f"ShipX API error {status_code}: {detail}",
            context={
                "status_code": status_code,
                "detail": detail,
                "errors": self.errors,
            },
        )


class ShipXAuthenticationError(ShipXAPIError):
    """ShipX API authentication failed (401)."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(status_code=401, detail=detail)


class ShipXValidationError(ShipXAPIError):
    """ShipX API validation error (422)."""

    def __init__(
        self,
        detail: str = "Validation failed",
        errors: list[dict] | None = None,
    ) -> None:
        super().__init__(status_code=422, detail=detail, errors=errors)
