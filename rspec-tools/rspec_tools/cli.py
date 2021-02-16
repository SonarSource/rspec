import os
import tempfile
from typing import Optional

import click
from rspec_tools.checklinks import check_html_links
from rspec_tools.errors import InvalidArgumenError, RuleNotFoundError
from rspec_tools.create_rule import RuleCreator, build_github_repository_url

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
  url = build_github_repository_url(token)
  config = {}
  if user:
    config['user.name'] = user
    config['user.email'] = f'<{user}@users.noreply.github.com>'
  lang_list = [lang.strip() for lang in languages.split(',')]
  if len(languages.strip()) == 0 or len(lang_list) == 0:
    raise InvalidArgumenError('Invalid argument for "languages". At least one language should be provided.')
  # TODO: accept only valid languages

  with tempfile.TemporaryDirectory() as tmpdirname:
    rule_creator = RuleCreator(url, tmpdirname, config)
    rule_number = rule_creator.reserve_rule_number()
    click.echo(f'Reserved Rule ID S{rule_number}')
    pull_request = rule_creator.create_new_rule_pull_request(token, rule_number, lang_list)
    click.echo(f'Created Rule Pull Request branch: {pull_request.head}  url: {pull_request.html_url}')



__all__=['cli']
