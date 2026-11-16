#!/usr/bin/env python3
"""
Quick validation for hermes-auto-improver skill.
Checks frontmatter, structure, and referenced files.
"""
import sys
import re
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent


def validate_frontmatter():
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text()
    
    if not content.startswith("---"):
        return False, "Missing frontmatter"
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, "Invalid frontmatter format"
    
    fm_text = parts[1]
    
    # Simple parsing for required fields
    required = ["name:", "description:", "version:", "author:", "license:"]
    for field in required:
        if field not in fm_text:
            return False, f"Missing frontmatter field: {field}"
    
    # Check description length
    desc_match = re.search(r'description:\s*(.+)', fm_text)
    if desc_match:
        desc = desc_match.group(1).strip().strip('"\'')
        if len(desc) > 60:
            return False, f"Description too long: {len(desc)} chars (max 60)"
    
    return True, "Frontmatter OK"


def validate_references():
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text()
    
    # Find all references/ references
    refs = re.findall(r'references/([a-zA-Z0-9_.-]+)', content)
    missing = []
    for ref in refs:
        if not (SKILL_DIR / "references" / ref).exists():
            missing.append(ref)
    
    if missing:
        return False, f"Missing referenced files: {missing}"
    
    return True, "All references exist"


def validate_scripts():
    scripts_dir = SKILL_DIR / "scripts"
    required = ["run_health_check.py", "improve_skill.py", "sync_memory.py", "quick_validate.py", "run_eval.py"]
    missing = []
    for script in required:
        if not (scripts_dir / script).exists():
            missing.append(script)
    
    if missing:
        return False, f"Missing scripts: {missing}"
    
    return True, "All scripts exist"


def validate_workflow():
    workflow = SKILL_DIR / ".github" / "workflows" / "hermes-auto-improver.yml"
    if not workflow.exists():
        return False, "Missing GitHub Actions workflow"
    return True, "Workflow exists"


def main():
    checks = [
        ("Frontmatter", validate_frontmatter),
        ("References", validate_references),
        ("Scripts", validate_scripts),
        ("Workflow", validate_workflow),
    ]
    
    all_pass = True
    for name, check_fn in checks:
        passed, msg = check_fn()
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}: {msg}")
        if not passed:
            all_pass = False
    
    if all_pass:
        print("\nAll checks passed!")
        return 0
    else:
        print("\nSome checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
