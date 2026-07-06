# Biomedical Agent Teams Skill

BMAT for Claude Code v1.1.0 is a lightweight biomedical workflow router with validator-backed artifacts. `SKILL.md` selects one of six command recipes and keeps detailed governance in lazy-loaded commands, references, schemas, templates, workflows, and scripts.

## Inventory

| Surface | Count |
|---|---:|
| Command teams | 6 |
| Role prompts | 36 |
| JSON contracts | 18 |
| Templates | 16 |
| References | 10 |
| Workflow DAGs | 6 |
| Domain packs | 3 |
| Golden tasks | 28 |

## Key Contracts

- `runtime_capability_preflight.json` is the runtime preflight artifact.
- `lead_decision.json` records the lead scientist/router decision; it is required for standard source-backed, deep, audit, team-DAG, and full-protocol workflows.
- `Full protocol followed` requires a complete artifact bundle, passing validator, lead decision evidence, and an independent/tool-backed/human review surface where required.
- Tool, reviewer, omics, or literature results that change claims, rankings, or release labels must be represented in `results_integration.json`.
- Tool-use claims require `tool_call_ledger.json`; unsupported tool-use claims block release labels.
- Workflow execution plans are represented by `workflows/*.json`.
- Domain-specific overlays live under `domain-packs/`.

## Local Checks

```bash
python scripts/bmat_package_check.py --root .
python scripts/bmat_selftest.py --root .
python evals/validate_golden_eval_schema.py --tasks evals/golden_tasks.jsonl --outputs evals/sample_outputs.jsonl
python evals/run_golden_eval.py --tasks evals/golden_tasks.jsonl --outputs evals/sample_outputs.jsonl --strict --gate
python evals/run_model_golden_eval.py --tasks evals/golden_tasks.jsonl --alias evidence-audit-team --runtime claude-code --model sample-model --out bmat_eval_outputs/model-sample.jsonl --sample-mode --then-score --gate
```

## Bundle Scaffold

```bash
python scripts/bmat_run.py --alias evidence-audit-team --mode audit --question "Audit a bounded biomedical claim" --out runs/example-audit --dry-run --validate --export markdown
python scripts/bmat_export_workbench.py --bundle runs/example-audit --format markdown --out runs/example-workbench.md --force
python scripts/bmat_entailment_check.py --bundle runs/example-audit
```

The runner scaffolds artifacts locally. It does not call external models, databases, or connectors.
