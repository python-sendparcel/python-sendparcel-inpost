"""Tests for ShipX exceptions."""

from sendparcel.exceptions import CommunicationError

from sendparcel_inpost.exceptions import (
    ShipXAPIError,
    ShipXAuthenticationError,
    ShipXValidationError,
)


class TestShipXAPIError:
    def test_inherits_communication_error(self) -> None:
        err = ShipXAPIError(status_code=400, detail="bad request")
        assert isinstance(err, CommunicationError)

    def test_attributes(self) -> None:
        err = ShipXAPIError(
            status_code=422,
            detail="validation failed",
            errors=[{"field": "phone", "message": "required"}],
        )
        assert err.status_code == 422
        assert err.detail == "validation failed"
        assert err.errors == [{"field": "phone", "message": "required"}]
        assert "422" in str(err)
        assert "validation failed" in str(err)

    def test_defaults(self) -> None:
        err = ShipXAPIError(status_code=500, detail="server error")
        assert err.errors == []


class TestShipXAuthenticationError:
    def test_inherits_shipx_api_error(self) -> None:
        err = ShipXAuthenticationError()
        assert isinstance(err, ShipXAPIError)
        assert err.status_code == 401

    def test_default_message(self) -> None:
        err = ShipXAuthenticationError()
        assert "authentication" in str(err).lower() or "401" in str(err)


class TestShipXValidationError:
    def test_inherits_shipx_api_error(self) -> None:
        err = ShipXValidationError(
            errors=[{"field": "phone", "message": "required"}],
        )
        assert isinstance(err, ShipXAPIError)
        assert err.status_code == 422

    def test_carries_field_errors(self) -> None:
        errors = [
            {"field": "phone", "message": "required"},
            {"field": "email", "message": "invalid format"},
        ]
        err = ShipXValidationError(errors=errors)
        assert err.errors == errors
