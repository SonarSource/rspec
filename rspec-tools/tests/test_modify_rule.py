import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo
from rspec_tools.errors import InvalidArgumentError
from rspec_tools.modify_rule import (
    batch_find_replace,
    RuleEditor,
    update_rule_quickfix_status,
)
from rspec_tools.repo import RspecRepo

from tests.conftest import mock_github


@pytest.fixture
def rule_editor(rspec_repo: RspecRepo):
    return RuleEditor(rspec_repo)


def test_update_quickfix_status_branch1(
    rule_editor: RuleEditor, mock_git_rspec_repo: Repo
):
    """Test update_quickfix_status_branch when quickfix field is not present in language-specific metadata"""
    rule_number = 100
    language = "cfamily"

    sub_path = Path("rules", f"S{rule_number}", language, "metadata.json")
    metadata_path = Path(mock_git_rspec_repo.working_dir) / sub_path
    mock_git_rspec_repo.git.checkout("master")
    initial_metadata = json.loads(metadata_path.read_text())
    assert "quickfix" not in initial_metadata  # It is in the parent metadata.json file.

    branch = rule_editor.update_quickfix_status_branch(
        "Some title", rule_number, language, "covered"
    )
    mock_git_rspec_repo.git.checkout(branch)
    new_metadata = json.loads(metadata_path.read_text())

    # Verify that only the quickfix status is introduced.
    assert len(initial_metadata.keys()) + 1 == len(new_metadata.keys())
    assert "quickfix" in new_metadata
    assert "covered" == new_metadata["quickfix"]
    for key in initial_metadata:
        assert initial_metadata[key] == new_metadata[key]

    # Ensure only one file is modified.
    modified_files = mock_git_rspec_repo.git.diff("master", "--name-only").strip()
    assert Path(modified_files) == sub_path


def test_update_quickfix_status_branch2(
    rule_editor: RuleEditor, mock_git_rspec_repo: Repo
):
    """Test update_quickfix_status_branch when quickfix field is already present in language-specific metadata"""
    rule_number = 100
    language = "java"

    sub_path = Path("rules", f"S{rule_number}", language, "metadata.json")
    metadata_path = Path(mock_git_rspec_repo.working_dir) / sub_path
    mock_git_rspec_repo.git.checkout("master")
    initial_metadata = json.loads(metadata_path.read_text())
    assert "quickfix" in initial_metadata
    assert initial_metadata["quickfix"] == "targeted"

    branch = rule_editor.update_quickfix_status_branch(
        "Some title", rule_number, language, "covered"
    )
    mock_git_rspec_repo.git.checkout(branch)
    new_metadata = json.loads(metadata_path.read_text())

    # Verify that only the quickfix status is updated.
    assert len(initial_metadata.keys()) == len(new_metadata.keys())
    assert "quickfix" in new_metadata
    assert "covered" == new_metadata["quickfix"]
    for key in initial_metadata:
        if key != "quickfix":
            assert initial_metadata[key] == new_metadata[key]

    # Ensure only one file is modified.
    modified_files = mock_git_rspec_repo.git.diff("master", "--name-only").strip()
    assert Path(modified_files) == sub_path


def test_update_quickfix_status_branch3(
    rule_editor: RuleEditor, mock_git_rspec_repo: Repo
):
    """Test update_quickfix_status_branch when new and old quickfix status are the same"""
    rule_number = 100
    language = "java"

    metadata_path = Path(
        mock_git_rspec_repo.working_dir,
        "rules",
        f"S{rule_number}",
        language,
        "metadata.json",
    )
    mock_git_rspec_repo.git.checkout("master")
    initial_metadata = json.loads(metadata_path.read_text())
    assert "quickfix" in initial_metadata
    assert initial_metadata["quickfix"] == "targeted"

    with pytest.raises(InvalidArgumentError):
        rule_editor.update_quickfix_status_branch(
            "Some title", rule_number, language, "targeted"
        )


def test_update_quickfix_status_branch4(
    rule_editor: RuleEditor, mock_git_rspec_repo: Repo
):
    """Test update_quickfix_status_branch when the rule does not exist"""
    rule_number = 404
    language = "java"

    metadata_path = Path(
        mock_git_rspec_repo.working_dir,
        "rules",
        f"S{rule_number}",
        language,
        "metadata.json",
    )
    mock_git_rspec_repo.git.checkout("master")
    assert not metadata_path.exists()

    with pytest.raises(InvalidArgumentError):
        rule_editor.update_quickfix_status_branch(
            "Some title", rule_number, language, "targeted"
        )


def test_update_quickfix_status_pull_request(rule_editor: RuleEditor):
    """Test update_quickfix_status_pull_request adds the right user and label."""
    with mock_github() as (token, user, mock_repo):
        rule_editor.update_quickfix_status_pull_request(
            token, 100, "cfamily", "covered", "label-fraicheur", user
        )
        mock_repo.create_pull.assert_called_once()
        assert mock_repo.create_pull.call_args.kwargs["title"].startswith(
            "Modify rule S100"
        )
        mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(user)
        mock_repo.create_pull.return_value.add_to_labels.assert_called_with(
            "label-fraicheur"
        )


def test_batch_find_replace_pull_request_multiple_rules(rule_editor: RuleEditor):
    """Test batch_find_replace_pull_request creates PR with appropriate labels and assignee for multiple rules."""
    with mock_github() as (token, user, mock_repo):
        # Mock the batch_find_replace_branch method to return expected values
        affected_rules = {"S123": {"java"}, "S456": {"python"}}
        modified_files = [
            Path("rules/S123/java/test.txt"),
            Path("rules/S456/python/test.txt"),
        ]

        with patch.object(
            rule_editor,
            "batch_find_replace_branch",
            return_value=("test-branch", affected_rules, modified_files),
        ):
            rule_editor.batch_find_replace_pull_request(
                token,
                "old text",
                "new text",
                "update text",
                "PR description",
                user,
                None,
            )

            # Assert PR was created
            mock_repo.create_pull.assert_called_once()

            # Verify PR title format
            title = mock_repo.create_pull.call_args.kwargs["title"]
            assert "Modify rules S123, S456: update text" in title

            # Verify assignees and labels
            mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(user)

            # Check that labels were added
            labels_call = mock_repo.create_pull.return_value.add_to_labels.call_args
            assert labels_call is not None

            # Test with specific assignee
            mock_repo.create_pull.reset_mock()
            rule_editor.batch_find_replace_pull_request(
                token,
                "old text",
                "new text",
                "update text",
                "PR description",
                user,
                "specific-user",
            )
            mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(
                "specific-user"
            )


def test_batch_find_replace_pull_request_single_rule(rule_editor: RuleEditor):
    """Test batch_find_replace_pull_request creates PR with proper title for a single rule."""
    with mock_github() as (token, user, mock_repo):
        # Mock the batch_find_replace_branch method to return values for a single rule
        affected_rules = {"S789": {"java"}}

        # Create paths using the repository working directory
        repo_dir = Path(rule_editor.rspec_repo.repository.working_dir)
        modified_files = [
            repo_dir / "rules/S789/java/rule.adoc",
        ]

        with patch.object(
            rule_editor,
            "batch_find_replace_branch",
            return_value=("test-branch-single", affected_rules, modified_files),
        ):
            rule_editor.batch_find_replace_pull_request(
                token,
                "old pattern",
                "new pattern",
                "fix description format",
                "PR description for single rule update",
                user,
                None,
            )

            # Assert PR was created
            mock_repo.create_pull.assert_called_once()

            # Verify PR title - should use singular form for single rule
            title = mock_repo.create_pull.call_args.kwargs["title"]
            assert "Modify rule S789: fix description format" in title
            assert "rules" not in title  # Should not use plural form

            # Verify labels are added
            mock_repo.create_pull.return_value.add_to_labels.assert_called_once()


def test_batch_find_replace_pull_request_auto_assignee(rule_editor: RuleEditor):
    """Test batch_find_replace_pull_request automatically finds the appropriate assignee based on file history."""
    with mock_github() as (token, user, mock_repo):
        # Modified files for the test
        repo_dir = Path(rule_editor.rspec_repo.repository.working_dir)
        modified_files = [
            repo_dir / "rules/S111/python/rule.adoc",
        ]
        affected_rules = {"S111": {"python"}}

        # Set up the mocks
        auto_detected_author = "file-author"

        with patch.object(
            rule_editor,
            "batch_find_replace_branch",
            return_value=("test-branch-auto-assignee", affected_rules, modified_files),
        ), patch(
            "rspec_tools.modify_rule.get_last_login_modified_file",
            return_value=auto_detected_author,
        ):
            rule_editor.batch_find_replace_pull_request(
                token,
                "old text",
                "new text",
                "update formatting",
                "PR description with auto assignee",
                user,
                None,  # Pass None to trigger auto assignee detection
            )

            # Verify that PR was created with the auto-detected assignee
            mock_repo.create_pull.assert_called_once()

            # The assignee should be the auto-detected author, not the user
            mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(
                auto_detected_author
            )
            assert (
                mock_repo.create_pull.return_value.add_to_assignees.call_args.args[0]
                != user
            )


@patch("rspec_tools.modify_rule.tmp_rspec_repo")
@patch("rspec_tools.modify_rule.RuleEditor")
def test_update_rule_quickfix_status(mockRuleEditor, mock_tmp_rspec_repo):
    """Test update_rule_quickfix_status uses the expected implementation."""
    prMock = mockRuleEditor.return_value.update_quickfix_status_pull_request
    update_rule_quickfix_status("cfamily", "S100", "covered", "my token", "testuser")
    prMock.assert_called_once()
    assert prMock.call_args.args[1] == 100
    assert prMock.call_args.args[2] == "cfamily"
    assert prMock.call_args.args[3] == "covered"
    assert prMock.call_args.args[4] == "cfamily"


@patch("rspec_tools.modify_rule.tmp_rspec_repo")
@patch("rspec_tools.modify_rule.RuleEditor")
def test_batch_find_replace(mockRuleEditor, mock_tmp_rspec_repo):
    """Test batch_find_replace uses the expected implementation."""
    prMock = mockRuleEditor.return_value.batch_find_replace_pull_request
    batch_find_replace(
        "text to find",
        "replacement text",
        "update description text",
        "PR description",
        "my token",
        "testuser",
        "assignee",
    )
    prMock.assert_called_once()
    assert prMock.call_args.args[1] == "text to find"
    assert prMock.call_args.args[2] == "replacement text"
    assert prMock.call_args.args[3] == "update description text"
    assert prMock.call_args.args[4] == "PR description"
    assert prMock.call_args.args[5] == "testuser"
    assert prMock.call_args.args[6] == "assignee"


def test_batch_find_replace_branch(rule_editor: RuleEditor, mock_git_rspec_repo: Repo):
    """Test that batch_find_replace_branch correctly identifies and modifies files."""
    # Need to simulate some files in the rules directory
    rules_dir = Path(mock_git_rspec_repo.working_dir) / "rules"
    test_rule_dir = rules_dir / "S123" / "java"
    test_rule_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_rule_dir / "test.txt"
    test_file.write_text("This is a test file with search_text in it.")

    mock_git_rspec_repo.git.checkout("master")
    mock_git_rspec_repo.index.add([str(test_file)])
    mock_git_rspec_repo.index.commit("Add test file")

    branch_name, affected_rules, modified_files = rule_editor.batch_find_replace_branch(
        "Test batch replace", "search_text", "replacement_text"
    )

    # Verify branch was created
    assert branch_name.startswith("rule/batch-replace-")

    # Check that the right rule and language were identified
    assert "S123" in affected_rules
    assert "java" in affected_rules["S123"]

    # Verify file was modified
    mock_git_rspec_repo.git.checkout(branch_name)
    modified_content = test_file.read_text()
    assert "replacement_text" in modified_content
    assert "search_text" not in modified_content
