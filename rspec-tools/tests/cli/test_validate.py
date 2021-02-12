from click.testing import CliRunner
from rspec_tools import cli

def test_hello_world():
  runner = CliRunner()
  result = runner.invoke(cli, ['--debug', 'validate', '--rule=42'])
  assert result.exit_code == 1
  assert result.output == 'Error: No rule has ID 42\n'