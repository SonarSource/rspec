import os
from pathlib import Path
from typing import Optional

import click

import rspec_tools.create_rule
import rspec_tools.modify_rule
from rspec_tools.checklinks import check_html_links
from rspec_tools.coverage import (
    update_coverage_for_all_repos,
    update_coverage_for_repo,
    update_coverage_for_repo_version,
)
from rspec_tools.errors import RuleValidationError
from rspec_tools.notify_failure_on_slack import notify_slack
from rspec_tools.repo import get_last_login_modified_file
from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.description import (
    validate_parameters,
    validate_section_levels,
    validate_section_names,
    validate_security_standard_links,
    validate_source_language,
    validate_subsections,
)
from rspec_tools.validation.metadata import validate_rule_metadata
from rspec_tools.validation.sanitize_asciidoc import sanitize_asciidoc


def _fatal_error(message: str):
    click.echo(message, err=True)
    raise click.Abort(message)


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    "Tools automating RSPEC workflows."


@cli.command()
@click.option("--d", required=True)
@click.option(
    "--history-file",
    default="./link_probes.history",
    help="Path to the link probes history file",
)
def check_links(d, history_file):
    """Check links in html."""
    check_html_links(d, history_file)


@cli.command()
@click.option("--languages", required=True)
@click.option("--user", required=False)
def create_rule(languages: str, user: Optional[str]):
    """Create a new rule."""
    token = os.environ.get("GITHUB_TOKEN")
    rspec_tools.create_rule.create_new_rule(languages, token, user)


@cli.command()
@click.option("--language", required=True)
@click.option("--rule", required=True)
@click.option("--user", required=False)
def add_lang_to_rule(language: str, rule: str, user: Optional[str]):
    """Add a new language to rule."""
    token = os.environ.get("GITHUB_TOKEN")
    rspec_tools.create_rule.add_language_to_rule(language, rule, token, user)


@cli.command()
@click.option("--language", required=True)
@click.option("--rule", required=True)
@click.option("--status", required=True)
@click.option("--user", required=False)
def update_quickfix_status(language: str, rule: str, status: str, user: Optional[str]):
    """Update the status of quick fix for the given rule/language"""
    token = os.environ.get("GITHUB_TOKEN")
    rspec_tools.modify_rule.update_rule_quickfix_status(
        language, rule, status, token, user
    )


@cli.command()
@click.option("--search", required=True, help="Text to search for")
@click.option("--replace", required=True, help="Text to replace with")
@click.option("--title", required=True, help="Pull request title suffix")
@click.option("--description", required=True, help="Pull request description")
@click.option(
    "--user", required=False, help="GitHub username for repository operations"
)
@click.option(
    "--assignee",
    required=False,
    help="GitHub username to assign the PR to (overrides automatic detection)",
)
def batch_replace(
    search: str,
    replace: str,
    title: str,
    description: str,
    user: Optional[str],
    assignee: Optional[str],
):
    """Perform a batch find and replace across rule files and create a PR"""
    token = os.environ.get("GITHUB_TOKEN")
    rspec_tools.modify_rule.batch_find_replace(
        search, replace, title, description, token, user, assignee
    )


@cli.command()
@click.argument("rules", nargs=-1, required=True)
def validate_rules_metadata(rules):
    """Validate rules metadata."""
    rule_repository = RulesRepository()
    error_counter = 0

    for rule_id in rules:
        try:
            rule = rule_repository.get_rule(rule_id)
            validate_rule_metadata(rule)
        except RuleValidationError as e:
            click.echo(e.message, err=True)
            error_counter += 1

    if error_counter > 0:
        _fatal_error(
            f"Validation failed due to {error_counter} errors out of {len(rules)} analyzed rules"
        )


@cli.command()
@click.argument("files", nargs=-1, required=True)
def check_asciidoc(files):
    """Sanitize the AsciiDoc description."""
    error_counter = 0
    for file in files:
        error_counter += sanitize_asciidoc(Path(file))
    if error_counter > 0:
        _fatal_error(
            f"Validation of the asciidoc description failed due to {error_counter} errors"
        )


VALIDATORS = [
    validate_subsections,
    validate_section_names,
    validate_section_levels,
    validate_parameters,
    validate_source_language,
    validate_security_standard_links,
]


def _validate_rule_specialization(lang_spec_rule: LanguageSpecificRule):
    error_counter = 0
    for validator in VALIDATORS:
        try:
            validator(lang_spec_rule)
        except RuleValidationError as e:
            click.echo(e.message, err=True)
            error_counter += 1
    return error_counter


@cli.command()
@click.option("--d", required=True)
@click.argument("rules", nargs=-1)
def check_description(d, rules):
    """Validate the rule.adoc description."""
    out_dir = Path(__file__).parent.parent.joinpath(d)
    rule_repository = RulesRepository(rules_path=out_dir)
    error_counter = 0
    for rule in rule_repository.rules:
        if rules and rule.id not in rules:
            continue
        for lang_spec_rule in rule.specializations:
            error_counter += _validate_rule_specialization(lang_spec_rule)
    if error_counter > 0:
        _fatal_error(f"Validation failed due to {error_counter} errors")


@cli.command()
@click.option("--rulesdir", required=True)
@click.option("--repository", required=False)
@click.option("--version", required=False)
def update_coverage(rulesdir: str, repository: Optional[str], version: Optional[str]):
    """Update rule coverage by adding rules implemented in the {version} of {repository}."""
    if repository is None:
        update_coverage_for_all_repos(Path(rulesdir))
    elif version is None:
        update_coverage_for_repo(repository, Path(rulesdir))
    else:
        update_coverage_for_repo_version(repository, version, Path(rulesdir))


@cli.command()
@click.option("--message", required=True)
@click.option("--channel", required=True)
def notify_failure_on_slack(message: str, channel: str):
    notify_slack(message, channel)


@cli.command()
@click.option("--d", required=True, help="Directory containing HTML files to check")
@click.option(
    "--history-file",
    default="./link_probes.history",
    help="Path to the link probes history file",
)
@click.option(
    "--user", required=False, help="GitHub username for repository operations"
)
@click.option(
    "--title", default="Fix broken links via web.archive.org", help="PR title"
)
@click.option(
    "--dry-run/--no-dry-run", default=False, help="Print actions without creating PRs"
)
def replace_broken_links(d, history_file, user, title, dry_run):
    """Find broken links and create PRs to replace them with web.archive.org URLs."""
    from rspec_tools.checklinks import (
        collect_confirmed_errors,
        get_all_links_from_htmls,
        load_url_probing_history,
    )
    from rspec_tools.modify_rule import batch_find_replace

    # Load link history
    load_url_probing_history(history_file)

    # Get all links from HTML files
    urls = get_all_links_from_htmls(d)

    # Collect confirmed errors (broken links)
    confirmed_errors, _, cache_stats = collect_confirmed_errors(urls)

    if not confirmed_errors:
        click.echo("No broken links found.")
        return

    click.echo(f"Found {len(confirmed_errors)} broken links.")

    token = os.environ.get("GITHUB_TOKEN")
    if not token and not dry_run:
        click.echo("GITHUB_TOKEN environment variable is not set", err=True)
        exit(1)

    # Create a PR for each broken link
    for broken_link in confirmed_errors:
        files_with_link = urls[broken_link]
        file_count = len(files_with_link)

        file_info = f"in {file_count} file{'s' if file_count > 1 else ''}"
        click.echo(f"Processing broken link: {broken_link} {file_info}")

        # Create web.archive.org URL
        archived_link = f"https://web.archive.org/web/{broken_link}"

        pr_description = f"""Please find an appropriate replacement for {broken_link}.

This automated PR was created because the link was no longer accessible.

Note, you are assigned to this PR only because you've been the last person to modify one of the affected rules.
Feel free to reassign to someone more appropriate.

Additionally, our link checker is sometimes blocked by bot-protection, so if you can reliably access the url in question, instead of replacing the link, add it to the exceptions.
To add a link to the exceptions, add an entry in `EXCEPTION_PREFIXES` in the rspec-tools/rspec_tools/checklinks.py file.
Don't forget to revert the changes proposed in this PR or merge your exception separately and close this PR without merging.

Original link: {broken_link}
Archived link: {archived_link}

The proposed replacement is very naive and relies on the Wayback Machine, which ideally should not be used for this purpose.
In the worst case, using the Internet Archive's Wayback Machine ensures that readers can still access the referenced content.
Please try to find the appropriate replacement link.


This link appears in the following files:
{chr(10).join(str(f) for f in files_with_link)}
"""

        if dry_run:
            click.echo(f"Would replace: {broken_link}")
            click.echo(f"With: {archived_link}")
            click.echo(f"Description: {pr_description}")
        else:
            try:
                pr_url = batch_find_replace(
                    broken_link,
                    archived_link,
                    f"Replace broken link with web.archive.org",
                    pr_description,
                    token,
                    user,
                )
                click.echo(f"Created PR: {pr_url}")
            except Exception as e:
                click.echo(f"Error creating PR for {broken_link}: {e}", err=True)


@cli.command("last-author")
@click.option(
    "--repo",
    help="Repository in format 'owner/repo'",
    default=lambda: os.environ.get("GITHUB_REPOSITORY", "SonarSource/rspec"),
)
@click.option(
    "--max-commits", default=3, type=int, help="Maximum number of commits to check"
)
@click.argument("file_path")
def last_author_command(repo: str, max_commits: int, file_path: str):
    """Find the last non-bot GitHub login that modified a given file.

    Requires GITHUB_TOKEN environment variable to be set.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        click.echo("GITHUB_TOKEN environment variable is not set", err=True)
        exit(1)

    author = get_last_login_modified_file(token, repo, file_path, max_commits)
    if author:
        click.echo(author)
    else:
        click.echo("No non-bot author found for the specified file", err=True)
        exit(1)


__all__ = ["cli"]
