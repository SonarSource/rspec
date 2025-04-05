import os
import pathlib
import shutil
import tempfile
from unittest import mock

from click.testing import CliRunner
from rspec_tools import checklinks, cli


def create_rule_structure(
    base_dir,
    rule_id,
    language,
    status="ready",
    link_url="https://www.google.com",
    link_text="test link",
):
    """
    Create a rule directory structure as described in README.adoc

    Args:
        base_dir: The base directory where the rule structure will be created
        rule_id: The rule ID (e.g., S100)
        language: The language (e.g., java)
        status: The rule status (ready, deprecated, etc.)
        link_url: The URL to include in the rule HTML
        link_text: The text for the link

    Returns:
        tuple: (rule_path, html_path) - paths to the rule directory and the HTML file
    """
    # Create paths
    rule_path = pathlib.Path(base_dir) / rule_id / language
    os.makedirs(rule_path, exist_ok=True)

    # Create generic metadata.json
    with open(pathlib.Path(base_dir) / rule_id / "metadata.json", "w") as f:
        f.write(f'{{"status": "{status}"}}')

    # Create language-specific metadata.json
    with open(rule_path / "metadata.json", "w") as f:
        f.write(f'{{"status": "{status}"}}')

    # Create HTML file
    html_path = rule_path / "rule.html"
    with open(html_path, "w") as f:
        f.write(
            f"""<!DOCTYPE html>
<html>
<head><title>Test Rule {rule_id}</title></head>
<body>
<p>This is a test rule with a <a href="{link_url}">{link_text}</a>.</p>
</body>
</html>
"""
        )

    return rule_path, html_path


def create_history_file(temp_dir):
    """Create an empty link probe history file in the temporary directory"""
    history_file = pathlib.Path(temp_dir) / "link_probes.history"
    with open(history_file, "w") as f:
        f.write("{}")
    return history_file


def test_find_urls():
    # Create a temporary file for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        _, html_file = create_rule_structure(
            temp_dir, "S100", "java", link_url="https://www.google.com/404"
        )

        urls = {}
        checklinks.findurl_in_html(str(html_file), urls)
        assert len(urls) == 1
        assert "https://www.google.com/404" in urls
        assert len(urls["https://www.google.com/404"]) == 1
        assert urls["https://www.google.com/404"][0]["html"] == str(html_file)


def test_live():
    assert checklinks.live_url("https://www.google.com")


def test_not_live():
    assert not checklinks.live_url("https://ww.nothing")


def test_404():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create history file
        history_file = create_history_file(temp_dir)

        # Create rule structure with a 404 link
        create_rule_structure(
            temp_dir, "S100", "java", link_url="https://www.google.com/404"
        )

        # Run test in isolated filesystem
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create symlink to history file
            os.symlink(history_file, "./link_probes.history")

            # Mock the live_url function to always return False for our test URL
            with mock.patch("rspec_tools.checklinks.live_url", return_value=False):
                result = runner.invoke(cli, ["check-links", f"--d={temp_dir}"])
                print(result.output)

                assert result.exit_code == 1
                assert "links are dead" in result.output
                assert "https://www.google.com/404" in result.output


def test_url():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create history file
        history_file = create_history_file(temp_dir)

        # Create rule structure with an invalid URL
        create_rule_structure(temp_dir, "S101", "java", link_url="https://ww.test")

        # Run test in isolated filesystem
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create symlink to history file
            os.symlink(history_file, "./link_probes.history")

            # Mock the live_url function to always return False for our test URL
            with mock.patch("rspec_tools.checklinks.live_url", return_value=False):
                result = runner.invoke(cli, ["check-links", f"--d={temp_dir}"])
                print(result.output)

                assert result.exit_code == 1
                assert "links are dead" in result.output
                assert "https://ww.test" in result.output


def test_ok():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create history file
        history_file = create_history_file(temp_dir)

        # Create rule structure with a valid link
        create_rule_structure(
            temp_dir, "S102", "java", link_url="https://www.google.com"
        )

        # Run test in isolated filesystem
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create symlink to history file
            os.symlink(history_file, "./link_probes.history")

            # Mock the live_url function to always return True for our test URL
            with mock.patch("rspec_tools.checklinks.live_url", return_value=True):
                result = runner.invoke(cli, ["check-links", f"--d={temp_dir}"])
                print(result.output)

                assert result.exit_code == 0
                assert "All 1 links are good" in result.output


def test_deprecated():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create history file
        history_file = create_history_file(temp_dir)

        # 1. Create a deprecated rule with a bad link
        deprecated_rule_dir = pathlib.Path(temp_dir) / "S103" / "java"
        os.makedirs(deprecated_rule_dir, exist_ok=True)

        # Create generic metadata.json with deprecated status
        with open(pathlib.Path(temp_dir) / "S103" / "metadata.json", "w") as f:
            f.write('{"status": "deprecated"}')

        # Create language-specific metadata.json for deprecated rule
        with open(deprecated_rule_dir / "metadata.json", "w") as f:
            f.write('{"status": "deprecated"}')

        # Create HTML file with a link that would fail if checked
        with open(deprecated_rule_dir / "rule.html", "w") as f:
            f.write(
                """<!DOCTYPE html>
<html>
<head><title>Test Deprecated Rule</title></head>
<body>
<p>This is a deprecated rule with a <a href="https://example.org/bad-link">bad link</a>.</p>
</body>
</html>
"""
            )

        # 2. Create a ready language variant of the same rule
        ready_rule_dir = pathlib.Path(temp_dir) / "S103" / "python"
        os.makedirs(ready_rule_dir, exist_ok=True)

        # Create language-specific metadata.json for ready variant
        with open(ready_rule_dir / "metadata.json", "w") as f:
            f.write('{"status": "ready"}')

        # Create HTML file with a link that would pass when checked
        with open(ready_rule_dir / "rule.html", "w") as f:
            f.write(
                """<!DOCTYPE html>
<html>
<head><title>Test Ready Rule Variant</title></head>
<body>
<p>This is a ready variant of the rule with a <a href="https://www.google.com">good link</a>.</p>
</body>
</html>
"""
            )

        # Run test in isolated filesystem
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create symlink to history file
            os.symlink(history_file, "./link_probes.history")

            # Use a mock to handle different URLs differently:
            # - Return False for the bad link in the deprecated rule
            # - Return True for the good link in the ready rule variant
            def mock_live_url(url, timeout=5):
                if "example.org/bad-link" in url:
                    return False
                return True

            with mock.patch(
                "rspec_tools.checklinks.live_url", side_effect=mock_live_url
            ):
                result = runner.invoke(cli, ["check-links", f"--d={temp_dir}"])
                print(result.output)

                # Should pass because:
                # 1. Deprecated rule links are skipped
                # 2. The ready rule variant has a valid link
                assert result.exit_code == 0
                assert "All 1 links are good" in result.output


def create_rule_with_adoc(
    rules_dir,
    output_dir,
    rule_id,
    language,
    status="ready",
    link_url="https://www.example.com",
    link_text="test link",
):
    """
    Create a rule structure with both HTML and adoc files

    Args:
        rules_dir: The base directory for rules (adoc files)
        output_dir: The base directory for output (HTML files)
        rule_id: The rule ID (e.g., S100)
        language: The language (e.g., java)
        status: The rule status (ready, deprecated, etc.)
        link_url: The URL to include in the files
        link_text: The text for the link

    Returns:
        tuple: (rules_path, output_path) - paths to the rule directories
    """
    # Create paths
    rules_path = pathlib.Path(rules_dir) / rule_id / language
    output_path = pathlib.Path(output_dir) / rule_id / language
    os.makedirs(rules_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    # Create metadata.json files in rules dir
    with open(pathlib.Path(rules_dir) / rule_id / "metadata.json", "w") as f:
        f.write(f'{{"status": "{status}"}}')
    with open(rules_path / "metadata.json", "w") as f:
        f.write(f'{{"status": "{status}"}}')

    # Create metadata.json files in output dir
    with open(pathlib.Path(output_dir) / rule_id / "metadata.json", "w") as f:
        f.write(f'{{"status": "{status}"}}')
    with open(output_path / "metadata.json", "w") as f:
        f.write(f'{{"status": "{status}"}}')

    # Create rule.adoc with a link
    with open(rules_path / "rule.adoc", "w") as f:
        f.write(
            f"""
= Title of Rule {rule_id}

This rule contains a <a href="{link_url}">{link_text}</a>.
"""
        )

    # Create corresponding rule.html
    with open(output_path / "rule.html", "w") as f:
        f.write(
            f"""
<!DOCTYPE html>
<html>
<head><title>Title of Rule {rule_id}</title></head>
<body>
<p>This rule contains a <a href="{link_url}">{link_text}</a>.</p>
</body>
</html>
"""
        )

    return rules_path, output_path


def test_show_adoc_when_exists():
    """Test that the link checker reports both adoc and html files when a link is dead."""
    # Create temporary directories for rules and output
    with tempfile.TemporaryDirectory() as rules_dir, tempfile.TemporaryDirectory() as output_dir:
        # Create history file
        history_file = create_history_file(rules_dir)

        # Create rule structure with a dead link in both places
        rule_id = "S999"
        language = "python"
        link_url = "https://example.com/nonexistent"

        rules_path, output_path = create_rule_with_adoc(
            rules_dir, output_dir, rule_id, language, link_url=link_url
        )

        # Run the link checker with both directories
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create symlink to history file
            os.symlink(history_file, "./link_probes.history")

            # Mock the live_url function to always return False for our test URL
            with mock.patch("rspec_tools.checklinks.live_url", return_value=False):
                result = runner.invoke(
                    cli, ["check-links", f"--d={output_dir}", f"--r={rules_dir}"]
                )

                print(result.output)

                # The command should exit with error code 1 (link check failure)
                assert result.exit_code == 1

                # Output should contain the dead link
                assert link_url in result.output

                # Output should contain reference to the adoc file
                adoc_path = str(rules_path / "rule.adoc")
                assert adoc_path in result.output


def test_show_adoc_with_relative_paths():
    """Test that the link checker works with relative paths for rules_dir and output_dir."""
    # Use a single temporary directory instead of relative paths
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        rules_dir = temp_path / "rules"
        output_dir = temp_path / "output"

        # Create directories
        os.makedirs(rules_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Create empty history file to avoid load errors
        history_file = pathlib.Path(temp_dir) / "link_probes.history"
        with open(history_file, "w") as f:
            f.write("{}")

        # Create rule structure
        rule_id = "S888"
        language = "javascript"
        link_url = "https://example.org/broken-link"

        rules_path, output_path = create_rule_with_adoc(
            rules_dir, output_dir, rule_id, language, link_url=link_url
        )

        # Run the link checker with absolute paths to make sure it works first
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create symlink to the history file in the isolated filesystem
            os.symlink(history_file, "./link_probes.history")

            # Mock the live_url function to always return False for our test URL
            with mock.patch("rspec_tools.checklinks.live_url", return_value=False):
                # Use absolute paths directly
                result = runner.invoke(
                    cli,
                    ["check-links", f"--d={output_dir}", f"--r={rules_dir}"],
                )

                print(result.output)

                # The command should exit with error code 1 (link check failure)
                assert result.exit_code == 1

                # Output should contain the dead link
                assert link_url in result.output

                # Output should contain reference to the adoc file
                adoc_path = str(rules_path / "rule.adoc")
                assert adoc_path in result.output
