# Biomedical Agent Teams — Claude Code Marketplace

Current plugin version: `1.0.0`
Runtime: Claude Code
Supported release surface: root `.claude-plugin/marketplace.json` plus `biomedical-agent-teams/.claude-plugin/plugin.json` and `biomedical-agent-teams/SKILL.md`.

Biomedical Agent Teams (BMAT) is a Claude Code plugin for biomedical research coordination, evidence audit, public omics planning, experiment design, translational scouting, and hypothesis discovery. The v1.0 package ships a lightweight router, 6 command teams, 36 role prompts, workflow DAGs, domain packs, lead-decision routing contracts, results-integration contracts, tool-call ledger checks, and validator-backed artifact bundles.

## Install

```bash
claude plugin marketplace add biomedical-agent-teams <this-repo-path-or-git-url>
claude plugin add biomedical-agent-teams
```

## Verify

```bash
python biomedical-agent-teams/scripts/bmat_package_check.py --root .
python biomedical-agent-teams/scripts/bmat_package_check.py --root biomedical-agent-teams
python biomedical-agent-teams/scripts/bmat_selftest.py --root .
python biomedical-agent-teams/evals/run_golden_eval.py --tasks biomedical-agent-teams/evals/golden_tasks.jsonl --outputs biomedical-agent-teams/evals/sample_outputs.jsonl --strict --gate
```

## v1.0 Release Surface

- Canonical runtime artifact: `runtime_capability_preflight.json`
- Legacy accepted alias: `preflight.json`
- Required full-protocol core artifacts: `run_state.json`, `runtime_capability_preflight.json`, `source_corpus.json`, `claim_ledger.json`, `stage_evaluation.json`, `post_write_validation.json`, and `final.md`
- Lead routing gate: `lead_decision.json` is required for standard source-backed, deep, audit, `team_level_selective_dag`, and `Full protocol followed` workflows
- Conditional gates: `results_integration.json` and `tool_call_ledger.json` when final wording, ranking, or release labels depend on tool/reviewer/result-backed evidence
- New workflow surfaces: `workflows/*.json`, `domain-packs/*`, `scripts/bmat_run.py`, `scripts/bmat_export_workbench.py`, `scripts/bmat_entailment_check.py`, and `evals/run_model_golden_eval.py`

Historical note: earlier releases were ported from a separate agent-team package. The current repository is maintained as a Claude Code marketplace package and no longer ships legacy TOML reviewer templates.
