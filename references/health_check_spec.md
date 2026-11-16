# Health Check Specification

## Protocol

For each skill, the health check runs:

1. **Discovery**: Find all skills in `~/.hermes/skills/**/SKILL.md`
2. **Eval Execution**: Run skill's `scripts/run_eval.py` if exists, else quick_validate
3. **Metric Collection**:
   - Trigger accuracy (via description testing)
   - Latency (p50/p95 of eval runs)
   - Hallucination rate (unverified claims / total claims)
   - Tool-use success rate (successful calls / total calls)
4. **Health Determination**: Skill is HEALTHY iff all:
   - `eval_success == true`
   - `trigger_accuracy >= 0.90`
   - `hallucination_rate < 0.05`
   - `tool_success_rate >= 0.95`
   - `latency_p95 < 30s`

## Metric Definitions

### Trigger Accuracy
Test the skill's description against a corpus of 100 realistic prompts (50 should-trigger, 50 should-not-trigger). Score = (TP + TN) / 100.

### Latency
Wall-clock time from skill invocation to completion. Measured over 10 runs, report p50 and p95.

### Hallucination Rate
For each claim in skill output, check if it has supporting tool evidence. Rate = unverified_claims / total_claims.

### Tool-Use Success Rate
Tool calls that return exit_code=0 / total tool calls. Excludes user-blocked calls.

## Output Format

```json
{
  "timestamp": 1699999999,
  "skills": [
    {
      "skill": "skill-name",
      "eval_success": true,
      "eval_output": "...",
      "latency_seconds": 12.3,
      "trigger_accuracy": 0.92,
      "hallucination_rate": 0.02,
      "tool_success_rate": 0.98,
      "healthy": true
    }
  ]
}
```
