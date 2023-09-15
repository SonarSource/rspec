import json
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Final, Iterable, Optional

import click
from github.PullRequest import PullRequest

from rspec_tools.errors import InvalidArgumentError
from rspec_tools.repo import RspecRepo, tmp_rspec_repo
from rspec_tools.utils import (LANG_TO_SOURCE, copy_directory_content,
                               get_label_for_language,
                               get_labels_for_languages, is_empty_metadata,
                               parse_and_validate_language_list, resolve_rule,
                               swap_metadata_files)


@contextmanager
def _rule_creator(token: str, user: Optional[str]):
  with tmp_rspec_repo(token, user) as repo:
    yield RuleCreator(repo)


def create_new_rule(languages: str, token: str, user: Optional[str]):
  lang_list = parse_and_validate_language_list(languages)
  label_list = get_labels_for_languages(lang_list)
  with _rule_creator(token, user) as rule_creator:
    rule_number = rule_creator.rspec_repo.reserve_rule_number()
    rule_creator.create_new_rule_pull_request(token, rule_number, lang_list, label_list, user)


def add_language_to_rule(language: str, rule: str, token: str, user: Optional[str]):
  label = get_label_for_language(language)
  rule_number = resolve_rule(rule)
  with _rule_creator(token, user) as rule_creator:
    rule_creator.add_language_pull_request(token, rule_number, language, label, user)


class RuleCreator:
  '''Create a new Rule in a repository following the official Github 'rspec' repository structure.'''
  TEMPLATE_PATH: Final[Path] = Path(__file__).parent.parent.joinpath('rspec_template')
  PR_TEMPLATE_PATH: Final[Path] = Path(__file__).parent.parent.parent.joinpath('.github/pull_request_template.md')

  def __init__(self, rspec_repo: RspecRepo):
    self.rspec_repo = rspec_repo
    self.repo_dir = Path(self.rspec_repo.repository.working_dir)

  def add_language_branch(self, rule_number: int, language: str) -> str:
    '''Create and move files to add a new language to an existing rule.'''
    branch_name = f'rule/S{rule_number}-add-{language}'
    with self.rspec_repo.checkout_branch(self.rspec_repo.MASTER_BRANCH, branch_name):
      rule_dir = self.repo_dir / 'rules' / f'S{rule_number}'
      if not rule_dir.is_dir():
        raise InvalidArgumentError(f"Rule \"S{rule_number}\" does not exist.")
      lang_dir = rule_dir / language
      if lang_dir.is_dir():
        lang_url = f"https://github.com/SonarSource/rspec/tree/master/rules/S{rule_number}/{language}"
        raise InvalidArgumentError(f"Rule \"S{rule_number}\" is already defined for language {language}. Modify the definition here: {lang_url}")
      lang_dirs = [d for d in rule_dir.glob('*/') if d.is_dir()]
      if 1 == len(list(lang_dirs)) and is_empty_metadata(rule_dir):
        swap_metadata_files(rule_dir, lang_dirs[0])
      lang_dir.mkdir()

      lang_specific_template = self.TEMPLATE_PATH / 'multi_language' / 'language_specific'
      copy_directory_content(lang_specific_template, lang_dir)
      self._fill_in_the_blanks_in_the_template(lang_dir, rule_number)
      self._fill_language_name_in_the_template(lang_dir, language)
      self.rspec_repo.commit_all_and_push(f'Add {language} to rule S{rule_number}')
    return branch_name

  def create_new_rule_branch(self, rule_number: int, languages: Iterable[str]) -> str:
    '''Create all the files required for a new rule.'''
    branch_name = f'rule/add-RSPEC-S{rule_number}'
    with self.rspec_repo.checkout_branch(self.rspec_repo.MASTER_BRANCH, branch_name):
      rule_dir = self.repo_dir / 'rules' / f'S{rule_number}'
      rule_dir.mkdir()
      lang_count = sum(1 for _ in languages)
      if lang_count > 1:
        self._fill_multi_lang_template_files(rule_dir, rule_number, languages)
      else:
        self._fill_single_lang_template_files(rule_dir, rule_number, next(iter(languages)))
      self.rspec_repo.commit_all_and_push(f'Create rule S{rule_number}')

    return branch_name

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
    common_template = self.TEMPLATE_PATH / 'multi_language' / 'common'
    lang_specific_template = self.TEMPLATE_PATH / 'multi_language' / 'language_specific'
    copy_directory_content(common_template, rule_dir)

    for lang in languages:
      lang_dir = rule_dir / lang
      lang_dir.mkdir()
      copy_directory_content(lang_specific_template, lang_dir)
      self._fill_language_name_in_the_template(lang_dir, lang)

    self._fill_in_the_blanks_in_the_template(rule_dir, rule_number)

  def _fill_single_lang_template_files(self, rule_dir: Path, rule_number: int, language: str):
    common_template = self.TEMPLATE_PATH / 'single_language' / 'common'
    lang_specific_template = self.TEMPLATE_PATH / 'single_language' / 'language_specific'
    copy_directory_content(common_template, rule_dir)

    lang_dir = rule_dir /language
    lang_dir.mkdir()
    copy_directory_content(lang_specific_template, lang_dir)

    self._fill_in_the_blanks_in_the_template(rule_dir, rule_number)
    self._fill_language_name_in_the_template(lang_dir, language)

  def add_language_pull_request(self, token: str, rule_number: int, language: str, label: str, user: Optional[str]):
    branch_name = self.add_language_branch(rule_number, language)
    click.echo(f'Created rule branch {branch_name}')
    return self.rspec_repo.create_pull_request(
      token,
      branch_name,
      f'Create rule S{rule_number}',
      f'You can preview this rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{language}) (updated a few minutes after each push).\n\n{self.PR_TEMPLATE_PATH.read_text()}',
      [label],
      user
    )

  def create_new_rule_pull_request(self, token: str, rule_number: int, languages: Iterable[str], labels: Iterable[str], user: Optional[str]) -> PullRequest:
    branch_name = self.create_new_rule_branch(rule_number, languages)
    click.echo(f'Created rule branch {branch_name}')
    first_lang = next(iter(languages))
    return self.rspec_repo.create_pull_request(
      token,
      branch_name,
      f'Create rule S{rule_number}',
      f'You can preview this rule [here](https://sonarsource.github.io/rspec/#/rspec/S{rule_number}/{first_lang}) (updated a few minutes after each push).\n\n{self.PR_TEMPLATE_PATH.read_text()}',
      labels,
      user
    )

