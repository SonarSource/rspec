import os
from typing import Optional
from pathlib import Path

import click
from rspec_tools.checklinks import check_html_links
from rspec_tools.errors import RuleNotFoundError, RuleValidationError
from rspec_tools.create_rule import create_new_rule, add_language_to_rule
from rspec_tools.rules import RulesRepository
from rspec_tools.validation.metadata import validate_metadata
from rspec_tools.validation.description import validate_section_names, validate_section_levels
from rspec_tools.coverage import update_coverage_for_all_repos, update_coverage_for_repo, update_coverage_for_repo_version

from rspec_tools.notify_failure_on_slack import notify_slack

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    'Tools automating RSPEC workflows.'

@cli.command()
@click.option('--rule', help='Validate only the rule matching the provided ID.')
def validate(rule):
  '''Validate rules.'''
  # TODO
  if rule == '42':
    raise RuleNotFoundError(rule)

@cli.command()
@click.option('--d', required=True)
def check_links(d):
  '''Check links in html.'''
  check_html_links(d)

@cli.command()
@click.option('--languages', required=True)
@click.option('--user', required=False)
def create_rule(languages: str, user: Optional[str]):
  '''Create a new rule.'''
  token = os.environ.get('GITHUB_TOKEN')
  create_new_rule(languages, token, user)

@cli.command()
@click.option('--language', required=True)
@click.option('--rule', required=True)
@click.option('--user', required=False)
def add_lang_to_rule(language: str, rule: str, user: Optional[str]):
  '''Add a new language to rule.'''
  token = os.environ.get('GITHUB_TOKEN')
  add_language_to_rule(language, rule, token, user)


@cli.command()
@click.argument('rules', nargs=-1)
def validate_rules_metadata(rules):
  '''Validate rules metadata.'''
  rule_repository = RulesRepository()
  error_counter = 0
  for rule in rule_repository.rules:

    if rules and rule.key not in rules:
      continue

    for lang_spec_rule in rule.specializations:
      try:
        validate_metadata(lang_spec_rule)
      except RuleValidationError as e:
        click.echo(e.message, err=True)
        error_counter += 1
  if error_counter > 0:
    message = f"Validation failed due to {error_counter} errors"
    click.echo(message, err=True)
    raise click.Abort(message)

@cli.command()
@click.option('--d', required=True)
@click.argument('rules', nargs=-1)
def check_sections(d, rules):
  '''Validate the section names.'''
  out_dir = Path(__file__).parent.parent.joinpath(d)
  rule_repository = RulesRepository(rules_path=out_dir)
  error_counter = 0
  for rule in rule_repository.rules:
    if rules and rule.key not in rules:
      continue
    for lang_spec_rule in rule.specializations:
      try:
        validate_section_names(lang_spec_rule)
      except RuleValidationError as e:
        click.echo(e.message, err=True)
        error_counter += 1
      try:
        validate_section_levels(lang_spec_rule)
      except RuleValidationError as e:
        click.echo(e.message, err=True)
        error_counter += 1
  if error_counter > 0:
    message = f"Validation failed due to {error_counter} errors"
    click.echo(message, err=True)
    raise click.Abort(message)

@cli.command()
@click.option('--repository', required=False)
@click.option('--version', required=False)
def update_coverage(repository: Optional[str], version: Optional[str]):
  '''Update rule coverage by adding rules implemented in the {version} of {repository}.'''
  if repository is None:
      update_coverage_for_all_repos()
  elif version is None:
      update_coverage_for_repo(repository)
  else:
      update_coverage_for_repo_version(repository, version)

@cli.command()
@click.option('--message', required=True)
@click.option('--channel', required=True)
def notify_failure_on_slack(message: str, channel: str):
  notify_slack(message, channel)

__all__=['cli']
