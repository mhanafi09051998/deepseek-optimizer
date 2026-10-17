import json
from pathlib import Path


def test_answer_file():
    answer = json.loads(Path("answer.json").read_text(encoding="utf-8"))

    assert set(answer) == {"file", "symbol", "value"}
    assert answer["file"].replace("\\", "/") == "settings/network.py"
    assert answer["symbol"] == "DEFAULT_TIMEOUT_SECONDS"
    assert int(answer["value"]) == 30
