import json
import os
import re
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import click

from rspec_tools.errors import InvalidArgumentError

from rspec_tools.repo import get_last_login_modified_file, RspecRepo, tmp_rspec_repo
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


def batch_find_replace(
    search: str,
    replace: str,
    title_suffix: str,
    description: str,
    token: str,
    user: Optional[str],
    assignee: Optional[str] = None,
):
    """
    Perform a batch find-and-replace operation across the rules directory and create a PR.

    Args:
        search: The string to search for
        replace: The string to replace with
        title_suffix: The suffix for the PR title
        description: The PR description
        token: GitHub token
        user: GitHub user
        assignee: Optional specific assignee for the PR (overrides automatic detection)
    """
    with _rule_editor(token, user) as editor:
        editor.batch_find_replace_pull_request(
            token, search, replace, title_suffix, description, user, assignee
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
            self.rspec_repo.MASTER_BRANCH, branch_name
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

    def batch_find_replace_branch(
        self, title: str, search: str, replace: str
    ) -> Tuple[str, Dict[str, Set[str]], List[Path]]:
        """
        Perform a batch find-and-replace operation in all files in the rules directory.

        Args:
            title: The commit title
            search: The string to search for
            replace: The string to replace with

        Returns:
            Tuple containing:
                - branch name
                - dictionary mapping rule IDs to affected languages
                - list of modified file paths
        """
        # Create a unique branch name for this operation
        import hashlib

        hash_suffix = hashlib.md5(f"{search}{replace}".encode()).hexdigest()[:8]
        branch_name = f"rule/batch-replace-{hash_suffix}"

        # Map to track affected rules and languages
        affected_rules = defaultdict(set)
        modified_files = []

        with self.rspec_repo.checkout_branch(
            self.rspec_repo.MASTER_BRANCH, branch_name
        ):
            rules_dir = self.repo_dir / "rules"

            # Process all files under rules directory
            for filepath in rules_dir.glob("**/*"):
                if not filepath.is_file():
                    continue
                try:
                    content = filepath.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Skip binary files
                    continue
                if search in content:
                    # Perform the replacement
                    new_content = content.replace(search, replace)
                    filepath.write_text(new_content, encoding="utf-8")

                    # Get relative path components to determine rule and language
                    rel_path = filepath.relative_to(rules_dir)
                    parts = rel_path.parts

                    if len(parts) >= 1:
                        rule_id = parts[0]  # The rule folder (e.g., "S123")

                        # If there's a language subfolder, record it
                        if len(parts) >= 2:
                            language = parts[1]
                            affected_rules[rule_id].add(language)
                        else:
                            # It's in the rule root folder
                            affected_rules[rule_id].add("")

                        modified_files.append(filepath)

            if modified_files:
                self.rspec_repo.commit_all_and_push(title)
            else:
                raise InvalidArgumentError(
                    f"No files were modified. The search string '{search}' was not found."
                )

        return branch_name, affected_rules, modified_files

    def compose_pr_title(self, rule_ids: List[str], title_suffix: str) -> str:
        """
        Compose an appropriate PR title based on the affected rules.

        Args:
            rule_ids: List of rule IDs affected by the change
            title_suffix: The suffix to append to the PR title

        Returns:
            A formatted PR title
        """
        # If there's just one rule affected, use singular form
        if len(rule_ids) == 1:
            return f"Modify rule {rule_ids[0]}: {title_suffix}"
        else:
            # For multiple rules, combine them up to a reasonable length
            if len(rule_ids) <= 5:
                rules_str = ", ".join(rule_ids)
            else:
                rules_str = f"{len(rule_ids)} rules"
            return f"Modify rules {rules_str}: {title_suffix}"

    def collect_labels_from_affected_rules(
        self, affected_rules: Dict[str, Set[str]]
    ) -> Set[str]:
        """
        Collect labels for the PR based on affected languages.

        Args:
            affected_rules: Dictionary mapping rule IDs to sets of languages

        Returns:
            Set of labels to apply to the PR
        """
        labels = set()
        for rule_id, languages in affected_rules.items():
            for lang in languages:
                if lang:  # Skip empty strings (rule-level files)
                    try:
                        label = get_label_for_language(lang)
                        labels.add(label)
                    except Exception:
                        # Skip invalid languages
                        continue
        return labels

    def find_appropriate_assignee(
        self, token: str, assignee: Optional[str], modified_files: List[Path]
    ) -> Optional[str]:
        """
        Find the most appropriate assignee for a PR based on file history.

        Args:
            token: GitHub token
            assignee: Optional explicitly provided assignee
            modified_files: List of files modified in the PR

        Returns:
            The appropriate assignee, or None if no assignee can be determined
        """
        if assignee:
            return assignee

        if not modified_files:
            return None

        repo_name = self.rspec_repo.get_repository_name()

        # Try to find the last author for each modified file
        for file_path in modified_files:
            try:
                last_author = get_last_login_modified_file(token, repo_name, file_path)
                if last_author:
                    return last_author
            except Exception:
                continue

        return None

    def batch_find_replace_pull_request(
        self,
        token: str,
        search: str,
        replace: str,
        title_suffix: str,
        description: str,
        user: Optional[str],
        assignee: Optional[str] = None,
    ):
        """
        Create a pull request with batch find-and-replace changes.

        Args:
            token: GitHub token
            search: The string to search for
            replace: The string to replace with
            title_suffix: Suffix for the PR title
            description: PR description text
            user: GitHub user for repo operations
            assignee: Optional specific assignee for the PR
        """
        # Run the find & replace operation
        title = f"Batch find and replace: {title_suffix}"
        branch_name, affected_rules, modified_files = self.batch_find_replace_branch(
            title, search, replace
        )

        # Build a comma-separated list of affected rule IDs for the PR title
        rule_ids = list(affected_rules.keys())
        rule_ids.sort()  # Sort rule IDs for consistent order

        pr_title = self.compose_pr_title(rule_ids, title_suffix)

        # Collect labels for the PR based on affected languages
        labels = self.collect_labels_from_affected_rules(affected_rules)

        # Find the appropriate assignee for the PR
        auto_assignee = self.find_appropriate_assignee(token, assignee, modified_files)

        click.echo(f"Created rule branch {branch_name}")
        return self.rspec_repo.create_pull_request(
            token, branch_name, pr_title, description, labels, auto_assignee or user
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
