# python-sendparcel-inpost

[![PyPI](https://img.shields.io/pypi/v/python-sendparcel-inpost.svg)](https://pypi.org/project/python-sendparcel-inpost/)
[![Python Version](https://img.shields.io/pypi/pyversions/python-sendparcel-inpost.svg)](https://pypi.org/project/python-sendparcel-inpost/)
[![License](https://img.shields.io/pypi/l/python-sendparcel-inpost.svg)](https://github.com/python-sendparcel/python-sendparcel-inpost/blob/main/LICENSE)

InPost ShipX API provider for the [python-sendparcel](https://github.com/python-sendparcel/python-sendparcel) shipping ecosystem.

> **Alpha (0.1.0)** — API may change between minor releases. Pin your dependency if you use it in production.

## Features

- **Two providers** — `InPostLockerProvider` (Paczkomat locker) and `InPostCourierProvider` (door-to-door courier) as separate `BaseProvider` subclasses.
- **Standalone ShipX client** — `ShipXClient` async HTTP wrapper usable independently of the sendparcel framework.
- **Auto-discovery** — both providers register via the `sendparcel.providers` entry-point group; no manual registration needed.
- **Status mapping** — 24 ShipX statuses mapped to 8 sendparcel lifecycle states.
- **Webhook support** — callback verification by InPost source IP range (`91.216.25.0/24`).
- **Address conversion** — automatic conversion between sendparcel `AddressInfo` and ShipX peer format, with legacy name-splitting fallback.
- **Structured error handling** — `ShipXAPIError` hierarchy inheriting from core `CommunicationError` with status codes and validation details.
- **Async-first** — fully asynchronous with `httpx` and `anyio`.

## Installation

```bash
uv add python-sendparcel-inpost
```

Or with pip:

```bash
pip install python-sendparcel-inpost
```

Both providers are auto-discovered via the `sendparcel.providers` entry-point group — no manual registration needed.

## Quick Start

### Using providers through sendparcel

The providers integrate with the `sendparcel` flow automatically:

```python
from sendparcel.registry import PluginRegistry

# Providers are discovered via entry points
registry = PluginRegistry()
choices = registry.get_choices()
# [('inpost_locker', 'InPost Paczkomat'), ('inpost_courier', 'InPost Kurier'), ...]
```

### Creating a locker shipment

```python
provider = InPostLockerProvider(shipment=shipment, config={
    "token": "your-shipx-api-token",
    "organization_id": 12345,
    "sandbox": True,  # use sandbox for testing
})

result = await provider.create_shipment(
    target_point="KRA010",       # required: locker machine ID
    parcel_template="small",     # optional: "small", "medium", "large"
    sending_method="dispatch_order",  # optional
)
# result["external_id"] = "123456789"
# result["tracking_number"] = "6100..."
```

### Creating a courier shipment

```python
provider = InPostCourierProvider(shipment=shipment, config={
    "token": "your-shipx-api-token",
    "organization_id": 12345,
    "sandbox": True,
})

result = await provider.create_shipment()
# Parcels are passed as explicit parameters to create_shipment()
# Dimensions are converted from cm to mm automatically
```

### Using ShipXClient standalone

The HTTP client can be used independently of the sendparcel framework:

```python
from sendparcel_inpost import ShipXClient

async with ShipXClient(
    token="your-token",
    organization_id=12345,
    sandbox=True,
) as client:
    # Create shipment
    result = await client.create_shipment(payload={
        "receiver": {
            "first_name": "Jan",
            "last_name": "Kowalski",
            "phone": "500100200",
            "email": "jan@example.com",
        },
        "parcels": [{"template": "small"}],
        "service": "inpost_locker_standard",
        "custom_attributes": {
            "target_point": "KRA010",
            "sending_method": "dispatch_order",
        },
    })

    # Get shipment details
    shipment = await client.get_shipment(result["id"])

    # Download label
    label_pdf = await client.get_label(result["id"])

    # Track (public, no auth required)
    tracking = await client.get_tracking("6100123456789")

    # Cancel (only for created/offers_prepared/offer_selected statuses)
    await client.cancel_shipment(result["id"])
```

## Configuration

Provider configuration is passed as a dict either through the `config` constructor parameter or via your framework adapter's settings:

| Key | Type | Default | Description |
|---|---|---|---|
| `token` | `str` | *(required)* | ShipX API bearer token |
| `organization_id` | `int` | *(required)* | ShipX organization ID |
| `sandbox` | `bool` | `False` | Use sandbox API endpoint |
| `base_url` | `str` | `None` | Override API base URL (takes precedence over `sandbox`) |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds |

### API endpoints

| Environment | Base URL |
|---|---|
| Production | `https://api-shipx-pl.easypack24.net` |
| Sandbox | `https://sandbox-api-shipx-pl.easypack24.net` |

### Integration with framework adapters

Pass InPost configuration through your adapter's provider settings:

```python
# Django settings.py
SENDPARCEL_PROVIDER_SETTINGS = {
    "inpost_locker": {
        "token": "your-shipx-token",
        "organization_id": 12345,
        "sandbox": True,
    },
    "inpost_courier": {
        "token": "your-shipx-token",
        "organization_id": 12345,
        "sandbox": True,
    },
}

# FastAPI / Litestar
config = SendparcelConfig(
    default_provider="inpost_locker",
    providers={
        "inpost_locker": {
            "token": "your-shipx-token",
            "organization_id": 12345,
            "sandbox": True,
        },
    },
)
```

## Providers

### InPostLockerProvider

Paczkomat locker delivery. The receiver picks up the parcel from a self-service locker machine.

- **Slug**: `inpost_locker`
- **Service**: `inpost_locker_standard`
- **Confirmation method**: PUSH (webhook-based)
- **Supported countries**: PL

**`create_shipment` parameters:**

| Parameter | Required | Description |
|---|---|---|
| `target_point` | yes | Locker machine ID (e.g. `"KRA010"`) |
| `parcel_template` | no | Size: `"small"`, `"medium"`, or `"large"`. Auto-detected from parcel dimensions if omitted. |
| `sending_method` | no | Default: `"dispatch_order"` |

Parcel template auto-detection logic (based on height):
- height > 19 cm: `large`
- height > 8 cm: `medium`
- otherwise: `small`

### InPostCourierProvider

Door-to-door courier delivery.

- **Slug**: `inpost_courier`
- **Service**: `inpost_courier_standard`
- **Confirmation method**: PUSH (webhook-based)
- **Supported countries**: PL

Parcel dimensions are received as explicit `parcels` parameter and converted from cm to mm for the ShipX API. If no parcels are provided, a default 1 kg parcel is used.

### Common provider methods

Both providers implement the full `BaseProvider` interface:

| Method | Purpose |
|---|---|
| `create_shipment(**kwargs)` | Create a shipment in ShipX |
| `create_label(**kwargs)` | Download shipping label (PDF by default) |
| `fetch_shipment_status(**kwargs)` | Poll ShipX API for current status |
| `cancel_shipment(**kwargs)` | Cancel the shipment (returns `True`/`False`) |
| `verify_callback(data, headers, **kwargs)` | Verify webhook source IP is in InPost's `91.216.25.0/24` range |
| `handle_callback(data, headers, **kwargs)` | Process webhook payload, map ShipX status to sendparcel status |

## Address Handling

The providers accept `sendparcel.types.AddressInfo` and convert it to the ShipX peer format. Two addressing styles are supported:

**InPost-style** (preferred):
```python
address: AddressInfo = {
    "first_name": "Jan",
    "last_name": "Kowalski",
    "street": "Krakowska",
    "building_number": "10",
    "flat_number": "5",
    "city": "Krakow",
    "postal_code": "30-001",
    "country_code": "PL",
    "phone": "500100200",
    "email": "jan@example.com",
}
```

**Legacy style** (auto-split):
```python
address: AddressInfo = {
    "name": "Jan Kowalski",     # split on first space -> first_name + last_name
    "line1": "Krakowska 10/5",  # used as street fallback
    "city": "Krakow",
    "postal_code": "30-001",
    "phone": "500100200",
}
```

## Status Mapping

ShipX uses 24 internal statuses. These are mapped to 8 sendparcel statuses:

| sendparcel status | ShipX statuses |
|---|---|
| `CREATED` | `created`, `offers_prepared`, `offer_selected` |
| `LABEL_READY` | `confirmed` |
| `IN_TRANSIT` | `dispatched_by_sender`, `collected_from_sender`, `taken_by_courier`, `adopted_at_source_branch`, `sent_from_source_branch`, `adopted_at_sorting_center` |
| `OUT_FOR_DELIVERY` | `out_for_delivery`, `ready_to_pickup`, `pickup_reminder_sent`, `avizo`, `stack_in_box_machine`, `stack_in_customer_service_point` |
| `DELIVERED` | `delivered` |
| `CANCELLED` | `canceled` |
| `RETURNED` | `returned_to_sender` |
| `FAILED` | `rejected_by_receiver`, `undelivered`, `oversized`, `missing`, `claim_created` |

## Error Handling

All ShipX API errors inherit from `sendparcel.exceptions.CommunicationError`:

```python
from sendparcel_inpost.exceptions import (
    ShipXAPIError,              # base: any non-2xx response
    ShipXAuthenticationError,   # 401 Unauthorized
    ShipXValidationError,       # 422 Unprocessable Entity
)

try:
    result = await client.create_shipment(payload=payload)
except ShipXAuthenticationError:
    # Invalid or expired token
    ...
except ShipXValidationError as exc:
    # Payload validation failed
    print(exc.detail)   # human-readable message
    print(exc.errors)   # list of field-level error dicts from ShipX
except ShipXAPIError as exc:
    # Other API error
    print(exc.status_code, exc.detail)
```

## Webhooks

Both providers support InPost webhook callbacks for real-time status updates.

**Verification**: Webhook source IP must be in the `91.216.25.0/24` range. The IP is read from the `X-Forwarded-For` header (first entry). Invalid or missing IPs raise `sendparcel.exceptions.InvalidCallbackError`.

**Payload format** (expected from InPost):
```json
{
  "payload": {
    "shipment_id": 123456,
    "status": "delivered"
  }
}
```

## Supported Versions

| Dependency | Version |
|---|---|
| Python | >= 3.12 |
| python-sendparcel | >= 0.1.0 |
| httpx | >= 0.27.0 |
| anyio | >= 4.0 |

## Running Tests

The test suite uses **pytest** with **pytest-asyncio** (`asyncio_mode = "auto"`)
and **respx** for HTTP mocking.

```bash
# Install dev dependencies
uv sync --extra dev

# Run the full test suite
uv run pytest

# With coverage
uv run pytest --cov=sendparcel_inpost --cov-report=term-missing
```

## Credits

- **Author**: Dominik Kozaczko ([dominik@kozaczko.info](mailto:dominik@kozaczko.info))
- Built on top of [python-sendparcel](https://github.com/python-sendparcel/python-sendparcel) core library
- Integrates with the [InPost ShipX API](https://docs.inpost24.com/)

## License

[MIT](https://github.com/python-sendparcel/python-sendparcel-inpost/blob/main/LICENSE)
