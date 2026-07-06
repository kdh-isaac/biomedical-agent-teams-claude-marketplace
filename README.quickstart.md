# Biomedical Agent Teams Quickstart

Run these checks from the marketplace repository root:

```bash
python biomedical-agent-teams/scripts/bmat_package_check.py --root .
python biomedical-agent-teams/scripts/bmat_selftest.py --root .
```

Create a local scaffold bundle without calling external services:

```bash
python biomedical-agent-teams/scripts/bmat_run.py --alias evidence-audit-team --mode audit --question "Audit a bounded biomedical claim" --out runs/example-audit --dry-run --validate --export markdown
python biomedical-agent-teams/scripts/bmat_export_workbench.py --bundle runs/example-audit --format markdown --out runs/example-workbench.md --force
```

Use `runtime_capability_preflight.json` as the preflight artifact. For standard source-backed, deep, audit, team-DAG, or full-protocol workflows, update `lead_decision.json` before final release.
