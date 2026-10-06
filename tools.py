"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────
_STOPWORDS = {"a", "an", "and", "the", "for", "with", "under", "over", "in", "of"}


def _stem(word: str) -> str:
    """Crude plural fold so 'sneakers' matches 'sneaker' and 'jeans' matches 'jean'."""
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def keywords(text: str) -> set[str]:
    """Lowercase words worth matching on, stopwords removed, plurals folded."""
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {_stem(w) for w in words if w not in _STOPWORDS and len(w) > 1}


def _size_tokens(size: str) -> set[str]:
    """
    Break a size string into the tokens it can match on.

      "S/M"            → {"S", "M"}
      "XL (oversized)" → {"XL"}               parenthetical dropped
      "W30 L30"        → {"W30 L30", "W30", "L30"}
      "US 8"           → {"US 8", "8"}        but never a bare "US"
    Whole tokens only, so "S" never matches "US 9" and "L" never matches "XL".
    """
    cleaned = re.sub(r"\([^)]*\)", " ", size or "")  # drop parentheticals
    tokens = set()
    for part in cleaned.split("/"):
        part = re.sub(r"\s+", " ", part).strip().upper()
        if not part:
            continue
        tokens.add(part)
        pieces = part.split(" ")
        if len(pieces) > 1 and not part.startswith("ONE SIZE"):
            tokens.update(p for p in pieces if p != "US")
    return tokens


def _size_matches(wanted: str, listing_size: str) -> bool:
    """True when no size was asked for, the listing is One Size, or a token is shared."""
    if not wanted:
        return True
    listing_tokens = _size_tokens(listing_size)
    if any(token.startswith("ONE SIZE") for token in listing_tokens):
        return True
    return bool(_size_tokens(wanted) & listing_tokens)


def _score(listing: dict, wanted: set[str]) -> int:
    """
    Keyword overlap, weighted by where the word appears.
    Title and style tags count 3, category 2, colors/brand 2, description 1.
    """
    fields = [
        (keywords(listing.get("title", "")), 3),
        (keywords(" ".join(listing.get("style_tags") or [])), 3),
        (keywords(listing.get("category", "")), 2),
        (keywords(" ".join(listing.get("colors") or [])), 2),
        (keywords(listing.get("brand") or ""), 2),
        (keywords(listing.get("description", "")), 1),
    ]
    return sum(weight * len(wanted & words) for words, weight in fields)

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    wanted = keywords(description)
    if not wanted:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if not _size_matches(size, listing.get("size", "")):
            continue
        score = _score(listing, wanted)
        if score > 0:
            scored.append((score, listing))

    # Highest score first; cheaper wins a tie.
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── helpers for the two model tools ──────────────────────────────────────────

EMPTY_FIT_CARD_MESSAGE = "No fit card: there was no outfit suggestion to write about."

_STYLIST_SYSTEM = (
    "You are a practical personal stylist for secondhand fashion. Give concrete "
    "outfit combinations, not general fashion theory. Plain text, no markdown headers."
)
_CAPTION_SYSTEM = (
    "You write short, casual social media captions about thrift finds. "
    "You sound like a real person, not an ad."
)


def _describe_item(item: dict) -> str:
    """A listing as prompt text. Skips brand when it's None (most listings)."""
    lines = [
        f"- {item.get('title', 'Untitled item')}",
        f"- category: {item.get('category', 'unknown')}",
        f"- colors: {', '.join(item.get('colors') or []) or 'unknown'}",
        f"- style: {', '.join(item.get('style_tags') or []) or 'unknown'}",
        f"- size: {item.get('size', 'unknown')}, condition: {item.get('condition', 'unknown')}",
    ]
    if item.get("brand"):
        lines.append(f"- brand: {item['brand']}")
    if item.get("description"):
        lines.append(f"- seller says: {item['description']}")
    return "\n".join(lines)


def _describe_wardrobe_item(w: dict) -> str:
    line = (
        f"- {w.get('name', 'unnamed piece')} ({w.get('category', '?')}; "
        f"{', '.join(w.get('colors') or [])}; {', '.join(w.get('style_tags') or [])})"
    )
    if w.get("notes"):
        line += f" — {w['notes']}"
    return line


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_text = _describe_item(new_item)
    items = (wardrobe or {}).get("items") or []

    if not items:
        # Empty wardrobe: general advice, no owned pieces to name.
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            "They haven't told us what's in their closet. Suggest one or two "
            "outfits built around this piece, describing the kinds of pieces to "
            "pair it with (e.g. 'straight-leg dark jeans', 'chunky white "
            "sneakers'). Keep it under 120 words."
        )
    else:
        closet = "\n".join(_describe_wardrobe_item(w) for w in items)
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            f"Here is what they already own:\n{closet}\n\n"
            "Suggest one or two outfits built around the thrifted piece. Each "
            "outfit must use 2-3 pieces from the list above, named exactly as "
            "written. Do not invent pieces they don't own. Add one short line on "
            "why each outfit works. Keep it under 120 words."
        )

    response = generate(prompt, system=_STYLIST_SYSTEM).strip()
    if not response:
        # The spec promises a non-empty string; never hand the loop "".
        return f"Style the {new_item.get('title', 'piece')} with simple basics in matching colors."
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return EMPTY_FIT_CARD_MESSAGE

    price = new_item.get("price")
    price_text = f"${price:g}" if isinstance(price, (int, float)) else "a thrift price"
    prompt = (
        f"The thrifted find:\n{_describe_item(new_item)}\n\n"
        f"How it's being styled:\n{outfit.strip()}\n\n"
        "Write a 2-4 sentence caption for a social post about this find. "
        f"Mention the item, the price ({price_text}) and the platform "
        f"({new_item.get('platform', 'thrift')}) once each. Be specific about the "
        "vibe of the outfit. Write like a real person posting, not a product "
        "listing. No hashtags. Return only the caption."
    )
    return generate(prompt, system=_CAPTION_SYSTEM).strip()
