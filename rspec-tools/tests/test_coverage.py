from git import Repo, Head
from unittest.mock import Mock, patch
import pytest
import os
import json

from rspec_tools.coverage import update_coverage_for_repo_version, update_coverage_for_repo
from rspec_tools.utils import load_json

def test_update_coverage_for_repo_version(tmpdir):
  previous_dir = os.getcwd()
  os.chdir(tmpdir)
  VER = '3.7.0.1603'
  REPO = 'sonar-abap'
  update_coverage_for_repo_version(REPO, VER)
  coverage = tmpdir.join('covered_rules.json')
  assert coverage.exists()
  cov = load_json(coverage)
  assert 'ABAP' in cov
  assert 'S100' in cov['ABAP']
  assert cov['ABAP']['S100'] == {'since': REPO + ' ' + VER, 'until': REPO + ' ' + VER}

  # running it again changes nothing
  update_coverage_for_repo_version(REPO, VER)
  assert cov == load_json(coverage)

  # running it for a newer version doesn't change when the rules are first implemented
  VER2 = '3.8.0.2034'
  update_coverage_for_repo_version(REPO, VER2)
  cov_new = load_json(coverage)
  assert set(cov['ABAP'].keys()).issubset(set(cov_new['ABAP'].keys()))
  assert cov_new['ABAP']['S100']['since'] == REPO + ' ' + VER
  assert cov_new['ABAP']['S100']['until'] == REPO + ' ' + VER2
  assert cov_new['ABAP']['S2809']['since'] == REPO + ' ' + VER2
  assert cov_new['ABAP']['S2809']['until'] == REPO + ' ' + VER2

  os.chdir(previous_dir)

def test_update_coverage_for_repo(tmpdir):
  previous_dir = os.getcwd()
  os.chdir(tmpdir)
  REPO = 'sonar-abap'
  update_coverage_for_repo(REPO)
  coverage = tmpdir.join('covered_rules.json')
  assert coverage.exists()
  with open(coverage) as f:
    cov = json.load(f)
    assert 'ABAP' in cov
    assert 'S100' in cov['ABAP']
    assert cov['ABAP']['S100'] == REPO + ' 3.5.0.1080'
    assert cov['ABAP']['S2076'] == {'since': REPO + ' 3.5.0.1080', 'until': REPO + ' 3.7.1.1762'}
  os.chdir(previous_dir)
