import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.job_store import JobStore
from evals.judges.book_rules import validate_book_output
from live.agents.book import BookAgent


def load_fixture(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_result(case_id, result, results_root=None):
    base = Path(results_root) if results_root else Path(__file__).resolve().parents[2] / "evals" / "results"
    base.mkdir(parents=True, exist_ok=True)
    out_path = base / f"{case_id}_result.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    return out_path


class FakeJobStore(JobStore):
    def __init__(self):
        super().__init__()

    def add_job(self, job_id, job_data):
        self._jobs[job_id] = job_data


class EvalBookAgent(BookAgent):
    def __init__(self, *args, **kwargs):
        self.last_llm_raw = None
        super().__init__(*args, **kwargs)

    def llm(self, prompt, system=None, model=None, temperature=None):
        raw = super().llm(prompt, system=system, model=model, temperature=temperature)
        self.last_llm_raw = raw
        return raw


def run_case(fixture_path, results_root=None):
    fixture = load_fixture(fixture_path)
    results_base = Path(results_root) if results_root else Path(__file__).resolve().parents[2] / "evals" / "results"
    runtime_dir = results_base / "runtime" / "book" / fixture["case_id"]
    runtime_dir.mkdir(parents=True, exist_ok=True)

    agent = EvalBookAgent(job_store=FakeJobStore(), data_root=runtime_dir)

    try:
        output = agent.run(fixture["input"])
    except Exception as exc:
        output = {"error": str(exc)}

    result = {
        "case_id": fixture["case_id"],
        "input": fixture["input"],
        "expected": fixture["expected"],
        "llm_raw": agent.last_llm_raw,
        "output": output,
        "score": validate_book_output(output, fixture["expected"]),
    }
    out_path = save_result(fixture["case_id"], result, results_root=results_base)
    return result, out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BOOK eval case")
    parser.add_argument("fixture", help="Path to eval fixture JSON")
    args = parser.parse_args()

    result, out_path = run_case(args.fixture)
    print(f"Case: {result['case_id']}")
    print(f"Result: {'PASS' if result['score']['pass'] else 'FAIL'}")
    if not result["score"]["pass"]:
        print("Reasons:")
        for reason in result["score"]["reasons"]:
            print(f"- {reason}")
    print(f"Result written to: {out_path}")
    sys.exit(0 if result["score"]["pass"] else 1)
