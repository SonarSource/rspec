import os
import re
from pathlib import Path
from typing import List
from unittest.mock import patch

from click.testing import CliRunner
from rspec_tools.cli import cli
from rspec_tools.rules import RulesRepository


class TestCLIUpdateQuickfixStatus:
    """Unit test for quickfix status update through Command Line Interface."""

    @patch.dict(os.environ, {"GITHUB_TOKEN": "TOKEN"})
    @patch("rspec_tools.modify_rule.update_rule_quickfix_status")
    def test_basic_cli_usage(self, mock):
        arguments = [
            "update-quickfix-status",
            "--language",
            "langA",
            "--rule",
            "ruleX",
            "--status",
            "myStatus",
            "--user",
            "bob",
        ]
        CliRunner().invoke(cli, arguments)
        mock.assert_called_once_with("langA", "ruleX", "myStatus", "TOKEN", "bob")


class TestCLIValidateRulesMetadata:
    """Unit tests for metadata validation through Command Line Interface."""

    def _run(self, rules: List[str]):
        runner = CliRunner()
        arguments = ["validate-rules-metadata"] + rules
        return runner.invoke(cli, arguments)

    def _mock_rule_ressources(self):
        mock_path = Path(__file__).parent.joinpath("resources", "invalid-rules")
        return patch.object(RulesRepository.__init__, "__defaults__", (mock_path,))

    def test_missing_parameters(self):
        result = self._run([])
        assert "Missing argument 'RULES...'" in result.output
        assert result.exit_code == 2

    def test_valid_rule(self):
        """This test uses the actual rules data, not the mock resources."""
        result = self._run(["S100"])
        assert result.output == ""
        assert result.exit_code == 0

    @patch("rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES", ["S501"])
    def test_invalid_rule_in_allow_list(self):
        with self._mock_rule_ressources():
            result = self._run(["S501"])
            assert result.output == ""
            assert result.exit_code == 0

    @patch("rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES", [])
    def test_invalid_rule(self):
        with self._mock_rule_ressources():
            result = self._run(["S501"])
            assert "Rule S501 has no language-specific data" in result.output
            assert (
                "Validation failed due to 1 errors out of 1 analyzed rules"
                in result.output
            )
            assert result.exit_code == 1

    @patch("rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES", [])
    def test_invalid_rules(self):
        with self._mock_rule_ressources():
            result = self._run(["S501", "S502"])
            assert "Rule S501 has no language-specific data" in result.output
            assert "Rule S502 failed validation for these reasons:" in result.output
            assert (
                "Rule scala:S502 has invalid metadata : 'remediation' is a required property"
                in result.output
            )
            assert (
                "Validation failed due to 2 errors out of 2 analyzed rules"
                in result.output
            )
            assert result.exit_code == 1


class TestCLIValidateDescription:
    """Unit tests for description validation through Command Line Interface."""

    def _run(self, rules: List[str]):
        runner = CliRunner()
        mock_path = os.path.realpath(
            Path(__file__).parent.joinpath("resources", "rules")
        )
        arguments = ["check-description", "--d", mock_path] + rules
        return runner.invoke(cli, arguments)

    def _run_invalid(self, rules: List[str]):
        runner = CliRunner()
        mock_path = os.path.realpath(
            Path(__file__).parent.joinpath("resources", "invalid-rules")
        )
        arguments = ["check-description", "--d", mock_path] + rules
        return runner.invoke(cli, arguments)

    def test_valid_rule(self):
        result = self._run(["S3649"])
        assert result.output == ""
        assert result.exit_code == 0

    def test_invalid_rule(self):
        result = self._run_invalid(["S100"])
        assert re.search(r"Validation failed due to \d+ errors", result.output)
        assert result.exit_code == 1


class TestCLILastAuthor:
    """Unit tests for the last-author command."""

    @patch.dict(
        os.environ,
        {"GITHUB_TOKEN": "fake-token", "GITHUB_REPOSITORY": "test-owner/test-repo"},
    )
    @patch("rspec_tools.repo.get_last_login_modified_file")
    def test_success(self, mock_get_login):
        """Test successful author lookup."""
        mock_get_login.return_value = "johndoe"

        runner = CliRunner()
        result = runner.invoke(cli, ["last-author", "path/to/file.txt"])

        mock_get_login.assert_called_once_with(
            "fake-token", "test-owner/test-repo", "path/to/file.txt", 3
        )
        assert result.output.strip() == "johndoe"
        assert result.exit_code == 0

    @patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"})
    @patch("rspec_tools.repo.get_last_login_modified_file")
    def test_custom_parameters(self, mock_get_login):
        """Test with custom repository and max commits."""
        mock_get_login.return_value = "janedoe"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "last-author",
                "--repo",
                "custom/repo",
                "--max-commits",
                "5",
                "path/to/file.txt",
            ],
        )

        mock_get_login.assert_called_once_with(
            "fake-token", "custom/repo", "path/to/file.txt", 5
        )
        assert result.output.strip() == "janedoe"
        assert result.exit_code == 0

    @patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"})
    @patch("rspec_tools.repo.get_last_login_modified_file")
    def test_no_author_found(self, mock_get_login):
        """Test when no non-bot author is found."""
        mock_get_login.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ["last-author", "path/to/file.txt"])

        assert "No non-bot author found" in result.output
        assert result.exit_code == 1

    @patch.dict(os.environ, {})
    def test_missing_token(self):
        """Test error when GITHUB_TOKEN is not set."""
        runner = CliRunner()
        result = runner.invoke(cli, ["last-author", "path/to/file.txt"])

        assert "GITHUB_TOKEN environment variable is not set" in result.output
        assert result.exit_code == 1
