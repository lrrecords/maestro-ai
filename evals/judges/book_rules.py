from pathlib import Path
from typing import Any, Dict


def validate_book_output(output: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "schema_valid": False,
        "status_valid": False,
        "action_valid": False,
        "audit_valid": None,
        "risk_valid": None,
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

    payload = output.get("result")
    if not isinstance(payload, dict):
        result["reasons"].append("BOOK output is missing a result object.")
        return result

    expected_action = expected.get("action")
    result["action_valid"] = payload.get("action") == expected_action
    if not result["action_valid"]:
        result["reasons"].append(
            f"Expected action {expected_action!r}, got {payload.get('action')!r}."
        )

    if expected_status == "error":
        missing_fields = expected.get("missing_fields", [])
        error_text = str(output.get("error", "")).lower()
        for field in missing_fields:
            if field.lower() not in error_text:
                result["reasons"].append(
                    f"Validation error did not mention missing field {field!r}."
                )
        booking = payload.get("booking")
        recommendations = payload.get("recommendations")
        result["schema_valid"] = isinstance(booking, dict) and isinstance(recommendations, list)
        if not result["schema_valid"]:
            result["reasons"].append("Error payload schema is invalid.")
    else:
        booking = payload.get("booking")
        recommendations = payload.get("recommendations")
        next_actions = payload.get("next_actions")
        risks = payload.get("risks")
        audit_trail = payload.get("audit_trail")
        saved_to = payload.get("saved_to")

        required_fields = expected.get("required_booking_fields", [])
        missing_booking_fields = [
            field for field in required_fields if field not in (booking or {})
        ]
        if missing_booking_fields:
            result["reasons"].append(
                "Booking payload is missing fields: " + ", ".join(missing_booking_fields) + "."
            )

        if expected.get("min_recommendations") is not None and len(recommendations or []) < expected["min_recommendations"]:
            result["reasons"].append(
                f"Expected at least {expected['min_recommendations']} recommendations."
            )
        if expected.get("min_next_actions") is not None and len(next_actions or []) < expected["min_next_actions"]:
            result["reasons"].append(
                f"Expected at least {expected['min_next_actions']} next actions."
            )

        result["schema_valid"] = all(
            (
                isinstance(booking, dict),
                isinstance(recommendations, list),
                isinstance(next_actions, list),
                isinstance(risks, list),
                isinstance(audit_trail, list),
                isinstance(saved_to, str),
            )
        )
        if not result["schema_valid"]:
            result["reasons"].append("Success payload schema is invalid.")

        if result["schema_valid"]:
            path = Path(saved_to)
            last_audit = audit_trail[-1] if audit_trail else None
            result["audit_valid"] = path.exists() and isinstance(last_audit, dict)
            if not result["audit_valid"]:
                result["reasons"].append("Audit trail file was not written correctly.")
            elif booking.get("artist") != last_audit.get("artist"):
                result["audit_valid"] = False
                result["reasons"].append("Latest audit entry does not match persisted booking.")

        risk_keywords = [keyword.lower() for keyword in expected.get("risk_keywords", [])]
        if risk_keywords:
            risk_text = " ".join(str(item) for item in (risks or [])).lower()
            result["risk_valid"] = any(keyword in risk_text for keyword in risk_keywords)
            if not result["risk_valid"]:
                result["reasons"].append(
                    "Risk output did not mention any expected capacity/territory risk keywords."
                )

    if (
        result["schema_valid"]
        and result["status_valid"]
        and result["action_valid"]
        and result["audit_valid"] is not False
        and result["risk_valid"] is not False
        and not result["reasons"]
    ):
        result["pass"] = True

    return result
