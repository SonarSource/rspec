import os
import pathlib
import shutil
import tempfile

from click.testing import CliRunner
from rspec_tools import checklinks, cli


def test_find_urls():
    urls = {}
    checklinks.findurl_in_html("tests/links/404/S100/java/rule.html", urls)
    assert urls == {
        "https://www.google.com/404": [{"html": "tests/links/404/S100/java/rule.html"}]
    }
    assert len(urls) == 1


def test_live():
    assert checklinks.live_url("https://www.google.com")


def test_not_live():
    assert not checklinks.live_url("https://ww.nothing")


def test_404():
    runner = CliRunner()
    result = runner.invoke(cli, ["check-links", "--d=tests/links/404"])
    print(result.output)
    assert result.exit_code == 1
    assert (
        "1/1 links are dead, see above ^^ the list and the related files"
        in result.output
    )


def test_url():
    runner = CliRunner()
    result = runner.invoke(cli, ["check-links", "--d=tests/links/URL"])
    print(result.output)
    assert result.exit_code == 1
    assert (
        "1/1 links are dead, see above ^^ the list and the related files"
        in result.output
    )


def test_ok():
    runner = CliRunner()
    result = runner.invoke(cli, ["check-links", "--d=tests/links/OK"])
    print(result.output)
    assert result.exit_code == 0
    assert "All 1 links are good" in result.output


def test_deprecated():
    runner = CliRunner()
    result = runner.invoke(cli, ["check-links", "--d=tests/links/deprecated"])
    print(result.output)
    assert result.exit_code == 0
    assert "All 1 links are good" in result.output


def test_show_adoc_when_exists():
    """Test that the link checker reports both adoc and html files when a link is dead."""
    # Create temporary directories for rules and output
    with tempfile.TemporaryDirectory() as rules_dir, tempfile.TemporaryDirectory() as output_dir:
        # Create rule structure with a dead link in both places
        rule_id = "S999"
        language = "python"

        # Create directories
        rules_path = pathlib.Path(rules_dir) / rule_id / language
        output_path = pathlib.Path(output_dir) / rule_id / language
        os.makedirs(rules_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)

        # Create metadata.json files
        for path in [rules_path.parent, output_path.parent]:
            with open(path / "metadata.json", "w") as f:
                f.write('{"status": "ready"}')

        for path in [rules_path, output_path]:
            with open(path / "metadata.json", "w") as f:
                f.write('{"status": "ready"}')

        # Create rule.adoc with a dead link
        with open(rules_path / "rule.adoc", "w") as f:
            f.write(
                """
= Title of the Rule
            
This rule contains a <a href="https://example.com/nonexistent">dead link</a>.
"""
            )

        # Create corresponding rule.html
        with open(output_path / "rule.html", "w") as f:
            f.write(
                """
<!DOCTYPE html>
<html>
<head><title>Title of the Rule</title></head>
<body>
<p>This rule contains a <a href="https://example.com/nonexistent">dead link</a>.</p>
</body>
</html>
"""
            )

        # Run the link checker with both directories
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["check-links", f"--d={output_dir}", f"--r={rules_dir}"]
            )

            print(result.output)

            # The command should exit with error code 1 (link check failure)
            assert result.exit_code == 1

            # Output should contain the dead link
            assert "https://example.com/nonexistent" in result.output

            # Output should contain reference to the adoc file
            adoc_path = str(rules_path / "rule.adoc")
            assert adoc_path in result.output


def test_show_adoc_with_relative_paths():
    """Test that the link checker works with relative paths for rules_dir and output_dir."""
    # Get current working directory
    cwd = os.getcwd()

    # Create temporary directories for rules and output relative to cwd
    with tempfile.TemporaryDirectory(dir=cwd) as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        rules_dir = temp_path / "rules"
        output_dir = temp_path / "output"

        # Create directories
        os.makedirs(rules_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Create rule structure
        rule_id = "S888"
        language = "javascript"

        rules_path = rules_dir / rule_id / language
        output_path = output_dir / rule_id / language
        os.makedirs(rules_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)

        # Create metadata.json files
        for path in [rules_path.parent, output_path.parent]:
            with open(path / "metadata.json", "w") as f:
                f.write('{"status": "ready"}')

        for path in [rules_path, output_path]:
            with open(path / "metadata.json", "w") as f:
                f.write('{"status": "ready"}')

        # Create rule.adoc with a dead link
        with open(rules_path / "rule.adoc", "w") as f:
            f.write(
                """
= Another Rule with a Dead Link
            
This is another rule with a <a href="https://example.org/broken-link">broken link</a>.
"""
            )

        # Create corresponding rule.html
        with open(output_path / "rule.html", "w") as f:
            f.write(
                """
<!DOCTYPE html>
<html>
<head><title>Another Rule with a Dead Link</title></head>
<body>
<p>This is another rule with a <a href="https://example.org/broken-link">broken link</a>.</p>
</body>
</html>
"""
            )

        # Get relative paths
        rel_rules_dir = os.path.relpath(rules_dir, cwd)
        rel_output_dir = os.path.relpath(output_dir, cwd)

        # Run the link checker with relative paths
        runner = CliRunner()
        result = runner.invoke(
            cli, ["check-links", f"--d={rel_output_dir}", f"--r={rel_rules_dir}"]
        )

        print(result.output)

        # The command should exit with error code 1 (link check failure)
        assert result.exit_code == 1

        # Output should contain the dead link
        assert "https://example.org/broken-link" in result.output

        # Output should contain reference to the adoc file (full path after resolution)
        adoc_path = str(rules_path / "rule.adoc")
        assert adoc_path in result.output
