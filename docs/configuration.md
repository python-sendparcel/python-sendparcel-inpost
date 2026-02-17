# Configuration

## Provider settings

Both `InPostLockerProvider` and `InPostCourierProvider` read their configuration
from the dict passed as `config` to the provider constructor (or through your
framework adapter's settings).

| Key | Type | Default | Description |
|---|---|---|---|
| `token` | `str` | *(required)* | ShipX API bearer token |
| `organization_id` | `int` | *(required)* | ShipX organization ID |
| `sandbox` | `bool` | `False` | Use sandbox API endpoint |
| `base_url` | `str` | `None` | Override API base URL (takes precedence over `sandbox`) |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds |

Settings are accessed inside the provider via `self.get_setting("token")`.

### API endpoints

| Environment | Base URL |
|---|---|
| Production | `https://api-shipx-pl.easypack24.net` |
| Sandbox | `https://sandbox-api-shipx-pl.easypack24.net` |

When `base_url` is set explicitly, it takes precedence over the `sandbox` flag.

## Providers

### InPostLockerProvider

Paczkomat locker delivery. The receiver picks up the parcel from a self-service
locker machine.

| Attribute | Value |
|---|---|
| slug | `inpost_locker` |
| display_name | `InPost Paczkomat` |
| service | `inpost_locker_standard` |
| confirmation_method | `PUSH` |
| supported_countries | `PL` |

#### `create_shipment` parameters

| Parameter | Required | Description |
|---|---|---|
| `target_point` | yes | Locker machine ID (e.g. `"KRA010"`) |
| `parcel_template` | no | Size: `"small"`, `"medium"`, or `"large"`. Auto-detected from parcel dimensions if omitted. |
| `sending_method` | no | Default: `"dispatch_order"` |

Parcel template auto-detection (based on parcel height):

- height > 19 cm: `large`
- height > 8 cm: `medium`
- otherwise: `small`

### InPostCourierProvider

Door-to-door courier delivery.

| Attribute | Value |
|---|---|
| slug | `inpost_courier` |
| display_name | `InPost Kurier` |
| service | `inpost_courier_standard` |
| confirmation_method | `PUSH` |
| supported_countries | `PL` |

#### `create_shipment` parameters

No required parameters beyond the shipment context. Parcel dimensions are
received as the explicit `parcels` parameter and converted from cm to mm.
If no parcels are provided, a default 1 kg parcel is used.

### Common provider methods

Both providers implement the full `BaseProvider` interface:

| Method | Description |
|---|---|
| `create_shipment(**kwargs)` | Create a shipment in ShipX |
| `create_label(**kwargs)` | Download shipping label (PDF by default) |
| `fetch_shipment_status(**kwargs)` | Poll ShipX API for current status |
| `cancel_shipment(**kwargs)` | Cancel the shipment (returns `True`/`False`) |
| `verify_callback(data, headers, **kwargs)` | Verify webhook source IP |
| `handle_callback(data, headers, **kwargs)` | Process webhook payload |

## ShipXClient

The standalone async HTTP client can be used independently of the sendparcel
framework. It wraps the ShipX REST API with typed methods.

```python
from sendparcel_inpost import ShipXClient

client = ShipXClient(
    token="your-token",
    organization_id=12345,
    sandbox=True,           # optional
    base_url=None,          # optional override
    timeout=30.0,           # optional
)
```

### Client methods

| Method | HTTP | Path | Returns |
|---|---|---|---|
| `create_shipment(payload)` | `POST` | `/v1/organizations/{org_id}/shipments` | `dict` |
| `get_shipment(shipment_id)` | `GET` | `/v1/shipments/{id}` | `dict` |
| `get_label(shipment_id, *, label_format, label_type)` | `GET` | `/v1/shipments/{id}/label` | `bytes` |
| `cancel_shipment(shipment_id)` | `DELETE` | `/v1/shipments/{id}` | `None` |
| `get_tracking(tracking_number)` | `GET` | `/v1/tracking/{number}` | `dict` |
| `get_statuses(lang)` | `GET` | `/v1/statuses` | `list[dict]` |
| `get_services()` | `GET` | `/v1/services` | `list[dict]` |

The client supports async context manager usage:

```python
async with ShipXClient(token="...", organization_id=123) as client:
    result = await client.create_shipment(payload={...})
```

## Address handling

The providers accept `sendparcel.types.AddressInfo` and convert it to the ShipX
peer format. Two addressing styles are supported:

### InPost-style (preferred)

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

### Legacy style (auto-split)

```python
address: AddressInfo = {
    "name": "Jan Kowalski",     # split on first space -> first_name + last_name
    "line1": "Krakowska 10/5",  # used as street fallback
    "city": "Krakow",
    "postal_code": "30-001",
    "phone": "500100200",
}
```

When `first_name` and `last_name` are not provided, the `name` field is split
on the first space. The `line1` field is used as a fallback for `street`.

## Status mapping

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

Unrecognized statuses return `None` from `map_shipx_status()`.

## Error handling

All ShipX API errors inherit from `sendparcel.exceptions.CommunicationError`:

| Exception | HTTP Status | Description |
|---|---|---|
| `ShipXAPIError` | any non-2xx | Base exception with `status_code`, `detail`, `errors` |
| `ShipXAuthenticationError` | 401 | Invalid or expired token |
| `ShipXValidationError` | 422 | Payload validation failed; `errors` contains field-level details |

## Webhooks

Both providers support InPost webhook callbacks for real-time status updates.

### Verification

Webhook source IP must be in the `91.216.25.0/24` range. The IP is read from
the `X-Forwarded-For` header (first entry). Invalid or missing IPs raise
`sendparcel.exceptions.InvalidCallbackError`.

### Payload format

```json
{
  "payload": {
    "shipment_id": 123456,
    "status": "delivered"
  }
}
```

The `handle_callback` method extracts the status and maps it to a sendparcel
status using `map_shipx_status()`. The actual FSM transition is handled by
`ShipmentFlow`.

## Enums

```python
from sendparcel_inpost.enums import ShipXService, ShipXParcelTemplate

ShipXService.INPOST_LOCKER_STANDARD   # "inpost_locker_standard"
ShipXService.INPOST_COURIER_STANDARD  # "inpost_courier_standard"

ShipXParcelTemplate.SMALL    # "small"
ShipXParcelTemplate.MEDIUM   # "medium"
ShipXParcelTemplate.LARGE    # "large"
```

## TypedDicts

The package provides ShipX-specific type definitions:

| Type | Description |
|---|---|
| `ShipXAddress` | Street, building, flat, city, post code, country |
| `ShipXPeer` | Name, company, phone, email, address |
| `ShipXParcel` | Template or dimensions + weight |
| `ShipXShipmentPayload` | Full create-shipment request body |
