#!/usr/bin/env python3
"""
Skill improvement script.
Proposes and validates fixes for degraded skills.
Works standalone (no Hermes runtime required).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def find_skill_dir(skill_name: str, skills_root: Path) -> Path | None:
    """Find skill directory by name"""
    # Direct match
    candidate = skills_root / "productivity" / skill_name
    if candidate.exists():
        return candidate
    
    # Search all categories
    for cat in skills_root.iterdir():
        if cat.is_dir():
            candidate = cat / skill_name
            if candidate.exists():
                return candidate
    return None


def run_comparator(skill_dir: Path, current_output: str, ideal_output: str) -> dict:
    """Run blind A/B comparison (placeholder)"""
    return {
        "winner": "ideal",
        "confidence": 0.85,
        "reasoning": "Ideal output had better tool use and fewer unverified claims"
    }


def run_analyzer(skill_dir: Path, comparison_result: dict) -> dict:
    """Run post-hoc analysis (placeholder)"""
    return {
        "key_differences": [
            "Ideal output used proper validation steps",
            "Ideal output verified file existence before claiming success"
        ],
        "recommended_fixes": [
            "Add verification step after each tool call",
            "Ensure all referenced files exist"
        ]
    }


def generate_improved_skill(skill_dir: Path, analyzer_result: dict) -> str:
    """Generate improved SKILL.md (placeholder - adds comment)"""
    current = (skill_dir / "SKILL.md").read_text()
    fixes = "; ".join(analyzer_result.get("recommended_fixes", []))
    return current + f"\n\n<!-- AUTO-IMPROVED: {fixes} -->\n"


def validate_skill(skill_dir: Path) -> bool:
    """Run quick_validate.py on the skill"""
    validate_script = skill_dir / "scripts" / "quick_validate.py"
    if validate_script.exists():
        result = subprocess.run(
            [sys.executable, str(validate_script)],
            capture_output=True, text=True,
            cwd=skill_dir
        )
        return result.returncode == 0
    return True


def run_full_evals(skill_dir: Path) -> dict:
    """Run full eval suite on skill"""
    eval_script = skill_dir / "scripts" / "run_eval.py"
    if eval_script.exists():
        result = subprocess.run(
            [sys.executable, str(eval_script)],
            capture_output=True, text=True, timeout=180,
            cwd=skill_dir
        )
        return {"success": result.returncode == 0, "output": result.stdout}
    return {"success": True, "output": "No eval script"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, help="Skill name to improve")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    parser.add_argument("--skills-root", help="Root skills directory", 
                        default=os.environ.get("HERMES_SKILLS_DIR", str(Path.home() / ".hermes" / "skills")))
    args = parser.parse_args()
    
    skills_root = Path(args.skills_root)
    skill_dir = find_skill_dir(args.skill, skills_root)
    
    if not skill_dir:
        print(f"Skill not found: {args.skill} in {skills_root}")
        sys.exit(1)
    
    print(f"Improving skill: {skill_dir.name} at {skill_dir}")
    
    # Step 1: Analyze current state
    current_skill = (skill_dir / "SKILL.md").read_text()
    
    # Step 2: Run comparator/analyzer (simulated)
    comparison = run_comparator(skill_dir, current_skill, "ideal_version")
    analysis = run_analyzer(skill_dir, comparison)
    
    print(f"Comparison: {comparison['winner']} won (confidence: {comparison['confidence']})")
    print(f"Analysis: {analysis['recommended_fixes']}")
    
    # Step 3: Generate improved version
    improved = generate_improved_skill(skill_dir, analysis)
    
    # Step 4: Validate
    if not args.dry_run:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_skill = Path(tmp) / skill_dir.name
            tmp_skill.mkdir()
            (tmp_skill / "SKILL.md").write_text(improved)
            # Copy other files
            for f in skill_dir.glob("**/*"):
                if f.is_file() and f.name != "SKILL.md":
                    rel = f.relative_to(skill_dir)
                    (tmp_skill / rel).parent.mkdir(parents=True, exist_ok=True)
                    (tmp_skill / rel).write_bytes(f.read_bytes())
            
            if validate_skill(tmp_skill):
                print("Validation passed")
                eval_result = run_full_evals(tmp_skill)
                if eval_result["success"]:
                    print("Evals passed - ready to merge")
                    # In real implementation: commit changes to actual skill_dir
                    return 0
                else:
                    print(f"Evals failed: {eval_result['output']}")
                    return 1
            else:
                print("Validation failed")
                return 1
    else:
        print("Dry run - improved version generated")
        print(improved[:500] + "...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
