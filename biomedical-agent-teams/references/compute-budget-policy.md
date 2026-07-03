# Compute Budget Policy

BMAT's modes historically scaled the **number of output items** (more roles,
more fields) but not the **amount of search** — the same idea pool was ranked
whether the user asked for `quick` or `deep`. Reference systems improve with
test-time compute: more iterations, more pairwise comparisons, wider candidate
generation. This policy makes that scaling explicit and bounded, so higher modes
buy more search — not just more prose — and so a run that hits its ceiling stops
honestly rather than silently truncating.

The rule is simple: **declare the budget before the loop, spend against it, and
when it is exhausted stop gracefully with a partial-results label.** A budget is
a ceiling, never a target — a loop that converges early stops early and reports
`converged`, not `budget_exhausted`.

## Scope

Applies to every workflow that runs the iterated hypothesis tournament
(`idea-discovery-team`, and any team that embeds a tournament). It parameterizes
three axes of test-time compute:

- **`iteration_budget`** — how many convergence iterations the loop may run
  (already present in `contracts/hypothesis-tournament.schema.json`; this policy
  formalizes its budget semantics and adds the two axes below).
- **`max_pairwise_matches`** — the ceiling on R4 head-to-head debates per
  iteration. Elo/Bradley-Terry needs enough matches to be meaningful but a full
  round-robin is O(n²); this caps it and licenses a partial Swiss-style pairing.
- **`max_candidates`** — the ceiling on R1 hypotheses carried past the R3
  novelty/plausibility filter into ranking.

It does **not** replace mode routing (which still selects roles and depth) — it
supplies the numeric envelope that a mode resolves to, and that an advanced user
may override.

## The `compute_budget` object

`contracts/preflight-contract.schema.json` gains an **optional** `compute_budget`
object (all fields optional, `additionalProperties:false`):

| Field | Type | Meaning |
|---|---|---|
| `iteration_budget` | integer ≥ 0 | Max convergence iterations (mirrors the tournament field). |
| `max_pairwise_matches` | integer ≥ 0 | Max R4 head-to-head matches per iteration. |
| `max_candidates` | integer ≥ 0 | Max hypotheses ranked per iteration after the novelty filter. |
| `on_exhaustion` | enum | `graceful_stop` (stop at the ceiling, report budget-bounded) or `partial_with_label` (emit whatever ranking exists, labelled partial). |

The tournament contract (`hypothesis-tournament.schema.json`) gains the matching
**optional** `max_pairwise_matches` and `max_candidates` integers alongside the
existing `iteration_budget`, so a tournament instance records the budget it
actually ran under. Legacy instances that omit all three remain valid.

## Per-mode default budgets

A mode resolves to a default budget. Defaults cover normal use; advanced users
override any field in the preflight. `null` means "no explicit cap — governed by
the loop's own stop criterion and the runtime capability ceiling."

| Mode | `iteration_budget` | `max_candidates` | `max_pairwise_matches` | Rationale |
|---|---|---|---|---|
| `quick` | 1 | 8 | 0 (no Elo loop) | Single pass, light sanity check. |
| `standard` | 2 | 16 | 60 | Enough matches for a stable partial ranking of ~12–16 candidates. |
| `deep` | 4 | 24 | 160 | Wider generation and more iterations for convergence. |
| `audit` | 0 | n/a | n/a | No generation; audits a supplied list. |

`max_pairwise_matches` defaults are sized for partial Swiss pairing (≈ `k·n` with
small `k`), not full round-robin (`n·(n-1)/2`). When the cap is below what a full
round-robin would need, R4 runs a Swiss-style subset and records
`pairing: swiss_partial`; the Elo aggregation still applies over the matches
actually played.

## Graceful exhaustion (threads the governance spine)

When any budget axis is reached before the stop criterion fires:

1. The loop **stops** — it does not silently exceed the ceiling.
2. `stop_reason` is set to `budget_exhausted` (distinct from `top_k_stable` and
   `no_new_survivors` — a budget-bounded result is **not** a converged result).
3. The final output carries a **partial-results downgrade label**, consistent
   with the **label-honesty ceiling** and the **runtime capability downgrade**
   governance: the ranking is reported as `budget_bounded`, and the meta-review
   states which axis bound it and what an additional iteration would have tested.
4. No claim silently gains confidence from an unfinished search. The central
   claim ledger and post-write final-validator see the same budget-bounded state.

This is the same honesty contract the rest of BMAT uses: a result produced under
a ceiling is labelled as such, never presented as if the search ran to
convergence.

## Non-negotiables

- **Budget is a ceiling, not a target.** Early convergence stops early; the
  budget never forces extra iterations.
- **Exhaustion is labelled, never hidden.** `budget_exhausted` + partial label
  are mandatory when a ceiling binds the result.
- **Defaults are overridable, overrides are recorded.** The preflight records the
  budget actually used, so a run is reproducible and auditable.
- **Governance floors are unaffected.** The data-safety/dual-use floor and
  label-honesty ceiling bind regardless of budget; a larger budget never buys a
  relaxation of any floor.
