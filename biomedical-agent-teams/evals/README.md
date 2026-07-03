# BMAT Offline Golden-Task Eval

This directory defines a public-only, synthetic golden-task gate for measuring
whether BMAT detects common biomedical audit failures. It includes 20 tasks:
18 positive failure-mode cases and 2 non-block negative controls so
false-positive block rate has a denominator.

The harness is offline. It does not call models, browse the web, or transmit
workspace context. Generate candidate outputs separately, save them as JSONL,
then score them locally.

## Input

`golden_tasks.jsonl` contains one task per line:

```json
{"task_id":"GT-001","failure_mode":"fabricated_pmid_identifier","expected_detection":["fabricated_identifier","pmid_drift"],"expected_block":true,"tags":["pmid_drift","citation","fabricated_identifier"]}
```

An output JSONL file should contain:

```json
{"task_id":"GT-001","detected_failure_modes":["fabricated_identifier"],"blocked":true,"downgraded":true,"output_text":"..."}
```

Required output fields are `task_id`, `detected_failure_modes`, and `blocked`.
`downgraded`, `output_text`, and `word_count` are optional but recommended.

## Run

```bash
python3 evals/run_golden_eval.py --tasks evals/golden_tasks.jsonl --outputs evals/sample_outputs.jsonl
```

Validate only the JSONL task/output shape with the dependency-free wrapper:

```bash
python3 evals/validate_golden_eval_schema.py --tasks evals/golden_tasks.jsonl --outputs evals/sample_outputs.jsonl
```

Use `--strict` in CI to fail when schema validation fails or an output file
contains unknown task IDs, duplicate task IDs, or missing task IDs:

```bash
python3 evals/run_golden_eval.py --tasks evals/golden_tasks.jsonl --outputs evals/sample_outputs.jsonl --strict
```

Use `--gate` for release checks. The default gate requires 10-20 tasks,
complete output integrity, schema-valid rows, perfect detection for PMID drift,
contradiction, and overclaim categories, and zero false-positive blocks in
negative controls:

```bash
python3 evals/run_golden_eval.py --tasks evals/golden_tasks.jsonl --outputs evals/sample_outputs.jsonl --strict --gate
```

## Metrics

- `unsupported_claim_detection_rate`
- `citation_drift_detection_rate`
- `fabricated_identifier_detection_rate`
- `overclaim_downgrade_rate`
- `pmid_drift_detection_rate`
- `contradiction_detection_rate`
- `tag_detection_rates`
- `false_positive_block_rate`
- `output_integrity_ok`
- `schema_valid`
- `gate`
- `unknown_output_task_ids`
- `duplicate_output_task_ids`
- `token_or_word_overhead`
