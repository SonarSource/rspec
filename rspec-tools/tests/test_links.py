import datetime
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from rspec_tools import checklinks, cli


def get_error_section(result_output):
    """
    Extract the error section from the check-links command output.

    Args:
        result_output: The output from running the check-links command

    Returns:
        The error section of the output containing the dead links and their files
    """
    return result_output.split("There were errors")[1].split("Cache statistics")[0]


def run_check_links_with_mocked_live_url(dir_path, history_file, mock_live_url_func):
    """
    Run check-links CLI command with a mocked live_url function.

    Args:
        dir_path: Directory to check links in
        history_file: Path to the history file
        mock_live_url_func: Function to use for mocking live_url

    Returns:
        Result of the CLI command
    """
    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url_func):
        runner = CliRunner()
        return runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                dir_path,
                "--history-file",
                str(history_file),
            ],
        )


def create_test_files(base_path, test_dirs):
    """
    Create test files based on a directory structure definition.

    Args:
        base_path: Base directory where files will be created
        test_dirs: Dictionary mapping directory names to file paths and contents
    """
    for test_dir, files in test_dirs.items():
        for file_path, content in files.items():
            full_path = base_path / test_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)


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
def setup_temp_dir():
    """Create a temporary directory for test files and clean it up after the test."""
    # Create a temp directory
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def setup_test_files(setup_temp_dir):
    """Populate the temporary directory with test files for each test case."""
    temp_path = setup_temp_dir

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
    create_test_files(temp_path, test_dirs)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    return temp_path


def test_find_urls(setup_temp_dir):
    temp_path = setup_temp_dir

    # Create test files with a URL to check
    test_dirs = {
        "404": {
            "S100/java/rule.html": '<a href="https://www.google.com/404">404</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files using the existing helper function
    create_test_files(temp_path, test_dirs)

    # Test URL extraction
    urls = {}
    test_file = temp_path / "404/S100/java/rule.html"
    checklinks.findurl_in_html(test_file, urls)
    assert urls == {"https://www.google.com/404": [test_file]}
    assert len(urls) == 1


def test_live_url_success():
    assert checklinks.live_url("https://www.google.com")


def test_live_url_failure():
    assert not checklinks.live_url("https://ww.nothing")


def test_live_url_with_anchor_only_link():
    """Test that the live_url function correctly handles anchor-only links."""
    # Test with an anchor-only link
    assert checklinks.live_url("#section-reference") is True

    # Test with a more complex anchor
    assert checklinks.live_url("#complex-anchor-with-numbers-123") is True


def test_link_initially_dead_then_alive(setup_temp_dir):
    """Test that a link initially marked as dead but then confirmed alive is not reported as dead."""
    temp_path = setup_temp_dir

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # Create test files with a link that will be initially dead but then alive
    test_link = "https://www.example.com/intermittent-link"
    test_dirs = {
        "intermittent_link": {
            "S100/java/rule.html": f'<a href="{test_link}">Intermittent Link</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Get the directory path for later use
    test_dir = temp_path / "intermittent_link"

    # First attempt counter to track calls to mock_live_url
    attempt_counter = {"count": 0}

    # Mock live_url to return False on first attempt, True on second attempt
    def mock_live_url(url, timeout=5):
        if url == test_link:
            attempt_counter["count"] += 1
            # Return False on first call (initial check), True on second call (confirmation)
            return attempt_counter["count"] > 1
        return True  # All other links are alive

    # Set up a history file with an old date so the link will be checked
    old_date = datetime.datetime.now() - datetime.timedelta(days=30)
    first_result = setup_history_file(
        temp_path, history_file, old_date, "intermittent_link"
    )
    assert first_result.exit_code == 0

    # Run check-links with the mocked live_url function
    result = run_check_links_with_mocked_live_url(test_dir, history_file, mock_live_url)

    # Verify that mock_live_url was called twice for our test link
    assert attempt_counter["count"] == 2

    # Verify the command succeeded (exit code 0 means no dead links)
    assert result.exit_code == 0

    # Verify the output indicates success
    assert "All 1 links are good" in result.output

    # Verify that the history file was updated with the now-alive link
    with open(history_file, "r") as f:
        history_content = f.read()
        assert test_link in history_content


def test_404(setup_temp_dir):
    temp_path = setup_temp_dir

    # Create test files with a 404 URL
    test_dirs = {
        "404": {
            "S100/java/rule.html": '<a href="https://www.google.com/404">404</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

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


def test_url(setup_temp_dir):
    temp_path = setup_temp_dir

    # Create test directories and files
    test_dirs = {
        "URL": {
            "S100/java/rule.html": '<a href="https://ww.test">error</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

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


def test_ok(setup_temp_dir):
    temp_path = setup_temp_dir

    # Create test directories and files
    test_dirs = {
        "OK": {
            "S100/java/rule.html": '<a href="https://www.google.com/">ok</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["check-links", "--d", temp_path / "OK", "--history-file", str(history_file)],
    )
    print(result.output)
    assert result.exit_code == 0
    assert "All 1 links are good" in result.output


def test_deprecated(setup_temp_dir):
    temp_path = setup_temp_dir

    # Create test directories and files
    test_dirs = {
        "deprecated": {
            "S100/java/rule.html": '<a href="https://www.google.com/404">404</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": '{"status": "deprecated"}',
            "S100/rpg/rule.html": '<a href="https://www.google.com/">ok</a>',
            "S100/rpg/metadata.json": '{"status": "ready"}',
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

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


def test_no_reprobe_recent_links(setup_temp_dir):
    """Test that links probed recently are not probed again."""
    temp_path = setup_temp_dir
    test_url = "https://www.google.com/"

    # Create test directories and files
    test_dirs = {
        "OK": {
            "S100/java/rule.html": f'<a href="{test_url}">ok</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create empty history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

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

    second_result = run_check_links_with_mocked_live_url(
        temp_path / "OK", history_file, mock_live_url
    )

    # Verify that the test URL wasn't probed again
    assert test_url not in probe_calls
    assert "skip probing because it was reached recently" in second_result.output
    assert second_result.exit_code == 0
    assert "All 1 links are good" in second_result.output


def test_reprobe_old_links(setup_temp_dir):
    """Test that links probed a long time ago are checked again."""
    temp_path = setup_temp_dir
    test_url = "https://www.google.com/"

    # Create test directories and files
    test_dirs = {
        "OK": {
            "S100/java/rule.html": f'<a href="{test_url}">ok</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # First run: Probe the links with a mocked datetime that's older than PROBING_COOLDOWN
    old_date = (
        datetime.datetime.now()
        - checklinks.PROBING_COOLDOWN
        - datetime.timedelta(days=1)
    )

    # Setup history file with an old date
    first_result = setup_history_file(temp_path, history_file, old_date, "OK")
    assert first_result.exit_code == 0

    # Second run: The link should be probed again because the timestamp in history is old
    # Mock the live_url function to track if it gets called
    probe_calls = []

    def mock_live_url(url, timeout=5):
        probe_calls.append(url)
        return True

    second_result = run_check_links_with_mocked_live_url(
        temp_path / "OK", history_file, mock_live_url
    )

    # Verify that the test URL was probed again
    assert test_url in probe_calls
    assert "skip probing because it was reached recently" not in second_result.output
    assert second_result.exit_code == 0


def test_tolerable_downtime(setup_temp_dir):
    """Test that links that were alive recently but are now dead are not reported as dead."""
    temp_path = setup_temp_dir
    test_url = "https://www.google.com/404"

    # Create test directories and files
    test_dirs = {
        "404": {
            "S100/java/rule.html": f'<a href="{test_url}">404</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # Setup history file with a recent date (3 days ago) - within TOLERABLE_LINK_DOWNTIME
    recent_date = datetime.datetime.now() - datetime.timedelta(days=3)
    first_result = setup_history_file(temp_path, history_file, recent_date, "404")
    assert first_result.exit_code == 0

    # Mock live_url to always return False for our test URL (simulating a dead link)
    def mock_live_url(url, timeout=5):
        # The link is "dead" now, but was alive 3 days ago according to our history
        return False

    second_result = run_check_links_with_mocked_live_url(
        temp_path / "404", history_file, mock_live_url
    )

    # Verify the link wasn't reported as dead (exit code 0 means all links are good)
    assert second_result.exit_code == 0
    assert "All 1 links are good" in second_result.output


def test_old_dead_link(setup_temp_dir):
    """Test that links that were alive a long time ago (1 month) but are now dead are reported as dead."""
    temp_path = setup_temp_dir
    test_url = "https://www.google.com/404"

    # Create test directories and files
    test_dirs = {
        "404": {
            "S100/java/rule.html": f'<a href="{test_url}">404</a>',
            "S100/java/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, test_dirs)

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # Setup history file with an old date (30 days ago) - beyond TOLERABLE_LINK_DOWNTIME
    old_date = datetime.datetime.now() - datetime.timedelta(days=30)
    first_result = setup_history_file(temp_path, history_file, old_date, "404")
    assert first_result.exit_code == 0

    # Mock live_url to always return False for our test URL (simulating a dead link)
    def mock_live_url(url, timeout=5):
        # The link is dead now and was last alive 30 days ago
        return False

    second_result = run_check_links_with_mocked_live_url(
        temp_path / "404", history_file, mock_live_url
    )

    # Verify the link was reported as dead (exit code 1 means dead links found)
    assert second_result.exit_code == 1
    assert "1/1 links are dead" in second_result.output


def test_exception_url(setup_temp_dir):
    """Test that URLs matching exception patterns are not probed and reported as live."""
    temp_path = setup_temp_dir

    # Create a test file with an exception URL
    exception_url = "https://wiki.sei.cmu.edu/confluence/display/java/SEC05-J"

    # Define the file structure for the exception URL test
    exception_test_dirs = {
        "exception": {
            "S100/java/rule.html": f'<a href="{exception_url}">Exception URL</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, exception_test_dirs)

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    exception_dir = temp_path / "exception"

    # Mock live_url to track if it gets called
    live_url_calls = []

    def mock_live_url(url, timeout=5):
        live_url_calls.append(url)
        # Don't call the original function to avoid possible network errors
        return True  # Just return True instead of calling the original function

    result = run_check_links_with_mocked_live_url(
        exception_dir, history_file, mock_live_url
    )

    # Verify that the exception URL was not probed (not in live_url_calls)
    assert exception_url not in live_url_calls
    # Verify that the test passed (exit code 0)
    assert result.exit_code == 0
    # Verify that the right message appears in the output
    assert "skip as an exception" in result.output
    assert "All 1 links are good" in result.output


def test_mixed_links_reporting(setup_temp_dir):
    """Test that when some links are dead and some are alive, only the dead ones are reported."""
    temp_path = setup_temp_dir

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # Create test files for mixed links test
    dead_url = "https://www.example.com/dead-link"
    live_url = "https://www.example.com/live-link"

    # Define the test directory structure with dead and live links
    mixed_test_dirs = {
        "mixed_links": {
            "S100/java/rule.html": f'<a href="{dead_url}">Dead Link</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
            "S200/java/rule.html": f'<a href="{live_url}">Live Link</a>',
            "S200/java/metadata.json": "{}",
            "S200/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, mixed_test_dirs)

    # Get paths to test files for later assertions
    mixed_dir = temp_path / "mixed_links"
    rule1_dir = mixed_dir / "S100" / "java"
    rule2_dir = mixed_dir / "S200" / "java"

    # Setup the history file to show that the dead_url was last alive a long time ago
    # (making it "long dead" without mocking url_is_long_dead)
    old_date = datetime.datetime.now() - datetime.timedelta(
        days=30
    )  # Well beyond TOLERABLE_LINK_DOWNTIME

    # Setup history file with an old date for the dead URL
    # Use the mixed_links directory to create links that will be checked against the history
    first_result = setup_history_file(temp_path, history_file, old_date, "mixed_links")
    assert first_result.exit_code == 0

    # Mock live_url to return different values based on URL
    def mock_live_url(url, timeout=5):
        if url == dead_url:
            return False  # This link is dead
        else:
            return True  # All other links are alive

    result = run_check_links_with_mocked_live_url(
        mixed_dir, history_file, mock_live_url
    )

    # Verify test fails because there's a dead link
    assert result.exit_code == 1

    # Verify that the dead URL and its file are reported in the errors section of the output
    error_section = get_error_section(result.output)
    assert dead_url in error_section
    assert str(rule1_dir / "rule.html") in error_section

    # Verify that the live URL and its file are NOT reported in the error section
    assert "1/2 links are dead" in result.output

    # Check that the live link's file path is not in the errors section
    assert str(rule2_dir / "rule.html") not in error_section


def test_duplicate_links_checked_once(setup_temp_dir):
    """Test that a link present in multiple files is only checked once."""
    temp_path = setup_temp_dir

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # Create test files for duplicate links test
    test_url = "https://www.example.com/test-link"

    # Define the test directory structure with the same URL in multiple files
    duplicate_test_dirs = {
        "duplicate_links": {
            "S100/java/rule.html": f'<a href="{test_url}">Test Link in File 1</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
            "S200/java/rule.html": f'<a href="{test_url}">Same Test Link in File 2</a>',
            "S200/java/metadata.json": "{}",
            "S200/metadata.json": "{}",
            "S300/java/rule.html": f'<a href="{test_url}">Same Test Link in File 3</a>',
            "S300/java/metadata.json": "{}",
            "S300/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, duplicate_test_dirs)

    # Get the directory path for later use
    dup_dir = temp_path / "duplicate_links"

    # Mock live_url to track how many times it gets called
    live_url_calls = []

    def mock_live_url(url, timeout=5):
        live_url_calls.append(url)
        return True  # All links are alive

    result = run_check_links_with_mocked_live_url(dup_dir, history_file, mock_live_url)

    # Verify the test passed
    assert result.exit_code == 0

    # Verify that the link shows up in all three files
    assert len(live_url_calls) == 1  # The link was only checked once
    assert live_url_calls[0] == test_url

    # Verify that the output mentions the link appears in 3 files
    assert f"{test_url} in 3 files" in result.output


def test_multiple_links_in_single_file(setup_temp_dir):
    """Test that multiple different links in a single file are all checked."""
    temp_path = setup_temp_dir

    # Create history file
    history_file = temp_path / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")

    # Create test file with multiple links
    link1 = "https://www.example.com/link1"
    link2 = "https://www.example.com/link2"
    link3 = "https://www.example.com/link3"

    # Define the test directory structure with multiple links in a single file
    multi_links_test_dirs = {
        "multi_links": {
            "S100/java/rule.html": f"""
                <a href="{link1}">First Link</a>
                <p>Some content between links</p>
                <a href="{link2}">Second Link</a>
                <div>
                    <a href="{link3}">Third Link</a>
                </div>
            """,
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, multi_links_test_dirs)

    # Get the directory path for later use
    multi_dir = temp_path / "multi_links"

    # Mock live_url to track which URLs are called
    live_url_calls = []

    def mock_live_url(url, timeout=5):
        live_url_calls.append(url)
        return True  # All links are alive

    result = run_check_links_with_mocked_live_url(
        multi_dir, history_file, mock_live_url
    )

    # Verify the test passed
    assert result.exit_code == 0

    # Verify that all three links were checked
    assert len(live_url_calls) == 3
    assert link1 in live_url_calls
    assert link2 in live_url_calls
    assert link3 in live_url_calls

    # Verify that the output mentions the correct number of links
    assert "All 3 links are good" in result.output


# AI! refactor this test to use only setup_temp_dir, and inline the relevant parts of setup_test_files, but keep using the create_test_files function
def test_dead_link_in_multiple_files(setup_test_files):
    """Test that if a dead link appears in multiple files, all those files are listed in the error report."""
    temp_path = setup_test_files
    history_file = temp_path / "link_probes.history"

    # Create test files with the same dead link in multiple files
    dead_url = "https://www.example.com/dead-link"

    # Define the test directory structure with the same dead link in multiple files
    multi_file_dead_link_dirs = {
        "multi_file_dead_link": {
            "S100/java/rule.html": f'<a href="{dead_url}">Dead Link in Java Rule</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
            "S200/python/rule.html": f'<a href="{dead_url}">Dead Link in Python Rule</a>',
            "S200/python/metadata.json": "{}",
            "S200/metadata.json": "{}",
            "S300/csharp/rule.html": f'<a href="{dead_url}">Dead Link in C# Rule</a>',
            "S300/csharp/metadata.json": "{}",
            "S300/metadata.json": "{}",
        }
    }

    # Create the test files
    create_test_files(temp_path, multi_file_dead_link_dirs)

    # Get the directory path and file paths for later use
    multi_file_dir = temp_path / "multi_file_dead_link"
    file1_path = multi_file_dir / "S100" / "java" / "rule.html"
    file2_path = multi_file_dir / "S200" / "python" / "rule.html"
    file3_path = multi_file_dir / "S300" / "csharp" / "rule.html"

    # Setup the history file with an old date for the dead URL
    old_date = datetime.datetime.now() - datetime.timedelta(days=30)
    first_result = setup_history_file(
        temp_path, history_file, old_date, "multi_file_dead_link"
    )
    assert first_result.exit_code == 0

    # Mock live_url to make our test URL return dead (False)
    def mock_live_url(url, timeout=5):
        return url != dead_url  # Only the dead_url returns False

    result = run_check_links_with_mocked_live_url(
        multi_file_dir, history_file, mock_live_url
    )

    # Verify the test fails (has a dead link)
    assert result.exit_code == 1

    # Get the error section of the output
    error_section = get_error_section(result.output)

    # Verify the dead URL is reported in the error section
    assert dead_url in error_section

    # Verify all three files with the dead link are listed in the error section
    assert str(file1_path) in error_section
    assert str(file2_path) in error_section
    assert str(file3_path) in error_section

    # Verify the output mentions the correct count of dead links
    assert "1/1 links are dead" in result.output


def test_create_history_file(setup_test_files):
    """Test that check-links creates a history file if none exists."""
    temp_path = setup_test_files

    # Create a new directory for this test
    test_dir_name = "create_history_test"
    test_dir = temp_path / test_dir_name

    # Create test files with a live link
    test_link = "https://www.example.com/test-link"
    test_dirs = {
        test_dir_name: {
            "S100/java/rule.html": f'<a href="{test_link}">Test Link</a>',
            "S100/java/metadata.json": "{}",
            "S100/metadata.json": "{}",
        }
    }

    # Create the test files using the helper function
    create_test_files(temp_path, test_dirs)

    # Define a non-existent history file
    history_file = temp_path / "new_history_file.json"

    # Make sure the history file doesn't exist
    if history_file.exists():
        history_file.unlink()

    # Mock the live_url function to return True
    def mock_live_url(url, timeout=5):
        return True

    # Run check-links with the mocked function
    with patch("rspec_tools.checklinks.live_url", side_effect=mock_live_url):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check-links",
                "--d",
                str(test_dir),
                "--history-file",
                str(history_file),
            ],
        )

    # Verify the command succeeded
    assert result.exit_code == 0

    # Verify the history file was created
    assert history_file.exists()

    # Verify the history file contains the URL we tested
    with open(history_file, "r") as f:
        history_content = f.read()
        assert test_link in history_content

    # Verify the output indicates success
    assert "All 1 links are good" in result.output
