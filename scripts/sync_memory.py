#!/usr/bin/env python3
"""
Syncs learned patterns and lessons to local Hermes memory.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".hermes" / "memory"
MEMORY_FILE = MEMORY_DIR / "memory.json"
USER_FILE = MEMORY_DIR / "user.json"

# Also sync to skill's references for persistence
SKILL_DIR = Path.home() / ".hermes" / "skills" / "productivity" / "hermes-auto-improver"
REFERENCES_DIR = SKILL_DIR / "references"
LESSONS_FILE = REFERENCES_DIR / "learned_lessons.jsonl"


def load_memory() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {"entries": []}


def save_memory(data: dict):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(data, indent=2))


def append_lesson(lesson: dict):
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    with open(LESSONS_FILE, "a") as f:
        f.write(json.dumps(lesson) + "\n")


def main():
    # Load health check metrics
    metrics_file = Path.home() / ".hermes" / "cache" / "health_metrics.json"
    if not metrics_file.exists():
        print("No metrics file found")
        return
    
    metrics = json.loads(metrics_file.read_text())
    
    # Generate lessons from degraded skills
    lessons = []
    for skill in metrics.get("skills", []):
        if not skill.get("healthy", True):
            lesson = {
                "timestamp": datetime.now().isoformat(),
                "skill": skill["skill"],
                "issue": "Health check failed",
                "metrics": {
                    "trigger_accuracy": skill.get("trigger_accuracy"),
                    "hallucination_rate": skill.get("hallucination_rate"),
                    "tool_success_rate": skill.get("tool_success_rate"),
                    "latency_seconds": skill.get("latency_seconds")
                },
                "action": "improvement_attempted",
                "tags": ["auto-improver", "health-check", skill["skill"]]
            }
            lessons.append(lesson)
    
    # Also record successful improvements
    # (In real implementation, this would come from git history)
    
    # Append to skill's learned lessons
    for lesson in lessons:
        append_lesson(lesson)
    
    print(f"Synced {len(lessons)} lessons to {LESSONS_FILE}")
    
    # Also update main memory (optional, for cross-session)
    memory = load_memory()
    for lesson in lessons:
        memory["entries"].append({
            "content": f"Skill {lesson['skill']} degraded: trigger_acc={lesson['metrics']['trigger_accuracy']:.2f}, hallucination={lesson['metrics']['hallucination_rate']:.2f}. Improvement attempted.",
            "tags": lesson["tags"]
        })
    save_memory(memory)
    print(f"Updated main memory at {MEMORY_FILE}")


if __name__ == "__main__":
    main()
