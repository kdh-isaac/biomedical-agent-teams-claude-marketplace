---
summary: 'BMAT handoff checklist for resumable biomedical workflows.'
read_when:
  - Creating a BMAT handoff or pausing long-running research work.
---
# BMAT Handoff

Use this when pausing deep, audit, omics run, translational, loop, generated-file,
or multi-artifact BMAT work.

1. Scope/status: objective, alias, selected mode, workflow label ceiling, done,
   pending, and blockers.
2. Runtime and install state: plugin version, skill root, active workspace root,
   source/cache path if package work is involved, spawned-subagent support, and
   downgrade rule.
3. Artifact state: preflight, source corpus, claim ledger, workflow-run state,
   biomedical passport, loop state, stage evaluation, final draft, and validator
   output paths.
4. Evidence/provenance: sources checked, accessions/PMIDs/DOIs, local files,
   retrieval dates, inclusion decisions, and unresolved source gaps.
5. Working tree/processes: `git status --short --branch`, local commits not
   pushed, running jobs, tmux/session attach commands, and any background tests.
6. Checks run: exact commands, results, skipped checks, and why they were skipped.
7. Next actions: ordered two to five steps for the next agent.
8. Risks/gotchas: private data boundaries, stale artifacts, mode downgrades,
   reviewer objections, brittle scripts, and claim wording that must not be
   upgraded without new evidence.
