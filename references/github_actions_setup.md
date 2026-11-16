# GitHub Actions Deployment

## Quick Setup

1. **Create a GitHub repo** for this skill (or add to existing dotfiles repo)
2. **Copy this skill** to the repo:
   ```bash
   cp -r ~/.hermes/skills/productivity/hermes-auto-improver /path/to/repo/
   ```
3. **Push to GitHub**
4. **Enable Actions** in repo settings
5. **Add secrets**:
   - `HERMES_TOKEN` — Personal access token for memory sync (optional, for pushing lessons back)
   - `GH_TOKEN` — Auto-provided by GitHub Actions

## Workflow File

Place at `.github/workflows/hermes-auto-improver.yml`:

```yaml
name: Hermes Auto-Improver

on:
  schedule:
    - cron: '0 3 * * *'  # Daily at 03:00 UTC
  workflow_dispatch:  # Manual trigger

permissions:
  contents: write
  pull-requests: write

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Hermes CLI
        run: |
          pip install hermes-agent  # or however Hermes is installed
      
      - name: Run Health Check
        run: |
          cd hermes-auto-improver
          python scripts/run_health_check.py
      
      - name: Upload Metrics
        uses: actions/upload-artifact@v4
        with:
          name: health-metrics
          path: ~/.hermes/cache/health_metrics.json
      
      - name: Check for Degraded Skills
        id: check
        run: |
          python -c "
          import json
          data = json.load(open('~/.hermes/cache/health_metrics.json'))
          degraded = [s for s in data['skills'] if not s['healthy']]
          print(f'degraded={len(degraded)}')
          print(f'skills={\" \".join(s[\"skill\"] for s in degraded)}')
          " >> $GITHUB_OUTPUT
      
      - name: Trigger Improvements
        if: steps.check.outputs.degraded != '0'
        run: |
          for skill in ${{ steps.check.outputs.skills }}; do
            python scripts/improve_skill.py --skill "$skill"
          done
      
      - name: Sync Memory
        if: env.HERMES_TOKEN != ''
        run: |
          python scripts/sync_memory.py
        env:
          HERMES_TOKEN: ${{ secrets.HERMES_TOKEN }}
      
      - name: Create PR for Uncertain Changes
        if: steps.check.outputs.degraded != '0'
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GH_TOKEN }}
          branch: auto-improve/${{ github.run_id }}
          title: "Auto-improve: degraded skills detected"
          body: |
            Health check found degraded skills: ${{ steps.check.outputs.skills }}
            
            See workflow run for details.
          labels: auto-improve, needs-review
```

## Local Testing

```bash
# Run health check locally
python scripts/run_health_check.py

# Test improvement on one skill
python scripts/improve_skill.py --skill skill-name --dry-run

# Validate skill structure
python ~/.hermes/skills/productivity/skill-creator/scripts/quick_validate.py ~/.hermes/skills/productivity/hermes-auto-improver
```
