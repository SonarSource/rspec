from click.testing import CliRunner
from rspec_tools import cli
from rspec_tools import checklinks

def test_find_urls():
  urls={}
  checklinks.findurl_in_html("tests/links/404/S100/java/rule.html",urls)
  assert urls == {'https://www.google.com/404': ['tests/links/404/S100/java/rule.html']}
  assert len(urls) == 1

def test_live():
  assert checklinks.live_url("https://www.google.com")

def test_live():
  assert not checklinks.live_url("https://ww.nothing")

def test_404():
  runner = CliRunner()
  result = runner.invoke(cli, ['check-links', '--d=tests/links/404'])
  print(result.output)
  assert result.exit_code == 1
  assert "1/1 links are dead, see above ^^ the list and the related files" in result.output

def test_url():
  runner = CliRunner()
  result = runner.invoke(cli, ['check-links', '--d=tests/links/URL'])
  print(result.output)
  assert result.exit_code == 1
  assert "1/1 links are dead, see above ^^ the list and the related files" in result.output

def test_ok():
  runner = CliRunner()
  result = runner.invoke(cli, ['check-links', '--d=tests/links/OK'])
  print(result.output)
  assert result.exit_code == 0
  assert "All 1 links are good" in result.output

def test_deprecated():
  runner = CliRunner()
  result = runner.invoke(cli, ['check-links', '--d=tests/links/deprecated'])
  print(result.output)
  assert result.exit_code == 0
  assert "All 1 links are good" in result.output
