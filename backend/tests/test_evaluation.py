import runpy
from pathlib import Path


def test_evaluation_reports_unavailable_separately_not_as_a_pass():
    script = Path(__file__).resolve().parents[2] / "scripts" / "evaluate_live.py"
    summary = runpy.run_path(str(script))["summarize"](
        [
            {"split": "development", "assessment": "matched_expectation"},
            {"split": "holdout", "assessment": "mismatch"},
            {"split": "holdout", "assessment": "unassessed"},
        ]
    )
    assert summary["total"] == 3
    assert summary["matched_expectation"] == 1
    assert summary["mismatch"] == 1
    assert summary["unassessed"] == 1
    assert summary["splits"]["holdout"]["total"] == 2
