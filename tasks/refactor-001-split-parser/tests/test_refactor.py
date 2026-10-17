import pytest

import config_parser
import parsing


def test_parse_value_is_shared():
    assert config_parser.parse_value is parsing.parse_value


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("42", 42),
        ("-7", -7),
        ("3.5", 3.5),
        ("true", True),
        ("FALSE", False),
        ('"hello world"', "hello world"),
        ("plain", "plain"),
        ("[1, 2,3]", [1, 2, 3]),
        ("[]", []),
        ('["a", "b"]', ["a", "b"]),
    ],
)
def test_parse_value_behavior(text, expected):
    assert parsing.parse_value(text) == expected


def test_parse_config_behavior():
    source = """
    # comment
    name = "demo"
    retries = 3
    ratio = 0.25
    debug = true
    tags = [a, b]
    """
    assert config_parser.parse_config(source) == {
        "name": "demo",
        "retries": 3,
        "ratio": 0.25,
        "debug": True,
        "tags": ["a", "b"],
    }


def test_invalid_line_still_raises():
    with pytest.raises(ValueError):
        config_parser.parse_config("valid = 1\nbroken line\n")
