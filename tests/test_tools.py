# tests/test_tools.py

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_substring_match():
    # "M" should match listings sized "S/M" or "M/L", not just exact "M"
    results = search_listings("vintage tee", size="M", max_price=100)
    for item in results:
        assert "m" in item["size"].lower()


def test_search_returns_at_most_three():
    results = search_listings("vintage", size=None, max_price=100)
    assert len(results) <= 3


def test_search_result_fields():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    if results:
        required = ["id", "title", "price", "platform", "style_tags", "size"]
        for field in required:
            assert field in results[0]


# ── suggest_outfit ────────────────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    result = suggest_outfit(item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0
    assert "WARDROBE_EMPTY" in result


def test_suggest_outfit_with_wardrobe():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    result = suggest_outfit(item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0
    assert "WARDROBE_EMPTY" not in result


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_fit_card_empty_outfit():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    result = create_fit_card("", item)
    assert isinstance(result, str)
    assert "Error" in result


def test_fit_card_missing_fields():
    incomplete_item = {"title": "Mystery Tee"}  # missing price and platform
    result = create_fit_card("baggy jeans and chunky sneakers", incomplete_item)
    assert isinstance(result, str)
    assert "Error" in result


def test_fit_card_returns_string():
    item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
    outfit = suggest_outfit(item, get_example_wardrobe())
    result = create_fit_card(outfit, item)
    assert isinstance(result, str)
    assert len(result) > 0