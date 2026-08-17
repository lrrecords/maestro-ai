import re
from typing import Any, Dict, List

ALLOWED_DOMAINS = {
    "drumming", "bass playing", "music production", "mixing", "recording", "mastering",
    "music business", "record labels", "music distribution", "brand reviews", "gear reviews"
}
FORBIDDEN_THEMES = {
    "productivity", "personal branding", "release reviews", "generic entrepreneurship",
    "mindset coaching", "generic sales", "startup productivity", "non-music SaaS reviews",
    "consumer electronics unrelated to music", "morning routine", "life hacks"
}

REFUSAL_TEXT = "Sorry, I only cover music industry topics as described above."

def validate_scribe_output(output: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "schema_valid": False,
        "topic_count_valid": None,
        "forbidden_theme_found": False,
        "required_domain_missing": False,
        "refusal_valid": None,
        "pass": False,
        "reasons": []
    }
    blog_topics = output.get("blogTopics")
    should_succeed = expected.get("should_succeed")
    # Schema check
    if isinstance(blog_topics, list) and all(isinstance(t, dict) and "title" in t and "rationale" in t for t in blog_topics):
        result["schema_valid"] = True
    else:
        result["reasons"].append("Output does not match blogTopics schema.")
    # Refusal check
    if not should_succeed:
        if blog_topics and len(blog_topics) == 1 and REFUSAL_TEXT in (blog_topics[0].get("title", "") + blog_topics[0].get("rationale", "")):
            result["refusal_valid"] = True
        else:
            result["refusal_valid"] = False
            result["reasons"].append("Expected refusal text not found.")
    # Topic count check
    if should_succeed:
        expected_count = expected.get("expected_topic_count")
        if expected_count is not None:
            result["topic_count_valid"] = len(blog_topics) == expected_count
            if not result["topic_count_valid"]:
                result["reasons"].append(f"Expected {expected_count} topics, got {len(blog_topics)}.")
    # Forbidden/required domain checks
    titles = [t.get("title", "") for t in blog_topics] if blog_topics else []
    all_text = " ".join(titles).lower()
    forbidden = expected.get("forbidden_domain_tags", [])
    for tag in forbidden:
        if tag.lower() in all_text:
            result["forbidden_theme_found"] = True
            result["reasons"].append(f"Forbidden domain '{tag}' found in output.")
    required = expected.get("required_domain_tags", [])
    for tag in required:
        if tag.lower() not in all_text:
            result["required_domain_missing"] = True
            result["reasons"].append(f"Required domain '{tag}' missing from output.")
    # Final pass/fail
    if result["schema_valid"] and not result["forbidden_theme_found"] and not result["required_domain_missing"]:
        if should_succeed:
            if result["topic_count_valid"] is not False:
                result["pass"] = True
        else:
            if result["refusal_valid"]:
                result["pass"] = True
    return result
