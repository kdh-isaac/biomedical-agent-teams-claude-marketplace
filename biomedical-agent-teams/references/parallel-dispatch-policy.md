# Parallel Dispatch Policy

BMAT's coordination is a **star topology**: a Lead delegates to specialist
teams, each team reports back to the Lead, and the Lead is the single point that
reconciles conflicts and writes the final synthesis. Historically that star ran
**sequentially** — the Lead spawned one lane, waited, spawned the next. When the
lanes are genuinely independent (a literature scan, an omics-feasibility check,
and a mechanistic-plausibility pass share no inputs), serializing them adds
latency for no analytical benefit.

This policy adds **parallel dispatch of independent lanes** while preserving the
star. Independent lanes fan out concurrently; dependent lanes still wait for
their prerequisites; and the Lead remains the **single join point** where
results merge. Parallelism is a scheduling optimization over the existing
dependency graph — it changes *when* lanes run, never *who* arbitrates.

## What stays invariant (non-negotiable)

- **Star preserved.** Specialist teams never talk to each other laterally. A lane
  that needs another lane's output declares a `depends_on` edge and receives that
  output *through the Lead*, not by peer-to-peer messaging. Parallel dispatch
  does not introduce a mesh.
- **Single join point.** The final synthesis, conflict arbitration, and the
  central claim ledger remain the Lead's sole responsibility. Fan-out widens the
  middle of the DAG; the join at the top is always one Lead.
- **The dependency graph is authoritative.** `team_spawn_plan.dependency_graph`
  (already carrying `phase` + `depends_on` per team) defines what may run in
  parallel. Two teams may be dispatched concurrently **iff** neither is in the
  other's transitive `depends_on` set. W7 adds execution semantics over this
  existing declaration; it does not add a new way to declare structure.
- **Governance runs per lane, joins at the Lead.** Every lane is still bound by
  the label-honesty ceiling, the data-safety/dual-use floor, and the tool
  ledger. A parallel lane cannot bypass a validator by running off to the side —
  its claims enter the same central ledger at join time.

## Execution semantics

A lane is **dispatchable** when all teams in its `depends_on` set have completed.
The Lead computes dispatch waves from the dependency graph:

1. **Wave 0** = all teams with empty `depends_on` (the independent lanes).
2. Dispatch every team in the current wave **concurrently** (in Claude Science,
   a `host.delegate` fan-out with `wait=False`, then collect).
3. When the join policy for the wave is satisfied, mark those teams complete and
   recompute the next wave (teams whose `depends_on` is now fully satisfied).
4. Repeat until no dispatchable teams remain. The final wave's results flow to
   the Lead for synthesis.

Sequential execution is the **degenerate case** of this schedule (every wave has
one team, or `parallel_dispatch` is absent/false) — so existing single-lane
plans behave exactly as before.

## The `parallel_dispatch` object

`team_spawn_plan` gains an **optional** `parallel_dispatch` object (all fields
optional, `additionalProperties:false`). Omitting it means sequential execution —
fully backward-compatible.

| Field | Type | Meaning |
|-------|------|---------|
| `enabled` | boolean | Whether the Lead may dispatch independent lanes concurrently. Default (absent) = sequential. |
| `max_parallel_lanes` | integer ≥ 1 | Ceiling on concurrently in-flight lanes per wave. Bounds fan-out width so a wide DAG doesn't over-subscribe the runtime. |
| `join_policy` | enum | How the Lead closes a wave: `wait_all` (default) or `wait_quorum`. |
| `quorum` | integer ≥ 1 | Required only when `join_policy = wait_quorum`: the number of lanes in the wave whose completion releases the join. |

### Join policies

- **`wait_all`** (default, conservative) — the wave closes only when every
  dispatched lane returns. Use when the synthesis needs all lanes (the common
  case). No lane's result is dropped.
- **`wait_quorum`** — the wave closes when `quorum` lanes return; slower lanes
  are still collected if they arrive before synthesis, but the Lead is not
  blocked on a straggler. Use only when the lanes are **substitutable evidence**
  (e.g. three redundant literature sources) and partial coverage is honestly
  acceptable. A quorum join **must** be reflected in the output: if any lane was
  not incorporated, the result carries a partial-coverage note — the label
  honesty ceiling applies to *lane coverage* exactly as it applies to compute
  budget. Never use `wait_quorum` to silently drop a lane that failed.

## Interaction with the compute budget

Parallel dispatch and the compute budget are orthogonal ceilings and both apply.
`max_parallel_lanes` bounds **concurrency** (how many lanes run at once);
`compute_budget` bounds **depth** (how much search each lane's tournament runs).
A wide fan-out of shallow lanes and a narrow fan-out of deep lanes are both
valid; the two limits compose without interacting.

## Failure and honesty

- A lane that **errors** is reported as failed, not silently dropped. Under
  `wait_all`, a failed lane blocks the join and the Lead surfaces the failure.
  Under `wait_quorum`, a failed lane counts against coverage and triggers the
  partial-coverage note.
- Parallel dispatch never changes a claim's provenance. Each lane's tool calls
  and evidence enter the **same** central claim ledger; concurrency is invisible
  to the post-write final validator.
- The Lead's synthesis must not present a quorum-closed wave as if all lanes
  agreed. Honest coverage reporting is a hard requirement, mirroring
  `budget_bounded` in the compute-budget policy.

## Non-negotiables

1. No lateral team-to-team communication — the star holds.
2. One Lead join point for synthesis, arbitration, and the ledger.
3. The dependency graph is authoritative; concurrency is derived from it, never
   asserted against it.
4. `wait_quorum` requires an honest partial-coverage label whenever a lane is
   not incorporated.
5. Per-lane governance (label honesty, data-safety floor, tool ledger) is
   preserved; join does not launder unvalidated claims.
