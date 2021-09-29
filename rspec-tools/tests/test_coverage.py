from git import Repo, Head
from unittest.mock import Mock, patch
import pytest
import json

from rspec_tools.coverage import update_coverage_for_repo_version, update_coverage_for_repo
from rspec_tools.utils import load_json, pushd

def test_update_coverage_for_repo_version(tmpdir):
  with pushd(tmpdir):
    VER = '3.3.0.5702'
    REPO = 'SonarJS'
    update_coverage_for_repo_version(REPO, VER)
    coverage = tmpdir.join('covered_rules.json')
    assert coverage.exists()
    cov = load_json(coverage)
    assert 'JAVASCRIPT' in cov
    assert 'S100' in cov['JAVASCRIPT']
    assert cov['JAVASCRIPT']['S100'] == {'since': REPO + ' ' + VER, 'until': REPO + ' ' + VER}

    # Running it again changes nothing
    update_coverage_for_repo_version(REPO, VER)
    assert cov == load_json(coverage)

    # Running it for a newer version doesn't change when the rules are first implemented
    VER2 = '5.0.0.6962'
    update_coverage_for_repo_version(REPO, VER2)
    cov_new = load_json(coverage)
    assert set(cov['JAVASCRIPT'].keys()).issubset(set(cov_new['JAVASCRIPT'].keys()))
    assert cov_new['JAVASCRIPT']['S100']['since'] == REPO + ' ' + VER
    assert cov_new['JAVASCRIPT']['S100']['until'] == REPO + ' ' + VER2
    assert cov_new['JAVASCRIPT']['S1192']['since'] == REPO + ' ' + VER2
    assert cov_new['JAVASCRIPT']['S1192']['until'] == REPO + ' ' + VER2

    # For rules supported on master only the 'since' part is kept
    update_coverage_for_repo_version(REPO, 'master')
    assert load_json(coverage)['JAVASCRIPT']['S100'] == REPO + ' ' + VER

def test_update_coverage_for_repo(tmpdir):
  with pushd(tmpdir):
    REPO = 'SonarJS'
    update_coverage_for_repo(REPO)
    coverage = tmpdir.join('covered_rules.json')
    assert coverage.exists()
    cov = load_json(coverage)
    assert 'JAVASCRIPT' in cov
    assert 'TYPESCRIPT' in cov
    assert 'S100' in cov['JAVASCRIPT']
    assert cov['JAVASCRIPT']['S100'] == REPO + ' 3.3.0.5702'
    assert 'S1145' in cov['JAVASCRIPT']
    assert cov['JAVASCRIPT']['S1145'] == {'since': REPO + ' 3.3.0.5702', 'until': REPO + ' 6.7.0.14237'}
