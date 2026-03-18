from live.agents import REGISTRY as LIVE
from studio.agents import REGISTRY as STUDIO

from live.agents.schema import LIVE_AGENT_SCHEMAS
from studio.agents.schema import STUDIO_AGENT_SCHEMAS


def validate(dept_name: str, registry: dict, schemas: dict):
    print(f"{dept_name} agents:  ", sorted(registry.keys()))
    print(f"{dept_name} schemas: ", sorted(schemas.keys()))

    missing = [slug for slug in registry.keys() if slug not in schemas]
    extra = [slug for slug in schemas.keys() if slug not in registry]

    assert not missing, f"{dept_name}: missing schemas for {missing}"
    assert not extra, f"{dept_name}: schema exists for unknown agents {extra}"

    for slug, cls in registry.items():
        sch = schemas[slug]
        assert isinstance(sch, dict), f"{dept_name}/{slug}: schema must be dict"
        assert "fields" in sch and isinstance(sch["fields"], list), f"{dept_name}/{slug}: schema missing fields list"
        assert hasattr(cls, "description"), f"{dept_name}/{slug}: agent missing description"
        assert hasattr(cls, "name"), f"{dept_name}/{slug}: agent missing name"
        assert hasattr(cls, "department"), f"{dept_name}/{slug}: agent missing department"

        # Validate fields
        for f in sch["fields"]:
            assert "name" in f and "type" in f, f"{dept_name}/{slug}: bad field: {f}"
            assert isinstance(f["name"], str) and f["name"], f"{dept_name}/{slug}: field.name must be non-empty string"
            assert f["type"] in {"text", "number", "textarea", "select", "checkbox"}, f"{dept_name}/{slug}: invalid field.type {f['type']}"
            if f["type"] == "select":
                assert "options" in f and isinstance(f["options"], list) and f["options"], f"{dept_name}/{slug}: select field needs options"

        print(f"  OK  {cls.name:<8} — {len(sch['fields'])} fields")


if __name__ == "__main__":
    validate("LIVE", LIVE, LIVE_AGENT_SCHEMAS)
    validate("STUDIO", STUDIO, STUDIO_AGENT_SCHEMAS)
    print("All agent registries + schemas OK")