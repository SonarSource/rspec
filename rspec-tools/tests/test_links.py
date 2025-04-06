import datetime
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

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


def test_no_reprobe_recent_links(setup_test_files):
    """Test that links probed recently are not probed again."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    test_url = "https://www.google.com/"

    # Create history file with a recent probe for our test URL
    with open(history_file, "w") as f:
        recent_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        f.write(
            f"{{{repr(test_url)}: datetime.datetime.strptime('{recent_time}', '%Y-%m-%d %H:%M:%S.%f')}}"
        )

    # Mock the live_url function to track if it gets called
    original_live_url = checklinks.live_url
    probe_calls = []

    def mock_live_url(url, timeout=5):
        probe_calls.append(url)
        return original_live_url(url, timeout)

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                temp_path / "OK",  # This directory has a link to google.com
                "--history-file",
                str(history_file),
            ],
        )

        # Verify that the test URL wasn't probed again
        assert test_url not in probe_calls
        assert "skip probing because it was reached recently" in result.output
        assert result.exit_code == 0
        assert "All 1 links are good" in result.output


def test_reprobe_old_links(setup_test_files):
    """Test that links probed a long time ago are checked again."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    test_url = "https://www.google.com/"

    # Create history file with an old probe for our test URL
    with open(history_file, "w") as f:
        # Set the date to be older than PROBING_COOLDOWN
        old_time = (
            datetime.datetime.now()
            - checklinks.PROBING_COOLDOWN
            - datetime.timedelta(days=1)
        ).strftime("%Y-%m-%d %H:%M:%S.%f")
        f.write(
            f"{{{repr(test_url)}: datetime.datetime.strptime('{old_time}', '%Y-%m-%d %H:%M:%S.%f')}}"
        )

    # Mock the live_url function to track if it gets called
    original_live_url = checklinks.live_url
    probe_calls = []

    def mock_live_url(url, timeout=5):
        probe_calls.append(url)
        return True  # Always return True for this test

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                temp_path / "OK",  # This directory has a link to google.com
                "--history-file",
                str(history_file),
            ],
        )

        # Verify that the test URL was probed again
        assert test_url in probe_calls
        assert "skip probing because it was reached recently" not in result.output
        assert result.exit_code == 0


def test_tolerable_downtime(setup_test_files):
    """Test that links that were alive recently but are now dead are not reported as dead."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    test_url = "https://www.google.com/404"  # This URL will return 404

    # Create history file with a recent probe (3 days ago) for our test URL
    # This is within the TOLERABLE_LINK_DOWNTIME period (7 days)
    with open(history_file, "w") as f:
        # Set the date to be 3 days ago (within the TOLERABLE_LINK_DOWNTIME of 7 days)
        recent_time = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        f.write(
            f"{{{repr(test_url)}: datetime.datetime.strptime('{recent_time}', '%Y-%m-%d %H:%M:%S.%f')}}"
        )

    # Mock url_is_long_dead to verify it's called with our test URL
    original_url_is_long_dead = checklinks.url_is_long_dead
    long_dead_calls = []

    def mock_url_is_long_dead(url):
        long_dead_calls.append(url)
        return original_url_is_long_dead(url)

    with patch(
        "rspec_tools.checklinks.url_is_long_dead", side_effect=mock_url_is_long_dead
    ):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                temp_path / "404",  # This directory has a link to google.com/404
                "--history-file",
                str(history_file),
            ],
        )

        # Verify url_is_long_dead was called with our test URL
        assert test_url in long_dead_calls
        # Verify the link wasn't reported as dead (exit code 0 means all links are good)
        assert result.exit_code == 0
        assert "All 1 links are good" in result.output
