import re
from typing import Any, Dict


_REQUIRED_FIELDS = {
    "gross_box_office",
    "deductible_expenses",
    "net_box_office",
    "deal_summary",
    "artist_share",
    "promoter_share",
    "explanation",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_settle_output(
    output: Dict[str, Any],
    expected: Dict[str, Any],
    pre_calculation_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    result = {
        "schema_valid": False,
        "status_valid": False,
        "exact_values_valid": None,
        "untouched_valid": None,
        "pass": False,
        "reasons": [],
    }

    if not isinstance(output, dict):
        result["reasons"].append("Output is not a dictionary.")
        return result

    expected_status = expected.get("status")
    result["status_valid"] = output.get("status") == expected_status
    if not result["status_valid"]:
        result["reasons"].append(
            f"Expected status {expected_status!r}, got {output.get('status')!r}."
        )
        return result

    data = output.get("data")
    if not isinstance(data, dict):
        result["reasons"].append("SETTLE output is missing a data object.")
        return result

    missing = sorted(_REQUIRED_FIELDS - set(data))
    wrong_numeric_types = sorted(
        key
        for key in (
            "gross_box_office",
            "deductible_expenses",
            "net_box_office",
            "artist_share",
            "promoter_share",
        )
        if not _is_number(data.get(key))
    )

    if missing:
        result["reasons"].append(f"Missing required fields: {', '.join(missing)}.")
    if wrong_numeric_types:
        result["reasons"].append(
            f"Expected numeric settlement fields, got invalid values for: {', '.join(wrong_numeric_types)}."
        )
    if not missing and not wrong_numeric_types and isinstance(data.get("deal_summary"), str) and isinstance(data.get("explanation"), str):
        result["schema_valid"] = True

    for snippet in expected.get("deal_summary_must_include", []):
        if snippet.lower() not in str(data.get("deal_summary", "")).lower():
            result["reasons"].append(
                f"deal_summary is missing required text {snippet!r}."
            )

    exact_values = expected.get("exact_values") or {}
    if exact_values:
        mismatches = []
        for key, expected_value in exact_values.items():
            actual_value = data.get(key)
            try:
                if float(actual_value) != float(expected_value):
                    mismatches.append(f"{key}={actual_value!r} (expected {expected_value!r})")
            except (TypeError, ValueError):
                mismatches.append(f"{key}={actual_value!r} (expected {expected_value!r})")
        result["exact_values_valid"] = not mismatches
        if mismatches:
            result["reasons"].append("Exact settlement math mismatch: " + "; ".join(mismatches) + ".")

    if expected.get("no_split_expected"):
        deal_summary = str(data.get("deal_summary", ""))
        if re.search(r"(\d{1,2})\s*/\s*(\d{1,2})", deal_summary):
            result["untouched_valid"] = False
            result["reasons"].append(
                "deal_summary unexpectedly contains a parseable X/Y split."
            )
        elif not isinstance(pre_calculation_data, dict):
            result["untouched_valid"] = False
            result["reasons"].append("Missing pre-calculation data for untouched check.")
        else:
            changed = []
            for field in expected.get("preserved_fields", []):
                if pre_calculation_data.get(field) != data.get(field):
                    changed.append(field)
            result["untouched_valid"] = not changed
            if changed:
                result["reasons"].append(
                    "Fields changed despite unparseable split: " + ", ".join(changed) + "."
                )

    if (
        result["schema_valid"]
        and result["status_valid"]
        and result["exact_values_valid"] is not False
        and result["untouched_valid"] is not False
        and not result["reasons"]
    ):
        result["pass"] = True

    return result
