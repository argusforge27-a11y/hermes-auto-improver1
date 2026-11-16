#!/usr/bin/env python3
"""
Syncs learned patterns and lessons to local Hermes memory.
Works standalone (no Hermes runtime required).
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def main():
    # Config via env vars (works in GitHub Actions and local)
    metrics_file = Path(os.environ.get("HERMES_METRICS_FILE", 
                           Path.home() / ".hermes" / "cache" / "health_metrics.json"))
    memory_file = Path(os.environ.get("HERMES_MEMORY_FILE",
                           Path.home() / ".hermes" / "memory" / "memory.json"))
    lessons_file = Path(os.environ.get("HERMES_LESSONS_FILE",
                           Path.home() / ".hermes" / "skills" / "productivity" / "hermes-auto-improver" / "references" / "learned_lessons.jsonl"))
    
    if not metrics_file.exists():
        print(f"No metrics file found at {metrics_file}")
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
    
    # Append to skill's learned lessons
    lessons_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lessons_file, "a") as f:
        for lesson in lessons:
            f.write(json.dumps(lesson) + "\n")
    
    print(f"Synced {len(lessons)} lessons to {lessons_file}")
    
    # Also update main memory (optional, for cross-session)
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    if memory_file.exists():
        memory = json.loads(memory_file.read_text())
    else:
        memory = {"entries": []}
    
    for lesson in lessons:
        memory["entries"].append({
            "content": f"Skill {lesson['skill']} degraded: trigger_acc={lesson['metrics']['trigger_accuracy']:.2f}, hallucination={lesson['metrics']['hallucination_rate']:.2f}. Improvement attempted.",
            "tags": lesson["tags"]
        })
    
    memory_file.write_text(json.dumps(memory, indent=2))
    print(f"Updated main memory at {memory_file}")


if __name__ == "__main__":
    main()
