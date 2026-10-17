import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = str(ROOT / "appconfig.py")


def clean_env(extra, tmp_path):
    env = os.environ.copy()
    for key in ("APP_HOST", "APP_PORT", "APP_DEBUG", "APP_CONFIG"):
        env.pop(key, None)
    env.update(extra)
    return env


def run(tmp_path, extra, args=()):
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        cwd=tmp_path,
        env=clean_env(extra, tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def write_file(tmp_path, payload):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_environment_beats_file(tmp_path):
    path = write_file(tmp_path, {"host": "from-file", "port": 1234})
    config = run(tmp_path, {"APP_CONFIG": path, "APP_HOST": "from-env"})
    assert config["host"] == "from-env"
    assert config["port"] == 1234


def test_command_line_beats_everything(tmp_path):
    path = write_file(tmp_path, {"host": "from-file"})
    config = run(
        tmp_path,
        {"APP_CONFIG": path, "APP_HOST": "from-env", "APP_PORT": "9000"},
        ["--host", "from-cli"],
    )
    assert config["host"] == "from-cli"
    assert config["port"] == 9000


def test_defaults(tmp_path):
    config = run(tmp_path, {})
    assert config == {"host": "localhost", "port": 8000, "debug": False}


def test_debug_parsing(tmp_path):
    assert run(tmp_path, {"APP_DEBUG": "TRUE"})["debug"] is True
    assert run(tmp_path, {"APP_DEBUG": "0"})["debug"] is False


def test_missing_config_file_is_ignored(tmp_path):
    config = run(tmp_path, {"APP_CONFIG": str(tmp_path / "missing.json")})
    assert config["host"] == "localhost"
