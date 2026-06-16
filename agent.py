"""
agent.py
The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parser ──────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query
    using regex. Documented approach: regex over LLM to keep this fast,
    free, and deterministic — no API call needed for parsing.

    Size: looks for standalone size tokens (XS, S, M, L, XL, XXL) or
          waist measurements like W28, W30, or US shoe sizes like US 8.
    Price: looks for "under $X", "less than $X", "max $X", "$X or less".
    Description: everything left after stripping size and price tokens.
    """
    # Extract max_price
    price_match = re.search(
        r'(?:under|less than|max|below|up to)\s*\$?([\d]+(?:\.\d+)?)'
        r'|\$([\d]+(?:\.\d+)?)\s*(?:or less|max|tops)',
        query, re.IGNORECASE
    )
    max_price = None
    if price_match:
        raw = price_match.group(1) or price_match.group(2)
        max_price = float(raw)

    # Extract size
    size_match = re.search(
        r'\b(XXS|XS|S/M|M/L|XL/XXL|XXL|XL|[SML]|W\d{2}(?:\s*L\d{2})?|US\s*\d+(?:\.\d+)?)\b',
        query, re.IGNORECASE
    )
    size = size_match.group(1) if size_match else None

    # Description: strip price/size phrases and filler words to get keywords
    desc = query
    if price_match:
        desc = desc[:price_match.start()] + desc[price_match.end():]
    if size_match:
        desc = desc[:size_match.start()] + desc[size_match.end():]

    # Strip common filler
    filler = re.compile(
        r'\b(i\'?m?\s+)?'
        r'(looking for|searching for|want|need|find me|got any|any)\b',
        re.IGNORECASE
    )
    desc = filler.sub('', desc)
    desc = re.sub(r'\s+', ' ', desc).strip().strip(',').strip()

    return {
        "description": desc if desc else query,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop and returns
    the completed session dict.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings — stop early if nothing found
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    if not results:
        session["error"] = (
            "No listings matched your search — try a broader description, "
            "a different size format (e.g. 'S/M' instead of 'S'), or a "
            "higher price limit."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit — check for empty wardrobe sentinel
    outfit = suggest_outfit(session["selected_item"], wardrobe)
    session["outfit_suggestion"] = outfit

    if outfit.startswith("WARDROBE_EMPTY"):
        session["error"] = outfit
        return session

    # Step 6: Create fit card
    fit_card = create_fit_card(outfit, session["selected_item"])
    session["fit_card"] = fit_card

    # Step 7: Return completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found:    {session['selected_item']['title']}")
        print(f"\nOutfit:   {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
    assert session2["fit_card"] is None, "fit_card should be None on no-results path"
    assert session2["outfit_suggestion"] is None, "outfit_suggestion should be None on no-results path"
    print("✓ fit_card and outfit_suggestion are both None — planning loop branched correctly")