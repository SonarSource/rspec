import click
from .checklinks import check_html_links
from .errors import RuleNotFoundError

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
  print("checking links")
  check_html_links(d)
    

__all__=['cli']
