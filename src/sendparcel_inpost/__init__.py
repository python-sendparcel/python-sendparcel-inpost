"""InPost ShipX provider for python-sendparcel."""

__version__ = "0.1.0"

from sendparcel_inpost.client import ShipXClient
from sendparcel_inpost.providers.courier import InPostCourierProvider
from sendparcel_inpost.providers.locker import InPostLockerProvider

__all__ = [
    "InPostCourierProvider",
    "InPostLockerProvider",
    "ShipXClient",
    "__version__",
]
