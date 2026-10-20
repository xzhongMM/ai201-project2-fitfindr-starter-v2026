# Community Label Design

Community and reading sample: [Hacker News Ask HN thread](https://news.ycombinator.com/item?id=50151036), documented in [COMMUNITY_NOTES.md](COMMUNITY_NOTES.md). These labels apply to one reply/post at a time, not to the author's overall view.

## Labels

### `procedure`
The post prescribes a repeatable action, workflow, checklist, or concrete method for handling AI-written code.

- **Real post 1, item 50157475, bitwizeshift:** “I don't let the LLM design the code at all, I let it implement a design I have created.” The reply then describes deciding the abstractions first and assigning implementation gaps to the LLM.
- **Real post 2, item 50158972, anupshinde:** “Ask questions, clarify and ask ‘Do you have any questions’”; the post continues with a checklist including examples, peer reviews, and clear division of responsibilities.

### `grounded_claim`
The post makes a claim anchored in a specific personal event, project, quantity, result, or inspectable artifact, but does not prescribe a repeatable procedure.

- **Real post 1, item 50156673, asimovDev:** Describes iterating throughout one day, with a fix around 1,000 lines, and the exhaustion that followed. This is a particular reported experience, not a general workflow recommendation.
- **Real post 2, item 50156532, gavinray:** Reports a transition from IDE completion to CLI agents and says the semantics of a system worked on for “~4-5 years” became fuzzier; then proposes formal verification as a general solution. The concrete account grounds the post, but it does not give a repeatable verification procedure.

### `stance`
The post expresses an evaluation, preference, or broad recommendation without a repeatable method or a specific supporting event, result, quantity, or artifact.

- **Real post 1, item 50156466, orblivion:** “I'm miles away from all of this as a non-user of AI and it seems like a mania to me.” It is a clear evaluation with no example or method.
- **Real post 2, item 50156667, movsx:** “Well, it's simple. Don't do it.” This is a broad recommendation, but it gives no operational steps or supporting example.

## Borderline Post and Decision Rule

**Borderline post:** item 50156740 by ChrisMarshallNY sits between `procedure` and `grounded_claim`:

> “Testing. Lots and lots of testing. I usually interactively test with the LLM. Now that I'm spending less time, coding, I get to spend more time, testing. In my experience, I test more, with an LLM, than I did, with my own code. I don't find coding errors, but I do find implementation errors. On another note: I ran an LLM on a bunch of really mature code that I wrote, and could swear was ‘perfect,’ and it found a number of issues. Nobody's perfect. Trust; but verify.”

**Decision rule:** If a post tells the reader to use a repeatable method or workflow, label it `procedure`, even when it also includes a personal example or result. Use `grounded_claim` only when the concrete experience or evidence supports the point but the post does not prescribe a method. Otherwise use `stance`.

I classify the borderline post as `procedure`: “I usually interactively test with the LLM” is a method the author recommends, so it takes precedence over the accompanying personal experience.

## AI Boundary Stress Test

I asked the AI assistant to draft eight short, fictional HN-style replies that deliberately mix or nearly mix the three signals, then classified each using the decision rule above. These are synthetic test cases, not posts from the community.

| # | Synthetic boundary post | Label | Why the rule resolves it |
|---|---|---|---|
| 1 | “We ran 80 generated-code tests last month and none caught the migration bug; require a rollback test before merging schema changes.” | `procedure` | It contains a concrete result, but the explicit repeatable merge check takes precedence. |
| 2 | “Our last release rolled back cleanly in four minutes after the agent broke the import path.” | `grounded_claim` | Specific event and measured duration; no procedure is prescribed. |
| 3 | “AI-written code is a disaster waiting to happen.” | `stance` | Evaluation only; no specific evidence or method. |
| 4 | “Before shipping, run the generated diff through static analysis and have a second reviewer check data mutations.” | `procedure` | Gives repeatable actions, even though it names tools and review targets. |
| 5 | “On three recent PRs, the second reviewer found two data-loss bugs the author missed.” | `grounded_claim` | Specific count and outcome support the point, but no workflow is requested. |
| 6 | “I don't trust these systems, so nobody should use them for production.” | `stance` | Personal preference and broad recommendation, without concrete support or an actionable method. |
| 7 | “For payment code, require a human sign-off and test restoring the latest backup; our last restore took 11 minutes.” | `procedure` | The evidence is secondary; the post prescribes a repeatable safeguard. |
| 8 | “I spent Friday tracing an agent-written timeout bug through three services before I found the retry loop.” | `grounded_claim` | A specific personal event and details, but no advice or repeatable method. |

All eight cases received one label using the written precedence rule. The main ambiguity exposed by the test is that recommendations can be a single broad stance (“don't use it”) or an operational procedure (“run this check before merge”); the distinction is whether a reader could repeat the specified method, not whether the sentence is phrased as advice.
