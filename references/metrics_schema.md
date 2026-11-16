# Metrics Schema

## Health Check Output (health_metrics.json)

```json
{
  "timestamp": "number (unix epoch)",
  "skills": [
    {
      "skill": "string",
      "eval_success": "boolean",
      "eval_output": "string (truncated to 2000 chars)",
      "latency_seconds": "number",
      "has_eval_script": "boolean",
      "trigger_accuracy": "number (0-1)",
      "hallucination_rate": "number (0-1)",
      "tool_success_rate": "number (0-1)",
      "healthy": "boolean"
    }
  ]
}
```

## Per-Skill Detailed Metrics (stored in skill's own directory)

```json
{
  "skill": "string",
  "last_check": "number",
  "history": [
    {
      "timestamp": "number",
      "trigger_accuracy": "number",
      "latency_p50": "number",
      "latency_p95": "number",
      "hallucination_rate": "number",
      "tool_success_rate": "number",
      "healthy": "boolean"
    }
  ],
  "trend": "improving | stable | degrading"
}
```

## Improvement Record (learned_lessons.jsonl)

Each line is a JSON object:

```json
{
  "timestamp": "ISO8601",
  "skill": "string",
  "issue": "string",
  "metrics_before": {
    "trigger_accuracy": "number",
    "hallucination_rate": "number",
    "tool_success_rate": "number",
    "latency_seconds": "number"
  },
  "metrics_after": {
    "trigger_accuracy": "number",
    "hallucination_rate": "number",
    "tool_success_rate": "number",
    "latency_seconds": "number"
  },
  "action": "auto-merged | pr-opened | failed",
  "fixes_applied": ["string"],
  "tags": ["string"]
}
```

## Thresholds (configurable via env vars)

| Metric | Warning | Critical | Env Var |
|--------|---------|----------|---------|
| Trigger Accuracy | < 0.95 | < 0.90 | `TRIGGER_ACC_THRESHOLD` |
| Hallucination Rate | > 0.02 | > 0.05 | `HALLUCINATION_THRESHOLD` |
| Tool Success Rate | < 0.98 | < 0.95 | `TOOL_SUCCESS_THRESHOLD` |
| Latency p95 | > 20s | > 30s | `LATENCY_THRESHOLD` |
