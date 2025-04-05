import json
import re
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

import click

from rspec_tools.errors import InvalidArgumentError, RuleNotFoundError

from rspec_tools.repo import RspecRepo, tmp_rspec_repo
from rspec_tools.utils import get_label_for_language, resolve_rule


@contextmanager
def _rule_editor(token: str, user: Optional[str]):
    with tmp_rspec_repo(token, user) as repo:
        yield RuleEditor(repo)


def update_rule_quickfix_status(
    language: str, rule: str, status: str, token: str, user: Optional[str]
):
    label = get_label_for_language(language)
    rule_number = resolve_rule(rule)
    with _rule_editor(token, user) as editor:
        editor.update_quickfix_status_pull_request(
            token, rule_number, language, status, label, user
        )


def replace_string_in_file(
    file_path: str,
    search_text: str,
    replace_text: str,
    token: str,
    user: Optional[str],
    title: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Create a pull request to replace a string in a specific file.

    Args:
        file_path: Path to the file relative to the repository root
        search_text: Text to search for
        replace_text: Text to replace with
        token: GitHub token
        user: GitHub username (optional)
        title: Custom PR title (optional)
        description: Custom PR description (optional)
    """
    with _rule_editor(token, user) as editor:
        editor.replace_string_in_file_pull_request(
            token,
            file_path,
            search_text,
            replace_text,
            user,
            title,
            description,
        )


class RuleEditor:
    """Modify an existing Rule in a repository following the official Github 'rspec' repository structure."""

    def __init__(self, rspec_repo: RspecRepo):
        self.rspec_repo = rspec_repo
        self.repo_dir = Path(self.rspec_repo.repository.working_dir)

    def update_quickfix_status_branch(
        self, title: str, rule_number: int, language: str, status: str
    ) -> str:
        """Update the given rule/language quick fix metadata field."""
        branch_name = f"rule/S{rule_number}-{language}-quickfix"
        with self.rspec_repo.checkout_branch(
            self.rspec_repo.master_branch, branch_name
        ):
            self._update_quickfix_status(rule_number, language, status)
            self.rspec_repo.commit_all_and_push(title)

        return branch_name

    def update_quickfix_status_pull_request(
        self,
        token: str,
        rule_number: int,
        language: str,
        status: str,
        label: str,
        user: Optional[str],
    ):
        title = f'Modify rule S{rule_number}: mark quick fix as "{status}"'
        branch_name = self.update_quickfix_status_branch(
            title, rule_number, language, status
        )
        click.echo(f"Created rule branch {branch_name}")
        return self.rspec_repo.create_pull_request(
            token,
            branch_name,
            title,
            f"""See the original rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{language}).

The rule won't be updated until this PR is merged, see [RULEAPI-655](https://jira.sonarsource.com/browse/RULEAPI-655)""",
            [label],
            user,
        )

    def _get_generic_quickfix_status(self, rule_number: int):
        DEFAULT = "unknown"
        generic_metadata_path = (
            self.repo_dir / "rules" / f"S{rule_number}" / "metadata.json"
        )
        if not generic_metadata_path.is_file():
            return DEFAULT
        generic_metadata = json.loads(generic_metadata_path.read_text())
        return generic_metadata.get("quickfix", DEFAULT)

    def _update_quickfix_status(self, rule_number: int, language: str, status: str):
        metadata_path = (
            self.repo_dir / "rules" / f"S{rule_number}" / language / "metadata.json"
        )
        if not metadata_path.is_file():
            raise InvalidArgumentError(
                f"{metadata_path} does not exist or is not a file"
            )

        metadata = json.loads(metadata_path.read_text())
        generic_status = self._get_generic_quickfix_status(rule_number)
        if status == metadata.get("quickfix", generic_status):
            raise InvalidArgumentError(
                f"{metadata_path} has already the same status {status}"
            )

        metadata["quickfix"] = status
        # When generating the JSON, ensure forward slashes are escaped. See RULEAPI-750.
        json_string = json.dumps(metadata, indent=2).replace("/", "\\/")
        metadata_path.write_text(json_string)

    def replace_string_in_file_branch(
        self,
        title: str,
        rule_number: int,
        language: Optional[str],
        file_path: str,
        search_text: str,
        replace_text: str,
    ) -> str:
        """
        Create a branch and replace a string in a file.

        Args:
            title: Commit message
            rule_number: Rule number (e.g., 1234 for S1234)
            language: Language identifier (e.g., "java") or None for generic files
            file_path: Path to the file relative to the repository root
            search_text: Text to search for
            replace_text: Text to replace with

        Returns:
            Name of the created branch
        """
        branch_suffix = f"{language}-" if language else ""
        branch_name = f"rule/S{rule_number}-{branch_suffix}text-replacement"
        with self.rspec_repo.checkout_branch(
            self.rspec_repo.master_branch, branch_name
        ):
            self._replace_text_in_file(file_path, search_text, replace_text)
            self.rspec_repo.commit_all_and_push(title)

        return branch_name

    def replace_string_in_file_pull_request(
        self,
        token: str,
        file_path: str,
        search_text: str,
        replace_text: str,
        user: Optional[str],
        custom_title: Optional[str] = None,
        custom_description: Optional[str] = None,
    ):
        """
        Create a pull request that replaces text in a file.

        Args:
            token: GitHub token
            file_path: Path to the file relative to the repository root (must follow pattern 'rules/S{rule_number}/...')
            search_text: Text to search for
            replace_text: Text to replace with
            user: GitHub username to assign the PR to
            custom_title: Optional custom PR title
            custom_description: Optional custom PR description
        """
        # Extract rule number and language from file path
        path_parts = Path(file_path).parts
        if len(path_parts) < 2 or path_parts[0] != "rules" or not path_parts[1].startswith("S"):
            raise InvalidArgumentError(
                f"File path '{file_path}' does not follow the expected pattern 'rules/S{{rule_number}}/...'"
            )

        rule_id = path_parts[1]
        rule_number = resolve_rule(rule_id)
        
        # Check if there's a language component
        language = None
        label = None
        if len(path_parts) >= 3:
            language = path_parts[2]
            try:
                label = get_label_for_language(language)
            except InvalidArgumentError:
                # If not a valid language, assume it's just a subfolder
                language = None
                label = None
        title = (
            custom_title or f"Modify rule S{rule_number}: update text in {file_path}"
        )
        branch_name = self.replace_string_in_file_branch(
            title, rule_number, language, file_path, search_text, replace_text
        )
        click.echo(f"Created rule branch {branch_name}")

        # Create description with or without language reference
        if language:
            description = custom_description or (
                f"""See the original rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{language}).

Text replacement in file `{file_path}`:
- Search: `{search_text}`
- Replace: `{replace_text}`

The rule won't be updated until this PR is merged."""
            )
        else:
            description = custom_description or (
                f"""See the rule S{rule_number} [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}).

Text replacement in file `{file_path}`:
- Search: `{search_text}`
- Replace: `{replace_text}`

The rule won't be updated until this PR is merged."""
            )

        # Create PR with or without label
        labels = [label] if label else []
        return self.rspec_repo.create_pull_request(
            token,
            branch_name,
            title,
            description,
            labels,
            user,
        )

    def _replace_text_in_file(
        self,
        file_path: str,
        search_text: str,
        replace_text: str,
    ):
        """
        Replace text in a file.

        Args:
            file_path: Path to the file relative to the repository root
            search_text: Text to search for
            replace_text: Text to replace with
        """

        # Resolve the full path to the specified file
        target_file = self.repo_dir / file_path
        if not target_file.exists() or not target_file.is_file():
            raise InvalidArgumentError(
                f"File {file_path} does not exist or is not a file"
            )

        # Read the file content
        content = target_file.read_text(encoding="utf-8")

        # Check if the search text exists in the file
        if search_text not in content:
            raise InvalidArgumentError(f"Search text not found in {file_path}")

        # Replace the text
        new_content = content.replace(search_text, replace_text)

        # Write the modified content back to the file
        target_file.write_text(new_content, encoding="utf-8")
