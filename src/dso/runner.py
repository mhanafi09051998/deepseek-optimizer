"""Run a coding agent against a task inside an isolated workspace."""

from __future__ import annotations

import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

from .agent import execute, opencode_version
from .grader import (
    changed_paths,
    copy_repo,
    git,
    init_repo,
    protected_violations,
    rmtree,
    run_grade,
)
from .slop import analyze
from .spec import Task

HARNESS_DIR = Path(__file__).resolve().parents[2] / "harness"

IGNORED_ARTIFACTS = [
    ".dso_tests/",
    "AGENTS.md",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    "node_modules/",
]


def _git_exclude(workspace: Path, names: list[str]) -> None:
    info = workspace / ".git" / "info"
    info.mkdir(parents=True, exist_ok=True)
    exclude = info / "exclude"
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    lines = {line.strip() for line in existing.splitlines()}
    with exclude.open("a", encoding="utf-8") as handle:
        for name in names:
            if name not in lines:
                handle.write(f"{name}\n")


def apply_harness(workspace: Path, harness: str) -> None:
    source = HARNESS_DIR / harness
    if not source.is_dir():
        raise FileNotFoundError(f"harness not found: {source}")

    names: list[str] = []
    for item in sorted(source.iterdir()):
        if item.is_file() and not item.name.startswith("README"):
            shutil.copy2(item, workspace / item.name)
            names.append(item.name)
    _git_exclude(workspace, [*names, *IGNORED_ARTIFACTS])


def diff_stats(workspace: Path) -> tuple[int, int]:
    paths = changed_paths(workspace)
    result = git(["diff", "--numstat"], workspace, check=False)
    lines = 0
    for row in result.stdout.splitlines():
        parts = row.split("\t")
        if len(parts) < 3 or parts[0] == "-":
            continue
        try:
            lines += int(parts[0]) + int(parts[1])
        except ValueError:
            continue

    status = git(["status", "--porcelain"], workspace, check=False).stdout
    for row in status.splitlines():
        if not row.startswith("??"):
            continue
        path = row[3:].strip().replace("\\", "/")
        candidate = workspace / path
        if candidate.is_file():
            try:
                lines += len(candidate.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                continue
    return len(paths), lines


def run_one(
    task: Task,
    *,
    model_key: str,
    model_id: str,
    harness: str,
    repeat: int,
    run_root: Path,
    timeout_scale: float = 1.0,
    keep: bool = False,
) -> dict:
    run_id = f"{task.id}__{model_key}__{harness}__r{repeat}"
    run_dir = run_root / run_id
    workspace = run_dir / "workspace"
    rmtree(run_dir)
    run_dir.mkdir(parents=True)

    copy_repo(task, workspace)
    init_repo(workspace)
    if harness == "v0":
        _git_exclude(workspace, IGNORED_ARTIFACTS)
    else:
        apply_harness(workspace, harness)

    timeout = int(task.max_minutes * 60 * timeout_scale)
    started = datetime.now(UTC)
    clock = time.perf_counter()
    agent = execute(workspace, model_id, task.prompt, timeout, run_dir / "transcript.jsonl")
    duration = time.perf_counter() - clock

    files_changed, diff_lines = diff_stats(workspace)
    violations = protected_violations(changed_paths(workspace))

    if agent.timed_out:
        passed, detail, grade_seconds = False, f"agent timed out after {timeout}s", 0.0
    elif agent.steps == 0:
        passed, detail, grade_seconds = False, "agent produced no completion", 0.0
    elif files_changed > task.max_files_changed:
        passed, detail, grade_seconds = (
            False,
            f"touched {files_changed} files (limit {task.max_files_changed})",
            0.0,
        )
    else:
        graded = run_grade(task, workspace)
        passed, detail, grade_seconds = graded.passed, graded.detail, graded.duration_s

    if violations:
        passed = False
        detail = f"test configuration modified: {', '.join(violations)}"

    style = analyze(agent.text_parts)
    record = {
        "schema": 2,
        "timestamp": started.isoformat(timespec="seconds"),
        "task": task.id,
        "category": task.category,
        "language": task.language,
        "difficulty": task.difficulty,
        "model_key": model_key,
        "model_id": model_id,
        "harness": harness,
        "repeat": repeat,
        "passed": passed,
        "grade_detail": detail,
        "grade_s": round(grade_seconds, 3),
        "duration_s": round(duration, 2),
        "cost_usd": round(agent.cost_usd, 6),
        "tokens": agent.tokens,
        "steps": agent.steps,
        "files_changed": files_changed,
        "diff_lines": diff_lines,
        "response_words": style["words"],
        "slop_total": style["total"],
        "slop_per_1k_words": style["per_1k_words"],
        "slop_markers": style["markers"],
        "timed_out": agent.timed_out,
        "stderr": agent.stderr,
        "opencode_version": opencode_version(),
        "run_dir": str(run_dir),
    }

    (run_dir / "record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if not keep:
        rmtree(workspace)
    return record
