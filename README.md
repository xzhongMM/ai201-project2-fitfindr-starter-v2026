# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a plain-language request for a secondhand clothing item, including optional size and budget filters. It searches and ranks the local listing data, then stops with suggestions for changing the search if nothing matches. When it finds an item, it uses the user's wardrobe to suggest outfits and generates a short fit-card caption for the find.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters `data/listings.json` by price and size, then ranks what's left by keyword overlap with the description. No model call.
- **Inputs:** `description` (str): the keywords, e.g. `"vintage graphic tee"`. `size` (str or None): `None` skips size filtering. `max_price` (float or None): inclusive ceiling, and `None` skips price filtering.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, best match first. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or **None**), and `platform`.
  - **Score:** for each word in the description (lowercased, stopwords dropped, plurals folded so "sneakers" = "sneaker"), the listing gets 3 points if it's in the title, 3 in style tags, 2 in category, 2 in colors, 2 in brand, and 1 in the description. A higher score ranks first; on a tie the cheaper item ranks first.
  - **Size match:** a listing size is split on `/`, with parentheticals dropped, and multi-word parts are also split on spaces. So `"S/M"` gives `{S, M}`, `"W30 L30"` gives `{W30, L30}`, and `"US 8"` gives `{US 8, 8}`. It matches if any whole part equals the wanted size. So `M` matches `S/M`, but `S` does **not** match `US 9`, `L` does not match `XL`, and `US 8` does not match `US 8.5`. Listings marked `One Size…` match any size.
- **When it has nothing:** `[]`, an empty list. It never returns `None` and never raises. That covers no listing scoring above 0, every listing being filtered out, or a description with no usable words.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two outfits built around the thrifted item.
- **Inputs:** `new_item` (dict): one listing dict from `search_listings`. `wardrobe` (dict): `{"items": [...]}`, where each item has `id`, `name`, `category`, `colors` (list), `style_tags` (list), and `notes` (str or None).
- **Returns:** A non-empty `str` of outfit suggestions. When the wardrobe has items, each outfit names specific pieces the user owns by their `name`, e.g. "Black combat boots".
- **When it has nothing:** If `wardrobe["items"]` is `[]` (the empty wardrobe), it still returns a non-empty `str`: general styling advice for the item, with the kinds of pieces to pair it with, and no owned pieces named. It never returns `""` and never raises for an empty wardrobe. If the model itself fails, `generate()` raises `ModelUnavailable`, and the loop handles that (unit 4).

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a short social-post caption about the find and how it's styled.
- **Inputs:** `outfit` (str): the string `suggest_outfit` returned. `new_item` (dict): the same listing dict.
- **Returns:** A `str` of 2–4 sentences written like a real post, not a product description. It names the item, its price (e.g. `$24`) and its platform once each, and says something specific about the vibe. The caption varies between runs (`TEMPERATURE` 0.9).
- **When it has nothing:** If `outfit` is empty or only whitespace, it skips the model call and returns the fixed string `"No fit card: there was no outfit suggestion to write about."`. It never raises for that. A model failure raises `ModelUnavailable`, same as above.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that says what the user could change, based on the filters they used: raise the budget, drop or change the size, or use broader words. Then return the session without calling `suggest_outfit` or `create_fit_card`, so `fit_card` stays `None`. Otherwise, take the first result as `selected_item` and go on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`, with no model call.
- **Price:** "under / below / less than / up to / max $N" or "$N or less" becomes `max_price` (float).
- **Size:** "size X" or "in size X" becomes `size`. Words like "medium" become `M`, and a bare number up to 15 becomes `US N` to match how shoes are listed.
- **Description:** what's left, after removing filler like "looking for a".

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` → *(branch: empty ⇒ `error` set, stop)* → `selected_item` → `outfit_suggestion` → `fit_card`. Every step reads its input from the session and writes its result back into it.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ ./.venv/bin/python app.py ask 'vintage graphic tee max 30'
     Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

     Outfit:   Outfit 1
Pair the Graphic Tee — 2003 Tour Bootleg Style with the Baggy straight-leg jeans, dark wash and the Black combat boots. Finish with the Black crossbody bag.
This leans into the Y2K streetwear vibe of the tee with a heavy, grunge-inspired silhouette from head to toe.

Outfit 2
Tuck the Graphic Tee — 2003 Tour Bootleg Style into the Wide-leg khaki trousers, add the Brown leather belt, and wear the Chunky white sneakers.
The tan trousers tone down the intense black of the vintage tee while keeping the look grounded and effortless.

     Fit card: Finally found the holy grail of Y2K tour tees and it’s already got that perfect worn-in fade. It’s up on my depop for $24, styled here with baggy denim and combat boots for full-on 2003 grunge energy.

0 model calls this session, 2 served from cache
```

**Empty-search path**

```
$ ./.venv/bin/python app.py ask 'designer ballgown size XXS max 5'
     Nothing matched 'designer ballgown' in size XXS under $5. Try to raise your budget, drop the size or try a neighbouring one, or use broader words (e.g. 'jacket' instead of 'designer bomber jacket').

0 model calls this session
```

**The three tools, tested one at a time**

```
$ ./.venv/bin/python -c "from tools import search_listings; print([(x['title'], x['size'], x['price']) for x in search_listings('graphic tee', size='M', max_price=30)])"
[('Y2K Baby Tee — Butterfly Print', 'S/M', 18.0), ('Mesh Long-Sleeve Top — Black', 'S/M', 15.0)]
```

```
$ ./.venv/bin/python -c "import json; from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(json.dumps(suggest_outfit(load_listings()[0], get_example_wardrobe()), ensure_ascii=False))"
"Outfit One\nPair the Vintage Levi's 501 Jeans — Medium Wash with the White ribbed tank top, the Vintage black denim jacket, and the Chunky white sneakers. Add the Brown leather belt to finish the waist.\nWhy it works: Double denim creates a classic vintage look, while the white tank and fresh sneakers keep it bright and casual.\n\nOutfit Two\nCombine the Vintage Levi's 501 Jeans — Medium Wash with the Oversized grey crewneck sweatshirt and the Black combat boots. \nWhy it works: The ultra-cozy, oversized grey sweatshirt contrasts the structured straight-leg denim, and the combat boots add a tough, streetwear edge."
```

```
$ AI201_CACHE=0 ./.venv/bin/python -c "import json; from tools import create_fit_card; from utils.data_loader import load_listings; item = load_listings()[0]; print(json.dumps([create_fit_card('jeans and white sneakers', item) for _ in range(3)]))"
["nothing beats a broken-in pair of 501s and fresh white sneakers for the ultimate off-duty look. snagged these vintage levis for $38 and they fit like an absolute dream. just dropped them on my depop if you need your new go-to denim.", "nothing beats the effortless look of vintage 501s with a fresh pair of white sneakers for that ultimate casual weekend fit. these have the best knee fading already broken in for you. just listed this W30 pair on my depop for $38 and they're ready for a new home.", "Nothing beats a broken-in pair of vintage Levi's 501s, especially with that ideal medium wash fade at the knees. Just threw them on with crisp white sneakers for the easiest casual streetwear fit. Grabbed these on depop for $38 and I honestly might never wear hard pants again."]
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Could someone check that my state criterion without asking what I meant? What observable proves that the item found by search is the one sent to the outfit tool?
- *What came back:* The useful check is to compare the listing `id` stored in `session["selected_item"]` with the `id` actually passed to `suggest_outfit`. For model-written cards, check stable facts and length instead of requiring identical wording.
- *What I changed:* I wrote a 5-of-5 ID handoff criterion and a fit-card criterion checking the item's price, platform, and sentence count while allowing the wording to vary.

**Moment 2**

- *What I asked for:* Check each tool from the terminal, including what it does when search finds nothing, the wardrobe is empty, or there is no outfit to caption.
- *What came back:* Search returned `[]` for no match; an empty wardrobe still received general styling advice; and an empty outfit returned the fixed no-card message. Three uncached captions for one item had different wording.
- *What I changed:* I kept those empty behaviors in the tool inventory and pasted the standalone commands and observed outputs into Sample Run, disabling the cache for the three-caption check.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
