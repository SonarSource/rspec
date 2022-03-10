import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo
from rspec_tools.create_rule import (RuleCreator, add_language_to_rule,
                                     create_new_rule)
from rspec_tools.errors import InvalidArgumentError
from rspec_tools.repo import RspecRepo
from rspec_tools.utils import LANG_TO_SOURCE, is_empty_metadata

from tests.conftest import mock_github


@pytest.fixture
def rule_creator(rspec_repo: RspecRepo):
  return RuleCreator(rspec_repo)


def test_create_new_multi_lang_rule_branch(rule_creator: RuleCreator, mock_git_rspec_repo: Repo):
  '''Test create_new_rule_branch for a multi-language rule.'''
  rule_number = rule_creator.rspec_repo.reserve_rule_number()

  languages = ['java', 'javascript']
  branch = rule_creator.create_new_rule_branch(rule_number, languages)

  # Check that the branch was pushed successfully to the origin
  mock_git_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()

  common_root = rule_creator.TEMPLATE_PATH.joinpath('multi_language', 'common')
  for common_item in common_root.glob('**/*'):
    if common_item.is_file():
      expected_content = common_item.read_text().replace('${RSPEC_ID}', str(rule_number))
      relative_path = common_item.relative_to(common_root)
      actual_content = rule_dir.joinpath(relative_path).read_text()
      assert actual_content == expected_content

  lang_root = rule_creator.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
  for lang in languages:
    for lang_item in lang_root.glob('**/*'):
      if lang_item.is_file():
        expected_content = lang_item.read_text().replace('${RSPEC_ID}', str(rule_number))
        expected_content = expected_content.replace('[source,text]', f'[source,{LANG_TO_SOURCE[os.path.basename(lang)]}]')
        relative_path = lang_item.relative_to(lang_root)
        actual_content = rule_dir.joinpath(lang, relative_path).read_text()
        assert actual_content == expected_content


def test_create_new_single_lang_rule_branch(rule_creator: RuleCreator, mock_git_rspec_repo: Repo):
  '''Test create_new_rule_branch for a single-language rule.'''
  rule_number = rule_creator.rspec_repo.reserve_rule_number()

  languages = ['cfamily']
  branch = rule_creator.create_new_rule_branch(rule_number, languages)

  # Check that the branch was pushed successfully to the origin
  mock_git_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()

  common_root = rule_creator.TEMPLATE_PATH.joinpath('single_language', 'common')
  for common_item in common_root.glob('**/*'):
    if common_item.is_file():
      expected_content = common_item.read_text().replace('${RSPEC_ID}', str(rule_number))
      relative_path = common_item.relative_to(common_root)
      actual_content = rule_dir.joinpath(relative_path).read_text()
      assert actual_content == expected_content

  lang_root = rule_creator.TEMPLATE_PATH.joinpath('single_language', 'language_specific')
  for lang in languages:
    for lang_item in lang_root.glob('**/*'):
      if lang_item.is_file():
        expected_content = lang_item.read_text().replace('${RSPEC_ID}', str(rule_number))
        dir_name = os.path.basename(lang)
        expected_content = expected_content.replace('[source,text]', f'[source,{LANG_TO_SOURCE[dir_name]}]')
        relative_path = lang_item.relative_to(lang_root)
        actual_content = rule_dir.joinpath(lang, relative_path).read_text()
        assert actual_content == expected_content


def test_create_new_rule_pull_request(rule_creator: RuleCreator):
  '''Test create_new_rule_branch adds the right user and labels.'''
  rule_number = rule_creator.rspec_repo.reserve_rule_number()
  languages = ['cfamily']

  with mock_github() as (token, user, mock_repo):
    rule_creator.create_new_rule_pull_request(token, rule_number, languages, ['mylab', 'other-lab'], user)

    mock_repo.create_pull.assert_called_once();
    assert mock_repo.create_pull.call_args.kwargs['title'].startswith('Create rule S')
    mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(user);
    mock_repo.create_pull.return_value.add_to_labels.assert_called_with('mylab', 'other-lab');


@patch('rspec_tools.create_rule.RuleCreator')
def test_create_new_rule(mockRuleCreator):
  prMock = mockRuleCreator.return_value.create_new_rule_pull_request
  create_new_rule('cfamily,php', 'my token', 'testuser')
  prMock.assert_called_once()
  assert set(prMock.call_args.args[2]) == set(['cfamily', 'php'])
  assert set(prMock.call_args.args[3]) == set(['cfamily', 'php'])


@patch('rspec_tools.create_rule.RuleCreator')
def test_create_new_rule_unsupported_language(mockRuleCreator):
  with pytest.raises(InvalidArgumentError):
    create_new_rule('russian,php', 'my token', 'testuser')


def test_add_lang_singlelang_nonconventional_rule_create_branch(rule_creator: RuleCreator, mock_git_rspec_repo: Repo):
  '''Test add_language_branch for a single-language rule with metadata lifted to the generic rule level.'''
  rule_number = 4727
  language = 'php'

  mock_git_rspec_repo.git.checkout('master')
  orig_rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert(not is_empty_metadata(orig_rule_dir)) # nonconventional: singlelang rule with metadata on the upper level
  assert(is_empty_metadata(orig_rule_dir.joinpath('cobol')))
  original_metadata = orig_rule_dir.joinpath('metadata.json').read_text()

  branch = rule_creator.add_language_branch(rule_number, language)

  # Check that the branch was pushed successfully to the origin
  mock_git_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()
  lang_dir = rule_dir.joinpath(f'{language}')
  assert lang_dir.exists()

  assert rule_dir.joinpath('metadata.json').read_text() == original_metadata
  assert(is_empty_metadata(rule_dir.joinpath('cobol')))

  lang_root = rule_creator.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
  for lang_item in lang_root.glob('**/*'):
    if lang_item.is_file():
      expected_content = lang_item.read_text().replace('${RSPEC_ID}', str(rule_number))
      expected_content = expected_content.replace('[source,text]', f'[source,{LANG_TO_SOURCE[language]}]')
      relative_path = lang_item.relative_to(lang_root)
      actual_content = rule_dir.joinpath(language, relative_path).read_text()
      assert actual_content == expected_content


def test_add_lang_singlelang_conventional_rule_create_branch(rule_creator: RuleCreator, mock_git_rspec_repo: Repo):
  '''Test add_language_branch for a regular single language rule.'''
  rule_number = 1033
  language = 'php'

  mock_git_rspec_repo.git.checkout('master')
  orig_rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert(is_empty_metadata(orig_rule_dir)) # conventional: singlelang rule with metadata on the lang-specific level
  assert(not is_empty_metadata(orig_rule_dir.joinpath('cfamily')))
  original_lmetadata = orig_rule_dir.joinpath('cfamily', 'metadata.json').read_text()

  branch = rule_creator.add_language_branch(rule_number, language)

  # Check that the branch was pushed successfully to the origin
  mock_git_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()
  lang_dir = rule_dir.joinpath(f'{language}')
  assert lang_dir.exists()

  assert rule_dir.joinpath('metadata.json').read_text() == original_lmetadata
  assert(is_empty_metadata(rule_dir.joinpath('cfamily')))


def test_add_lang_multilang_rule_create_branch(rule_creator: RuleCreator, mock_git_rspec_repo: Repo):
  '''Test add_language_branch for a multi-language rule.'''
  rule_number = 120
  language = 'php'

  branch = rule_creator.add_language_branch(rule_number, language)

  # Check that the branch was pushed successfully to the origin
  mock_git_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_git_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()
  lang_dir = rule_dir.joinpath(f'{language}')
  assert lang_dir.exists()

  lang_root = rule_creator.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
  for lang_item in lang_root.glob('**/*'):
    if lang_item.is_file():
      expected_content = lang_item.read_text().replace('${RSPEC_ID}', str(rule_number))
      expected_content = expected_content.replace('[source,text]', f'[source,{LANG_TO_SOURCE[language]}]')
      relative_path = lang_item.relative_to(lang_root)
      actual_content = rule_dir.joinpath(language, relative_path).read_text()
      assert actual_content == expected_content


@patch('rspec_tools.create_rule.RuleCreator')
def test_add_unsupported_language(mock):
  '''Test language validation.'''
  with pytest.raises(InvalidArgumentError):
    add_language_to_rule('russian', 'S1033', 'my token', 'testuser')
  mock.return_value.add_language_pull_request.assert_not_called()


@patch('rspec_tools.create_rule.RuleCreator')
def test_add_supported_language(mock):
  '''Test language validation.'''
  add_language_to_rule('cfamily', 'S1033', 'my token', 'testuser')
  mock.return_value.add_language_pull_request.assert_called_once()


def test_add_language_the_rule_is_already_defined_for(rule_creator: RuleCreator):
  '''Test add_language_branch fails when trying to add a langage already added to the rule.'''
  with pytest.raises(InvalidArgumentError):
    rule_creator.add_language_branch(100, 'cfamily')


def test_add_language_to_nonexistent_rule(rule_creator: RuleCreator):
  '''Test add_language_branch correctly fails when invoked for a non-existent rule.'''
  with pytest.raises(InvalidArgumentError):
    rule_creator.add_language_branch(101, 'cfamily')


def test_add_language_new_pull_request(rule_creator: RuleCreator):
  '''Test add_language_pull_request adds the right user and labels.'''
  rule_number = 120
  language = 'php'

  with mock_github() as (token, user, mock_repo):
    rule_creator.add_language_pull_request(token, rule_number, language, 'mylab', user)

    mock_repo.create_pull.assert_called_once();
    assert mock_repo.create_pull.call_args.kwargs['title'].startswith(f'Create rule S{rule_number}')
    assert mock_repo.create_pull.call_args.kwargs['head'].startswith('rule/')
    mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(user)
    mock_repo.create_pull.return_value.add_to_labels.assert_called_with('mylab')
