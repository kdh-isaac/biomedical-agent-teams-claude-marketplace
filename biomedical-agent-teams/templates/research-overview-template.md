# Research Overview Template

A one-page, human-readable research overview in the register of an NIH Specific
Aims page. This is a **reformat, not new analysis**: every field is populated
from material that already exists in the run — the `meta-review-synthesizer`
output, the hypothesis tournament's `final_ranking` (with Elo ratings and
rationales), the red-team/risk-of-bias downgrades, and the recommended
kill-tests. It adds no claim that is not already in the central claim ledger.

Produce it as the reader-facing companion to the audit-bundle final output. The
audit bundle remains the authoritative record; this overview is the digest a
human reads first.

## Honesty and provenance rules

- **No new claims.** Every statement traces to a ledger claim ID or a tournament
  output already produced. If it is not in the ledger, it does not belong here.
- **Labels carry through.** If the tournament closed as `budget_bounded`, the
  ranking here is presented as budget-bounded, not converged. If a parallel wave
  closed on quorum with a dropped lane, the coverage note carries through. The
  label-honesty ceiling applies to this document exactly as to the final output.
- **Elo is a tie-break, not proof.** Report Elo ratings for transparency and
  ordering; never present a rating as evidence strength. Qualitative rationale is
  the substance; the number is the ordering aid.
- **Downgrades are visible.** Risks and kill-tests are not an appendix — a
  hypothesis whose support was downgraded by red-team or risk-of-bias review
  shows that downgrade next to its rank.

## Overview

| field | value |
|---|---|
| overview_id | BMAT-OVERVIEW-YYYYMMDD-001 |
| source_run | plan_id / tournament_id this overview reformats |
| mode | quick / standard / deep / audit |
| result_label | converged / budget_bounded / single_pass / audit_only |
| coverage_note | all_lanes_incorporated / partial_coverage (carry from parallel dispatch) |
| final_workflow_label | (carry the run's final workflow label verbatim) |

## Significance

2–4 sentences: the problem, why it matters, and the gap this line of inquiry
addresses. Reformatted from the protocol/context lock and the meta-review's
framing. State the gap as a gap, not as a solved result.

## Innovation

2–3 sentences: what is genuinely new or differentiating about the top-ranked
direction relative to what the evidence lanes already established. Sourced from
the meta-review's novelty assessment; do not inflate beyond the novelty-filter
verdict.

## Specific Aims

One line per aim, each tied to a ranked hypothesis. Keep to 2–4 aims.

| aim | linked_hypothesis_id | one_line_objective | expected_information_gain |
|---|---|---|---|
| Aim 1 |  |  |  |
| Aim 2 |  |  |  |
| Aim 3 |  |  |  |

## Ranked Hypotheses

Directly from `final_ranking`. Elo for ordering/transparency; rationale is the
substance; downgrade column makes red-team/risk-of-bias visible inline.

| rank | hypothesis_id | hypothesis (one line) | elo_rating | rationale (from tournament) | downgrades (red-team / risk-of-bias) | ledger_claim_ids |
|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |

## Key Risks and Kill-Tests

The most decisive risk for each top hypothesis and the experiment that would
falsify it. Reformatted from the recommended kill-tests and the
contradiction-red-team output. A kill-test must be a test that could actually
return a negative result.

| hypothesis_id | key_risk | kill_test (falsifying experiment) | expected_result_if_true |
|---|---|---|---|
|  |  |  |  |

## Next Experiments

The concrete near-term actions, ordered. Carried from the run's recommended
experiments/next-analyses; no new experiments invented here.

| priority | experiment_or_analysis | rationale | depends_on |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |

## Provenance Footer

- Claim ledger IDs referenced: (list)
- Tournament summary: `iterations_used` / `stop_reason` / Elo aggregation status
- Verification status: claim + citation verification verdict (carry from final output)
- This overview introduces no claim absent from the above.
