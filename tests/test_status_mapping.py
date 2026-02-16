"""Tests for ShipX to sendparcel status mapping."""

import pytest
from sendparcel.enums import ShipmentStatus

from sendparcel_inpost.status_mapping import (
    SHIPX_TO_SENDPARCEL_STATUS,
    map_shipx_status,
)


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("shipx_status", "expected"),
        [
            ("created", ShipmentStatus.CREATED),
            ("offers_prepared", ShipmentStatus.CREATED),
            ("offer_selected", ShipmentStatus.CREATED),
            ("confirmed", ShipmentStatus.LABEL_READY),
            ("dispatched_by_sender", ShipmentStatus.IN_TRANSIT),
            ("collected_from_sender", ShipmentStatus.IN_TRANSIT),
            ("taken_by_courier", ShipmentStatus.IN_TRANSIT),
            ("adopted_at_source_branch", ShipmentStatus.IN_TRANSIT),
            ("sent_from_source_branch", ShipmentStatus.IN_TRANSIT),
            ("adopted_at_sorting_center", ShipmentStatus.IN_TRANSIT),
            ("out_for_delivery", ShipmentStatus.OUT_FOR_DELIVERY),
            ("ready_to_pickup", ShipmentStatus.OUT_FOR_DELIVERY),
            ("pickup_reminder_sent", ShipmentStatus.OUT_FOR_DELIVERY),
            ("avizo", ShipmentStatus.OUT_FOR_DELIVERY),
            ("stack_in_box_machine", ShipmentStatus.OUT_FOR_DELIVERY),
            (
                "stack_in_customer_service_point",
                ShipmentStatus.OUT_FOR_DELIVERY,
            ),
            ("delivered", ShipmentStatus.DELIVERED),
            ("canceled", ShipmentStatus.CANCELLED),
            ("returned_to_sender", ShipmentStatus.RETURNED),
            ("rejected_by_receiver", ShipmentStatus.FAILED),
            ("undelivered", ShipmentStatus.FAILED),
            ("oversized", ShipmentStatus.FAILED),
            ("missing", ShipmentStatus.FAILED),
            ("claim_created", ShipmentStatus.FAILED),
        ],
    )
    def test_known_status_maps_correctly(
        self, shipx_status: str, expected: ShipmentStatus
    ) -> None:
        assert map_shipx_status(shipx_status) == expected

    def test_unknown_status_returns_none(self) -> None:
        assert map_shipx_status("completely_unknown_status") is None

    def test_mapping_dict_is_complete(self) -> None:
        """Every key maps to a valid ShipmentStatus."""
        for shipx, sendparcel in SHIPX_TO_SENDPARCEL_STATUS.items():
            assert isinstance(shipx, str)
            assert isinstance(sendparcel, ShipmentStatus)
