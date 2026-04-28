#!/usr/bin/env python3
"""
CLI example: List and run agents (open core + premium) using dynamic loader.
"""
import sys
from core.agent_loader import discover_agents

def main():
    agent_classes = discover_agents()
    print("Available agents:")
    for name in agent_classes:
        print(f" - {name}")

    if len(sys.argv) > 1:
        agent_name = sys.argv[1]
        if agent_name in agent_classes:
            print(f"\nInstantiating agent: {agent_name}")
            agent = agent_classes[agent_name]()
            print(f"Instance: {agent}")
            # Optionally, run the agent if it has a run() method
            if hasattr(agent, "run"):
                print("Running agent.run({})...")
                try:
                    result = agent.run({})
                    print("Result:", result)
                except NotImplementedError:
                    print("run() not implemented for this agent.")
        else:
            print(f"Agent '{agent_name}' not found.")

if __name__ == "__main__":
    main()
