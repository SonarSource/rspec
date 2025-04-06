import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from git import Repo
from rspec_tools.repo import get_last_login_modified_file, RspecRepo


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


def test_get_last_login_modified_file():
    """Test get_last_login_modified_file with various commit author scenarios."""

    with patch("rspec_tools.repo.Github") as mock_github:
        # Create mock objects
        mock_repo = mock_github.return_value.get_repo.return_value

        # Scenario 1: First commit has non-bot author
        mock_commit1 = MagicMock()
        mock_commit1.author.login = "real-user"
        mock_commit1.author.__bool__.return_value = True

        mock_repo.get_commits.return_value = [mock_commit1]
        result = get_last_login_modified_file(
            "fake-token", "owner/repo", "some/file.txt"
        )
        assert result == "real-user"
        mock_github.assert_called_once_with("fake-token")
        mock_github.return_value.get_repo.assert_called_once_with("owner/repo")

        # Scenario 2: First commit has bot author, second has real committer
        mock_github.reset_mock()
        mock_commit1 = MagicMock()
        mock_commit1.author.login = "dependabot[bot]"
        mock_commit1.author.__bool__.return_value = True
        mock_commit1.committer.login = "github-actions[bot]"
        mock_commit1.committer.__bool__.return_value = True
        mock_commit1.commit.message = "Update dependency"

        mock_commit2 = MagicMock()
        mock_commit2.committer.login = "real-committer"
        mock_commit2.committer.__bool__.return_value = True
        mock_commit2.author = None

        mock_repo.get_commits.return_value = [mock_commit1, mock_commit2]
        result = get_last_login_modified_file(
            "fake-token", "owner/repo", "some/file.txt"
        )
        assert result == "real-committer"

        # Scenario 3: Only co-authored-by is available
        mock_github.reset_mock()
        mock_commit1 = MagicMock()
        mock_commit1.author.login = "dependabot[bot]"
        mock_commit1.author.__bool__.return_value = True
        mock_commit1.committer.login = "github-actions[bot]"
        mock_commit1.committer.__bool__.return_value = True
        mock_commit1.commit.message = "Update dependency\n\nCo-authored-by: John Doe <johndoe@users.noreply.github.com>"

        mock_repo.get_commits.return_value = [mock_commit1]
        result = get_last_login_modified_file(
            "fake-token", "owner/repo", "some/file.txt"
        )
        assert result == "johndoe"

        # Scenario 4: No suitable author found
        mock_github.reset_mock()
        mock_commit1 = MagicMock()
        mock_commit1.author.login = "dependabot[bot]"
        mock_commit1.author.__bool__.return_value = True
        mock_commit1.committer.login = "github-actions[bot]"
        mock_commit1.committer.__bool__.return_value = True
        mock_commit1.commit.message = "Update dependency"

        mock_repo.get_commits.return_value = [mock_commit1]
        result = get_last_login_modified_file(
            "fake-token", "owner/repo", "some/file.txt"
        )
        assert result is None

        # Scenario 5: Using token from environment
        mock_github.reset_mock()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env-token"}):
            token = os.environ.get("GITHUB_TOKEN")
            result = get_last_login_modified_file(token, "owner/repo", "some/file.txt")
            mock_github.assert_called_once_with("env-token")
