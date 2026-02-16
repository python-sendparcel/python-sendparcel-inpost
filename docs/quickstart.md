# Quickstart

## Installation

Install `python-sendparcel-inpost` using your preferred package manager:

**Using uv:**

```bash
uv add python-sendparcel-inpost
```

**Using pip:**

```bash
pip install python-sendparcel-inpost
```

Both providers are auto-discovered via the `sendparcel.providers` entry-point
group. No manual registration is needed.

## Basic setup

### 1. Create a shipment via ShipmentFlow

The recommended way to use InPost providers is through the `ShipmentFlow`
orchestrator. Pass InPost credentials in the provider config:

```python
import anyio
from sendparcel import ShipmentFlow


async def main():
    repo = MyShipmentRepository()
    flow = ShipmentFlow(
        repository=repo,
        config={
            "inpost_locker": {
                "token": "your-shipx-api-token",
                "organization_id": 12345,
                "sandbox": True,
            },
        },
    )

    order = MyOrder(...)
    shipment = await flow.create_shipment(
        order,
        provider_slug="inpost_locker",
        target_point="KRA010",
    )
    print(shipment.tracking_number)


anyio.run(main)
```

### 2. Locker shipment (direct provider usage)

```python
from sendparcel_inpost import InPostLockerProvider

provider = InPostLockerProvider(shipment=shipment, config={
    "token": "your-shipx-api-token",
    "organization_id": 12345,
    "sandbox": True,
})

result = await provider.create_shipment(
    target_point="KRA010",       # required: locker machine ID
    parcel_template="small",     # optional: "small", "medium", "large"
)
```

The `target_point` parameter is required for locker shipments — it identifies
the Paczkomat machine where the receiver will pick up the parcel.

### 3. Courier shipment (direct provider usage)

```python
from sendparcel_inpost import InPostCourierProvider

provider = InPostCourierProvider(shipment=shipment, config={
    "token": "your-shipx-api-token",
    "organization_id": 12345,
    "sandbox": True,
})

result = await provider.create_shipment()
```

Parcel dimensions are taken from `shipment.order.get_parcels()` and converted
from cm to mm for the ShipX API automatically.

### 4. Standalone ShipXClient

The HTTP client can be used independently of the sendparcel framework:

```python
from sendparcel_inpost import ShipXClient

async with ShipXClient(
    token="your-token",
    organization_id=12345,
    sandbox=True,
) as client:
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

    label_pdf = await client.get_label(result["id"])
    tracking = await client.get_tracking("6100123456789")
```

## Framework integration

### Django

```python
# settings.py
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
```

### FastAPI / Litestar

```python
from fastapi_sendparcel import SendparcelConfig  # or litestar_sendparcel

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

## Next steps

- {doc}`configuration` — full configuration and provider reference
- {doc}`api` — API module documentation
