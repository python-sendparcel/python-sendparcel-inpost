# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-02-16

### Added

- InPost ShipX provider for python-sendparcel
- `InPostLockerProvider` for Paczkomat locker deliveries
- `InPostCourierProvider` for door-to-door courier deliveries
- `ShipXClient` standalone async HTTP client for the ShipX API
- ShipX exception hierarchy (`ShipXAPIError`, `ShipXAuthenticationError`, `ShipXValidationError`)
- ShipX-specific enums (`ShipXService`, `ShipXParcelTemplate`)
- ShipX-specific TypedDicts (`ShipXAddress`, `ShipXPeer`, `ShipXParcel`, `ShipXShipmentPayload`)
- Status mapping from 24 ShipX statuses to 8 sendparcel statuses
- Webhook verification by InPost source IP range (`91.216.25.0/24`)
- Address conversion with legacy name-splitting fallback
- Entry-point registration for auto-discovery
- Full test suite (93 tests)
