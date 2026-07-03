# Biomedical Agent Teams — Claude Code Edition

Claude Code 전용 포트: [kdh-isaac/biomedical-agent-teams-codex-marketplace](https://github.com/kdh-isaac/biomedical-agent-teams-codex-marketplace) v0.4.9 를 Claude Code 마켓플레이스 형식(v0.5.0)으로 변환한 패키지.

## 설치

```bash
claude plugin marketplace add biomedical-agent-teams <이 레포 경로 또는 GitHub URL>
claude plugin add biomedical-agent-teams
```

## 구성

- **6개 연구 팀 커맨드**: `biomedical-research-council`, `idea-discovery-team`, `omics-analysis-team`, `evidence-audit-team`, `experiment-design-team`, `translational-scout-team`
- **37개 전문 에이전트 프롬프트** (agents/)
- **검증 스크립트** (scripts/bmat_package_check.py, bmat_validate.py)
- **황금 평가 케이스** (evals/) — PMID drift, 모순, 과장 탐지

## 원본 대비 변경 사항 (v0.5.0)

| 항목 | Codex (v0.4.9) | Claude Code (v0.5.0) |
|------|---------------|----------------------|
| 마켓플레이스 | `.agents/plugins/marketplace.json` | `.claude-plugin/marketplace.json` |
| 플러그인 메타 | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| Reviewer 스폰 | TOML 템플릿 (`codex-agents/*.toml`) | Claude Code `Agent` 툴 (agent/*.md 직접 참조) |
| 경로 구조 | `plugins/.../skills/biomedical-agent-teams/` | `biomedical-agent-teams/` (플래트닝) |
| `agent-registry.json` | `toml_template_path` 포함 | 제거됨, `runtime: "claude-code"` |
| `source-manifest.json` | `runtime: "codex"` | `runtime: "claude-code"` |
| capability matrix | `codex-runtime-capability-matrix.md` | `claude-code-runtime-capability-matrix.md` |
| 패키지 검사 스크립트 | Codex default-prompt 한도 검사 | Claude Code plugin.json 필드 검사 |

## 검증

```bash
python biomedical-agent-teams/scripts/bmat_package_check.py --root .
python biomedical-agent-teams/scripts/bmat_selftest.py --root .
```
