import pytest

from dso.report import aggregate, bootstrap_ci, render


def record(model, harness, passed, cost, duration=10.0, tokens=1000, files=1):
    return {
        "model_key": model,
        "harness": harness,
        "passed": passed,
        "cost_usd": cost,
        "duration_s": duration,
        "tokens": {"input": tokens},
        "files_changed": files,
        "category": "bugfix",
        "task": "t",
        "grade_detail": "",
    }


def test_bootstrap_ci_is_bounded():
    low, high = bootstrap_ci([1.0, 0.0, 1.0, 1.0])
    assert 0.0 <= low <= high <= 1.0


def test_single_value_ci_collapses():
    assert bootstrap_ci([1.0]) == (1.0, 1.0)


def test_cost_per_solved_task():
    rows = aggregate(
        [
            record("m", "v0", True, 0.10),
            record("m", "v0", False, 0.10),
            record("m", "v0", True, 0.10),
        ]
    )
    assert rows[0]["runs"] == 3
    assert rows[0]["pass_rate"] == 2 / 3
    assert rows[0]["cost_per_solved"] == pytest.approx(0.15)


def test_no_solves_yields_no_cost_per_solved():
    rows = aggregate([record("m", "v0", False, 0.05)])
    assert rows[0]["cost_per_solved"] is None


def test_render_contains_tables():
    text = render([record("m", "v0", True, 0.01), record("m", "v1", True, 0.02)])
    assert "## Model x harness" in text
    assert "## Delta vs v0" in text
    assert "pass@1 by category" in text
