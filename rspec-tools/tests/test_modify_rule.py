import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo
from rspec_tools.errors import InvalidArgumentError
from rspec_tools.modify_rule import RuleEditor, update_rule_quickfix_status
from rspec_tools.repo import RspecRepo

from tests.conftest import mock_github


@pytest.fixture
def rule_editor(rspec_repo: RspecRepo):
  return RuleEditor(rspec_repo)


def test_update_quickfix_status_branch1(rule_editor: RuleEditor, mock_git_rspec_repo: Repo):
  '''Test update_quickfix_status_branch when quickfix field is not present in language-specific metadata'''
  rule_number = 100
  language = 'cfamily'

  sub_path = Path('rules', f'S{rule_number}', language, 'metadata.json')
  metadata_path = Path(mock_git_rspec_repo.working_dir) / sub_path
  mock_git_rspec_repo.git.checkout('master')
  initial_metadata = json.loads(metadata_path.read_text())
  assert 'quickfix' not in initial_metadata # It is in the parent metadata.json file.

  branch = rule_editor.update_quickfix_status_branch('Some title', rule_number, language, 'covered')
  mock_git_rspec_repo.git.checkout(branch)
  new_metadata = json.loads(metadata_path.read_text())

  # Verify that only the quickfix status is introduced.
  assert len(initial_metadata.keys()) + 1 == len(new_metadata.keys())
  assert 'quickfix' in new_metadata
  assert 'covered' == new_metadata['quickfix']
  for key in initial_metadata:
    assert initial_metadata[key] == new_metadata[key]

  # Ensure only one file is modified.
  modified_files = mock_git_rspec_repo.git.diff('master', '--name-only').strip()
  assert modified_files == str(sub_path).replace('\\', '/')


def test_update_quickfix_status_branch2(rule_editor: RuleEditor, mock_git_rspec_repo: Repo):
  '''Test update_quickfix_status_branch when quickfix field is already present in language-specific metadata'''
  rule_number = 100
  language = 'java'

  sub_path = Path('rules', f'S{rule_number}', language, 'metadata.json')
  metadata_path = Path(mock_git_rspec_repo.working_dir) / sub_path
  mock_git_rspec_repo.git.checkout('master')
  initial_metadata = json.loads(metadata_path.read_text())
  assert 'quickfix' in initial_metadata
  assert initial_metadata['quickfix'] == 'targeted'

  branch = rule_editor.update_quickfix_status_branch('Some title', rule_number, language, 'covered')
  mock_git_rspec_repo.git.checkout(branch)
  new_metadata = json.loads(metadata_path.read_text())

  # Verify that only the quickfix status is updated.
  assert len(initial_metadata.keys()) == len(new_metadata.keys())
  assert 'quickfix' in new_metadata
  assert 'covered' == new_metadata['quickfix']
  for key in initial_metadata:
    if key != 'quickfix':
      assert initial_metadata[key] == new_metadata[key]

  # Ensure only one file is modified.
  modified_files = mock_git_rspec_repo.git.diff('master', '--name-only').strip()
  assert modified_files == str(sub_path).replace('\\', '/')


def test_update_quickfix_status_branch3(rule_editor: RuleEditor, mock_git_rspec_repo: Repo):
  '''Test update_quickfix_status_branch when new and old quickfix status are the same'''
  rule_number = 100
  language = 'java'

  metadata_path = Path(mock_git_rspec_repo.working_dir, 'rules', f'S{rule_number}', language, 'metadata.json')
  mock_git_rspec_repo.git.checkout('master')
  initial_metadata = json.loads(metadata_path.read_text())
  assert 'quickfix' in initial_metadata
  assert initial_metadata['quickfix'] == 'targeted'

  with pytest.raises(InvalidArgumentError):
    rule_editor.update_quickfix_status_branch('Some title', rule_number, language, 'targeted')


def test_update_quickfix_status_branch4(rule_editor: RuleEditor, mock_git_rspec_repo: Repo):
  '''Test update_quickfix_status_branch when the rule does not exist'''
  rule_number = 404
  language = 'java'

  metadata_path = Path(mock_git_rspec_repo.working_dir, 'rules', f'S{rule_number}', language, 'metadata.json')
  mock_git_rspec_repo.git.checkout('master')
  assert not metadata_path.exists()

  with pytest.raises(InvalidArgumentError):
    rule_editor.update_quickfix_status_branch('Some title', rule_number, language, 'targeted')


def test_update_quickfix_status_pull_request(rule_editor: RuleEditor):
  '''Test update_quickfix_status_pull_request adds the right user and label.'''
  with mock_github() as (token, user, mock_repo):
    rule_editor.update_quickfix_status_pull_request(token, 100, 'cfamily', 'covered', 'label-fraicheur', user)
    mock_repo.create_pull.assert_called_once();
    assert mock_repo.create_pull.call_args.kwargs['title'].startswith('Modify rule S100')
    mock_repo.create_pull.return_value.add_to_assignees.assert_called_with(user)
    mock_repo.create_pull.return_value.add_to_labels.assert_called_with('label-fraicheur')


@patch('rspec_tools.modify_rule.tmp_rspec_repo')
@patch('rspec_tools.modify_rule.RuleEditor')
def test_update_rule_quickfix_status(mockRuleEditor, mock_tmp_rspec_repo):
  '''Test update_rule_quickfix_status uses the expected implementation.'''
  prMock = mockRuleEditor.return_value.update_quickfix_status_pull_request
  update_rule_quickfix_status('cfamily', 'S100', 'covered', 'my token', 'testuser')
  prMock.assert_called_once()
  assert prMock.call_args.args[1] == 100
  assert prMock.call_args.args[2] == 'cfamily'
  assert prMock.call_args.args[3] == 'covered'
  assert prMock.call_args.args[4] == 'cfamily'
