"""Single source of truth for demo product catalog (IDs, pricing, stock, image-matching keywords)."""

from __future__ import annotations

from typing import TypedDict


class ProductRecord(TypedDict):
    name: str
    price: float
    in_stock: bool
    keywords: list[str]


PRODUCTS: dict[str, ProductRecord] = {
    "PROD-001": {
        "name": "Wireless Headphones",
        "price": 24.99,
        "in_stock": True,
        "keywords": ["headphone", "headset", "earphone", "audio", "wireless"],
    },
    "PROD-002": {
        "name": "Phone Case",
        "price": 9.99,
        "in_stock": True,
        "keywords": ["case", "cover", "phone", "mobile"],
    },
    "PROD-003": {
        "name": "USB-C Cable",
        "price": 14.99,
        "in_stock": False,
        "keywords": ["cable", "usb", "charger", "cord"],
    },
}


def valid_product_ids() -> tuple[str, ...]:
    return tuple(PRODUCTS.keys())
