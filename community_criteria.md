# Acceptance Criteria — Hacker News Reply Classifier

These criteria are written before training. They apply to the three labels in [COMMUNITY_LABELS.md](COMMUNITY_LABELS.md): `procedure`, `grounded_claim`, and `stance`.

## Evaluation Protocol

Label 200 public Hacker News posts with exactly one label each. Before training, reserve a stratified random 25% (50 posts) as a held-out test set using a recorded random seed; use the remaining 150 for training and any tuning. Report test-set metrics only once the model and decision threshold are fixed. For inter-annotator agreement, have a second person label the same 50 randomly selected posts independently, before discussion or adjudication. Report the confusion matrix and the number of examples behind every metric.

## Criteria

### 1. Overall accuracy

The classifier must correctly label at least **70%** of the 50 held-out posts (at least 35 correct).

**Why this target:** With three labels, an uninformed equal-choice guess has about 33% accuracy. A 70% target is meaningfully above that baseline while leaving room for disagreements on short or mixed-purpose replies.

### 2. Per-label performance

The F1 score for **each** of `procedure`, `grounded_claim`, and `stance` must be at least **0.55** on the held-out set. Calculate each one-vs-rest F1 from its precision and recall; do not average labels to decide whether this criterion passes.

**Why this target:** Overall accuracy can conceal a label the classifier nearly never recognizes. Requiring every label to reach 0.55 sets a useful floor without pretending 50 test examples will support a very precise estimate for each class.

### 3. Label balance in the annotated data

In the 200-post labeled dataset, each label must account for at least **15%** and no more than **60%** of posts (at least 30 and no more than 120 posts per label).

**Why this target:** The initial 30-post reading showed all three patterns, with no single one dominating. A 15% floor gives each label enough examples to learn from, while a 60% ceiling keeps a majority-label guess from looking useful by accuracy alone; it still allows natural imbalance.

### 4. Human labeling consistency

The two independent human labelers must achieve unweighted Cohen's kappa of at least **0.60** on the 50 shared posts, before resolving disagreements.

**Why this target:** The labels depend on observable text features but some replies blend a procedure with a personal example. A 0.60 agreement target requires substantial consistency while allowing genuine borderline cases; the written precedence rule should make agreement better than chance.

### 5. High-confidence predictions

Among held-out predictions where the model's highest class probability is at least **0.80**, at least **80%** must be correct, with at least **10** held-out predictions meeting that confidence threshold. If fewer than 10 qualify, this criterion is **not met**.

**Why this target:** A confidence score should help prioritize human review, not just look precise on one or two easy examples. Requiring 10 predictions prevents a tiny, cherry-pickable subset from passing; 80% correctness makes the high-confidence flag useful enough to trust as a review signal, not as a guarantee.
