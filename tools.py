"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of up to 3 matching listing dicts, sorted by relevance (style
        tag overlap with description keywords). Returns an empty list if
        nothing matches — does NOT raise an exception.
    """
    listings = load_listings()

    # Step 1: Apply hard filters
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and size.lower() not in item["size"].lower():
            continue
        filtered.append(item)

    # Step 2: Score by keyword overlap with description
    keywords = set(description.lower().split())

    def score(item):
        tag_words = set(
            word
            for tag in item["style_tags"]
            for word in tag.lower().split()
        )
        title_words = set(item["title"].lower().split())
        return len(keywords & (tag_words | title_words))

    scored = [(item, score(item)) for item in filtered]

    # Step 3: Drop zero-score results and sort
    scored = [(item, s) for item, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [item for item, _ in scored[:3]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest a complete outfit.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handled gracefully.

    Returns:
        A non-empty string with outfit suggestions. If the wardrobe is empty,
        asks the user to describe a few pieces they own rather than crashing.
    """
    wardrobe_items = wardrobe.get("items", [])

    # Empty wardrobe — pause and ask rather than proceeding
    if not wardrobe_items:
        return (
            "WARDROBE_EMPTY: To suggest an outfit, I need to know a bit about "
            "what you already own. Tell me 2–3 pieces — for example, 'baggy "
            "jeans, white sneakers, black hoodie' — and I'll put a full look "
            "together."
        )

    client = _get_groq_client()

    # Format wardrobe for the prompt
    wardrobe_lines = "\n".join(
        f"- {w['name']} ({w['category']})"
        + (f": {w['notes']}" if w.get('notes') else "")
        for w in wardrobe_items
    )

    prompt = f"""You are a thrift-savvy personal stylist. A user is considering buying this secondhand item:

Item: {new_item['title']}
Category: {new_item['category']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}
Condition: {new_item['condition']}

Their current wardrobe includes:
{wardrobe_lines}

Suggest one complete outfit using the new item and specific pieces from their wardrobe. \
Name the exact wardrobe pieces you're pairing it with. Include one specific styling tip \
(e.g. how to tuck it, layer it, or what to roll). Keep it to 2–3 sentences, conversational \
and specific — not generic fashion advice."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–3 sentence casual Instagram-style caption. If outfit is empty
        or missing required item fields, returns a descriptive error string
        rather than raising an exception.
    """
    # Guard: empty outfit string
    if not outfit or not outfit.strip():
        return (
            "Error: fit card unavailable — outfit description was empty. "
            "Here's the item: "
            f"{new_item.get('title', 'unknown item')} from "
            f"{new_item.get('platform', 'unknown platform')}."
        )

    # Guard: missing required item fields
    required = ["title", "price", "platform"]
    missing = [f for f in required if not new_item.get(f)]
    if missing:
        return (
            f"Error: fit card unavailable — item is missing fields: "
            f"{', '.join(missing)}. Outfit suggestion: {outfit}"
        )

    client = _get_groq_client()

    prompt = f"""You're writing an Instagram caption for a thrift find. Keep it casual, \
lowercase, and specific — like something a real person would actually post, not a brand. \
1–3 sentences max.

The thrifted item:
- Name: {new_item['title']}
- Price: ${new_item['price']}
- Platform: {new_item['platform']}
- Colors: {', '.join(new_item.get('colors', []))}

The outfit it's being worn with:
{outfit}

Write the caption. No hashtags. No quotes around it. Just the caption text."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,  # High temp for variety across identical inputs
        max_tokens=120,
    )

    return response.choices[0].message.content.strip()