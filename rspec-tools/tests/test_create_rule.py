from git import Repo, Head
from rspec_tools.errors import InvalidArgumentError
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch
import pytest
import shutil

from rspec_tools.create_rule import RuleCreator, create_new_rule, add_language_to_rule
from rspec_tools.utils import is_empty_metadata

@pytest.fixture
def git_config():
  '''Create a mock git configuration.'''
  return {
    'user.name': 'testuser',
    'user.email': 'testuser@mock.mock'
  }

@pytest.fixture
def mock_rspec_repo(tmpdir, mockrules: Path):
  repo_dir = tmpdir.mkdir("mock_rspec")
  repo = Repo.init(str(repo_dir))
  repo.init()
  rules_dir = repo_dir.join('rules')
  shutil.copytree(mockrules, rules_dir)

  with repo.config_writer() as config_writer:
    config_writer.set_value('user', 'name', 'originuser')
    config_writer.set_value('user', 'email', 'originuser@mock.mock')

  repo.git.add('--all')
  repo.index.commit('init rules')

  # Create the id counter branch. Note that it is an orphan branch.
  repo.head.reference = Head(repo, f'refs/heads/{RuleCreator.ID_COUNTER_BRANCH}')
  repo.git.reset('--hard')
  counter_file = repo_dir.join(RuleCreator.ID_COUNTER_FILENAME)
  counter_file.write('0')
  repo.index.add([str(counter_file)])
  commit = repo.index.commit('init counter', parent_commits=None)

  # Checkout a specific commit so that the repo can be pushed to without
  # making the index and work tree inconsistent.
  repo.git.checkout(commit.hexsha)

  return repo

@pytest.fixture
def rule_creator(tmpdir, mock_rspec_repo: Repo, git_config: dict[str, str]):
  cloned_repo = tmpdir.mkdir("cloned_repo")
  return RuleCreator(mock_rspec_repo.working_dir, str(cloned_repo), git_config)


def test_reserve_rule_number_simple(rule_creator: RuleCreator, mock_rspec_repo: Repo):
  '''Test that RuleCreator.reserve_rule_id() increments the id and returns the old value.'''
  assert rule_creator.reserve_rule_number() == 0

  assert read_counter_file(mock_rspec_repo) == '1'


def test_reserve_rule_number_parallel_reservations(tmpdir, mock_rspec_repo: Repo, git_config):
  '''Test that RuleCreator.reserve_rule_id() works when multiple reservations are done in parallel.'''
  cloned_repo1 = tmpdir.mkdir("cloned_repo1")
  rule_creator1 = RuleCreator(mock_rspec_repo.working_dir, str(cloned_repo1), git_config)
  cloned_repo2 = tmpdir.mkdir("cloned_repo2")
  rule_creator2 = RuleCreator(mock_rspec_repo.working_dir, str(cloned_repo2), git_config)

  assert rule_creator1.reserve_rule_number() == 0
  assert rule_creator2.reserve_rule_number() == 1
  assert rule_creator1.reserve_rule_number() == 2

  assert read_counter_file(mock_rspec_repo) == '3'


def read_counter_file(repo):
  '''Reads the counter file from the provided repository and returns its content.'''
  repo.git.checkout(RuleCreator.ID_COUNTER_BRANCH)
  counter_path = Path(repo.working_dir).joinpath(RuleCreator.ID_COUNTER_FILENAME)
  return counter_path.read_text()


def test_create_new_multi_lang_rule_branch(rule_creator: RuleCreator, mock_rspec_repo: Repo):
  '''Test create_new_rule_branch for a multi-language rule.'''
  rule_number = rule_creator.reserve_rule_number()

  languages = ['java', 'javascript']
  branch = rule_creator.create_new_rule_branch(rule_number, languages)

  # Check that the branch was pushed successfully to the origin
  mock_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
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
        relative_path = lang_item.relative_to(lang_root)
        actual_content = rule_dir.joinpath(lang, relative_path).read_text()
        assert actual_content == expected_content

def test_create_new_single_lang_rule_branch(rule_creator: RuleCreator, mock_rspec_repo: Repo):
  '''Test create_new_rule_branch for a single-language rule.'''
  rule_number = rule_creator.reserve_rule_number()

  languages = ['cfamily']
  branch = rule_creator.create_new_rule_branch(rule_number, languages)

  # Check that the branch was pushed successfully to the origin
  mock_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
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
        relative_path = lang_item.relative_to(lang_root)
        actual_content = rule_dir.joinpath(lang, relative_path).read_text()
        assert actual_content == expected_content

def test_create_new_rule_pr(rule_creator: RuleCreator):
  '''Test create_new_rule_branch adds the right user and labels.'''
  rule_number = rule_creator.reserve_rule_number()
  languages = ['cfamily']

  ghMock = Mock()
  ghRepoMock = Mock()
  pullMock = Mock()
  ghRepoMock.create_pull = Mock(return_value=pullMock)
  ghMock.get_repo = Mock(return_value=ghRepoMock)
  def mockGithub(user: Optional[str]):
    return ghMock

  rule_creator.create_new_rule_pull_request(mockGithub, rule_number, languages, ['mylab', 'other-lab'], user='testuser')

  ghRepoMock.create_pull.assert_called_once();
  assert ghRepoMock.create_pull.call_args.kwargs['title'].startswith('Create rule S')
  pullMock.add_to_assignees.assert_called_with('testuser');
  pullMock.add_to_labels.assert_called_with('mylab', 'other-lab');

@patch('rspec_tools.create_rule.RuleCreator')
def test_create_new_rule(mockRuleCreator):
  mockRuleCreator.return_value = Mock()
  mockRuleCreator.return_value.create_new_rule_pull_request = Mock()
  prMock = mockRuleCreator.return_value.create_new_rule_pull_request
  create_new_rule('cfamily,php', 'my token', 'testuser')
  prMock.assert_called_once()
  assert set(prMock.call_args.args[2]) == set(['cfamily', 'php'])
  assert set(prMock.call_args.args[3]) == set(['cfamily', 'php'])

@patch('rspec_tools.create_rule.RuleCreator')
def test_create_new_rule_unsupported_language(mockRuleCreator):
  mockRuleCreator.return_value = Mock()
  mockRuleCreator.return_value.create_new_rule_pull_request = Mock()
  prMock = mockRuleCreator.return_value.create_new_rule_pull_request
  with pytest.raises(InvalidArgumentError):
    create_new_rule('russian,php', 'my token', 'testuser')


def test_add_lang_singlelang_nonconventional_rule_create_branch(rule_creator: RuleCreator, mock_rspec_repo: Repo):
  '''Test add_language_branch for a single-language rule with metadata lifted to the generic rule level.'''
  rule_number = 4727
  language = 'php'

  mock_rspec_repo.git.checkout('master')
  orig_rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert(not is_empty_metadata(orig_rule_dir)) # nonconventional: singlelang rule with metadata on the upper level
  assert(is_empty_metadata(orig_rule_dir.joinpath('cobol')))
  original_metadata = orig_rule_dir.joinpath('metadata.json').read_text()

  branch = rule_creator.add_language_branch(rule_number, language)

  # Check that the branch was pushed successfully to the origin
  mock_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()
  lang_dir = rule_dir.joinpath(f'{language}')
  assert lang_dir.exists()

  assert rule_dir.joinpath('metadata.json').read_text() == original_metadata
  assert(is_empty_metadata(rule_dir.joinpath('cobol')))

  lang_root = rule_creator.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
  for lang_item in lang_root.glob('**/*'):
    if lang_item.is_file():
      expected_content = lang_item.read_text().replace('${RSPEC_ID}', str(rule_number))
      relative_path = lang_item.relative_to(lang_root)
      actual_content = rule_dir.joinpath(language, relative_path).read_text()
      assert actual_content == expected_content

def test_add_lang_singlelang_conventional_rule_create_branch(rule_creator: RuleCreator, mock_rspec_repo: Repo):
  '''Test add_language_branch for a regular single language rule.'''
  rule_number = 1033
  language = 'php'

  mock_rspec_repo.git.checkout('master')
  orig_rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert(is_empty_metadata(orig_rule_dir)) # conventional: singlelang rule with metadata on the lang-specific level
  assert(not is_empty_metadata(orig_rule_dir.joinpath('cfamily')))
  original_lmetadata = orig_rule_dir.joinpath('cfamily', 'metadata.json').read_text()

  branch = rule_creator.add_language_branch(rule_number, language)

  # Check that the branch was pushed successfully to the origin
  mock_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()
  lang_dir = rule_dir.joinpath(f'{language}')
  assert lang_dir.exists()

  assert rule_dir.joinpath('metadata.json').read_text() == original_lmetadata
  assert(is_empty_metadata(rule_dir.joinpath('cfamily')))

def test_add_lang_multilang_rule_create_branch(rule_creator: RuleCreator, mock_rspec_repo: Repo):
  '''Test add_language_branch for a multi-language rule.'''
  rule_number = 120
  language = 'php'

  branch = rule_creator.add_language_branch(rule_number, language)

  # Check that the branch was pushed successfully to the origin
  mock_rspec_repo.git.checkout(branch)
  rule_dir = Path(mock_rspec_repo.working_dir).joinpath('rules', f'S{rule_number}')
  assert rule_dir.exists()
  lang_dir = rule_dir.joinpath(f'{language}')
  assert lang_dir.exists()

  lang_root = rule_creator.TEMPLATE_PATH.joinpath('multi_language', 'language_specific')
  for lang_item in lang_root.glob('**/*'):
    if lang_item.is_file():
      expected_content = lang_item.read_text().replace('${RSPEC_ID}', str(rule_number))
      relative_path = lang_item.relative_to(lang_root)
      actual_content = rule_dir.joinpath(language, relative_path).read_text()
      assert actual_content == expected_content

@patch('rspec_tools.create_rule.RuleCreator')
def test_add_unsupported_language(mockRuleCreator):
  '''Test language validation.'''
  mockRuleCreator.return_value = Mock()
  mockRuleCreator.return_value.create_new_rule_pull_request = Mock()
  prMock = mockRuleCreator.return_value.create_new_rule_pull_request
  with pytest.raises(InvalidArgumentError):
    add_language_to_rule('russian', 'S1033', 'my token', 'testuser')

def test_add_language_the_rule_is_already_defined_for(rule_creator: RuleCreator):
  '''Test add_language_branch fails when trying to add a langage already added to the rule.'''
  with pytest.raises(InvalidArgumentError):
    rule_creator.add_language_branch(100, 'cfamily')

def test_add_language_to_nonexistent_rule(rule_creator: RuleCreator):
  '''Test add_language_branch correctly fails when invoked for a non-existent rule.'''
  with pytest.raises(InvalidArgumentError):
    rule_creator.add_language_branch(101, 'cfamily')

def test_add_language_new_pr(rule_creator: RuleCreator):
  '''Test add_language_pull_request adds the right user and labels.'''
  rule_number = 120
  language = 'php'

  ghMock = Mock()
  ghRepoMock = Mock()
  pullMock = Mock()
  ghRepoMock.create_pull = Mock(return_value=pullMock)
  ghMock.get_repo = Mock(return_value=ghRepoMock)
  def mockGithub(user: Optional[str]):
    return ghMock

  rule_creator.add_language_pull_request(mockGithub, rule_number, language, 'mylab', user='testuser')

  ghRepoMock.create_pull.assert_called_once();
  assert ghRepoMock.create_pull.call_args.kwargs['title'].startswith(f'Create rule S{rule_number}[{language}]')
  ghRepoMock.create_pull.call_args.kwargs['head'].startswith('rule/')
  pullMock.add_to_assignees.assert_called_with('testuser');
  pullMock.add_to_labels.assert_called_with('mylab');
