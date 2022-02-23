import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Final, Iterable, Optional

import click
from git import Repo
from github import Github
from github.PullRequest import PullRequest

from rspec_tools.errors import InvalidArgumentError
from rspec_tools.utils import (LANG_TO_SOURCE, copy_directory_content,
                               get_label_for_language,
                               get_labels_for_languages, is_empty_metadata,
                               parse_and_validate_language_list, resolve_rule,
                               swap_metadata_files, validate_language)


def build_github_repository_url(token: str, user: Optional[str]):
  '''Builds the rspec repository url'''
  repo = os.environ.get('GITHUB_REPOSITORY', 'SonarSource/rspec')
  if user:
    return f'https://{user}:{token}@github.com/{repo}.git'
  else:
    return f'https://{token}@github.com/{repo}.git'

def extract_repository_name(url):
  url_end = url.split('/')[-2:]
  return '/'.join(url_end).removesuffix('.git')

def auto_github(token: str) -> Callable[[Optional[str]], Github]:
  def ret(user: Optional[str]):
    if user:
      return Github(user, token)
    else:
      return Github(token)
  return ret

def _get_url_and_config(token: str, user: Optional[str]):
  url = build_github_repository_url(token, user)
  config = {}
  if user:
    config['user.name'] = user
    config['user.email'] = f'{user}@users.noreply.github.com'

  return url, config

def _get_valid_label_for_language(language: str):
  validate_language(language)
  return get_label_for_language(language)

@contextmanager
def _rule_creator(token: str, user: Optional[str]):
  url, config = _get_url_and_config(token, user)
  with tempfile.TemporaryDirectory() as tmpdirname:
    rule_creator = RuleCreator(url, tmpdirname, config)
    yield rule_creator

def create_new_rule(languages: str, token: str, user: Optional[str]):
  lang_list = parse_and_validate_language_list(languages)
  label_list = get_labels_for_languages(lang_list)
  with _rule_creator(token, user) as rule_creator:
    rule_number = rule_creator.reserve_rule_number()
    rule_creator.create_new_rule_pull_request(auto_github(token), rule_number, lang_list, label_list, user=user)

def add_language_to_rule(language: str, rule: str, token: str, user: Optional[str]):
  label = _get_valid_label_for_language(language)
  rule_number = resolve_rule(rule)
  with _rule_creator(token, user) as rule_creator:
    rule_creator.add_language_pull_request(auto_github(token), rule_number, language, label, user=user)

def update_rule_quickfix_status(language: str, rule: str, status: str, token: str, user: Optional[str]):
  label = _get_valid_label_for_language(language)
  rule_number = resolve_rule(rule)
  with _rule_creator(token, user) as rule_creator:
    rule_creator.update_quickfix_status_pull_request(auto_github(token), rule_number, language, status, label, user)

class RuleCreator:
  ''' Create a new Rule in a repository following the official Github 'rspec' repository structure.'''
  MASTER_BRANCH: Final[str] = 'master'
  ID_COUNTER_BRANCH: Final[str] = 'rspec-id-counter'
  ID_COUNTER_FILENAME: Final[str] = 'next_rspec_id.txt'
  TEMPLATE_PATH: Final[Path] = Path(__file__).parent.parent.joinpath('rspec_template')

  repository: Final[Repo]
  origin_url: Final[str]

  def __init__(self, repository_url: str, clone_directory: str, configuration: dict[str, str]):
    self.repository = Repo.clone_from(repository_url, clone_directory)
    self.origin_url = repository_url

    # create local branches tracking remote ones
    for branch in [self.MASTER_BRANCH, self.ID_COUNTER_BRANCH]:
      self.repository.remote().fetch(branch)
      self.repository.git.checkout('-B', branch, f'origin/{branch}')

    # update repository config
    with self.repository.config_writer() as config_writer:
      for key, value in configuration.items():
        split_key = key.split('.')
        config_writer.set_value(*split_key, value)

  def reserve_rule_number(self) -> int:
    '''Reserve an id on the id counter branch of the repository.'''
    with self._current_git_branch(self.ID_COUNTER_BRANCH):
      counter_file_path = Path(self.repository.working_dir).joinpath(self.ID_COUNTER_FILENAME)
      counter = int(counter_file_path.read_text())
      counter_file_path.write_text(str(counter + 1))

      self.repository.index.add([str(counter_file_path)])
      self.repository.index.commit('Increment RSPEC ID counter')

    origin = self.repository.remote(name='origin')
    origin.push()

    click.echo(f'Reserved Rule ID S{counter}')
    return counter

  def add_language_branch(self, rule_number: int, language: str) -> str:
    '''Create and move files to add a new language to an existing rule.'''
    branch_name = f'rule/S{rule_number}-add-{language}'
    with self._current_git_branch(self.MASTER_BRANCH, branch_name):
      repo_dir = Path(self.repository.working_dir)
      rule_dir = repo_dir.joinpath('rules', f'S{rule_number}')
      if not rule_dir.is_dir():
        raise InvalidArgumentError(f"Rule \"S{rule_number}\" does not exist.")
      lang_dir = rule_dir.joinpath(language)
      if lang_dir.is_dir():
        lang_url = f"https://github.com/SonarSource/rspec/tree/master/rules/S{rule_number}/{language}"
        raise InvalidArgumentError(f"Rule \"S{rule_number}\" is already defined for language {language}. Modify the definition here: {lang_url}")
      lang_dirs = [d for d in rule_dir.glob('*/') if d.is_dir()]
      if 1 == len(list(lang_dirs)) and is_empty_metadata(rule_dir):
        swap_metadata_files(rule_dir, lang_dirs[0])
      lang_dir.mkdir()

      lang_specific_template = self.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
      copy_directory_content(lang_specific_template, lang_dir)
      self._fill_in_the_blanks_in_the_template(lang_dir, rule_number)
      self._fill_language_name_in_the_template(lang_dir, language)
      self.repository.git.add('--all')
      self.repository.index.commit(f'Add {language} to rule S{rule_number}')
    self.repository.git.push('origin', branch_name)
    return branch_name

  def create_new_rule_branch(self, rule_number: int, languages: Iterable[str]) -> str:
    '''Create all the files required for a new rule.'''
    branch_name = f'rule/add-RSPEC-S{rule_number}'
    with self._current_git_branch(self.MASTER_BRANCH, branch_name):
      repo_dir = Path(self.repository.working_dir)
      rule_dir = repo_dir.joinpath('rules', f'S{rule_number}')
      rule_dir.mkdir()
      lang_count = sum(1 for _ in languages)
      if lang_count > 1:
        self._fill_multi_lang_template_files(rule_dir, rule_number, languages)
      else:
        self._fill_single_lang_template_files(rule_dir, rule_number, next(iter(languages)))

      self.repository.git.add('--all')
      self.repository.index.commit(f'Create rule S{rule_number}')
    self.repository.git.push('origin', branch_name)
    return branch_name

  def update_quickfix_status_branch(self, title: str, rule_number: int, language: str, status: str) -> str:
    '''Update the given rule/language quick fix metadata field.'''
    branch_name = f'rule/S{rule_number}-{language}-quickfix'
    with self._current_git_branch(self.MASTER_BRANCH, branch_name):
      self._update_quickfix_status(rule_number, language, status)
      self.repository.git.add('--all')
      self.repository.index.commit(title)
    self.repository.git.push('origin', branch_name)
    return branch_name

  def _get_generic_quickfix_status(self, rule_number: int):
    DEFAULT = 'unknown'
    generic_metadata_path = Path(self.repository.working_dir, 'rules', f'S{rule_number}', 'metadata.json')
    if not generic_metadata_path.is_file():
      return DEFAULT
    generic_metadata = json.loads(generic_metadata_path.read_text())
    return generic_metadata.get('quickfix', DEFAULT)

  def _update_quickfix_status(self, rule_number: int, language: str, status: str):
    metadata_path = Path(self.repository.working_dir, 'rules', f'S{rule_number}', language, 'metadata.json')
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

  def _fill_in_the_blanks_in_the_template(self, rule_dir: Path, rule_number: int):
    for rule_item in rule_dir.glob('**/*'):
      if rule_item.is_file():
        template_content = rule_item.read_text()
        final_content = template_content.replace('${RSPEC_ID}', str(rule_number))
        rule_item.write_text(final_content)

  def _fill_language_name_in_the_template(self, lang_dir: Path, language: str):
    for rule_item in lang_dir.glob('*.adoc'):
      if rule_item.is_file():
        template_content = rule_item.read_text()
        lang = LANG_TO_SOURCE[language]
        final_content = template_content.replace('[source,text]', f'[source,{lang}]')
        rule_item.write_text(final_content)

  def _fill_multi_lang_template_files(self, rule_dir: Path, rule_number: int, languages: Iterable[str]):
    common_template = self.TEMPLATE_PATH.joinpath('multi_language', 'common')
    lang_specific_template = self.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
    copy_directory_content(common_template, rule_dir)

    for lang in languages:
      lang_dir = rule_dir.joinpath(lang)
      lang_dir.mkdir()
      copy_directory_content(lang_specific_template, lang_dir)
      self._fill_language_name_in_the_template(lang_dir, lang)

    self._fill_in_the_blanks_in_the_template(rule_dir, rule_number)

  def _fill_single_lang_template_files(self, rule_dir: Path, rule_number: int, language: str):
    common_template = self.TEMPLATE_PATH.joinpath('single_language', 'common')
    lang_specific_template = self.TEMPLATE_PATH.joinpath('single_language', 'language_specific')
    copy_directory_content(common_template, rule_dir)

    lang_dir = rule_dir.joinpath(language)
    lang_dir.mkdir()
    copy_directory_content(lang_specific_template, lang_dir)

    self._fill_in_the_blanks_in_the_template(rule_dir, rule_number)
    self._fill_language_name_in_the_template(lang_dir, language)

  def _create_pull_request(self, github_api: Callable[[Optional[str]], Github], branch_name: str, title: str, body: str, labels: Iterable[str], user: Optional[str]):
    repository_url = extract_repository_name(self.origin_url)
    github = github_api(user)
    github_repo = github.get_repo(repository_url)
    pull_request = github_repo.create_pull(
      title=title,
      body=body,
      head=branch_name, base=self.MASTER_BRANCH,
      draft=True, maintainer_can_modify=True
    )
    click.echo(f'Created rule Pull Request {pull_request.html_url}')

    # Note: It is not possible to get the authenticated user using get_user() from a github action.
    login = user if user else github.get_user().login
    pull_request.add_to_assignees(login)
    pull_request.add_to_labels(*labels)
    click.echo(f'Pull request assigned to {login}')
    return pull_request

  def add_language_pull_request(self, github_api: Callable[[Optional[str]], Github], rule_number: int, language: str, label: str, user: Optional[str]):
    branch_name = self.add_language_branch(rule_number, language)
    click.echo(f'Created rule branch {branch_name}')
    return self._create_pull_request(
      github_api,
      branch_name,
      f'Create rule S{rule_number}',
      f'You can preview this rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{language}) (updated a few minutes after each push).',
      [label],
      user
    )

  def create_new_rule_pull_request(self, github_api: Callable[[Optional[str]], Github], rule_number: int, languages: Iterable[str], labels: Iterable[str], *, user: Optional[str]) -> PullRequest:
    branch_name = self.create_new_rule_branch(rule_number, languages)
    click.echo(f'Created rule branch {branch_name}')
    first_lang = next(iter(languages))
    return self._create_pull_request(
      github_api,
      branch_name,
      f'Create rule S{rule_number}',
      f'You can preview this rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{first_lang}) (updated a few minutes after each push).',
      labels,
      user
    )

  def update_quickfix_status_pull_request(self, github_api: Callable[[Optional[str]], Github], rule_number: int, language: str, status: str, label: str, user: Optional[str]):
    title = f'Modify rule S{rule_number}: mark quick fix as "{status}"'
    branch_name = self.update_quickfix_status_branch(title, rule_number, language, status)
    click.echo(f'Created rule branch {branch_name}')
    return self._create_pull_request(
      github_api,
      branch_name,
      title,
      f'''See the original rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{language}).

The rule won't be updated until this PR is merged, see [RULEAPI-655](https://jira.sonarsource.com/browse/RULEAPI-655)''',
      [label],
      user
    )

  @contextmanager
  def _current_git_branch(self, base_branch: str, new_branch: Optional[str] = None):
    '''Checkout a given branch before yielding, then revert to the previous branch.'''
    past_branch = self.repository.active_branch
    try:
      self.repository.git.checkout(base_branch)
      origin = self.repository.remote(name='origin')
      origin.pull()
      if new_branch is not None:
        self.repository.git.checkout('-B', new_branch)
      yield
    finally:
      self.repository.git.checkout(past_branch)
