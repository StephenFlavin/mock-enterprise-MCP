# Adjudication

Two judges graded this conversation under the rules above and disagree. Their verdicts follow the payload, as
`judge_a` and `judge_b`. Decide the final verdict yourself.

- List the points where they differ: the outcome, a fact present or missing, a figure or claim supported or not, a write
  justified or not, whether the trap was handled.
- Settle each point from the payload evidence alone: the conversation, `expected`, `grounding`, `actions`, `trap`,
  `calls_made`. Quote the evidence that settles it.
- A judge's confidence, wording or length is not evidence. Do not split the difference, and do not prefer either judge:
  each is right on some points and wrong on others.
- When the evidence does not settle a point, apply the rule that fits most narrowly and say which.

Return the final Verdict in the schema above. Begin `rationale` with "A right", "B right", or "neither" (whose verdict
your final outcome matches), then the deciding point with its quote.
