import shutil
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Head, Repo
from rspec_tools.repo import RspecRepo


@pytest.fixture
def mockrules():
  '''Provides a path to test rules resources.'''
  return Path(__file__).parent.joinpath('resources', 'rules')


@pytest.fixture
def mockinvalidrules():
  '''Provides a path to test rules resources.'''
  return Path(__file__).parent.joinpath('resources', 'invalid-rules')


@pytest.fixture
def git_config():
  '''Create a mock git configuration.'''
  return {
    'user.name': 'testuser',
    'user.email': 'testuser@mock.mock'
  }


@pytest.fixture
def mock_git_rspec_repo(tmpdir, mockrules: Path):
  repo_dir = tmpdir.mkdir("mock_rspec")
  repo = Repo.init(str(repo_dir))
  rules_dir = repo_dir.join('rules')
  shutil.copytree(mockrules, rules_dir)

  with repo.config_writer() as config_writer:
    config_writer.set_value('user', 'name', 'originuser')
    config_writer.set_value('user', 'email', 'originuser@mock.mock')

  repo.git.add('--all')
  repo.index.commit('init rules')

  # Create the id counter branch. Note that it is an orphan branch.
  repo.head.reference = Head(repo, f'refs/heads/{RspecRepo.ID_COUNTER_BRANCH}')
  repo.git.reset('--hard')
  counter_file = repo_dir.join(RspecRepo.ID_COUNTER_FILENAME)
  counter_file.write('0')
  repo.index.add([str(counter_file)])
  commit = repo.index.commit('init counter', parent_commits=None)

  # Checkout a specific commit so that the repo can be pushed to without
  # making the index and work tree inconsistent.
  repo.git.checkout(commit.hexsha)

  return repo


@pytest.fixture
def rspec_repo(tmpdir, mock_git_rspec_repo: Repo, git_config: dict[str, str]):
  cloned_repo = tmpdir.mkdir("cloned_repo")
  return RspecRepo(mock_git_rspec_repo.working_dir, str(cloned_repo), git_config)


@contextmanager
def mock_github():
  token = 'TOKEN'
  user = 'testuser'
  mock_repo = Mock()
  mock_github = Mock()
  mock_github.get_repo = Mock(return_value=mock_repo)
  mock_github_api = Mock(return_value=mock_github)
  mock_auto_github = Mock(return_value=mock_github_api)
  with patch('rspec_tools.repo._auto_github', mock_auto_github):
    yield (token, user, mock_repo)
    mock_auto_github.assert_called_once_with(token)
    mock_github_api.assert_called_once_with(user)
    mock_github.get_repo.assert_called_once()
