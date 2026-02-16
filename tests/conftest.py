"""Shared test fixtures for sendparcel-inpost."""

import pytest

from sendparcel_inpost.client import ShipXClient

SANDBOX_BASE_URL = "https://sandbox-api-shipx-pl.easypack24.net"


@pytest.fixture
def shipx_client() -> ShipXClient:
    """ShipXClient pointed at sandbox with a fake token."""
    return ShipXClient(
        token="test-token-123",
        organization_id=12345,
        sandbox=True,
    )
