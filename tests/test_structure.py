from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "dso"
MAX_LINES = 300


def test_source_files_stay_small():
    oversized = []
    for path in sorted(SRC.rglob("*.py")):
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > MAX_LINES:
            oversized.append(f"{path.name}: {lines} lines")
    assert not oversized, "split these files: " + ", ".join(oversized)


def test_core_modules_exist():
    for name in (
        "agent.py",
        "cli.py",
        "grader.py",
        "report.py",
        "runner.py",
        "slop.py",
        "spec.py",
    ):
        assert (SRC / name).is_file()
