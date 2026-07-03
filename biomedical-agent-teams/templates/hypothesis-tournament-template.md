# Hypothesis Tournament Template

Use for `idea-discovery-team` standard/deep workflows and for broad research
council ideation when the user asks for candidate ideas, ranked mechanisms, or
experimentable hypotheses.

## Tournament Header

| field | value |
|---|---|
| tournament_id | HT-YYYYMMDD-001 |
| context_lock |  |
| source_scope | source-checked / partially source-checked / not source-checked |
| candidate_budget |  |
| branch_budget |  |
| iteration_budget | quick=1 / standard=2 / deep=4 / audit=0 |
| iterations_used |  |
| stop_reason | top_k_stable / no_new_survivors / budget_exhausted / single_pass / audit_only |
| ranking_method | elo-bradley-terry / elo-sequential / qualitative (downgrade fallback) |

## Candidate Pool

| hypothesis_id | hypothesis | cluster_id | status | first_seen_iteration | elo_rating | matches_played | matches_won | notes |
|---|---|---|---|---|---|---|---|---|
| H-001 |  |  | active / merged / held / discarded / winner |  |  |  |  |  |

## Rounds

R0 runs once. R1–R8 form one tournament iteration; the loop repeats from R1
using the meta-review generation guidance until the stop criterion is met or
`iteration_budget` is exhausted. Record one block of rows per iteration
(suffix round_id with the iteration index, e.g. `R1.2`).

| round_id | round_type | output_summary |
|---|---|---|
| R0 | context/entity/source scope lock |  |
| R1 | diverse generation (seeded by prior meta-review guidance on iterations ≥2) |  |
| R2 | proximity clustering and duplicate collapse |  |
| R3 | novelty/plausibility filter |  |
| R4 | pairwise debate or tournament (emit match records for Elo) |  |
| R5 | evolution or recombination |  |
| R6 | Bayesian expected information gain ranking (+ Elo aggregation via `bmat_elo.py`) |  |
| R7 | contradiction red-team and claim ledger |  |
| R8 | meta-review + convergence-check (stop or iterate) |  |

## Convergence / Meta-Review Log

One row per completed iteration. `meta-review-synthesizer` fills this and
recommends stop vs. iterate against the stop criterion.

| iteration | recurring_weakness_patterns | generation_guidance_for_next_round | top_k_stability | novel_survivors | budget_remaining | convergence_recommendation |
|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  | stop / iterate |

## Results Integration Log (semi-open loop)

One row per result folded back into the tournament. `results-integration-analyst`
fills this after verifying provenance and mapping the effect to claim IDs. The
`next_action` is a recommendation to the human gate, not an automatic advance.
See `references/results-integration-policy.md`.

| result_id | source_kind | provenance | affected_hypothesis_ids | affected_claim_ids | effect | ranking_delta | human_gate_status | next_action |
|---|---|---|---|---|---|---|---|---|
| R1 | experimental_readout / dataset_reanalysis / new_publication / internal_analysis / reviewer_finding |  |  |  | confirms / refutes / refines / inconclusive |  | pending / approved / rejected / not-required | resume_iteration / route_to_experiment_design / hold / close |

## Ranking Criteria

| hypothesis_id | novelty | evidence_strength | mechanism_specificity | assayability | feasibility | safety_or_privacy_risk | domain_translational_relevance | expected_information_gain | verdict |
|---|---|---|---|---|---|---|---|---|---|
| H-001 | low / moderate / high | low / moderate / high | low / moderate / high | low / moderate / high | low / moderate / high | low / moderate / high | low / moderate / high | low / moderate / high | advance / hold / discard |

## Safety Rule

Do not select a winner only because it is novel. For biomedical hypotheses,
penalize weak assayability, uncontrolled confounding, unsafe disclosure,
translational overreach, and low expected information gain.
