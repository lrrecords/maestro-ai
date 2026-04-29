import json
import datetime
import subprocess

# Auto-update claude-progress.md after test run

def update_progress_log():
    now = datetime.datetime.now().isoformat()
    with open('claude-progress.md', 'a') as f:
        f.write(f"\nSession Log Entry: {now}\n")
        f.write("Verification run: python test_agents.py\n")
        f.write("Evidence captured: test_agents.py output\n")

# Enforce only one in_progress feature

def enforce_feature_state():
    with open('feature_list.json') as f:
        features = json.load(f)
    in_progress = [ft for ft in features if ft['status'] == 'in_progress']
    if len(in_progress) > 1:
        raise Exception('More than one feature is in_progress!')

# Capture test output as evidence

def capture_evidence():
    result = subprocess.run(['python', 'test_agents.py'], capture_output=True, text=True)
    with open('claude-progress.md', 'a') as f:
        f.write(f"Test output:\n{result.stdout}\n")

if __name__ == "__main__":
    update_progress_log()
    enforce_feature_state()
    capture_evidence()
