import click
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


__all__=['cli']
