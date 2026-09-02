import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from evals.judges.book_rules import validate_book_output
from evals.judges.settle_rules import validate_settle_output
from evals.runners.run_book_case import run_case as run_book_case
from evals.runners.run_settle_case import run_case as run_settle_case


def _write_fixture(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_run_settle_case_writes_result_and_scores_exact_split(tmp_path):
    fixture = {
        "case_id": "settle_standard",
        "input": {
            "gross_box_office": 10000,
            "deal_memo": "70/30 split after deductible expenses.",
            "expenses": 1000,
            "currency": "GBP",
        },
        "expected": {
            "status": "complete",
            "exact_values": {
                "gross_box_office": 10000,
                "deductible_expenses": 1000,
                "net_box_office": 9000,
                "artist_share": 6300,
                "promoter_share": 2700,
            },
            "deal_summary_must_include": ["70/30"],
        },
    }
    fixture_path = _write_fixture(tmp_path, "settle_standard.json", fixture)
    llm_payload = json.dumps(
        {
            "gross_box_office": 10000,
            "deductible_expenses": 1000,
            "net_box_office": 0,
            "deal_summary": "70/30 split after deductible expenses.",
            "artist_share": 0,
            "promoter_share": 0,
            "explanation": "Net is split 70/30.",
        }
    )

    with patch("live.agents.settle.BaseAgent.llm", return_value=llm_payload):
        result, out_path = run_settle_case(fixture_path, results_root=tmp_path / "results")

    assert result["score"]["pass"] is True
    assert result["output"]["data"]["artist_share"] == 6300
    assert out_path.exists()


def test_validate_settle_output_passes_when_unparseable_split_leaves_values_untouched():
    pre_calc = {
        "gross_box_office": 5000,
        "deductible_expenses": 500,
        "net_box_office": 4500,
        "deal_summary": "Flat guarantee of £2,500 against net receipts after taxes.",
        "artist_share": 2500,
        "promoter_share": 2000,
        "explanation": "Guarantee governs the settlement.",
    }
    output = {"status": "complete", "data": dict(pre_calc)}
    expected = {
        "status": "complete",
        "no_split_expected": True,
        "preserved_fields": [
            "gross_box_office",
            "deductible_expenses",
            "net_box_office",
            "artist_share",
            "promoter_share",
        ],
    }

    score = validate_settle_output(output, expected, pre_calculation_data=pre_calc)
    assert score["pass"] is True


def test_validate_settle_output_zero_case_passes_exact_math():
    output = {
        "status": "complete",
        "data": {
            "gross_box_office": 0,
            "deductible_expenses": 0,
            "net_box_office": 0,
            "deal_summary": "70/30 split after deductible expenses.",
            "artist_share": 0,
            "promoter_share": 0,
            "explanation": "Zero gross produces zero shares.",
        },
    }
    expected = {
        "status": "complete",
        "exact_values": {
            "gross_box_office": 0,
            "deductible_expenses": 0,
            "net_box_office": 0,
            "artist_share": 0,
            "promoter_share": 0,
        },
        "deal_summary_must_include": ["70/30"],
    }

    score = validate_settle_output(output, expected)
    assert score["pass"] is True


def test_run_book_case_writes_result_and_audit_trail(tmp_path):
    fixture = {
        "case_id": "book_valid",
        "input": {
            "artist": "Bicep",
            "dates": ["2026-04-02", "2026-04-15"],
            "capacity": 1800,
            "territory": "UK",
            "deal_type": "versus",
            "notes": "Prioritize London or Manchester holds.",
        },
        "expected": {
            "status": "ok",
            "action": "created",
            "required_booking_fields": [
                "artist",
                "dates",
                "capacity",
                "territory",
                "deal_type",
                "notes",
            ],
            "min_recommendations": 1,
            "min_next_actions": 1,
        },
    }
    fixture_path = _write_fixture(tmp_path, "book_valid.json", fixture)
    llm_payload = json.dumps(
        {
            "recommendations": ["Confirm avails with top venues."],
            "next_actions": ["Send holds for both target dates."],
            "risks": ["Competitive routing could compress ticket demand."],
        }
    )

    with patch("live.agents.book.BaseAgent.llm", return_value=llm_payload):
        result, out_path = run_book_case(fixture_path, results_root=tmp_path / "results")

    assert result["score"]["pass"] is True
    assert Path(result["output"]["result"]["saved_to"]).exists()
    assert out_path.exists()


def test_validate_book_output_passes_missing_required_fields_case():
    output = {
        "status": "error",
        "error": "Missing required fields: artist, dates, deal_type",
        "result": {
            "action": "error",
            "booking": {},
            "recommendations": ["Fill all required fields: artist, dates, deal type."],
        },
    }
    expected = {
        "status": "error",
        "action": "error",
        "missing_fields": ["artist", "dates", "deal_type"],
    }

    score = validate_book_output(output, expected)
    assert score["pass"] is True


def test_validate_book_output_requires_capacity_risk_keyword(tmp_path):
    saved_to = tmp_path / "booking_history.json"
    saved_to.write_text("[]", encoding="utf-8")
    output = {
        "status": "ok",
        "result": {
            "action": "created",
            "booking": {
                "artist": "Newcomer Duo",
                "dates": ["2026-06-12"],
                "capacity": 15000,
                "territory": "Faroe Islands",
                "deal_type": "guarantee",
                "notes": "First headline show in the market.",
            },
            "recommendations": ["Consider a smaller room or co-headline."],
            "next_actions": ["Ask local promoter for comps on recent electronic shows."],
            "risks": ["Capacity is oversized for likely demand in the territory."],
            "audit_trail": [
                {
                    "artist": "Newcomer Duo",
                    "dates": ["2026-06-12"],
                    "capacity": 15000,
                    "territory": "Faroe Islands",
                    "deal_type": "guarantee",
                    "notes": "First headline show in the market.",
                    "created_at": "2026-06-01T00:00:00+00:00",
                }
            ],
            "saved_to": str(saved_to),
        },
    }
    expected = {
        "status": "ok",
        "action": "created",
        "required_booking_fields": [
            "artist",
            "dates",
            "capacity",
            "territory",
            "deal_type",
            "notes",
        ],
        "risk_keywords": ["capacity", "market", "territory", "demand"],
    }

    score = validate_book_output(output, expected)
    assert score["pass"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
