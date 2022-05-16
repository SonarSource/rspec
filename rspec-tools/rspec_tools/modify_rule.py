from contextlib import contextmanager
import json
from pathlib import Path
from typing import Optional

import click
from rspec_tools.errors import InvalidArgumentError

from rspec_tools.repo import RspecRepo, tmp_rspec_repo
from rspec_tools.utils import get_label_for_language, resolve_rule


@contextmanager
def _rule_editor(token: str, user: Optional[str]):
  with tmp_rspec_repo(token, user) as repo:
    yield RuleEditor(repo)


def update_rule_quickfix_status(language: str, rule: str, status: str, token: str, user: Optional[str]):
  label = get_label_for_language(language)
  rule_number = resolve_rule(rule)
  with _rule_editor(token, user) as editor:
    editor.update_quickfix_status_pull_request(token, rule_number, language, status, label, user)


class RuleEditor:
  '''Modify an existing Rule in a repository following the official Github 'rspec' repository structure.'''

  def __init__(self, rspec_repo: RspecRepo):
    self.rspec_repo = rspec_repo
    self.repo_dir = Path(self.rspec_repo.repository.working_dir)

  def update_quickfix_status_branch(self, title: str, rule_number: int, language: str, status: str) -> str:
    '''Update the given rule/language quick fix metadata field.'''
    branch_name = f'rule/S{rule_number}-{language}-quickfix'
    with self.rspec_repo.checkout_branch(self.rspec_repo.MASTER_BRANCH, branch_name):
      self._update_quickfix_status(rule_number, language, status)
      self.rspec_repo.commit_all_and_push(title)

    return branch_name

  def update_quickfix_status_pull_request(self, token: str, rule_number: int, language: str, status: str, label: str, user: Optional[str]):
    title = f'Modify rule S{rule_number}: mark quick fix as "{status}"'
    branch_name = self.update_quickfix_status_branch(title, rule_number, language, status)
    click.echo(f'Created rule branch {branch_name}')
    return self.rspec_repo.create_pull_request(
      token,
      branch_name,
      title,
      f'''See the original rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{language}).

The rule won't be updated until this PR is merged, see [RULEAPI-655](https://jira.sonarsource.com/browse/RULEAPI-655)''',
      [label],
      user
    )

  def _get_generic_quickfix_status(self, rule_number: int):
    DEFAULT = 'unknown'
    generic_metadata_path = self.repo_dir / 'rules' / f'S{rule_number}' / 'metadata.json'
    if not generic_metadata_path.is_file():
      return DEFAULT
    generic_metadata = json.loads(generic_metadata_path.read_text())
    return generic_metadata.get('quickfix', DEFAULT)

  def _update_quickfix_status(self, rule_number: int, language: str, status: str):

    WINDOWS_LINE_ENDING = b'\r\n'
    UNIX_LINE_ENDING = b'\n'

    metadata_path = self.repo_dir / 'rules' / f'S{rule_number}' / language / 'metadata.json'
    if not metadata_path.is_file():
      raise InvalidArgumentError(f'{metadata_path} does not exist or is not a file')

    metadata = json.loads(metadata_path.read_text())
    generic_status = self._get_generic_quickfix_status(rule_number)
    if status == metadata.get('quickfix', generic_status):
      raise InvalidArgumentError(f'{metadata_path} has already the same status {status}')

    metadata['quickfix'] = status
    # When generating the JSON, ensure forward slashes are escaped. See RULEAPI-750.
    json_string = json.dumps(metadata, indent=2).replace("/", "\\/")
    metadata_path.write_text(json_string)

    with open(metadata_path, 'rb') as open_file:
      content = open_file.read()

    # Windows ➡ Unix
    content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

    # Unix ➡ Windows
    # content = content.replace(UNIX_LINE_ENDING, WINDOWS_LINE_ENDING)

    with open(metadata_path, 'wb') as open_file:
      open_file.write(content)
