---
name: hermes-auto-improver
description: Auto-improves Hermes skills daily via GitHub Actions evals.
version: 1.0.0
author: Hermes Auto-Improver
license: MIT
metadata:
  hermes:
    tags: [automation, self-improvement, eval-driven, github-actions]
    related_skills: [skill-creator, power-core]
---

# Hermes Auto-Improver

## When to Use

This skill runs automatically via GitHub Actions on a daily schedule (03:00 UTC).

It should trigger when:
- You want Hermes skills to continuously improve without manual intervention
- You want health metrics (trigger accuracy, latency, hallucination rate, tool success) tracked over time
- You want degraded skills automatically fixed or flagged for review
- You want learned patterns synced to Hermes memory across sessions

**Do not invoke this skill manually** — it runs on the cloud scheduler. Use `scripts/run_health_check.py` locally for one-off checks.

A skill that runs on a cloud scheduler (GitHub Actions) to continuously improve all Hermes skills without user intervention.

## What It Does

- **Daily health checks**: Runs evals on every installed skill, measures trigger accuracy, latency, hallucination rate, tool-use success
- **Automatic improvement**: When a skill degrades, drafts fixes using skill-creator's improve_description.py + comparator/analyzer agents
- **Smart merge**: Auto-merges improvements that pass all evals; opens PR for uncertain changes
- **Memory sync**: Pushes learned patterns and lessons to local Hermes memory

## Architecture

```
GitHub Actions (daily cron)
    │
    ▼
scripts/run_health_check.py ──► collects metrics per skill
    │
    ├── all skills healthy ──► logs success, updates dashboard
    │
    └── degraded skills found ──► scripts/improve_skill.py
                                        │
                                        ▼
                                  proposes fixes
                                        │
                                        ▼
                                  runs evals on fixes
                                        │
                                        ├── passes ──► auto-commit to skill
                                        │
                                        └── uncertain ──► open PR for review
```

## Core Scripts

| Script | Purpose |
|--------|---------|
| `run_health_check.py` | Discovers all skills, runs their evals, computes metrics |
| `improve_skill.py` | Uses skill-creator agents to propose and validate fixes |
| `sync_memory.py` | Writes lessons to ~/.hermes/memory/ and skill references/ |
| `github_actions.yml` | Daily cron workflow definition |

## Metrics Tracked (per skill)

- **Trigger accuracy**: % of relevant prompts that correctly invoke the skill (target: ≥90%)
- **Latency**: p50/p95 response time (target: p95 < 30s)
- **Hallucination rate**: % of claims unverified by tool output (target: <5%)
- **Tool-use success**: % of tool calls that complete without error (target: ≥95%)

## Improvement Loop

For each degraded skill:
1. **Analyze**: Run comparator/analyzer on current vs. ideal outputs
2. **Draft**: Generate improved SKILL.md + reference files
3. **Validate**: Run quick_validate.py + full eval suite
4. **Decide**: If all metrics improve → auto-merge; else → open PR
5. **Record**: Write lesson to memory/references/

## Deployment

1. Push this skill's repo to GitHub
2. Enable GitHub Actions (Settings → Actions → Allow all actions)
3. Add `HERMES_TOKEN` secret (for memory sync back to local)
4. Workflow runs daily at 03:00 UTC

## Local Testing

```bash
# Run health check once
python scripts/run_health_check.py

# Test improvement on one skill
python scripts/improve_skill.py --skill skill-name

# Validate skill structure
python scripts/quick_validate.py
```

## GitHub Actions Workflow Notes

- **Do NOT install `hermes-agent` via pip** — it does not exist on PyPI
- Scripts are standalone: only `pyyaml` is required (`pip install pyyaml`)
- Use environment variables for paths (`HERMES_SKILLS_DIR`, `HERMES_METRICS_FILE`, `HERMES_MEMORY_FILE`, `HERMES_LESSONS_FILE`)
- Workflow uses `actions/checkout@v4` and runs from the checked-out repo
- Health check discovers skills in the workspace, not ~/.hermes/skills

## References

- `references/health_check_spec.md` — Detailed health check protocol
- `references/improvement_protocol.md` — How fixes are proposed and validated
- `references/metrics_schema.md` — JSON schema for metrics output
- `references/github_actions_setup.md` — Deployment instructions

---

*This skill improves itself too — its own evals run daily.*

## Pitfalls

- **Description too long**: skill_manage rejects descriptions >60 chars. Keep it trigger-first, one sentence, ends with period.
- **Missing referenced files**: Lint fails if SKILL.md references files that don't exist. Create all references/ files before linting.
- **GitHub Actions permissions**: Workflow needs `contents: write` and `pull-requests: write` permissions to auto-merge and create PRs.
- **HERMES_TOKEN secret**: Required for memory sync back to local Hermes. Without it, lessons only stay in GitHub repo.
- **Skill discovery**: Health check only finds skills under ~/.hermes/skills/**/SKILL.md. Skills installed elsewhere won't be checked.
- **Eval script dependency**: Skills without scripts/run_eval.py fall back to quick_validate only, giving limited metrics.
- **Auto-merge safety**: Only merges changes to SKILL.md and references/. Script/logic changes always open PR for review.
- **False positives**: Trigger accuracy measurement uses synthetic prompts; real-world accuracy may differ. Verify manually periodically.
- **Health check timeout**: Checking many skills (47+) can exceed default 60s timeout. Set `timeout=180` in run_eval.py subprocess calls or increase GitHub Actions job timeout.
- **GitHub Actions pip install hermes-agent fails**: The `hermes-agent` package does not exist on PyPI. Workflow must only install `pyyaml`. Scripts must run standalone without Hermes runtime — use environment variables for paths, not hardcoded `~/.hermes` paths.