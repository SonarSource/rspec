import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from git import Repo
from rspec_tools.errors import InvalidArgumentError, RuleNotFoundError
from rspec_tools.modify_rule import (
    replace_string_in_file,
    replace_string_in_all_rules,
    RuleEditor,
    update_rule_quickfix_status,
)
from rspec_tools.repo import RspecRepo
from rspec_tools.utils import get_default_branch

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

    mock_git_rspec_repo.git.checkout(get_default_branch(mock_git_rspec_repo))
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
    modified_files = mock_git_rspec_repo.git.diff(
        get_default_branch(mock_git_rspec_repo), "--name-only"
    ).strip()
    assert Path(modified_files) == sub_path


def test_update_quickfix_status_branch2(
    rule_editor: RuleEditor, mock_git_rspec_repo: Repo
):
    """Test update_quickfix_status_branch when quickfix field is already present in language-specific metadata"""
    rule_number = 100
    language = "java"

    sub_path = Path("rules", f"S{rule_number}", language, "metadata.json")
    metadata_path = Path(mock_git_rspec_repo.working_dir) / sub_path
    mock_git_rspec_repo.git.checkout(get_default_branch(mock_git_rspec_repo))
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
    modified_files = mock_git_rspec_repo.git.diff(
        get_default_branch(mock_git_rspec_repo), "--name-only"
    ).strip()
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
    mock_git_rspec_repo.git.checkout(get_default_branch(mock_git_rspec_repo))
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
    mock_git_rspec_repo.git.checkout(get_default_branch(mock_git_rspec_repo))
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


# Tests for new text replacement functionality


@pytest.fixture
def setup_rule_editor():
    # Mock RspecRepo
    mock_repo = Mock(spec=RspecRepo)
    mock_repo.repository = Mock()
    mock_repo.master_branch = "main"

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create necessary directories and files
        rule_path = tmp_path / "rules" / "S1234" / "java"
        rule_path.mkdir(parents=True)

        # Create metadata.json
        metadata_file = rule_path / "metadata.json"
        metadata_file.write_text('{"title": "Test Rule", "type": "CODE_SMELL"}')

        # Create a test file
        test_file = rule_path / "rule.adoc"
        test_file.write_text("This is a test rule with some text to replace.")

        # Setup mock repo to use this directory
        mock_repo.repository.working_dir = str(tmp_path)

        # Create RuleEditor with the mock repo
        rule_editor = RuleEditor(mock_repo)

        yield rule_editor, mock_repo, tmp_path


def test_replace_text_in_file(setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Call the method under test
    rule_editor._replace_text_in_file(
        file_path="rules/S1234/java/rule.adoc",
        search_text="some text to replace",
        replace_text="replaced text",
    )

    # Verify the content was changed
    test_file = tmp_path / "rules" / "S1234" / "java" / "rule.adoc"
    assert test_file.read_text() == "This is a test rule with replaced text."


def test_replace_string_in_file_branch(setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Setup checkout_branch context manager mock
    mock_repo.checkout_branch.return_value.__enter__ = Mock()
    mock_repo.checkout_branch.return_value.__exit__ = Mock()

    # Call the method under test
    branch_name = rule_editor.replace_string_in_file_branch(
        title="Update rule text",
        rule_number=1234,
        language="java",
        file_path="rules/S1234/java/rule.adoc",
        search_text="some text to replace",
        replace_text="replaced text",
    )

    # Verify the branch name format
    assert branch_name == "rule/S1234-java-text-replacement"

    # Verify commit was made
    mock_repo.commit_all_and_push.assert_called_once_with("Update rule text")


@patch("rspec_tools.modify_rule.click.echo")
def test_replace_string_in_file_pull_request(mock_echo, setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Setup mocks
    mock_repo.checkout_branch.return_value.__enter__ = Mock()
    mock_repo.checkout_branch.return_value.__exit__ = Mock()
    mock_pr = Mock()
    mock_repo.create_pull_request.return_value = mock_pr

    # Call the method under test
    rule_editor.replace_string_in_file_pull_request(
        token="fake-token",
        file_path="rules/S1234/java/rule.adoc",
        search_text="some text to replace",
        replace_text="replaced text",
        user="testuser",
    )

    # Verify PR creation
    mock_repo.create_pull_request.assert_called_once()

    # Verify the PR title and description contain the file path and search/replace text
    call_args = mock_repo.create_pull_request.call_args[0]
    assert "rules/S1234/java/rule.adoc" in call_args[2]  # Title
    description = call_args[3]  # Description
    assert "rules/S1234/java/rule.adoc" in description
    assert "some text to replace" in description
    assert "replaced text" in description

    # Verify labels and user assignment
    assert call_args[4] == ["java"]  # Labels
    assert call_args[5] == "testuser"  # User


def test_replace_text_file_not_found(setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Test with non-existent file
    with pytest.raises(InvalidArgumentError, match="does not exist"):
        rule_editor._replace_text_in_file(
            file_path="rules/S1234/java/nonexistent.adoc",
            search_text="text",
            replace_text="new text",
        )


def test_replace_text_search_not_found(setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Test with text that doesn't exist in the file
    with pytest.raises(InvalidArgumentError, match="Search text not found"):
        rule_editor._replace_text_in_file(
            file_path="rules/S1234/java/rule.adoc",
            search_text="nonexistent text",
            replace_text="new text",
        )


def test_invalid_file_path_format(setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Test with an invalid file path format
    with pytest.raises(
        InvalidArgumentError, match="does not follow the expected pattern"
    ):
        rule_editor.replace_string_in_file_pull_request(
            token="fake-token",
            file_path="invalid/path/format.txt",
            search_text="text",
            replace_text="new text",
            user="testuser",
        )


def test_generic_rule_file_without_language(setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Create a generic rule file directly under the rule ID
    generic_rule_dir = tmp_path / "rules" / "S1234"
    os.makedirs(generic_rule_dir, exist_ok=True)
    generic_file = generic_rule_dir / "metadata.json"
    generic_file.write_text('{"title": "Generic Rule", "type": "CODE_SMELL"}')

    # Setup mocks
    mock_repo.checkout_branch.return_value.__enter__ = Mock()
    mock_repo.checkout_branch.return_value.__exit__ = Mock()
    mock_pr = Mock()
    mock_repo.create_pull_request.return_value = mock_pr

    # Call the method with a path that doesn't include a language
    rule_editor.replace_string_in_file_pull_request(
        token="fake-token",
        file_path="rules/S1234/metadata.json",
        search_text="Generic Rule",
        replace_text="Updated Generic Rule",
        user="testuser",
    )

    # Verify PR creation
    mock_repo.create_pull_request.assert_called_once()

    # Verify branch name doesn't include a language
    call_args = mock_repo.create_pull_request.call_args[0]
    branch_name = call_args[1]
    assert "rule/S1234-text-replacement" == branch_name

    # Verify PR description doesn't reference a specific language
    description = call_args[3]
    assert "rules/S1234/metadata.json" in description
    assert "Generic Rule" in description
    assert "Updated Generic Rule" in description

    # Verify no labels were added
    assert call_args[4] == []
    

@patch("rspec_tools.modify_rule.click.echo")
def test_replace_string_in_all_rules_pull_request(mock_echo, setup_rule_editor):
    rule_editor, mock_repo, tmp_path = setup_rule_editor

    # Create multiple rule directories with files containing the search text
    rules_dir = tmp_path / "rules"
    
    # Create S1234 rule with two language-specific files
    s1234_dir = rules_dir / "S1234"
    java_dir = s1234_dir / "java"
    python_dir = s1234_dir / "python"
    os.makedirs(java_dir, exist_ok=True)
    os.makedirs(python_dir, exist_ok=True)
    
    java_file = java_dir / "rule.adoc"
    java_file.write_text("This is a sample rule with TEXT_TO_REPLACE in it.")
    
    python_file = python_dir / "rule.adoc"
    python_file.write_text("Python version with TEXT_TO_REPLACE in a different file.")
    
    # Create S5678 rule with a file
    s5678_dir = rules_dir / "S5678"
    js_dir = s5678_dir / "javascript"
    os.makedirs(js_dir, exist_ok=True)
    
    js_file = js_dir / "rule.adoc"
    js_file.write_text("JavaScript rule with TEXT_TO_REPLACE to be changed.")
    
    # Create a file that shouldn't match
    no_match_dir = rules_dir / "S9999" / "go"
    os.makedirs(no_match_dir, exist_ok=True)
    no_match_file = no_match_dir / "rule.adoc"
    no_match_file.write_text("This file doesn't have the text to replace.")

    # Setup mocks
    mock_repo.checkout_branch.return_value.__enter__ = Mock()
    mock_repo.checkout_branch.return_value.__exit__ = Mock()
    mock_pr = Mock()
    mock_repo.create_pull_request.return_value = mock_pr
    
    # Mock datetime to get a predictable branch name
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value.timestamp.return_value = 1234567890
        
        # Call the method
        rule_editor.replace_string_in_all_rules_pull_request(
            token="fake-token",
            search_text="TEXT_TO_REPLACE",
            replace_text="REPLACED_TEXT",
            user="testuser",
        )
    
    # Verify files were modified
    assert "REPLACED_TEXT" in java_file.read_text()
    assert "REPLACED_TEXT" in python_file.read_text()
    assert "REPLACED_TEXT" in js_file.read_text()
    assert "TEXT_TO_REPLACE" not in java_file.read_text()
    assert "TEXT_TO_REPLACE" not in python_file.read_text()
    assert "TEXT_TO_REPLACE" not in js_file.read_text()
    
    # The no-match file should be unchanged
    assert "This file doesn't have the text to replace." == no_match_file.read_text()
    
    # Verify PR creation
    mock_repo.create_pull_request.assert_called_once()
    
    # Verify the PR title contains both rule IDs
    call_args = mock_repo.create_pull_request.call_args[0]
    title = call_args[2]
    assert "S1234" in title
    assert "S5678" in title
    
    # Verify PR description includes info about all modified files
    description = call_args[3]
    assert "TEXT_TO_REPLACE" in description
    assert "REPLACED_TEXT" in description
    assert "rules/S1234/java/rule.adoc" in description
    assert "rules/S1234/python/rule.adoc" in description
    assert "rules/S5678/javascript/rule.adoc" in description
    
    # Verify labels include all affected languages
    labels = call_args[4]
    assert "java" in labels
    assert "python" in labels
    assert "jsts" in labels  # JavaScript uses this label


@patch("rspec_tools.modify_rule.tmp_rspec_repo")
@patch("rspec_tools.modify_rule.RuleEditor")
def test_replace_string_in_file_function(mock_rule_editor, mock_tmp_rspec_repo):
    """Test replace_string_in_file properly calls the underlying implementation."""
    # Setup mock
    pr_mock = mock_rule_editor.return_value.replace_string_in_file_pull_request

    # Call the function
    replace_string_in_file(
        file_path="rules/S1234/java/rule.adoc",
        search_text="old text",
        replace_text="new text",
        token="fake-token",
        user="testuser",
        title="Custom title",
        description="Custom description",
    )

    # Verify the call
    pr_mock.assert_called_once()
    assert pr_mock.call_args.args[0] == "fake-token"
    assert pr_mock.call_args.args[1] == "rules/S1234/java/rule.adoc"
    assert pr_mock.call_args.args[2] == "old text"
    assert pr_mock.call_args.args[3] == "new text"
    assert pr_mock.call_args.args[4] == "testuser"
    assert pr_mock.call_args.args[5] == "Custom title"
    assert pr_mock.call_args.args[6] == "Custom description"


@patch("rspec_tools.modify_rule.tmp_rspec_repo")
@patch("rspec_tools.modify_rule.RuleEditor")
def test_replace_string_in_all_rules_function(mock_rule_editor, mock_tmp_rspec_repo):
    """Test replace_string_in_all_rules properly calls the underlying implementation."""
    # Setup mock
    pr_mock = mock_rule_editor.return_value.replace_string_in_all_rules_pull_request
    
    # Call the function
    from rspec_tools.modify_rule import replace_string_in_all_rules
    replace_string_in_all_rules(
        search_text="old text",
        replace_text="new text",
        token="fake-token",
        user="testuser",
        description="Custom description",
    )
    
    # Verify the call
    pr_mock.assert_called_once()
    assert pr_mock.call_args.args[0] == "fake-token"
    assert pr_mock.call_args.args[1] == "old text"
    assert pr_mock.call_args.args[2] == "new text"
    assert pr_mock.call_args.args[3] == "testuser"
    assert pr_mock.call_args.args[4] == "Custom description"
