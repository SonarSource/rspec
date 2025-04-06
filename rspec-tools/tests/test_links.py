import datetime
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from rspec_tools import checklinks, cli


def setup_history_file(temp_path, history_file, mock_date, test_dir="OK"):
    """
    Helper function to run check-links and setup a history file.

    Args:
        temp_path: Path to temporary directory
        history_file: Path to history file
        mock_date: Date to use for the history entry
        test_dir: Directory containing test files

    Returns:
        Result of the check-links command
    """
    # Always mock datetime.now() with the provided date
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_date
        mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

        # Run check-links with mocked live_url
        with patch("rspec_tools.checklinks.live_url", return_value=True):
            runner = CliRunner()
            return runner.invoke(
                cli,
                [
                    "check-links",
                    "--d",
                    temp_path / test_dir,
                    "--history-file",
                    str(history_file),
                ],
            )


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

    # First run: Probe the links and update the history file with current date
    current_date = datetime.datetime.now()
    first_result = setup_history_file(temp_path, history_file, current_date)
    assert first_result.exit_code == 0
    assert "All 1 links are good" in first_result.output

    # Second run: The link should not be probed again
    # Mock the live_url function to track if it gets called
    probe_calls = []

    def mock_live_url(url, timeout=5):
        probe_calls.append(url)
        return True

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        second_result = runner.invoke(
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
        assert "skip probing because it was reached recently" in second_result.output
        assert second_result.exit_code == 0
        assert "All 1 links are good" in second_result.output


def test_reprobe_old_links(setup_test_files):
    """Test that links probed a long time ago are checked again."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    test_url = "https://www.google.com/"

    # First run: Probe the links with a mocked datetime that's older than PROBING_COOLDOWN
    old_date = (
        datetime.datetime.now()
        - checklinks.PROBING_COOLDOWN
        - datetime.timedelta(days=1)
    )

    # Setup history file with an old date
    first_result = setup_history_file(temp_path, history_file, old_date)
    assert first_result.exit_code == 0

    # Second run: The link should be probed again because the timestamp in history is old
    # Mock the live_url function to track if it gets called
    probe_calls = []

    def mock_live_url(url, timeout=5):
        probe_calls.append(url)
        return True

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        second_result = runner.invoke(
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
        assert (
            "skip probing because it was reached recently" not in second_result.output
        )
        assert second_result.exit_code == 0


def test_tolerable_downtime(setup_test_files):
    """Test that links that were alive recently but are now dead are not reported as dead."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    test_url = "https://www.google.com/404"  # This URL will return 404

    # Setup history file with a recent date (3 days ago) - within TOLERABLE_LINK_DOWNTIME
    recent_date = datetime.datetime.now() - datetime.timedelta(days=3)
    first_result = setup_history_file(temp_path, history_file, recent_date, "404")
    assert first_result.exit_code == 0

    # Mock live_url to always return False for our test URL (simulating a dead link)
    def mock_live_url(url, timeout=5):
        # The link is "dead" now, but was alive 3 days ago according to our history
        return False

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        second_result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                temp_path / "404",  # This directory has a link to google.com/404
                "--history-file",
                str(history_file),
            ],
        )

        # Verify the link wasn't reported as dead (exit code 0 means all links are good)
        assert second_result.exit_code == 0
        assert "All 1 links are good" in second_result.output


def test_old_dead_link(setup_test_files):
    """Test that links that were alive a long time ago (1 month) but are now dead are reported as dead."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"
    test_url = "https://www.google.com/404"  # This URL will return 404

    # Setup history file with an old date (30 days ago) - beyond TOLERABLE_LINK_DOWNTIME
    old_date = datetime.datetime.now() - datetime.timedelta(days=30)
    first_result = setup_history_file(temp_path, history_file, old_date, "404")
    assert first_result.exit_code == 0

    # Mock live_url to always return False for our test URL (simulating a dead link)
    def mock_live_url(url, timeout=5):
        # The link is dead now and was last alive 30 days ago
        return False

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        second_result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                temp_path / "404",  # This directory has a link to google.com/404
                "--history-file",
                str(history_file),
            ],
        )

        # Verify the link was reported as dead (exit code 1 means dead links found)
        assert second_result.exit_code == 1
        assert "1/1 links are dead" in second_result.output


def test_exception_url(setup_test_files):
    """Test that URLs matching exception patterns are not probed and reported as live."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"

    # Create a test file with an exception URL
    exception_dir = temp_path / "exception"
    exception_dir.mkdir(exist_ok=True)
    rule_dir = exception_dir / "S100" / "java"
    rule_dir.mkdir(parents=True, exist_ok=True)

    # Create a rule.html file with a URL that matches an exception prefix
    exception_url = "https://wiki.sei.cmu.edu/confluence/display/java/SEC05-J"
    with open(rule_dir / "rule.html", "w") as f:
        f.write(f'<a href="{exception_url}">Exception URL</a>')

    # Create empty metadata files
    with open(exception_dir / "S100" / "metadata.json", "w") as f:
        f.write("{}")
    with open(rule_dir / "metadata.json", "w") as f:
        f.write("{}")

    # Initialize history with empty content
    with open(history_file, "w") as f:
        f.write("{}")

    # Mock live_url to track if it gets called
    live_url_calls = []
    original_live_url = checklinks.live_url

    def mock_live_url(url, timeout=5):
        live_url_calls.append(url)
        # Don't call the original function to avoid possible network errors
        return True  # Just return True instead of calling the original function

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                exception_dir,
                "--history-file",
                str(history_file),
            ],
        )

        # Verify that the exception URL was not probed (not in live_url_calls)
        assert exception_url not in live_url_calls
        # Verify that the test passed (exit code 0)
        assert result.exit_code == 0
        # Verify that the right message appears in the output
        assert "skip as an exception" in result.output
        assert "All 1 links are good" in result.output


def test_mixed_links_reporting(setup_test_files):
    """Test that when some links are dead and some are alive, only the dead ones are reported."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"

    # Create a directory for mixed links test
    mixed_dir = temp_path / "mixed_links"
    mixed_dir.mkdir(exist_ok=True)

    # Create first rule with a dead link
    rule1_dir = mixed_dir / "S100" / "java"
    rule1_dir.mkdir(parents=True, exist_ok=True)
    dead_url = "https://www.example.com/dead-link"
    with open(rule1_dir / "rule.html", "w") as f:
        f.write(f'<a href="{dead_url}">Dead Link</a>')
    with open(rule1_dir / "metadata.json", "w") as f:
        f.write("{}")
    with open(mixed_dir / "S100" / "metadata.json", "w") as f:
        f.write("{}")

    # Create second rule with a live link
    rule2_dir = mixed_dir / "S200" / "java"
    rule2_dir.mkdir(parents=True, exist_ok=True)
    live_url = "https://www.example.com/live-link"
    with open(rule2_dir / "rule.html", "w") as f:
        f.write(f'<a href="{live_url}">Live Link</a>')
    with open(rule2_dir / "metadata.json", "w") as f:
        f.write("{}")
    with open(mixed_dir / "S200" / "metadata.json", "w") as f:
        f.write("{}")

    # Initialize history with empty content
    with open(history_file, "w") as f:
        f.write("{}")

    # Mock live_url to return different values based on URL
    def mock_live_url(url, timeout=5):
        if url == dead_url:
            return False  # This link is dead
        else:
            return True  # All other links are alive

    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        # Mock url_is_long_dead to always return True for our dead URL
        def mock_url_is_long_dead(url):
            return url == dead_url

        with patch(
            "rspec_tools.checklinks.url_is_long_dead", side_effect=mock_url_is_long_dead
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "check-links",
                    "--d",
                    mixed_dir,
                    "--history-file",
                    str(history_file),
                ],
            )

            # Verify test fails because there's a dead link
            assert result.exit_code == 1

            # Verify that the dead URL and its file are reported in the errors section of the output
            error_section = result.output.split("There were errors")[1].split("Cache statistics")[0]
            assert dead_url in error_section
            assert str(rule1_dir / "rule.html") in error_section

            # Verify that the live URL and its file are NOT reported in the error section
            assert "1/2 links are dead" in result.output

            # Check that the live link's file path is not in the errors section
            error_section = result.output.split("There were errors")[1].split(
                "Cache statistics"
            )[0]
            assert str(rule2_dir / "rule.html") not in error_section
