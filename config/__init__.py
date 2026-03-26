"""Central configuration for ADK practice agents."""

from .catalog import PRODUCTS, ProductRecord, valid_product_ids
from . import settings

__all__ = [
    "PRODUCTS",
    "ProductRecord",
    "settings",
    "valid_product_ids",
]
