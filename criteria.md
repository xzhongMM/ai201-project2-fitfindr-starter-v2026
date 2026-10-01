# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I picked 4 of 5 because search is a plain keyword match, so a query can describe
a real listing with words that do not overlap its title, tags, or description.
Requiring a fit card every time would ignore those search misses.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
I picked 5 of 5 because an empty result is a clear branch in the loop, not a
model-generated judgment. Every empty search should stop before outfit
suggestion and explain a useful change.

---

## 3. Something about state

Given 5 searches that return at least one listing, the `id` in
`session["selected_item"]` is the same as the `id` passed to `suggest_outfit` —
5 of 5 runs.

**Why this target:**
I picked 5 of 5 because passing the selected item through the session is a
deterministic part of the loop, not a model response. Checking the listing ID
directly catches the wrong-item handoff without depending on its wording.


---

## 4. Something about the fit card

Given 5 different listings, at least 4 of 5 fit cards include that listing's
exact price and platform exactly once and contain 2–4 sentences. The wording may
differ between cards.

**Why this target:**
I picked 4 of 5 because the model can vary its wording and occasionally miss a
detail, but price and platform are facts the card should preserve. Sentence
count and those two fields are checkable without requiring identical captions.


---

## 5. Your choice

Given 5 searches with a maximum-price filter, every returned listing costs no
more than the requested maximum — 5 of 5 searches.

**Why this target:**
I picked 5 of 5 because the price ceiling is a direct numeric filter in the
search, so model variation should not affect it. Returning an over-budget item
would violate a clear constraint the user gave.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
