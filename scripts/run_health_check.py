#!/usr/bin/env python3
"""
Health check runner for all Hermes skills.
Discovers installed skills, runs their evals, computes metrics.
Works standalone (no Hermes runtime required).
"""
import json
import os
import subprocess
import sys
import time
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any

# In GitHub Actions, skills are checked out to the repo
# In local, they're in ~/.hermes/skills
# Support both via env var or auto-detect
SKILLS_DIR = Path(os.environ.get("HERMES_SKILLS_DIR", Path.home() / ".hermes" / "skills"))
METRICS_FILE = Path(os.environ.get("HERMES_METRICS_FILE", Path.home() / ".hermes" / "cache" / "health_metrics.json"))


def discover_skills() -> List[Path]:
    """Find all skill directories with SKILL.md"""
    skills = []
    if not SKILLS_DIR.exists():
        print(f"Skills directory not found: {SKILLS_DIR}")
        return skills
    for cat_dir in SKILLS_DIR.iterdir():
        if cat_dir.is_dir():
            for skill_dir in cat_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills.append(skill_dir)
    return skills


def validate_skill_frontmatter(skill_dir: Path) -> tuple[bool, str]:
    """Validate skill frontmatter without hermes_tools"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, "No SKILL.md"
    
    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "Missing frontmatter"
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, "Invalid frontmatter format"
    
    try:
        fm = yaml.safe_load(parts[1])
    except Exception as e:
        return False, f"YAML parse error: {e}"
    
    required = ["name", "description", "version", "author", "license"]
    for field in required:
        if field not in fm:
            return False, f"Missing frontmatter field: {field}"
    
    desc = fm.get("description", "")
    if len(desc) > 60:
        return False, f"Description too long: {len(desc)} chars (max 60)"
    
    return True, "Frontmatter OK"


def validate_skill_references(skill_dir: Path) -> tuple[bool, str]:
    """Check that referenced files exist"""
    skill_md = skill_dir / "SKILL.md"
    content = skill_md.read_text()
    
    refs = re.findall(r'references/([a-zA-Z0-9_.-]+)', content)
    missing = []
    for ref in refs:
        if not (skill_dir / "references" / ref).exists():
            missing.append(ref)
    
    if missing:
        return False, f"Missing referenced files: {missing}"
    
    return True, "All references exist"


def run_skill_evals(skill_dir: Path) -> Dict[str, Any]:
    """Run evals for a single skill, return metrics"""
    skill_name = skill_dir.name
    start = time.time()
    
    # Try to run skill's own eval script if it exists
    eval_script = skill_dir / "scripts" / "run_eval.py"
    if eval_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(eval_script)],
                capture_output=True, text=True, timeout=120,
                cwd=skill_dir
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            success = False
            output = "TIMEOUT"
        except Exception as e:
            success = False
            output = str(e)
    else:
        # No eval script - run quick validation checks
        fm_ok, fm_msg = validate_skill_frontmatter(skill_dir)
        ref_ok, ref_msg = validate_skill_references(skill_dir)
        success = fm_ok and ref_ok
        output = f"Frontmatter: {fm_msg}; References: {ref_msg}"
    
    latency = time.time() - start
    
    return {
        "skill": skill_name,
        "eval_success": success,
        "eval_output": output[:2000],
        "latency_seconds": latency,
        "has_eval_script": eval_script.exists()
    }


def compute_trigger_accuracy(skill_dir: Path) -> float:
    """Estimate trigger accuracy by testing skill description against sample prompts"""
    # Placeholder - would use skill-creator's improve_description.py logic
    return 0.85


def compute_hallucination_rate(skill_dir: Path) -> float:
    """Estimate hallucination rate from eval outputs"""
    # Placeholder - would analyze actual outputs vs tool evidence
    return 0.03


def compute_tool_success_rate(skill_dir: Path) -> float:
    """Estimate tool-use success rate"""
    # Placeholder
    return 0.97


def main():
    print(f"Discovering skills in {SKILLS_DIR}...")
    skills = discover_skills()
    print(f"Found {len(skills)} skills")
    
    if not skills:
        print("No skills found. Exiting.")
        sys.exit(1)
    
    all_metrics = {
        "timestamp": time.time(),
        "skills": []
    }
    
    for skill_dir in skills:
        print(f"Checking {skill_dir.name}...")
        metrics = run_skill_evals(skill_dir)
        
        # Add computed metrics
        metrics["trigger_accuracy"] = compute_trigger_accuracy(skill_dir)
        metrics["hallucination_rate"] = compute_hallucination_rate(skill_dir)
        metrics["tool_success_rate"] = compute_tool_success_rate(skill_dir)
        
        # Determine health status
        healthy = (
            metrics["eval_success"] and
            metrics["trigger_accuracy"] >= 0.90 and
            metrics["hallucination_rate"] < 0.05 and
            metrics["tool_success_rate"] >= 0.95 and
            metrics["latency_seconds"] < 30
        )
        metrics["healthy"] = healthy
        
        all_metrics["skills"].append(metrics)
        status = "HEALTHY" if healthy else "DEGRADED"
        print(f"  {skill_dir.name}: {status}")
    
    # Save metrics
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(all_metrics, indent=2))
    print(f"\nMetrics saved to {METRICS_FILE}")
    
    # Print summary
    healthy_count = sum(1 for s in all_metrics["skills"] if s["healthy"])
    print(f"\nSummary: {healthy_count}/{len(all_metrics['skills'])} skills healthy")
    
    # Exit with error if any degraded (for GitHub Actions)
    if healthy_count < len(all_metrics["skills"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
