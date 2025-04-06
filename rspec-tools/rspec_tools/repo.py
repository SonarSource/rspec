import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Final, Iterable, List, Optional

import click
from git import Repo
from github import Github
from github.Commit import Commit
from github.Repository import Repository


def _auto_github(token: str) -> Callable[[Optional[str]], Github]:
    def ret(user: Optional[str]):
        if user:
            return Github(user, token)
        else:
            return Github(token)

    return ret


class RspecRepo:
    """Provide operations on a git repository for rule specifications."""

    MASTER_BRANCH: Final[str] = "master"
    ID_COUNTER_BRANCH: Final[str] = "rspec-id-counter"
    ID_COUNTER_FILENAME: Final[str] = "next_rspec_id.txt"

    repository: Final[Repo]
    origin_url: Final[str]

    def __init__(
        self, origin_url: str, clone_directory: str, configuration: dict[str, str]
    ):
        self.repository = Repo.clone_from(origin_url, clone_directory)
        self.origin_url = origin_url

        # Create local branches tracking remote ones
        for branch in [self.MASTER_BRANCH, self.ID_COUNTER_BRANCH]:
            self.repository.remote().fetch(branch)
            self.repository.git.checkout("-B", branch, f"origin/{branch}")

        # Update repository config
        with self.repository.config_writer() as config_writer:
            for key, value in configuration.items():
                split_key = key.split(".")
                config_writer.set_value(*split_key, value)

    def get_repository_name(self):
        url_end = self.origin_url.split("/")[-2:]
        return "/".join(url_end).removesuffix(".git")

    @contextmanager
    def checkout_branch(self, base_branch: str, new_branch: Optional[str] = None):
        """Checkout a given branch before yielding, then revert to the previous branch."""
        past_branch = self.repository.active_branch
        try:
            self.repository.git.checkout(base_branch)
            origin = self.repository.remote(name="origin")
            origin.pull()
            if new_branch is not None:
                self.repository.git.checkout("-B", new_branch)
            yield
        finally:
            self.repository.git.checkout(past_branch)

    def commit_all_and_push(self, message: str):
        self.repository.git.add("--all")
        self.repository.index.commit(message)
        self.repository.git.push("origin", self.repository.active_branch)

    def create_pull_request(
        self,
        token: str,
        branch_name: str,
        title: str,
        body: str,
        labels: Iterable[str],
        user: Optional[str],
    ):
        """Create a pull request from the given branch."""
        repository_url = self.get_repository_name()
        github_api = _auto_github(token)
        github = github_api(user)
        github_repo = github.get_repo(repository_url)
        pull_request = github_repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base=self.MASTER_BRANCH,
            draft=True,
            maintainer_can_modify=True,
        )
        click.echo(f"Created rule Pull Request {pull_request.html_url}")

        # Note: It is not possible to get the authenticated user using get_user() from a github action.
        login = user if user else github.get_user().login
        pull_request.add_to_assignees(login)
        pull_request.add_to_labels(*labels)
        click.echo(f"Pull request assigned to {login}")
        return pull_request

    def reserve_rule_number(self) -> int:
        """Reserve an id on the id counter branch of the repository."""
        with self.checkout_branch(self.ID_COUNTER_BRANCH):
            counter_file_path = Path(
                self.repository.working_dir, self.ID_COUNTER_FILENAME
            )
            counter = int(counter_file_path.read_text())
            counter_file_path.write_text(str(counter + 1))

            self.repository.index.add([str(counter_file_path)])
            self.repository.index.commit("Increment RSPEC ID counter")

        origin = self.repository.remote(name="origin")
        origin.push()

        click.echo(f"Reserved Rule ID S{counter}")
        return counter


def is_a_bot(username: str):
    return "[bot]" in username or username == "web-flow"


def get_last_login_modified_file(
    repo_name: str, file_path: str, max_commits: int = 3, token: Optional[str] = None # AI! make the token required argument and return the fallback from the body
) -> Optional[str]:
    """
    Find the last non-bot GitHub login that modified a given file.

    Args:
        repo_name: Repository name in format 'owner/repo'
        file_path: The path to the file within the repository
        max_commits: Maximum number of commits to check (default: 3)
        token: GitHub token (if None, will use GITHUB_TOKEN environment variable)

    Returns:
        The GitHub login of the last non-bot author, or None if not found
    """
    # Initialize GitHub client and get repository
    if token is None: # AI: here
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable is not set")

    github = Github(token)
    github_repo = github.get_repo(repo_name)

    # Get the last few commits for the file
    commits = list(github_repo.get_commits(path=file_path))[:max_commits]

    for commit in commits:
        # Try to get author login
        author = commit.author
        if author and not is_a_bot(author.login):
            return author.login

        # Try to get committer login
        committer = commit.committer
        if committer and not is_a_bot(committer.login):
            return committer.login

        # Try to find co-authors in commit message
        message = commit.commit.message
        co_author_matches = re.findall(
            r"Co-authored-by:.*?<(.+?)@users\.noreply\.github\.com>", message
        )
        if co_author_matches and not is_a_bot(co_author_matches[0]):
            return co_author_matches[0]  # Return the first co-author login

    # No suitable author found in any of the commits
    return None


def _build_github_repository_url(token: str, user: Optional[str]):
    """Builds the rspec repository url"""
    repo = os.environ.get("GITHUB_REPOSITORY", "SonarSource/rspec")
    if user:
        return f"https://{user}:{token}@github.com/{repo}.git"
    else:
        return f"https://{token}@github.com/{repo}.git"


def _get_url_and_config(token: str, user: Optional[str]):
    url = _build_github_repository_url(token, user)
    config = {}
    if user:
        config["user.name"] = user
        config["user.email"] = f"{user}@users.noreply.github.com"

    return url, config


@contextmanager
def tmp_rspec_repo(token: str, user: Optional[str]):
    """Yield a temporary repository"""
    url, config = _get_url_and_config(token, user)
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield RspecRepo(url, tmpdirname, config)
