"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── query parsing (regex) ─────────────────────────────────────────────────────

# "under $30", "below 30", "less than $30.50", "max $30", "up to $30", "<$30"
_PRICE_BEFORE = re.compile(
    r"(?:under|below|less\s+than|no\s+more\s+than|max(?:imum)?|up\s+to|at\s+most|<=?)"
    r"\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
# "$30 or less", "$30 max", "$30 and under"
_PRICE_AFTER = re.compile(
    r"\$\s*(\d+(?:\.\d+)?)\s*(?:or\s+less|max|and\s+under|or\s+under)",
    re.IGNORECASE,
)
# "size M", "size: xl", "in size 8", "size W30", "size 8.5"
_SIZE = re.compile(r"(?:in\s+)?size\s*:?\s*([a-z0-9][a-z0-9./]*)", re.IGNORECASE)

_SIZE_WORDS = {
    "xxs": "XXS", "xs": "XS", "small": "S", "medium": "M", "large": "L",
    "xl": "XL", "xxl": "XXL",
}

# Conversational filler that isn't part of what the user wants.
_FILLER = re.compile(
    r"\b(?:i'?m|i\s+am|i\s+want|i'?d\s+like|looking\s+for|searching\s+for|"
    r"find\s+me|show\s+me|can\s+you\s+find|please|some|a|an|any)\b",
    re.IGNORECASE,
)


def _normalize_size(raw: str) -> str:
    """Map what people type onto the size strings the listings use."""
    s = raw.strip().rstrip(".,")
    if s.lower() in _SIZE_WORDS:
        return _SIZE_WORDS[s.lower()]
    # A bare number like "8" or "8.5" is a shoe size; the data writes "US 8".
    if re.fullmatch(r"\d{1,2}(?:\.5)?", s) and float(s) <= 15:
        return f"US {s}"
    return s.upper()


def parse_query(query: str) -> dict:
    """
    Pull description, size and max_price out of a plain-language query.

    Regex, no model call: the three things we need have predictable shapes
    ("under $30", "size M"), and a parser we can test without quota is one we
    can trust when a search comes back empty.

    Returns {"description": str, "size": str | None, "max_price": float | None}.
    """
    text = query or ""
    max_price = None
    size = None

    for pattern in (_PRICE_BEFORE, _PRICE_AFTER):
        m = pattern.search(text)
        if m:
            max_price = float(m.group(1))
            text = text[: m.start()] + " " + text[m.end():]
            break

    m = _SIZE.search(text)
    if m:
        size = _normalize_size(m.group(1))
        text = text[: m.start()] + " " + text[m.end():]

    text = _FILLER.sub(" ", text)
    text = re.sub(r"[,;]+", " ", text)
    description = re.sub(r"\s+", " ", text).strip()

    return {"description": description, "size": size, "max_price": max_price}


def _empty_search_message(parsed: dict) -> str:
    """Say what the user could change, based on which filters they used."""
    asked = f"'{parsed['description']}'" if parsed["description"] else "your search"
    if parsed["size"]:
        asked += f" in size {parsed['size']}"
    if parsed["max_price"] is not None:
        asked += f" under ${parsed['max_price']:g}"

    tips = []
    if parsed["max_price"] is not None:
        tips.append("raise your budget")
    if parsed["size"]:
        tips.append("drop the size or try a neighbouring one")
    tips.append("use broader words (e.g. 'jacket' instead of 'designer bomber jacket')")

    if len(tips) > 1:
        tip_text = ", ".join(tips[:-1]) + ", or " + tips[-1]
    else:
        tip_text = tips[0]
    return f"Nothing matched {asked}. Try to {tip_text}."


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    searched = False   # search_results starts as [], so track "ran" separately
    count = 0

    while True:
        count += 1
        trace.check_iterations(count)

        # Each pass looks at the session and picks the next step from it.

        if not session["parsed"]:
            session["parsed"] = parse_query(query)
            continue

        if not searched:
            p = session["parsed"]
            session["search_results"] = search_listings(
                p["description"], size=p["size"], max_price=p["max_price"]
            )
            searched = True

            # ── THE BRANCH ──────────────────────────────────────────────────
            # Empty results: explain what to change and stop. suggest_outfit
            # and create_fit_card never run, so fit_card stays None.
            if not session["search_results"]:
                session["error"] = _empty_search_message(p)
                return session
            continue

        if session["selected_item"] is None:
            session["selected_item"] = session["search_results"][0]
            continue

        if session["outfit_suggestion"] is None:
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            continue

        if session["fit_card"] is None:
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            continue

        return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
