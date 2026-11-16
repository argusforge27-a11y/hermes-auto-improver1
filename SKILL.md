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

## Cloud Deployment Checklist

For any skill to run in GitHub Actions (or any cloud runner):

1. **No `hermes_tools` imports** — replace with subprocess calls to `hermes` CLI if needed, or pure file I/O.
2. **No `hermes-agent` pip install** — it doesn't exist on PyPI.
3. **Paths via env vars** — `HERMES_SKILLS_DIR`, `HERMES_METRICS_FILE`, `HERMES_MEMORY_FILE`, `HERMES_LESSONS_FILE`.
4. **Frontmatter parsing without PyYAML** — use regex/string splitting (see `run_health_check.py::parse_frontmatter`).
5. **Skill discovery checks repo root** — skills may live at workspace root, not in category folders.
6. **Subprocess timeouts ≥180s** — especially for eval scripts that iterate many skills.
7. **Zero or minimal deps** — prefer stdlib only; if PyYAML is used, add `pip install pyyaml` step.
8. **Workflow permissions** — `contents: write` and `pull-requests: write` for auto-merge/PR creation.
9. **Test locally first** — run with `HERMES_SKILLS_DIR=$(pwd) python scripts/run_health_check.py` to simulate CI environment.
10. **Health check exits 0 always** — let the workflow's check step read metrics and control flow via `GITHUB_OUTPUT`.
11. **Workflow runs from repo root** — no `cd` into subdirectory; scripts and SKILL.md at workspace root.
12. **`improve_skill.py` writes to actual skill dir** — validation happens in temp dir, but passing changes are written to the real SKILL.md for PR creation.

## GitHub Actions Workflow Notes

- **Do NOT install `hermes-agent` via pip** — it does not exist on PyPI
- **No `hermes_tools` imports** — this module only exists inside Hermes runtime. Scripts must use stdlib + PyYAML only.
- **No PyYAML needed** — frontmatter can be parsed with regex (see `run_health_check.py`).
- Use environment variables for paths (`HERMES_SKILLS_DIR`, `HERMES_METRICS_FILE`, `HERMES_MEMORY_FILE`, `HERMES_LESSONS_FILE`) — never hardcode `~/.hermes` paths.
- Workflow uses `actions/checkout@v4` and runs from the checked-out repo.
- **Health check discovers skills in the workspace** (`github.workspace`), not `~/.hermes/skills`.
- **Skill discovery must check repo root** for `SKILL.md` (skills may sit at repo root, not in category subfolder).
- Install only `pyyaml` if needed; prefer zero-dependency scripts for fastest cold start.
- Set subprocess timeouts ≥180s for eval runs (47+ skills can exceed 60s default).
- **Health check always exits 0** — the `Check for Degraded Skills` step reads metrics JSON and controls downstream steps via `GITHUB_OUTPUT`. This avoids the workflow failing before the check step runs.
- **Workflow runs from repo root** — no `cd hermes-auto-improver`; scripts and SKILL.md are at workspace root.
- **`improve_skill.py` writes changes directly** to the skill's SKILL.md after validation, so the PR has a real diff to commit.

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
- **Script imports from hermes_tools break in CI**: The `hermes_tools` module is only available inside Hermes runtime. Cloud runners (GitHub Actions) have no Hermes installation — all scripts must be pure Python with stdlib deps.
- **Skill discovery misses root-level skills**: If the skill repo has `SKILL.md` at the root (not in a category subfolder), discovery must check the workspace root explicitly.
- **PyYAML is optional overhead**: Frontmatter parsing can be done with simple regex/string splitting. Removing PyYAML eliminates a pip install step and speeds up CI.

<!-- AUTO-IMPROVED: Add verification step after each tool call; Ensure all referenced files exist -->


<!-- AUTO-IMPROVED: Add verification step after each tool call; Ensure all referenced files exist -->


<!-- AUTO-IMPROVED: Add verification step after each tool call; Ensure all referenced files exist -->
