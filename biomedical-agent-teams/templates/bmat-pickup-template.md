---
summary: 'BMAT pickup checklist for resuming biomedical workflows.'
read_when:
  - Resuming a BMAT run, audit bundle, omics analysis, loop, or package update.
---
# BMAT Pickup

Use this before resuming deep, audit, omics run, translational, loop,
generated-file, or package-update BMAT work.

1. Read the nearest handoff, workflow-run state, biomedical passport, checklist,
   and workspace instructions.
2. Confirm runtime state: current date/timezone, workspace root, BMAT plugin
   version, skill root, install/cache path, and available web/shell/file/spawned
   runtime surfaces.
3. Inspect working state: `git status --short --branch`, current branch, local
   commits, source/cache parity if package work is involved, and generated
   artifact folders.
4. Rehydrate artifacts by path: preflight, source corpus, claim ledger,
   stage evaluation, loop state, final draft, validation report, figures/tables,
   and logs.
5. Verify freshness: rerun the narrowest relevant parser, validator, smoke test,
   or source-cache diff before trusting old status.
6. Set next actions: two to five concrete steps, expected outputs, and stop
   criteria.
7. Preserve claim boundaries: do not upgrade workflow label, independent-review
   status, or biological claim strength unless the required artifacts and checks
   are current.
