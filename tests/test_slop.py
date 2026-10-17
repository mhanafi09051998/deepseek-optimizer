from dso.slop import analyze, format_report, strip_code


def test_flags_markdown_and_connector_hyphen():
    result = analyze(["**Done** with the parser.", "The fix is in place - tests pass."])
    assert result["markers"]["bold"] == 1
    assert result["markers"]["spaced_hyphen"] == 1
    assert result["total"] == 2


def test_flags_em_dash():
    result = analyze(["The fix works \u2014 mostly."])
    assert result["markers"]["em_dash"] == 1


def test_ignores_code_blocks_and_inline_code():
    result = analyze(["```\n**not slop** - inside code\n```", "Run `a - b` now."])
    assert result["total"] == 0


def test_flags_cliche():
    result = analyze(["It's important to note that certainly! this works."])
    assert result["markers"]["it's important to note"] == 1
    assert result["markers"]["certainly!"] == 1


def test_score_is_normalized_per_thousand_words():
    result = analyze(["**word** " + " ".join(["filler"] * 999)])
    assert result["words"] == 1000
    assert result["per_1k_words"] == 1.0


def test_strip_code_keeps_prose():
    text = strip_code("before `inline` after")
    assert "inline" not in text
    assert "before" in text and "after" in text


def test_format_report_lists_markers():
    text = format_report(analyze(["**a**"]))
    assert "markers: 1" in text
    assert "bold" in text
