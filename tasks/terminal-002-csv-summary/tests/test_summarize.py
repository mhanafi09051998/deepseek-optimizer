import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = str(ROOT / "summarize.py")


def run(args=(), stdin=""):
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        cwd=ROOT,
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_header_is_skipped_and_quoted_amounts_parse():
    data = 'category,amount\nfood,"1,234.50"\ntravel,100\nfood,0.50\n'
    result = run(stdin=data)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "food,1235.00\ntravel,100.00\n"


def test_file_argument(tmp_path):
    path = tmp_path / "expenses.csv"
    path.write_text("category,amount\nrent,900\nrent,100.25\n", encoding="utf-8")
    result = run([str(path)])
    assert result.returncode == 0
    assert result.stdout == "rent,1000.25\n"


def test_malformed_row_exits_two_and_names_the_row():
    data = "category,amount\nfood,10\nbroken\n"
    result = run(stdin=data)
    assert result.returncode == 2
    assert "error: row 3" in result.stderr
    assert result.stdout == ""


def test_empty_input():
    result = run(stdin="")
    assert result.returncode == 0
    assert result.stdout == ""
