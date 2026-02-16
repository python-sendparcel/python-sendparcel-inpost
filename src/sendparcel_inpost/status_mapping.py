"""ShipX status to sendparcel status mapping."""

from sendparcel.enums import ShipmentStatus

SHIPX_TO_SENDPARCEL_STATUS: dict[str, ShipmentStatus] = {
    # CREATED
    "created": ShipmentStatus.CREATED,
    "offers_prepared": ShipmentStatus.CREATED,
    "offer_selected": ShipmentStatus.CREATED,
    # LABEL_READY
    "confirmed": ShipmentStatus.LABEL_READY,
    # IN_TRANSIT
    "dispatched_by_sender": ShipmentStatus.IN_TRANSIT,
    "collected_from_sender": ShipmentStatus.IN_TRANSIT,
    "taken_by_courier": ShipmentStatus.IN_TRANSIT,
    "adopted_at_source_branch": ShipmentStatus.IN_TRANSIT,
    "sent_from_source_branch": ShipmentStatus.IN_TRANSIT,
    "adopted_at_sorting_center": ShipmentStatus.IN_TRANSIT,
    # OUT_FOR_DELIVERY
    "out_for_delivery": ShipmentStatus.OUT_FOR_DELIVERY,
    "ready_to_pickup": ShipmentStatus.OUT_FOR_DELIVERY,
    "pickup_reminder_sent": ShipmentStatus.OUT_FOR_DELIVERY,
    "avizo": ShipmentStatus.OUT_FOR_DELIVERY,
    "stack_in_box_machine": ShipmentStatus.OUT_FOR_DELIVERY,
    "stack_in_customer_service_point": ShipmentStatus.OUT_FOR_DELIVERY,
    # DELIVERED
    "delivered": ShipmentStatus.DELIVERED,
    # CANCELLED
    "canceled": ShipmentStatus.CANCELLED,
    # RETURNED
    "returned_to_sender": ShipmentStatus.RETURNED,
    # FAILED
    "rejected_by_receiver": ShipmentStatus.FAILED,
    "undelivered": ShipmentStatus.FAILED,
    "oversized": ShipmentStatus.FAILED,
    "missing": ShipmentStatus.FAILED,
    "claim_created": ShipmentStatus.FAILED,
}


def map_shipx_status(shipx_status: str) -> ShipmentStatus | None:
    """Map a ShipX status string to a sendparcel ShipmentStatus.

    Returns None if the status is not recognized.
    """
    return SHIPX_TO_SENDPARCEL_STATUS.get(shipx_status)
