import datetime
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Set

import click

from rspec_tools.errors import InvalidArgumentError, RuleNotFoundError

from rspec_tools.repo import get_last_file_modifier, RspecRepo, tmp_rspec_repo
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


def replace_string_in_all_rules(
    search_text: str,
    replace_text: str,
    token: str,
    user: Optional[str],
    description: Optional[str] = None,
):
    """
    Create a pull request to replace a string in all rule files.

    Args:
        search_text: Text to search for
        replace_text: Text to replace with
        token: GitHub token
        user: GitHub username (optional)
        description: Custom PR description (optional)
    """
    with _rule_editor(token, user) as editor:
        editor.replace_string_in_all_rules_pull_request(
            token,
            search_text,
            replace_text,
            user,
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

    def replace_string_in_all_rules_pull_request(
        self,
        token: str,
        search_text: str,
        replace_text: str,
        user: Optional[str],
        custom_description: Optional[str] = None,
    ):
        """
        Create a pull request that replaces text in all rule files.

        Args:
            token: GitHub token
            search_text: Text to search for
            replace_text: Text to replace with
            user: GitHub username to assign the PR to
            custom_description: Optional custom PR description
        """
        # Create a unique branch name for this operation
        branch_name = (
            f"global-text-replacement-{int(datetime.datetime.now().timestamp())}"
        )

        # Track modified files and affected rules
        modified_files = []
        affected_rule_ids = set()

        with self.rspec_repo.checkout_branch(
            self.rspec_repo.master_branch, branch_name
        ):
            # Process all files in the rules directory
            rules_dir = self.repo_dir / "rules"
            if not rules_dir.exists() or not rules_dir.is_dir():
                raise InvalidArgumentError("Rules directory not found")

            # Iterate through each rule directory
            for rule_path in rules_dir.iterdir():
                if not rule_path.is_dir() or not rule_path.name.startswith("S"):
                    continue

                # Extract rule ID
                rule_id = rule_path.name

                # Walk through all files in this rule directory
                for root, _, files in os.walk(rule_path):
                    for file in files:
                        file_path = Path(root) / file
                        relative_path = file_path.relative_to(self.repo_dir)

                        # Skip binary files and special directories
                        if file_path.suffix in (
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".gif",
                            ".svg",
                        ):
                            continue

                        try:
                            # Read the file content
                            try:
                                content = file_path.read_text(encoding="utf-8")
                            except UnicodeDecodeError:
                                # Skip binary files
                                continue

                            # Check if the search text exists in the file
                            if search_text in content:
                                # Replace the text
                                new_content = content.replace(search_text, replace_text)
                                file_path.write_text(new_content, encoding="utf-8")
                                modified_files.append(str(relative_path))
                                affected_rule_ids.add(rule_id)
                                click.echo(f"Modified {relative_path}")
                        except Exception as e:
                            click.echo(f"Error processing {relative_path}: {str(e)}")

            # If no user was provided, try to find the last modifier of one of the changed files
            assignee = self._find_assignee_from_file_history(
                token, user, modified_files
            )

            # If we have modified files, create a commit
            if modified_files:
                affected_rules_list = ",".join(sorted(affected_rule_ids))
                commit_title = (
                    f"Modify rules {affected_rules_list}: global text replacement"
                )
                self.rspec_repo.commit_all_and_push(commit_title)
                click.echo(
                    f"Created branch {branch_name} with {len(modified_files)} modified files"
                )
            else:
                raise InvalidArgumentError(
                    f"No files were modified. Text '{search_text}' not found in any rule files."
                )

            # AI! factor out this search for labels into a separate function
            # Get all relevant labels based on affected rules
            all_labels = set()
            for rule_id in affected_rule_ids:
                rule_path = rules_dir / rule_id
                # Add labels for language-specific rule folders
                for item in rule_path.iterdir():
                    if item.is_dir():
                        try:
                            label = get_label_for_language(item.name)
                            all_labels.add(label)
                        except InvalidArgumentError:
                            # Not a language folder, skip
                            pass

            labels = list(all_labels)

        # Create PR title and description
        affected_rules_str = ",".join(sorted(affected_rule_ids))
        if len(affected_rule_ids) == 1:
            title = f"Modify rule {affected_rules_str}: global text replacement"
        else:
            title = f"Modify rules {affected_rules_str}: global text replacement"

        description = custom_description or (
            f"""Global text replacement across rule files:
- Search: `{search_text}`
- Replace: `{replace_text}`

Modified files ({len(modified_files)}):
{chr(10).join('- ' + file for file in modified_files[:20])}
{"..." if len(modified_files) > 20 else ""}

The rules won't be updated until this PR is merged."""
        )

        return self.rspec_repo.create_pull_request(
            token,
            branch_name,
            title,
            description,
            labels,
            assignee,
        )

    def _find_assignee_from_file_history(
        self, token: str, user: Optional[str], modified_files: List[str]
    ) -> Optional[str]:
        """
        Find a user to assign the PR to based on file modification history.

        Args:
            token: GitHub token
            user: Explicitly provided user (if any)
            modified_files: List of files that were modified

        Returns:
            GitHub username to assign the PR to, or None if no suitable user is found
        """
        # If user is explicitly provided, use that
        if user is not None:
            return user

        # If no files were modified, can't determine an assignee
        if not modified_files:
            return None

        repo_name = self.rspec_repo.get_repository_name()

        # Try to find a contributor from the modified files
        for file_path in modified_files:
            try:
                file_info = get_last_file_modifier(token, repo_name, file_path)
                if (
                    file_info
                    and "login" in file_info
                    and file_info["login"] != "Unknown"
                ):
                    assignee = file_info["login"]
                    click.echo(
                        f"Auto-assigning PR to {assignee} (last modifier of {file_path})"
                    )
                    return assignee
            except Exception as e:
                click.echo(f"Error finding last modifier for {file_path}: {str(e)}")
                continue

        # If no suitable assignee is found
        return None

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
