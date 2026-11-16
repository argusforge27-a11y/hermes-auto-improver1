# Improvement Protocol

## When to Improve
A skill enters the improvement pipeline when any health metric falls below threshold.

## Improvement Steps

### 1. Analyze (Comparator + Analyzer)
- Run `agents/comparator.md` on current skill output vs ideal output
- Run `agents/analyzer.md` on comparison result to identify root causes
- Output: list of specific, actionable fixes

### 2. Draft Fixes
- Apply fixes to generate new SKILL.md and reference files
- Use `scripts/improve_description.py` from skill-creator for description improvements
- Preserve all working functionality

### 3. Validate
- Run `scripts/quick_validate.py` on draft skill (syntax, frontmatter, structure)
- Run full eval suite (`scripts/run_eval.py`) on draft skill
- Compare metrics: all must improve or stay same, none can regress

### 4. Decide
| Condition | Action |
|-----------|--------|
| All metrics improved, validation passed | Auto-merge to skill |
| Some metrics improved, none regressed, validation passed | Auto-merge |
| Any metric regressed OR validation failed | Open PR for human review |
| Uncertain (confidence < 0.8) | Open PR for human review |

### 5. Record
- Write lesson to `references/learned_lessons.jsonl`
- Update main Hermes memory with pattern
- Tag with skill name, issue type, fix applied

## Auto-Merge Criteria
- Git diff shows only SKILL.md and reference files (no script/logic changes without review)
- All existing evals pass
- New metrics strictly better than baseline
- No new dependencies added

## PR Template
When opening PR, include:
- Skill name and degraded metrics
- Comparator/analyzer output summary
- Proposed changes (diff)
- Validation results
- Metric comparison table
