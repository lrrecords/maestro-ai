import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from label.web import quality_gate_release_json, validate_release_json


def test_quality_gate_normalizes_tbd_and_release_day_timeline():
    raw = {
        "artist": "Aria Velvet",
        "project": "Neon Letters",
        "project_type": "Release",
        "release_date": "TBD",
        "generated": "2026-06-13",
        "phases": [
            {
                "phase": "Release Day",
                "timeline": "2 weeks before release date (day of release)",
                "tasks": [
                    {
                        "task": "Go live",
                        "priority": "HIGH",
                        "status": "completed",
                        "notes": "All channels"
                    }
                ],
            }
        ],
        "critical_path": ["A"],
        "immediate_actions": ["B"],
        "blockers": ["None"],
        "recommendations": ["C"],
    }

    out = quality_gate_release_json(raw)

    assert out["release_date"] == "UNSCHEDULED"
    assert out["phases"][0]["timeline"] == "Release day"
    assert out["phases"][0]["tasks"][0]["status"] == "DONE"


def test_quality_gate_fills_missing_fields_and_validates_shape():
    raw = {
        "artist": "Aria Velvet",
        "phases": [
            {
                "phase": "Pre-Production",
                "timeline": "8 weeks before release date",
                "tasks": [
                    {
                        "task": "Finalize track list",
                        "priority": "urgent",
                        "status": "todo",
                    }
                ],
            }
        ],
    }

    out = quality_gate_release_json(raw)
    validate_release_json(out)

    assert out["project"] == "Untitled Release"
    assert out["project_type"] == "Release"
    assert out["phases"][0]["tasks"][0]["priority"] == "MEDIUM"
    assert out["phases"][0]["tasks"][0]["status"] == "PENDING"
    assert isinstance(out["recommendations"], list)
