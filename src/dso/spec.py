"""Task and model registry loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASKS_DIR = PROJECT_ROOT / "tasks"
DEFAULT_HARNESS_DIR = PROJECT_ROOT / "harness"
DEFAULT_MODELS_FILE = Path(__file__).with_name("models.yaml")

GRADE_TYPES = {"pytest", "node", "mutation"}
CATEGORIES = {
    "comprehension",
    "bugfix",
    "feature",
    "refactor",
    "tests",
    "long-context",
}


class TaskError(ValueError):
    """Raised when a task spec is malformed."""


@dataclass(frozen=True)
class Task:
    id: str
    category: str
    difficulty: int
    language: str
    title: str
    prompt: str
    root: Path
    grade_type: str = "pytest"
    grade_timeout: int = 180
    max_minutes: float = 10.0
    max_files_changed: int = 6
    test_file: str | None = None

    @property
    def repo_dir(self) -> Path:
        return self.root / "repo"

    @property
    def tests_dir(self) -> Path:
        return self.root / "tests"

    @property
    def solution_patch(self) -> Path:
        return self.root / "solution.patch"

    @property
    def reference_test(self) -> Path | None:
        if not self.test_file:
            return None
        candidate = self.root / "reference" / Path(self.test_file).name
        return candidate if candidate.exists() else None

    @classmethod
    def load(cls, root: Path) -> Task:
        spec_path = root / "task.yaml"
        if not spec_path.exists():
            raise TaskError(f"{root}: missing task.yaml")

        raw: dict[str, Any] = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        for key in ("id", "category", "title", "prompt"):
            if not raw.get(key):
                raise TaskError(f"{root}: missing required key '{key}'")

        category = str(raw["category"])
        if category not in CATEGORIES:
            raise TaskError(f"{root}: unknown category '{category}'")

        grade_type = str(raw.get("grade", {}).get("type", "pytest"))
        if grade_type not in GRADE_TYPES:
            raise TaskError(f"{root}: unknown grade type '{grade_type}'")

        task = cls(
            id=str(raw["id"]),
            category=category,
            difficulty=int(raw.get("difficulty", 1)),
            language=str(raw.get("language", "python")),
            title=str(raw["title"]),
            prompt=str(raw["prompt"]).strip() + "\n",
            root=root,
            grade_type=grade_type,
            grade_timeout=int(raw.get("grade", {}).get("timeout", 180)),
            max_minutes=float(raw.get("limits", {}).get("max_minutes", 10)),
            max_files_changed=int(raw.get("limits", {}).get("max_files_changed", 6)),
            test_file=raw.get("grade", {}).get("test_file"),
        )

        if not task.repo_dir.is_dir():
            raise TaskError(f"{root}: missing repo/ directory")
        if not task.solution_patch.exists():
            raise TaskError(f"{root}: missing solution.patch")
        if grade_type in {"pytest", "node"} and not task.tests_dir.is_dir():
            raise TaskError(f"{root}: missing tests/ directory")
        if grade_type == "mutation" and not task.test_file:
            raise TaskError(f"{root}: mutation tasks require grade.test_file")

        return task


def discover_tasks(tasks_dir: Path = DEFAULT_TASKS_DIR) -> list[Task]:
    if not tasks_dir.is_dir():
        raise TaskError(f"tasks directory not found: {tasks_dir}")
    tasks = [
        Task.load(path)
        for path in sorted(tasks_dir.iterdir())
        if path.is_dir() and (path / "task.yaml").exists()
    ]
    if not tasks:
        raise TaskError(f"no tasks found in {tasks_dir}")
    return tasks


def select_tasks(tasks: list[Task], spec: str | None) -> list[Task]:
    """Select tasks by comma separated ids, category names, or globs."""
    if not spec or spec == "all":
        return tasks

    import fnmatch

    wanted = [part.strip() for part in spec.split(",") if part.strip()]
    selected: list[Task] = []
    for task in tasks:
        for pattern in wanted:
            if (
                task.id == pattern
                or task.category == pattern
                or fnmatch.fnmatch(task.id, pattern)
            ):
                selected.append(task)
                break
    if not selected:
        raise TaskError(f"no tasks matched: {spec}")
    return selected


@dataclass(frozen=True)
class ModelEntry:
    key: str
    id: str
    label: str
    pricing: dict[str, float]

    @property
    def variant(self) -> str | None:
        return self.id.split("#", 1)[1] if "#" in self.id else None


def load_models(path: Path | None = None) -> dict[str, ModelEntry]:
    path = Path(os.environ.get("DSO_MODELS_FILE", path or DEFAULT_MODELS_FILE))
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    models: dict[str, ModelEntry] = {}
    for key, raw in (data.get("models") or {}).items():
        models[key] = ModelEntry(
            key=key,
            id=str(raw["id"]),
            label=str(raw.get("label", key)),
            pricing=dict(raw.get("pricing") or {}),
        )
    if not models:
        raise TaskError(f"no models defined in {path}")
    return models


def load_harnesses(path: Path | None = None) -> dict[str, dict[str, str]]:
    path = Path(os.environ.get("DSO_MODELS_FILE", path or DEFAULT_MODELS_FILE))
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(k): dict(v or {}) for k, v in (data.get("harnesses") or {}).items()}
