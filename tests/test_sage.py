import sys
from pathlib import Path
import json

# Add root to sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from premium_agents.sage_daily_brief import SageAgent

def test_sage_run():
    agent = SageAgent()
    # Test with daily scope
    result = agent.run({"scope": "daily"})
    
    print("Agent Name:", result["agent"])
    print("Status:", result["status"])
    if result["status"] == "error":
        print("Error Message:", result.get("message"))
        return
    print("Data Summary:")
    print(json.dumps(result["data"], indent=2))
    
    assert result["agent"] == "SAGE"
    assert result["status"] == "complete"
    assert "headline" in result["data"]
    assert "priority_actions" in result["data"]
    print("\nTest Passed!")

if __name__ == "__main__":
    test_sage_run()
