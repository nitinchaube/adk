"""Unit tests for tool-level validation and API helpers (no LLM required)."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Tools.ShoppingCartTool import AddToCartInput


# ---------------------------------------------------------------------------
# AddToCartInput validation
# ---------------------------------------------------------------------------


class TestAddToCartValidation:
    def test_valid_product_passes(self):
        inp = AddToCartInput(product_id="PROD-001", quantity=2)
        assert inp.product_id == "PROD-001"
        assert inp.quantity == 2

    def test_invalid_product_rejected(self):
        with pytest.raises(ValueError, match="Invalid product_id"):
            AddToCartInput(product_id="FAKE-999", quantity=1)

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValueError, match="at least 1"):
            AddToCartInput(product_id="PROD-001", quantity=0)

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValueError, match="at least 1"):
            AddToCartInput(product_id="PROD-001", quantity=-3)

    def test_all_valid_product_ids_accepted(self):
        from config.catalog import valid_product_ids

        for pid in valid_product_ids():
            inp = AddToCartInput(product_id=pid, quantity=1)
            assert inp.product_id == pid


# ---------------------------------------------------------------------------
# GitHub tool — live API smoke tests (requires network)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_repo_info_real():
    from Tools.GitHubTool import get_repo_info

    result = await get_repo_info("python", "cpython")
    assert "error" not in result
    assert result["name"] == "python/cpython"
    assert isinstance(result["stars"], int) and result["stars"] > 0


@pytest.mark.asyncio
async def test_get_repo_info_nonexistent():
    from Tools.GitHubTool import get_repo_info

    result = await get_repo_info("nonexistent-org-xyz", "nonexistent-repo-xyz")
    assert "error" in result


@pytest.mark.asyncio
async def test_get_repo_issues_real():
    from Tools.GitHubTool import get_repo_issues

    result = await get_repo_issues("python", "cpython", limit=3)
    assert "error" not in result
    assert isinstance(result["issues"], list)


@pytest.mark.asyncio
async def test_get_repo_contributors_real():
    from Tools.GitHubTool import get_repo_contributors

    result = await get_repo_contributors("python", "cpython", limit=3)
    assert "error" not in result
    assert len(result["contributors"]) > 0
    assert "username" in result["contributors"][0]


# ---------------------------------------------------------------------------
# Open Library tool — live API smoke test (requires network)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_books_real():
    from Tools.ExternalAPITool import search_books

    result = await search_books("python programming", max_results=2)
    assert "error" not in result
    assert len(result.get("books", [])) > 0


@pytest.mark.asyncio
async def test_search_books_clamped_limit():
    """max_results above OPEN_LIBRARY_MAX_LIMIT should be clamped, not crash."""
    from Tools.ExternalAPITool import search_books

    result = await search_books("javascript", max_results=9999)
    assert "error" not in result
    assert len(result.get("books", [])) <= 10


# ---------------------------------------------------------------------------
# Catalog sanity checks
# ---------------------------------------------------------------------------


class TestCatalog:
    def test_products_not_empty(self):
        from config.catalog import PRODUCTS

        assert len(PRODUCTS) > 0

    def test_every_product_has_required_fields(self):
        from config.catalog import PRODUCTS

        for pid, record in PRODUCTS.items():
            assert "name" in record, f"{pid} missing name"
            assert "price" in record, f"{pid} missing price"
            assert "in_stock" in record, f"{pid} missing in_stock"
            assert "keywords" in record, f"{pid} missing keywords"
            assert record["price"] > 0, f"{pid} has non-positive price"

    def test_valid_product_ids_matches_keys(self):
        from config.catalog import PRODUCTS, valid_product_ids

        assert set(valid_product_ids()) == set(PRODUCTS.keys())
