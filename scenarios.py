"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # The same matching search repeats five times. Criterion 3.
        "name": "selected item state handoff",
        "query": "denim jacket",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Each try uses a different matching listing. Criterion 4.
        "name": "fit cards preserve item facts",
        "queries": [
            "graphic tee",
            "flannel shirt",
            "knit cardigan",
            "platform mary janes",
            "cargo pants",
        ],
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # The maximum-price filter is exercised on every search. Criterion 5.
        "name": "maximum price is respected",
        "query": "graphic tee under $20",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        queries = scenario.get("queries", [scenario.get("query", "")])
        if not queries or any(not query.strip() for query in queries):
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
        if scenario.get("criterion") not in range(1, 6):
            problems.append(f"scenario {i} needs a criterion number from 1 to 5")

    covered = {scenario.get("criterion") for scenario in SCENARIOS}
    missing = sorted(set(range(1, 6)) - covered)
    if missing:
        problems.append(f"no scenario tests criteria: {', '.join(map(str, missing))}")
    return problems
