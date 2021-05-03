from git import Repo, Head
from pathlib import Path
import pytest

from rspec_tools.create_rule import RuleCreator

@pytest.fixture
def git_config():
  '''Create a mock git configuration.'''
  return {
    'user.name': 'testuser',
    'user.email': 'testuser@mock.mock'
  }

@pytest.fixture
def mock_rspec_repo(tmpdir):
  repo_dir = tmpdir.mkdir("mock_rspec")
  repo = Repo.init(str(repo_dir))
  repo.init()

  with repo.config_writer() as config_writer:
    config_writer.set_value('user', 'name', 'originuser')
    config_writer.set_value('user', 'email', 'originuser@mock.mock')

  rules_dir = repo_dir.mkdir('rules')
  # create a file just to have a "rules" directory
  gitignore = rules_dir.join('.gitignore')
  gitignore.ensure()
  repo.index.add([str(gitignore)])
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
