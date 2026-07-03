---
description: "Biomedical idea-discovery team for CAR cell therapy hypotheses, mechanism critique, public-omics feasibility, causal audit, ranking, red-team review, and experimental planning"
argument-hint: "<research question or idea seed> [--mode quick|standard|deep|audit]"
allowed-tools: Read, Glob, Grep, WebSearch, WebFetch, Bash
---

# Idea Discovery Team

User request: $ARGUMENTS

Run a biomedical idea-discovery workflow. Default to Korean.

## Required Preflight Contract

Before literature/database expansion, external tools, file writes, spawned-agent
claims, or final writing, produce or update runtime capability preflight and a
compact preflight contract with:
`requested_alias`, `selected_mode`, `deliverable_type`, `evidence_scope`,
`risk_class`, `required_role_outputs`, `skipped_role_outputs_with_reason`,
`external_tools_allowed`, `file_write_plan`, `stop_criteria`, and
`checkpoint_plan`. For v0.4.3+, also record `execution_strategy`,
`spawned_review_plan`, `team_spawn_plan`,
`all_role_spawn_avoidance_reason`, `nested_spawn_policy`, and
`post_team_audit_plan`. If runtime capability preflight or this contract is absent,
use the strongest downgraded workflow label supported by the produced artifacts
and runtime rather than a full idea-discovery audit.

If shell/code execution is unavailable, or if `scripts/bmat_validate.py` cannot
be run because shell/code execution is unavailable, record
`validator_unavailable_due_to_runtime` in preflight, workflow-run downgrade
reasons, and final skipped gates. Do not claim `Full protocol followed` in that
state.

## Spawned Team Bundle Policy

This recipe may run as a selected team-level spawned subagent in the first
parallel phase of a broad BMAT decision workflow. If spawned, run the internal
roles inline, do not spawn child agents unless `nested_spawn_policy` explicitly
allows it, and return one formal idea-discovery team report. The report must
include candidate hypotheses, duplicate collapse, ranking criteria, red-team
downgrades, expected-information-gain logic, useful excluded ideas, confidence,
files changed or `none`, checks run or skipped, and a handoff to the central
claim ledger.

## Use These Agents When Useful

- `protocol-context-locker`
- `life-science-lead-scientist`
- `scenario-playbook-router`
- `entity-normalizer`
- `life-science-literature-curator`
- `scientific-literature-researcher`
- `public-omics-analyst`
- `immunology-mechanism-critic`
- `causal-inference-confounder-analyst`
- `hypothesis-generator`
- `hypothesis-ranker`
- `meta-review-synthesizer`
- `results-integration-analyst`
- `bayesian-decision-modeler`
- `central-claim-ledger-evidence-graph`
- `contradiction-red-team`
- `risk-of-bias-study-quality-auditor`
- `safety-ethics-privacy-dual-use-auditor`
- `experimental-design-planner`
- `protocol-reagent-logistics-planner`
- `claim-level-evidence-verifier`
- `citation-verifier`
- `provenance-traceability-architect`
- `scientific-writer-citation-agent`
- `post-write-final-validator`

## Operating Rules

1. Start with `protocol-context-locker`: question schema, deliverable, evidence scope, risk/safety/privacy class, depth, stop criteria, and human approval gate.
2. Record runtime capabilities before claiming source-backed, tool-backed, or independent multi-agent work.
3. Run preliminary `entity-normalizer` before literature or public database expansion.
4. Lock source corpus for source-backed idea ranking, including PMID/DOI/accession/database record, version or retrieval date, inclusion status, and claim use.
5. Use a PI agenda gate: assumptions, agenda questions, privacy boundary, and success criteria.
6. Select the smallest useful lane set; do not involve every subagent by default.
7. Maintain `central-claim-ledger-evidence-graph` for all candidate hypotheses and supporting/weakening evidence.
8. Keep tumor-intrinsic, TME-intrinsic, product-intrinsic, and CAR-T-intrinsic evidence separate.
9. Use `public-omics-analyst` for feasibility. Escalate to `omics-analysis-team` only when organism, dataset/cohort, assay, contrast/endpoint, and output are specific.
10. Use `causal-inference-confounder-analyst` before causal or CAR-T-intrinsic claims.
11. Use `bayesian-decision-modeler` before recommending the first experiment.
12. Use `risk-of-bias-study-quality-auditor`, `safety-ethics-privacy-dual-use-auditor`, `contradiction-red-team`, and `claim-level-evidence-verifier` before final ranked recommendations.
13. For `standard` or `deep` candidate discovery, run the iterated hypothesis tournament loop (below) unless the user asked for a compact brainstorm. Set `iteration_budget` from the mode, and after each iteration use `meta-review-synthesizer` to decide stop-versus-iterate against the stop criterion. Never exceed `iteration_budget`.
14. For `deep` or `audit`, maintain workflow-run state and biomedical passport state and run the integrity gate before final ranked recommendations.
15. Apply `references/independent-review-policy.md` before describing validation as independent.
16. The writer can use only verified ledger material; run `post-write-final-validator` before final output.
17. Do not fabricate PMIDs, DOIs, accessions, reagent details, trial status, or public database records.
18. If this was a spawned team output, provide `spawned_team_output_status`,
    `nested_spawn_used`, and `ledger_handoff_claim_ids` before final ranking.
19. When the user brings back a result (experimental readout, dataset re-analysis, new paper, internal analysis, or reviewer finding) against an existing tournament, run `results-integration-analyst` under `references/results-integration-policy.md`: verify provenance, map the effect to claim IDs (`confirms`/`refutes`/`refines`/`inconclusive`), propose ranking deltas, and present the human gate. Do not auto-advance the loop past that gate.
20. For `standard`, `deep`, or `audit` ranked deliverables, produce a human-readable research overview using `templates/research-overview-template.md`. It is a reformat of the meta-review and `final_ranking` — Significance, Innovation, Specific Aims, ranked hypotheses with Elo and rationale, key risks and kill-tests, and next experiments. It introduces no claim absent from the central claim ledger, and it carries the run's `result_label` (e.g. `budget_bounded`) and any partial-coverage note verbatim.

## Hypothesis Tournament Loop

For `standard` and `deep` idea discovery, use
`templates/hypothesis-tournament-template.md`,
`contracts/hypothesis-tournament.schema.json`, or the same field order. The
tournament is an **iterated convergence loop**, not a single pass. Each
iteration runs the round sequence below; a meta-review then decides whether to
stop or run another iteration with improved generation guidance.

Set `iteration_budget` in the preflight before the first iteration (see Mode
Routing for defaults). Record `iterations_used` and a `stop_reason` in the
tournament state and final output.

Round sequence (one iteration):

1. R0 context/entity/source scope lock (first iteration only; carry the lock
   forward on later iterations).
2. R1 diverse hypothesis generation, usually n=8-20 when budget allows. On
   iterations after the first, seed generation with
   `generation_guidance_for_next_round` from the previous meta-review and keep
   surviving winners as protected incumbents.
3. R2 proximity clustering and duplicate collapse.
4. R3 novelty/plausibility filter.
5. R4 pairwise debate or tournament. Record each head-to-head verdict as an
   `a|b|draw` match. When shell/code execution is available, aggregate the
   matches into a single ranking with `scripts/bmat_elo.py` (Bradley-Terry by
   default; deterministic and order-independent) and record the numeric
   `elo_rating` per candidate. If code execution is unavailable, fall back to a
   qualitative pairwise ranking and mark `elo_aggregation: not_run` with the
   runtime downgrade reason.
6. R5 evolution or recombination of surviving candidates.
7. R6 Bayesian expected information gain ranking. Use Elo ratings, when present,
   as a tie-break and transparency signal — never as standalone proof of a
   hypothesis being correct.
8. R7 contradiction red-team and claim ledger update.
9. R8 meta-review and convergence check with `meta-review-synthesizer`: extract
   recurring weakness patterns across rounds and iterations, produce
   `generation_guidance_for_next_round`, and record `convergence_signals`
   (top-k stability versus the previous iteration, novel-survivor count, budget
   remaining). Then apply the stop criterion below.

### Stop Criterion

After R8, **stop** the loop when any of these holds:

- the top-k ranking is stable versus the previous iteration, or
- no new candidate survived the R3 novelty/plausibility filter this iteration, or
- `iteration_budget` (or the compute budget) is exhausted.

Otherwise **iterate**: run another iteration from R1, injecting the meta-review
`generation_guidance_for_next_round` and carrying protected incumbents forward.
On the final iteration only, produce the R8-final recommendation with
kill-tests.

Rank by novelty, evidence strength, mechanistic specificity, assayability,
feasibility, safety/privacy/translational risk, domain/translational relevance,
and expected information gain. Do not select winners by novelty alone, and do
not let a single round or a single Elo rating override the red-team and claim
ledger.

## Results Integration (semi-open loop)

When a result comes back against a tournament that already produced a ranking,
fold it in with `results-integration-analyst` under
`references/results-integration-policy.md` rather than starting a fresh
tournament. This loop is **semi-open**: mapping and ranking movement are
computed, but advancing the loop is a human decision. BMAT does not close the
loop autonomously.

1. Inject the result as a `results_integration` record (`result_id`,
   `source_kind`, `provenance`).
2. Verify provenance — accession, PMID/DOI, artifact ref, or a `success` row in
   the tool-call ledger. Unsourced results are `inconclusive` and move nothing.
3. Map the effect per claim ID: `confirms`, `refutes`, `refines`, or
   `inconclusive`, with a scope-match note (species, tissue, assay, endpoint).
4. Propose ranking deltas — as Elo match outcomes / prior adjustments when the
   Elo layer is active, or the qualitative fallback when it is downgraded.
5. Present the human gate with `next_action` options: `resume_iteration`,
   `route_to_experiment_design`, `hold`, or `close`.
6. On `resume_iteration`, re-enter the tournament from R1 with the adjusted
   rankings and meta-review guidance; on `route_to_experiment_design`, hand off
   the confirmed/refuted claim map to the experiment-design lane.

## Mode Routing

The mode sets both the depth of roles and the tournament `iteration_budget`.
Higher modes buy more test-time compute through more iterations and more
pairwise matches, not just more output fields.

| Mode | `iteration_budget` | Agent selection and depth |
|---|---|---|
| `quick` | 1 (no loop) | Generate a small number of hypotheses with `hypothesis-generator` and a light mechanism sanity check. Single pass, no meta-review loop. Use compact final output and mark literature/database status as not source-checked unless verified. |
| `standard` | up to 2 | Add runtime capability preflight, entity normalization, source corpus lock for source-backed claims, targeted literature/public-omics feasibility, mechanism critique, the iterated hypothesis tournament with `meta-review-synthesizer` and Elo aggregation when code execution is available, and a compact claim ledger. |
| `deep` | up to 4 | Add workflow-run state, causal/confounder review, Bayesian decision modeling, risk-of-bias, contradiction red-team, safety auditor when triggered, claim/citation verification, independent-review status, and post-write validation. Run the convergence loop until the stop criterion or `iteration_budget` is reached. |
| `audit` | 0 (no generation) | Do not generate new ideas first. Audit the supplied idea or ranked list against evidence, provenance, causal language, and feasibility before recommending changes. |

Never exceed `iteration_budget`. When the budget is reached before the ranking
stabilizes, stop and label the result as budget-bounded rather than converged.

For all ranked recommendations, record useful but unverified ideas as excluded
or not-ledger-verified claims rather than adding them to the final narrative.

## Final Output

1. normalized entities
2. protocol/context lock
3. agenda and assumptions
4. evidence lanes checked
5. central claim ledger summary
6. source corpus status
7. candidate hypotheses
8. hypothesis tournament summary when used, including `iterations_used`, `stop_reason`, and Elo aggregation status
9. meta-review synthesis: recurring weakness patterns and the human-readable research overview per `templates/research-overview-template.md` (Significance, Innovation, Specific Aims, ranked hypotheses with Elo + rationale, key risks and kill-tests, next experiments), carrying the run's `result_label` and any partial-coverage note
10. results integration log when a result was folded back in: per result, effect on affected claim IDs, ranking delta, human-gate status, and next action
11. ranked matrix with expected information gain
12. red-team and risk-of-bias downgrades
13. causal/confounder and safety/privacy boundary
14. recommended experiments or kill-tests
15. citation/provenance/claim verification status
16. useful but excluded or not-ledger-verified ideas
17. independent-review status
18. post-write validation verdict
19. workflow-run state, biomedical passport, and integrity-gate status
20. final claim-strength verdict
21. spawned team output status and ledger handoff if this recipe was spawned
22. final workflow label and skipped gates with reasons
