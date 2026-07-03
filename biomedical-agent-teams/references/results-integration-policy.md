# Results Integration Policy (semi-open loop)

BMAT can generate, rank, and converge on hypotheses (v0.6 iterated tournament),
and it can now record real tool execution (v0.7 execution layer). What it did
not have is a defined way to fold *results* — new experimental data, a
reviewer's finding, a fresh literature result, a re-analysis — back into an
existing hypothesis tournament. This policy adds that stage.

The loop is deliberately **semi-open**, not fully automatic. Following the
Virtual Lab human-in-the-loop philosophy, results are injected and mapped
programmatically, but a human checkpoint gates whether the loop re-ranks and
resumes iteration or routes to experiment design. BMAT does not close the loop
autonomously — it has no wet lab, and a fully-automatic closed loop is out of
scope. What it does is make each human-supervised turn of the loop provenance-
checked, claim-mapped, and auditable.

## When this stage runs

After a tournament has produced ranked hypotheses and the researcher returns
with a result: an assay readout, a public dataset re-analysis, a new paper, a
reviewer objection with evidence, or an internal analysis output. It also runs
inside a recurring loop (`loops/`) when a scheduled source-delta surfaces a
result bearing on live hypotheses.

## Procedure

1. **Inject the result.** Capture it as a `results_integration` record
   (`result_id`, `source_kind`, `provenance`). Nothing enters the tournament
   without provenance — the same bar as the central claim ledger.
2. **Provenance check.** Confirm the result's source is real and cited
   (accession, PMID/DOI, artifact ref, or tool-call-ledger `output_ref`). A
   result with no verifiable source is recorded as `inconclusive` and does not
   move rankings. This reuses the execution-layer discipline: a result that
   claims a tool was run must point at a `success` row in the tool-call ledger.
3. **Map to hypotheses and claims.** For each affected hypothesis, classify the
   effect: `confirms`, `refutes`, `refines`, or `inconclusive`. Tie the effect
   to specific claim IDs in the central claim ledger — never to a hypothesis as
   an undifferentiated whole.
4. **Adjust ranking signals.** Translate confirms/refutes into ranking movement:
   a confirmed key claim can raise a candidate; a refuted load-bearing claim
   must lower or eliminate it. When the Elo layer is active
   (`scripts/bmat_elo.py`), express the update as match outcomes or prior
   adjustments (`ranking_delta`), not as a hand-edited rating. When Elo is
   downgraded, apply the qualitative fallback and say so.
5. **Human checkpoint.** Present the mapped effects and proposed ranking deltas
   to the researcher. The human decides `next_action`: `resume_iteration`
   (feed back into the tournament with meta-review guidance),
   `route_to_experiment_design` (a candidate is mature enough to design a
   confirmatory experiment), `hold` (insufficient to move), or `close`
   (question resolved). BMAT does not auto-advance past this gate.
6. **Resume or route.** On `resume_iteration`, the adjusted rankings and any new
   generation guidance re-enter the iterated convergence loop. On
   `route_to_experiment_design`, hand off to the experiment-design lane with the
   confirmed/refuted claim map attached.

## Non-negotiables

- **Provenance before influence.** No result changes a ranking until its source
  is verified. Unsourced results are `inconclusive` by construction.
- **Claim-level mapping.** Effects attach to claim IDs, so a single refuted
  claim does not silently discredit an entire hypothesis and a single confirmed
  claim does not launder an otherwise weak one.
- **Human gate is mandatory.** The loop is semi-open. Re-ranking may be
  computed automatically; advancing the loop is a human decision.
- **Label honesty.** A `confirms` requires evidence that actually bears on the
  claim, at matching scope (species, tissue, assay, endpoint). Scope drift
  downgrades the effect to `refines` or `inconclusive`. Never present an
  integrated result as validation beyond what its provenance supports.
- **Data-safety floor.** Injected results must respect the data-safety floor:
  no PHI/PII, controlled-access payloads, or unpublished third-party text enters
  the record without an explicit human gate.

## Relationship to other stages

- `references/execution-layer-policy.md` — supplies the `output_ref` provenance
  a result points at when it comes from a tool run.
- `contracts/hypothesis-tournament.schema.json` — carries the optional
  `results_integration[]` array these records populate.
- `agents/results-integration-analyst.md` — the role that performs this stage.
- `agents/meta-review-synthesizer.md` — consumes the adjusted state to guide the
  next generation round when the human chooses `resume_iteration`.
