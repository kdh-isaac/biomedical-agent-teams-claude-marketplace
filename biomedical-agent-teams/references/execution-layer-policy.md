# Execution Layer Policy

BMAT governs evidence well but historically performed few real computations
outside `omics-analysis-team`. This policy adds a declarative execution layer so
that tool use is (a) declared before it runs, (b) recorded as it runs, and
(c) verifiable after it runs — without weakening the label-honesty ceiling, the
central claim ledger, or the data-safety floor.

The rule is simple: **declare, invoke, record, then map into the ledger.** A
capability is never "used" in final wording unless a matching successful call is
recorded in the tool-call ledger.

## Scope

Applies to every workflow step that reaches an external source or runs code:
literature/database lookups (PubMed, Crossref, ClinicalTrials.gov, UniProt,
Reactome, Open Targets, ChEMBL), public omics metadata retrieval, and statistical
or bioinformatic code execution (including bundled analysis skills such as
`single-cell-rna-qc` and `pydeseq2-differential-expression`). It does not replace
`connector-binding-matrix.md` (which says *which* connector to prefer per
workflow) or `hybrid-execution-policy.md` (inline vs. spawned execution) — it
adds the *declaration + recording + verification* contract that ties those
together.

## Two Objects

The `contracts/tool-binding.schema.json` contract defines two
backward-compatible objects.

1. **`tool_registry`** — the declared catalog. Each entry names a `tool_id`, the
   `capability` it satisfies, the `surface` it runs on (`mcp` | `skill` |
   `code` | `web`), how it is invoked, the `output_kind` it returns, the
   `provenance_fields` it must record, its known `failure_modes`, and the
   `downgrade_label` to apply when it is unavailable. Registration turns a prose
   mention of a tool or skill into a validated binding rather than a dangling
   reference.
2. **`tool_call_ledger`** — the execution record. Each entry references a
   registered `tool_id`, an `inputs_digest` (short, non-sensitive summary of the
   call inputs), an `output_ref` (artifact path, accession, or PMID/DOI list),
   a `status` (`success` | `failure` | `downgraded` | `skipped`), the
   `provenance` actually captured, and the `affected_claim_ids` in the central
   claim ledger.

## Operating Rules

1. **Declare before invoke.** A step that will call a tool names the `tool_id`
   from the registry and the expected `output_kind` before invocation. An
   unregistered `tool_id` is a binding error, not a runtime improvisation.
2. **Record every invocation.** Each real call appends one `tool_call_ledger`
   entry, whether it succeeded, failed, or was downgraded. Silence is not
   allowed: a claim cannot cite a tool that has no ledger row.
3. **Map outputs into the claim ledger before writing.** Tool output is evidence
   input, not final truth. Accepted facts enter the central claim ledger with
   their `output_ref` and `provenance` before any writer uses them.
4. **No unbacked "used" wording.** If final wording says a source was checked,
   a database was queried, or an analysis was run, a `success` ledger row for a
   registered tool must exist. This is the execution-layer form of the
   label-honesty ceiling.
5. **Downgrade honestly.** When a declared tool is unavailable in the active
   runtime, record a `downgraded` (or `skipped`) row with the reason and apply
   the registry's `downgrade_label`; keep dependent claims out of
   high-confidence final wording. This mirrors the runtime capability downgrade
   rule.
6. **Respect the data-safety floor.** Never place PHI/PII, controlled-access
   data, private sample IDs, unpublished text, or patent-sensitive detail into
   `inputs_digest`, `output_ref`, or any external call without an explicit human
   gate. `inputs_digest` is a summary, never raw sensitive payload.

## Registered Skill Tools (canonical bindings)

These bundled analysis skills are first-class registered tools. Registering
them here turns a prose mention in an agent role into a declared, validatable
binding — the agent no longer references a skill that exists nowhere in the
contract layer. A concrete, schema-valid instance ships at
`tests/fixtures/tool_ledger_valid/binding.json`.

| tool_id | capability | surface | output_kind | used by | downgrade_label |
| --- | --- | --- | --- | --- | --- |
| `skill.single-cell-rna-qc` | single-cell RNA QC (counts, mito/ribo%, doublets) | `skill` | `dataset_metadata` | `scrna-qc-specialist` | `plan-only` |
| `skill.pydeseq2-differential-expression` | bulk RNA-seq differential expression (DESeq2/pydeseq2) | `skill` | `table` | `bulk-deg-analyst` | `plan-only` |

Each records provenance appropriate to its output: QC records key parameters and
pre/post cell counts; DEG records design formula, reference level, and shrinkage.
When the skill or its runtime is unavailable, the agent records a `downgraded`
call with the `plan-only` label and describes the intended analysis rather than
asserting a result exists.

## Verification

`scripts/bmat_tool_ledger_check.py` is the deterministic gate for this policy.
It confirms that every ledger entry references a registered tool, that every
tool-backed claim has at least one matching `success` row, that downgrade labels
are drawn from the allowed set, and that no "used" assertion lacks a matching
call. It runs offline, has no third-party dependencies, and never fabricates a
result — an unverifiable assertion is flagged, not assumed.

## Relationship to Other References

- `connector-binding-matrix.md` — chooses the preferred connector per workflow.
- `claude-code-runtime-capability-matrix.md` — maps capability wording to real
  Claude Code surfaces and the downgrade to apply when absent.
- `hybrid-execution-policy.md` — inline vs. spawned execution surface.
- `data-safety-floor.md` — what must never leave the local boundary.

This policy is the connective tissue: it makes the choices in those references
**declared, recorded, and checkable** rather than implicit.
