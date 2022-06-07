from pathlib import Path

import pytest
from git import Repo
from rspec_tools.repo import RspecRepo


def _read_counter_file(repo: Repo):
  '''Reads the counter file from the provided repository and returns its content.'''
  repo.git.checkout(RspecRepo.ID_COUNTER_BRANCH)
  counter_path = Path(repo.working_dir, RspecRepo.ID_COUNTER_FILENAME)
  return counter_path.read_text()


def test_reserve_rule_number_simple(rspec_repo: RspecRepo, mock_git_rspec_repo: Repo):
  '''Test that RspecRepo.reserve_rule_number() increments the id and returns the old value.'''
  assert rspec_repo.reserve_rule_number() == 0

  assert _read_counter_file(mock_git_rspec_repo) == '1'


def test_reserve_rule_number_parallel_reservations(tmpdir, mock_git_rspec_repo: Repo, git_config):
  '''Test that RspecRepo.reserve_rule_number() works when multiple reservations are done in parallel.'''
  cloned_repo1 = tmpdir.mkdir("cloned_repo1")
  rule_creator1 = RspecRepo(mock_git_rspec_repo.working_dir, str(cloned_repo1), git_config)
  cloned_repo2 = tmpdir.mkdir("cloned_repo2")
  rule_creator2 = RspecRepo(mock_git_rspec_repo.working_dir, str(cloned_repo2), git_config)

  assert rule_creator1.reserve_rule_number() == 0
  assert rule_creator2.reserve_rule_number() == 1
  assert rule_creator1.reserve_rule_number() == 2

  assert _read_counter_file(mock_git_rspec_repo) == '3'
