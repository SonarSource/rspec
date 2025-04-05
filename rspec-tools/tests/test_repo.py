from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import Repo
from rspec_tools.repo import get_last_file_modifier, RspecRepo


def _read_counter_file(repo: Repo):
    """Reads the counter file from the provided repository and returns its content."""
    repo.git.checkout(RspecRepo.ID_COUNTER_BRANCH)
    counter_path = Path(repo.working_dir, RspecRepo.ID_COUNTER_FILENAME)
    return counter_path.read_text()


def test_reserve_rule_number_simple(rspec_repo: RspecRepo, mock_git_rspec_repo: Repo):
    """Test that RspecRepo.reserve_rule_number() increments the id and returns the old value."""
    assert rspec_repo.reserve_rule_number() == 0

    assert _read_counter_file(mock_git_rspec_repo) == "1"


def test_reserve_rule_number_parallel_reservations(
    tmpdir, mock_git_rspec_repo: Repo, git_config
):
    """Test that RspecRepo.reserve_rule_number() works when multiple reservations are done in parallel."""
    cloned_repo1 = tmpdir.mkdir("cloned_repo1")
    rule_creator1 = RspecRepo(
        mock_git_rspec_repo.working_dir, str(cloned_repo1), git_config
    )
    cloned_repo2 = tmpdir.mkdir("cloned_repo2")
    rule_creator2 = RspecRepo(
        mock_git_rspec_repo.working_dir, str(cloned_repo2), git_config
    )

    assert rule_creator1.reserve_rule_number() == 0
    assert rule_creator2.reserve_rule_number() == 1
    assert rule_creator1.reserve_rule_number() == 2

    assert _read_counter_file(mock_git_rspec_repo) == "3"


@patch("rspec_tools.repo._auto_github")
def test_get_last_file_modifier(mock_auto_github):
    # Setup mocks
    mock_commit_author = MagicMock()
    mock_commit_author.login = "test-user"
    mock_commit_author.id = 12345

    mock_commit_info = MagicMock()
    mock_commit_info.author.name = "Test User"
    mock_commit_info.author.email = "test@example.com"
    mock_commit_info.author.date.isoformat.return_value = "2023-01-01T12:00:00Z"
    mock_commit_info.message = "Test commit message"

    mock_commit = MagicMock()
    mock_commit.author = mock_commit_author
    mock_commit.commit = mock_commit_info

    mock_commits = MagicMock()
    mock_commits.totalCount = 1
    mock_commits.__getitem__.return_value = mock_commit

    mock_repo = MagicMock()
    mock_repo.get_commits.return_value = mock_commits

    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    mock_github_api = MagicMock(return_value=mock_github)
    mock_auto_github.return_value = mock_github_api

    # Call the function
    result = get_last_file_modifier("fake-token", "owner/repo", "path/to/file.txt")

    # Verify the result
    assert result["login"] == "test-user"
    assert result["id"] == "12345"
    assert result["name"] == "Test User"
    assert result["email"] == "test@example.com"
    assert result["message"] == "Test commit message"

    # Verify the mocks were called correctly
    mock_auto_github.assert_called_once_with("fake-token")
    mock_github_api.assert_called_once_with(None)
    mock_github.get_repo.assert_called_once_with("owner/repo")
    mock_repo.get_commits.assert_called_once_with(path="path/to/file.txt")
