import pytest

from dso.spec import TaskError, discover_tasks, select_tasks


def test_discovers_tasks():
    tasks = discover_tasks()
    assert len(tasks) >= 8
    assert all(task.repo_dir.is_dir() for task in tasks)
    assert all(task.solution_patch.exists() for task in tasks)


def test_ids_are_unique():
    tasks = discover_tasks()
    assert len({task.id for task in tasks}) == len(tasks)


def test_select_by_category_and_glob():
    tasks = discover_tasks()
    bugfixes = select_tasks(tasks, "bugfix")
    assert bugfixes and all(task.category == "bugfix" for task in bugfixes)

    globbed = select_tasks(tasks, "feature-*")
    assert globbed and all(task.id.startswith("feature-") for task in globbed)


def test_unknown_selection_raises():
    tasks = discover_tasks()
    with pytest.raises(TaskError):
        select_tasks(tasks, "does-not-exist")
