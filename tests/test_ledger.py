import sys
from pathlib import Path
import json

# Add root to sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from premium_agents.ledger import LedgerAgent

def test_ledger_run():
    agent = LedgerAgent()
    # Test with empty context
    result = agent.run({})
    
    print("Agent Name:", result["agent"])
    print("Status:", result["status"])
    print("Data Summary:")
    print(json.dumps(result["data"], indent=2))
    
    assert result["agent"] == "LEDGER"
    assert result["status"] == "complete"
    assert "live_revenue" in result["data"]
    assert "session_costs" in result["data"]
    assert "artist_count" in result["data"]
    print("\nTest Passed!")

if __name__ == "__main__":
    test_ledger_run()
