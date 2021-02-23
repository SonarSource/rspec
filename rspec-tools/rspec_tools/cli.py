import os
import tempfile
from typing import Optional

import click
from rspec_tools.checklinks import check_html_links
from rspec_tools.errors import InvalidArgumenError, RuleNotFoundError, RuleValidationError
from rspec_tools.create_rule import RuleCreator, build_github_repository_url
from rspec_tools.rules import RulesRepository
from rspec_tools.validation.metadata import validate_metadata

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
  url = build_github_repository_url(token, user)
  config = {}
  if user:
    config['user.name'] = user
    config['user.email'] = f'{user}@users.noreply.github.com'
  lang_list = [lang.strip() for lang in languages.split(',')]
  if len(languages.strip()) == 0 or len(lang_list) == 0:
    raise InvalidArgumenError('Invalid argument for "languages". At least one language should be provided.')
  # TODO: accept only valid languages

  with tempfile.TemporaryDirectory() as tmpdirname:
    rule_creator = RuleCreator(url, tmpdirname, config)
    rule_number = rule_creator.reserve_rule_number()
    pull_request = rule_creator.create_new_rule_pull_request(token, rule_number, lang_list, user=user)


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


__all__=['cli']
