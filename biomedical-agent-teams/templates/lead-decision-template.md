# Lead Decision Template

Use this when `life-science-lead-scientist` and `scenario-playbook-router`
decide the BMAT mode, playbook, execution strategy, selected specialist lanes,
or team-level DAG. It is optional for quick or narrow standard answers, but
required for standard source-backed, deep, audit, `team_level_selective_dag`,
and `Full protocol followed` claims.

| field | value |
|---|---|
| decision_id | BMAT-LEAD-YYYYMMDD-001 |
| workflow_run_id |  |
| requested_alias | biomedical-research-council / idea-discovery-team / omics-analysis-team / evidence-audit-team / experiment-design-team / translational-scout-team |
| selected_mode | quick / standard / deep / audit / plan / run |
| lead_agent | life-science-lead-scientist |
| router_agent | scenario-playbook-router |
| selected_playbook | mechanism-review / public-omics-feasibility / omics-analysis / hypothesis-ranking / evidence-audit / wet-lab-validation / clinical-translation / manuscript-or-grant / general-biomedical-council |
| decision_scope |  |
| execution_strategy | inline_only / inline_first_selective_review / team_level_selective_dag / user_requested_full_spawn / blocked |
| mode_rule | quick_or_narrow_standard_optional / standard_source_backed_required / deep_required / audit_required / team_level_selective_dag_required / full_protocol_required / blocked |
| lead_route_required | true / false |
| label_ceiling | Full protocol followed / Contract-shaped artifact bundle / Compact standard workflow / Biomedical Agent Teams-informed narrative review / Limited capability-downgraded workflow / Partial workflow; formal gates skipped / Blocked |
| routing_rationale |  |

## Selected Lanes

| lane | purpose | status |
|---|---|---|
| life-science-literature-curator | source lock | planned / running / complete / skipped / blocked |
| omics-analysis-team | omics feasibility or run axis | planned / running / complete / skipped / blocked |
| experiment-design-team | validation design after narrowed claims | planned / running / complete / skipped / blocked |
| evidence-audit-team | final claim defensibility audit | planned / running / complete / skipped / blocked |

## Skipped Lanes

| lane | reason |
|---|---|
|  |  |

## Spawned Review Plan

| allowed | budget | selected_roles | rationale |
|---|---|---|---|
| false / true | 0 / 1 / 2 / 3 / 4 |  |  |

## Team Spawn Plan

| allowed | budget | selected_teams | dependency_graph | nested_spawn_allowed | rationale |
|---|---|---|---|---|---|
| false / true | 0 / 1 / 2 / 3 / 4 |  |  | false / true |  |

## Post-Team Audit Plan

Describe how the lead will merge team outputs into the central claim ledger,
which findings must be independently checked, and which claims must be
downgraded or excluded before final writing.
