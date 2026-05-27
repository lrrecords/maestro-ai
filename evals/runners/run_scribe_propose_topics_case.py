import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # Add repo root to path

from agents.label.scribe.scribe_agent import ScribeAgent
from core.job_store import JobStore
from evals.judges.scribe_rules import validate_scribe_output

def load_fixture(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_result(case_id, result):
    out_path = Path(__file__).resolve().parents[2] / 'evals' / 'results' / f'{case_id}_result.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return out_path

class FakeJobStore(JobStore):
    def __init__(self):
        super().__init__()
    def add_job(self, job_id, job_data):
        self._jobs[job_id] = job_data  # Never touch Redis

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run SCRIBE propose_topics eval case')
    parser.add_argument('fixture', help='Path to eval fixture JSON')
    args = parser.parse_args()
    fixture = load_fixture(args.fixture)
    # Setup agent
    job_store = FakeJobStore()
    agent = ScribeAgent(job_store=job_store, llm_provider='anthropic')
    # Run method
    try:
        output = agent.propose_topics(topic_preferences=fixture['input'].get('topic_preferences'))
    except Exception as e:
        output = {'error': str(e)}
    # Judge
    result = {
        'case_id': fixture['case_id'],
        'input': fixture['input'],
        'expected': fixture['expected'],
        'output': output,
        'score': validate_scribe_output(output, fixture['expected'])
    }
    out_path = save_result(fixture['case_id'], result)
    # Print summary
    print(f"Case: {fixture['case_id']}")
    print(f"Result: {'PASS' if result['score']['pass'] else 'FAIL'}")
    if not result['score']['pass']:
        print('Reasons:')
        for reason in result['score']['reasons']:
            print(f"- {reason}")
    print(f"Result written to: {out_path}")
    sys.exit(0 if result['score']['pass'] else 1)
