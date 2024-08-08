import re
from pathlib import Path

import pytest
from rspec_tools.validation.sanitize_asciidoc import sanitize_asciidoc


def relative_output(capsys, path: Path):
    return capsys.readouterr().out.replace(str(path), "$PATH")


@pytest.mark.parametrize(
    "invalid_file,expected_count",
    [
        ("unbalanced_single_backquotes", 1),
        ("unbalanced_double_backquotes", 1),
        ("triple_backquotes", 1),
        ("unprotected_formatting", 4),
        ("unprotected_formatting_with_plusses", 1),
        ("wrong_constrained_passthrough", 1),
        ("unclosed_ifdef", 1),
        ("close_unopened_ifdef", 1),
        ("two_ifdef", 1),
        ("two_ifdef_unclosed", 1),
        ("vscode_ifdef", 2),
        ("wrong_ifdef", 1),
        ("wrong_endif", 1),
        ("include_stuck_before", 1),
        ("include_stuck_after", 1),
        ("two_stuck_includes", 2),
        ("unnamed_language", 2),
        ("link_rule_sonarsource_com", 3),
    ],
)
def test_need_sanitation(
    mockinvalidasciidoc: Path, invalid_file, expected_count, capsys, snapshot
):
    """Check that we detect needs for sanitation."""
    name_path = Path(invalid_file)
    adoc = mockinvalidasciidoc / name_path.with_suffix(".adoc")
    expected = mockinvalidasciidoc / "snapshots" / name_path.with_suffix(".txt")
    assert sanitize_asciidoc(adoc) == expected_count
    snapshot.snapshot_dir = mockinvalidasciidoc / "snapshots"
    snapshot.assert_match(relative_output(capsys, mockinvalidasciidoc), expected)


def test_correctly_sanitized(mockasciidoc: Path):
    """Check that we raise no issue on correctly sanitized asciidoc"""
    name_path = Path("valid")
    adoc = mockasciidoc / name_path.with_suffix(".adoc")
    assert sanitize_asciidoc(adoc) == 0
