import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner
from rspec_tools import checklinks, cli


@pytest.fixture
def setup_test_files():
    """Create a temporary directory with test files for each test case."""
    # Create a temp directory
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # Create test directories
    test_dirs = {
        "404": {
            "S100/java/rule.html": '<a href="https://www.google.com/404">404</a>',
            "S100/java/metadata.json": "{}",
        },
        "URL": {
            "S100/java/rule.html": '<a href="https://ww.test">error</a>',
            "S100/java/metadata.json": "{}",
        },
        "OK": {
            "S100/java/rule.html": '<a href="https://www.google.com/">ok</a>',
            "S100/java/metadata.json": "{}",
        },
        "deprecated": {
            "S100/java/rule.html": '<a href="https://www.google.com/404">404</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": '{"status": "deprecated"}',
            "S100/rpg/rule.html": '<a href="https://www.google.com/">ok</a>',
            "S100/rpg/metadata.json": '{"status": "ready"}',
        },
    }

    # Create all test files
    for test_dir, files in test_dirs.items():
        for file_path, content in files.items():
            full_path = temp_path / test_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_dir)


def test_find_urls(setup_test_files):
    temp_path = setup_test_files
    urls = {}
    test_file = temp_path / "404/S100/java/rule.html"
    checklinks.findurl_in_html(test_file, urls)
    assert urls == {"https://www.google.com/404": [test_file]}
    assert len(urls) == 1


def test_live_url_success():
    assert checklinks.live_url("https://www.google.com")


def test_live_url_failure():
    assert not checklinks.live_url("https://ww.nothing")


def test_404(setup_test_files):
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["check-links", "--d", temp_path / "404", "--history-file", str(history_file)],
    )
    print(result.output)
    assert result.exit_code == 1
    assert (
        "1/1 links are dead, see above ^^ the list and the related files"
        in result.output
    )


def test_url(setup_test_files):
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["check-links", "--d", temp_path / "URL", "--history-file", str(history_file)],
    )
    print(result.output)
    assert result.exit_code == 1
    assert (
        "1/1 links are dead, see above ^^ the list and the related files"
        in result.output
    )


def test_ok(setup_test_files):
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["check-links", "--d", temp_path / "OK", "--history-file", str(history_file)],
    )
    print(result.output)
    assert result.exit_code == 0
    assert "All 1 links are good" in result.output


def test_deprecated(setup_test_files):
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "check-links",
            "--d",
            temp_path / "deprecated",
            "--history-file",
            str(history_file),
        ],
    )
    print(result.output)
    assert result.exit_code == 0
    assert "All 1 links are good" in result.output
