# Team Spawn Plan Template

Use this for BMAT workflows that use selective spawned review or
dependency-aware team-level spawned subagents. Keep it compact enough to paste
into a final answer or save as a local workflow artifact.

| field | value |
|---|---|
| plan_id | BMAT-SPAWN-YYYYMMDD-001 |
| workflow_alias | biomedical-research-council / idea-discovery-team / omics-analysis-team / evidence-audit-team / experiment-design-team / translational-scout-team |
| mode | quick / standard / deep / audit / plan / run |
| execution_strategy | inline_only / inline_first_selective_review / team_level_selective_dag / user_requested_full_spawn / blocked |
| spawned_subagents_supported | yes / no / unknown / not-applicable |
| spawn_budget | 0 / 1 / 2 / 3 / 4 / user-approved |
| nested_spawn_allowed | false / true-with-explicit-approval |
| all_role_spawn_avoidance_reason |  |
| privacy_and_safety_boundary |  |
| central_claim_ledger_owner | main lead |
| post_team_audit_plan |  |

## Selected Spawned Reviewers

| reviewer_role | reason_selected | input_scope | required_output | status |
|---|---|---|---|---|
| claim-level-evidence-verifier |  | claim IDs / draft section | formal reviewer output | planned / running / complete / skipped |
| citation-verifier |  | source corpus rows | formal reviewer output | planned / running / complete / skipped |
| contradiction-red-team |  | candidate claims | formal reviewer output | planned / running / complete / skipped |
| biostats-repro-auditor |  | methods/results | formal reviewer output | planned / running / complete / skipped |
| omics-provenance-validator |  | omics artifacts | formal reviewer output | planned / running / complete / skipped |
| risk-of-bias-study-quality-auditor |  | evidence set | formal reviewer output | planned / running / complete / skipped |

## Team-Level Dependency DAG

| phase | spawned_team | mode | depends_on | input_scope | required_output | nested_spawn_allowed | status |
|---|---|---|---|---|---|---|---|
| 0 | main lead inline |  | none | protocol/context/source scope | lock and dispatch plan | false | planned / complete |
| 1 | idea-discovery-team | quick / standard / deep / audit | phase 0 | idea seed / decision context | formal idea team report | false | planned / running / complete / skipped |
| 1 | omics-analysis-team | plan / audit / run | phase 0 | accession/cohort/assay/contrast | formal omics team report | false | planned / running / complete / skipped |
| 1 | translational-scout-team | quick / standard / deep / audit | phase 0 | target/indication/therapy concept | formal translational team report | false | planned / running / complete / skipped |
| 2 | experiment-design-team | quick / standard / deep / audit | narrowed candidate claims | selected hypothesis/design | formal experiment-design team report | false | planned / running / complete / skipped |
| 2 | evidence-audit-team | standard / deep / audit | draft claims or results | claim ledger / draft text / report | formal evidence-audit team report | false | planned / running / complete / skipped |
| 3 | main lead inline |  | completed spawned outputs | accepted team outputs | ledger merge and final synthesis | false | planned / complete |

## Ledger Handoff

| spawned_output_id | accepted_findings | rejected_or_downgraded_findings | affected_claim_ids | lead_action |
|---|---|---|---|---|
| SO-001 |  |  |  | accept / revise / downgrade / exclude |

## Skipped Spawn Reasons

| skipped_role_or_team | reason | expected_impact |
|---|---|---|
|  |  |  |
