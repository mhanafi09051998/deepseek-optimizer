"""Workspace preparation and deterministic grading."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .spec import Task

HIDDEN_TESTS = ".dso_tests"
IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", "*.pyc", "node_modules", ".venv", "venv", HIDDEN_TESTS
)

# A model must not be able to neutralize grading through test configuration.
PROTECTED_NAMES = {
    "conftest.py",
    "pytest.ini",
    "setup.cfg",
    "tox.ini",
    "sitecustomize.py",
}

ANSI = re.compile(r"\x1b\[[0-9;]*m")


@dataclass
class GradeResult:
    passed: bool
    detail: str
    duration_s: float


def rmtree(path: Path) -> None:
    """Remove a tree, clearing read-only flags that Windows leaves on git objects."""

    def onexc(func, target, _exc):  # noqa: ANN001
        try:
            os.chmod(target, 0o700)
            func(target)
        except OSError:
            pass

    if path.exists():
        shutil.rmtree(path, onexc=onexc)


def copy_repo(task: Task, dest: Path) -> None:
    rmtree(dest)
    shutil.copytree(task.repo_dir, dest, ignore=IGNORE)


def git(
    args: list[str], cwd: Path, check: bool = True, isolated: bool = False
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if isolated:
        # Stop git from discovering a repository above the workspace. Without
        # this, running inside a checkout applies patches relative to that
        # outer repository root and silently skips every hunk.
        env["GIT_CEILING_DIRECTORIES"] = str(Path(cwd).resolve().parent)
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
        env=env,
    )


def init_repo(workspace: Path) -> None:
    git(["init", "-q"], workspace)
    git(["config", "user.email", "dso@example.invalid"], workspace)
    git(["config", "user.name", "dso"], workspace)
    git(["add", "-A"], workspace)
    git(["commit", "-q", "-m", "baseline"], workspace)


def apply_patch(workspace: Path, patch: Path) -> None:
    result = git(
        ["apply", "--whitespace=nowarn", str(patch.resolve())],
        workspace,
        check=False,
        isolated=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git apply failed: {result.stderr.strip()}")


def changed_paths(workspace: Path) -> list[str]:
    if not (workspace / ".git").exists():
        return []
    result = git(["status", "--porcelain"], workspace, check=False)
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return paths


def protected_violations(paths: list[str]) -> list[str]:
    hits = []
    for path in paths:
        name = Path(path).name
        if "/" not in path and name in PROTECTED_NAMES:
            hits.append(path)
    return hits


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(cwd), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["NO_COLOR"] = "1"
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        out = ANSI.sub("", (proc.stdout or "") + (proc.stderr or ""))
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 124, f"grading timed out after {timeout}s"


def _copy_tests(task: Task, workspace: Path) -> None:
    target = workspace / HIDDEN_TESTS
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(task.tests_dir, target)


def _pytest(workspace: Path, timeout: int, target: str = HIDDEN_TESTS) -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "-o",
        "addopts=",
        target,
    ]
    return _run(cmd, workspace, timeout)


def _node(workspace: Path, timeout: int) -> tuple[int, str]:
    root = workspace / HIDDEN_TESTS
    files = sorted(
        path for pattern in ("*.test.ts", "*.test.js", "*.test.mjs")
        for path in root.glob(pattern)
    )
    if not files:
        return 1, "no node test files found"
    cmd = [
        "node",
        "--experimental-strip-types",
        "--test",
        *[str(path.relative_to(workspace)).replace("\\", "/") for path in files],
    ]
    return _run(cmd, workspace, timeout)


def _count_tests(source: str) -> int:
    py = len(re.findall(r"^\s*def test_", source, re.MULTILINE))
    js = len(re.findall(r"^\s*(?:it|test)\s*\(", source, re.MULTILINE))
    return py + js


def _mutation(task: Task, workspace: Path, test_override: Path | None) -> GradeResult:
    assert task.test_file
    test_path = test_override or (workspace / task.test_file)
    if not test_path.exists():
        return GradeResult(False, f"expected test file not found: {task.test_file}", 0.0)

    source = test_path.read_text(encoding="utf-8", errors="replace")
    if _count_tests(source) < 2:
        return GradeResult(False, "fewer than 2 test functions", 0.0)

    start = time.perf_counter()
    code, out = _run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(test_path)],
        workspace,
        task.grade_timeout,
    )
    if code == 0:
        return GradeResult(
            False,
            "written tests pass on the buggy code (they catch nothing)",
            time.perf_counter() - start,
        )

    with tempfile.TemporaryDirectory() as td:
        fixed = Path(td) / "fixed"
        copy_repo(task, fixed)
        apply_patch(fixed, task.solution_patch)
        dest = fixed / task.test_file
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(source, encoding="utf-8")
        code2, out2 = _run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(dest)],
            fixed,
            task.grade_timeout,
        )
    elapsed = time.perf_counter() - start
    if code2 != 0:
        return GradeResult(False, f"tests fail on the fixed implementation\n{out2[-600:]}", elapsed)
    return GradeResult(True, "tests fail on buggy code and pass on fixed code", elapsed)


def run_reference(task: Task, workspace: Path, test_path: Path) -> GradeResult:
    """Run a known test file directly. Used to validate mutation tasks."""
    start = time.perf_counter()
    code, out = _run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(test_path)],
        workspace,
        task.grade_timeout,
    )
    return GradeResult(code == 0, out[-800:], time.perf_counter() - start)


def run_grade(task: Task, workspace: Path, test_override: Path | None = None) -> GradeResult:
    violations = protected_violations(changed_paths(workspace))
    if violations:
        return GradeResult(False, f"test configuration modified: {', '.join(violations)}", 0.0)

    start = time.perf_counter()
    if task.grade_type == "mutation":
        return _mutation(task, workspace, test_override)

    _copy_tests(task, workspace)
    if task.grade_type == "pytest":
        code, out = _pytest(workspace, task.grade_timeout)
    elif task.grade_type == "node":
        code, out = _node(workspace, task.grade_timeout)
    else:  # pragma: no cover - guarded by Task.load
        raise ValueError(f"unsupported grade type: {task.grade_type}")

    elapsed = time.perf_counter() - start
    if code == 5:
        return GradeResult(False, "no tests collected", elapsed)
    return GradeResult(code == 0, out[-1200:] or f"exit code {code}", elapsed)
