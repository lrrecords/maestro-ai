"""
CI check: Detect README-vs-registry drift for agent names
- Run as part of CI to ensure README agent list matches actual registry
"""
import re
import sys

README = "README.md"
REGISTRIES = [
    "studio/agents/__init__.py",
    "live/agents/__init__.py",
    "label/agents/__init__.py",
]

def extract_readme_agents():
    with open(README, encoding="utf-8") as f:
        text = f.read()
    # Simple regex for agent names in README tables/lists
    return set(re.findall(r"`([A-Z_]+)`", text))

def extract_registry_agents(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # Look for agent registry dicts/lists
    return set(re.findall(r"['\"]([A-Z_]+)['\"]", text))

def main():
    readme_agents = extract_readme_agents()
    registry_agents = set()
    for reg in REGISTRIES:
        try:
            registry_agents |= extract_registry_agents(reg)
        except Exception as e:
            print(f"Could not read {reg}: {e}")
    missing = registry_agents - readme_agents
    extra = readme_agents - registry_agents
    if missing or extra:
        print("Agent registry drift detected!")
        if missing:
            print(f"Agents in registry but not README: {sorted(missing)}")
        if extra:
            print(f"Agents in README but not registry: {sorted(extra)}")
        sys.exit(1)
    print("README and registries are in sync.")

if __name__ == "__main__":
    main()
