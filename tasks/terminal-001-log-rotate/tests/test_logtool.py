import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = str(ROOT / "logtool.py")


def run(directory, *extra):
    return subprocess.run(
        [sys.executable, SCRIPT, str(directory), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def place(directory, name, content, mtime):
    path = directory / name
    path.write_text(content, encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_newest_is_first_and_old_files_are_removed(tmp_path):
    place(tmp_path, "a.log", "a", 1000)
    place(tmp_path, "b.log", "b", 2000)
    place(tmp_path, "c.log", "c", 3000)
    place(tmp_path, "d.log", "d", 4000)

    result = run(tmp_path, "--keep", "2")
    assert result.returncode == 0, result.stderr

    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["c.log.2", "d.log.1"]
    assert (tmp_path / "d.log.1").read_text() == "d"
    assert (tmp_path / "c.log.2").read_text() == "c"


def test_other_files_and_empty_directory(tmp_path):
    (tmp_path / "notes.txt").write_text("keep me")
    result = run(tmp_path, "--keep", "3")
    assert result.returncode == 0
    assert (tmp_path / "notes.txt").read_text() == "keep me"


def test_invalid_keep_exits_nonzero(tmp_path):
    place(tmp_path, "a.log", "a", 1000)
    result = run(tmp_path, "--keep", "0")
    assert result.returncode != 0
    assert (tmp_path / "a.log").exists()


def test_existing_rotations_are_replaced(tmp_path):
    place(tmp_path, "a.log", "new", 5000)
    (tmp_path / "a.log.1").write_text("stale")
    result = run(tmp_path, "--keep", "2")
    assert result.returncode == 0
    assert (tmp_path / "a.log.1").read_text() == "new"
