import os
from pathlib import Path
from typing import Optional

import click

import rspec_tools.create_rule
import rspec_tools.modify_rule
from rspec_tools.checklinks import check_html_links
from rspec_tools.coverage import (update_coverage_for_all_repos,
                                  update_coverage_for_repo,
                                  update_coverage_for_repo_version)
from rspec_tools.errors import RuleValidationError
from rspec_tools.notify_failure_on_slack import notify_slack
from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.description import (validate_parameters,
                                                validate_section_levels,
                                                validate_section_names,
                                                validate_source_language)
from rspec_tools.validation.metadata import validate_rule_metadata


def _fatal_error(message: str):
  click.echo(message, err=True)
  raise click.Abort(message)

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    'Tools automating RSPEC workflows.'


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
  rspec_tools.create_rule.create_new_rule(languages, token, user)


@cli.command()
@click.option('--language', required=True)
@click.option('--rule', required=True)
@click.option('--user', required=False)
def add_lang_to_rule(language: str, rule: str, user: Optional[str]):
  '''Add a new language to rule.'''
  token = os.environ.get('GITHUB_TOKEN')
  rspec_tools.create_rule.add_language_to_rule(language, rule, token, user)


@cli.command()
@click.option('--language', required=True)
@click.option('--rule', required=True)
@click.option('--status', required=True)
@click.option('--user', required=False)
def update_quickfix_status(language: str, rule: str, status: str, user: Optional[str]):
  '''Update the status of quick fix for the given rule/language'''
  token = os.environ.get('GITHUB_TOKEN')
  rspec_tools.modify_rule.update_rule_quickfix_status(language, rule, status, token, user)


@cli.command()
@click.argument('rules', nargs=-1, required=True)
def validate_rules_metadata(rules):
  '''Validate rules metadata.'''
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
    _fatal_error(f"Validation failed due to {error_counter} errors out of {len(rules)} analyzed rules")


VALIDATORS = [validate_section_names,
              validate_section_levels,
              validate_parameters,
              validate_source_language,
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
@click.option('--d', required=True)
@click.argument('rules', nargs=-1)
def check_description(d, rules):
  '''Validate the rule.adoc description.'''
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
