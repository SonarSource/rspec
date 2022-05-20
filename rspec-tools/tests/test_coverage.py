import os
import shutil
import pytest
from git import Repo
from pathlib import Path
from datetime import datetime
from unittest.mock import (patch, PropertyMock)
from contextlib import contextmanager

from rspec_tools.coverage import (update_coverage_for_all_repos,
                                  update_coverage_for_repo,
                                  update_coverage_for_repo_version)
from rspec_tools.utils import (load_json, pushd)

def clear_working_dir(repo_dir):
  for f in os.listdir(repo_dir):
    if f != '.git':
      if os.path.isdir(repo_dir / f):
        shutil.rmtree(repo_dir / f)
      else:
        os.remove(repo_dir / f)

@pytest.fixture
def rules_dir():
  return Path(__file__).parent.joinpath('resources', 'rules')

JSTS_SONARPEDIA='{"rules-metadata-path": "rules", "languages":["JS", "TS"]}'
MOCK_REPOS=[{'name':'SonarJS',
             'versions': [
               {'name': '3.3.0.5702',
                'date': '2020-03-03 10:00:00',
                'files': [['sonarpedia.json', JSTS_SONARPEDIA],
                          ['rules/Sonar_way_profile.json', '{}'],
                          # MethodName is a lagacy key for S100
                          ['rules/MethodName.json', '{}'], ['rules/S1145.json', '{}'],
                          # not in the rules directory, so not a rule:
                          ['S200.json', '{}']]},
               {'name': '5.0.0.6962',
                'date': '2020-05-01 10:00:00',
                'files': [['sonarpedia.json', JSTS_SONARPEDIA],
                          ['rules/Sonar_way_profile.json', '{}'],
                          ['rules/S100.json', '{}'], ['rules/S1145.json', '{}'], ['rules/S1192.json', '{}']]},
               {'name': '6.7.0.14237',
                'date': '2020-06-07 10:00:00',
                'files': [['sonarpedia.json', JSTS_SONARPEDIA],
                          ['rules/Sonar_way_profile.json', '{}'],
                          ['rules/S100.json', '{}'], ['rules/S1145.json', '{}'], ['rules/S1192.json', '{}']]},
               {'name': '7.0.0.14528',
                'date': '2020-07-01 10:00:00',
                'files': [['sonarpedia.json', JSTS_SONARPEDIA],
                          ['rules/Sonar_way_profile.json', '{}'],
                          ['rules/S100.json', '{}'], ['rules/S1192.json', '{}'],
                          # add a CSS analyzer in this version
                          ['css-plugin/sonarpedia.json', '{"rules-metadata-path":"cssr", "languages":["CSS"]}'],
                          ['css-plugin/cssr/S100.json', '{}'],
                          # add a XML analyzer here too
                          ['xml/sonarpedia.json', '{"rules-metadata-path":"r", "languages":["XML"]}'],
                          ['xml/r/S1000.json', '{}']]},
             ]},
            {'name':'sonar-xml',
             'versions': [
               {'name': '1.2.0.1342',
                'date': '2020-01-02 10:00:00',
                'files': [['rules/Sonar_way_profile.json', '{}'],
                          ['sonarpedia.json', '{"rules-metadata-path": "rules", "languages":["XML"]}'],
                          ['rules/S103.json', '{}']]}
             ]},
            {'name':'broken',
             'versions': [
               {'name': 'v1',
                'date': '2020-01-01 01:01:01',
                'files': [['sonarpedia.json', 'non-json'], # sonarpedia is non-json
                          ['rules/S100.json', '{}']]}
             ]}]

def test_mock_tags_are_sorted_chronologically():
  for mock_spec in MOCK_REPOS:
    prev_date = datetime.strptime('1970-01-01 00:00:01', '%Y-%m-%d %H:%M:%S')
    for tag in mock_spec['versions']:
      cur_date = datetime.strptime(tag['date'], '%Y-%m-%d %H:%M:%S')
      assert prev_date < cur_date
      prev_date = cur_date

@pytest.fixture
def mock_git_analyzer_repos(tmpdir):
  mocked_repos = {};
  for mock_spec in MOCK_REPOS:
    repo_name = mock_spec['name']
    repo_dir = tmpdir.mkdir('mock-' + repo_name)
    repo = Repo.init(str(repo_dir))
    with repo.config_writer() as config_writer:
      config_writer.set_value('user', 'name', 'originuser')
      config_writer.set_value('user', 'email', 'originuser@mock.mock')
    for tag in mock_spec['versions']:
      clear_working_dir(repo_dir)
      for fname, contents in tag['files']:
        path = Path(repo_dir / fname)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'x') as f:
          f.write(contents)
      repo.git.add('--all')
      repo.index.commit(f"adding version {tag['name']}", commit_date=tag['date'], author_date=tag['date'])
      repo.create_tag(tag['name'])
    mocked_repos[repo_name] = repo
  def mock_clone_repo(repo_url, repo_name):
    return mocked_repos[repo_url.split('/')[-1]]
  def precloned_repo(x):
    Repo(x)
  mock=PropertyMock(side_effect=precloned_repo)
  mock.clone_from=PropertyMock(side_effect=mock_clone_repo)
  return mock

def test_update_coverage_for_repo_version(tmpdir, rules_dir: Path, mock_git_analyzer_repos):
  with pushd(tmpdir), patch('rspec_tools.coverage.Repo', mock_git_analyzer_repos):
    VER = '3.3.0.5702'
    REPO = 'SonarJS'
    update_coverage_for_repo_version(REPO, VER, rules_dir)
    coverage = tmpdir.join('covered_rules.json')
    assert coverage.exists()
    cov = load_json(coverage)
    assert 'JAVASCRIPT' in cov
    assert 'S100' in cov['JAVASCRIPT']
    assert 'MethodName' not in cov['JAVASCRIPT'] # MethodName is a legacy key for S100
    assert 'S200' not in cov['JAVASCRIPT'] # S200.json is not in the rules directory in mock
    assert cov['JAVASCRIPT']['S100'] == {'since': REPO + ' ' + VER, 'until': REPO + ' ' + VER}

    # Running it again changes nothing
    update_coverage_for_repo_version(REPO, VER, rules_dir)
    assert cov == load_json(coverage)

    # Running it for a newer version doesn't change when the rules are first implemented
    VER2 = '5.0.0.6962'
    update_coverage_for_repo_version(REPO, VER2, rules_dir)
    cov_new = load_json(coverage)
    assert set(cov['JAVASCRIPT'].keys()).issubset(set(cov_new['JAVASCRIPT'].keys()))
    assert cov_new['JAVASCRIPT']['S100']['since'] == REPO + ' ' + VER
    assert cov_new['JAVASCRIPT']['S100']['until'] == REPO + ' ' + VER2
    assert cov_new['JAVASCRIPT']['S1192']['since'] == REPO + ' ' + VER2
    assert cov_new['JAVASCRIPT']['S1192']['until'] == REPO + ' ' + VER2

    # For rules supported on master only the 'since' part is kept
    update_coverage_for_repo_version(REPO, 'master', rules_dir)
    assert load_json(coverage)['JAVASCRIPT']['S100'] == REPO + ' ' + VER


def test_update_coverage_for_repo(tmpdir, rules_dir: Path, mock_git_analyzer_repos):
  with pushd(tmpdir), patch('rspec_tools.coverage.Repo', mock_git_analyzer_repos):
    REPO = 'SonarJS'
    update_coverage_for_repo(REPO, rules_dir)
    coverage = tmpdir.join('covered_rules.json')
    assert coverage.exists()
    cov = load_json(coverage)
    assert 'JAVASCRIPT' in cov
    assert 'TYPESCRIPT' in cov
    assert 'S100' in cov['JAVASCRIPT']
    assert 'MethodName' not in cov['JAVASCRIPT'] # MethodName is a legacy key for S100
    assert cov['JAVASCRIPT']['S100'] == REPO + ' 3.3.0.5702'
    assert 'S1145' in cov['JAVASCRIPT']
    assert cov['JAVASCRIPT']['S1145'] == {'since': REPO + ' 3.3.0.5702', 'until': REPO + ' 6.7.0.14237'}


@patch('rspec_tools.coverage.REPOS', ['SonarJS', 'sonar-xml'])
def test_update_coverage_for_all_repos(tmpdir, rules_dir: Path, mock_git_analyzer_repos):
  with pushd(tmpdir), patch('rspec_tools.coverage.Repo', mock_git_analyzer_repos):
    update_coverage_for_all_repos(rules_dir)
    coverage = tmpdir.join('covered_rules.json')
    assert coverage.exists()
    cov = load_json(coverage)
    assert {'JAVASCRIPT', 'TYPESCRIPT', 'XML', 'CSS'} == set(cov.keys())
    assert 'S100' in cov['JAVASCRIPT']
    assert 'MethodName' not in cov['JAVASCRIPT'] # MethodName is a legacy key for S100
    assert {'S100'} == set(cov['CSS'].keys())
    assert {'S103', 'S1000'} == set(cov['XML'].keys())
    assert cov['XML']['S1000'] == 'SonarJS 7.0.0.14528'

def test_update_coverage_no_sonarpedia(tmpdir, rules_dir: Path, mock_git_analyzer_repos, capsys):
  with pushd(tmpdir), patch('rspec_tools.coverage.Repo', mock_git_analyzer_repos):
    update_coverage_for_repo_version('broken', 'v1', rules_dir)
    assert 'failed to collect implemented rules for' in capsys.readouterr().out
    coverage = tmpdir.join('covered_rules.json')
    assert coverage.exists()
    cov = load_json(coverage)
    assert cov == {}

def test_update_coverage_nonexisting_versio(tmpdir, rules_dir: Path, mock_git_analyzer_repos, capsys):
  with pushd(tmpdir), patch('rspec_tools.coverage.Repo', mock_git_analyzer_repos):
    with pytest.raises(Exception):
      update_coverage_for_repo_version('broken', 'non-existing', rules_dir)
    assert 'checkout failed' in capsys.readouterr().out
