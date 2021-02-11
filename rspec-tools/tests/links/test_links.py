from click.testing import CliRunner
from rspec_tools import cli

def test_404():
  runner = CliRunner()
  result = runner.invoke(cli, ['check-links', '--d=tests/links/404'])
  print(result.output)
  assert result.exit_code == 1
  assert "1/1 links are dead, see the list and related files before" in result.output


def test_url():
  runner = CliRunner()
  result = runner.invoke(cli, ['check-links', '--d=tests/links/URL'])
  print(result.output)
  assert result.exit_code == 1
  assert "1/1 links are dead, see the list and related files before" in result.output
