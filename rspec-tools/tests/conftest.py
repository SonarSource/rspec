from pathlib import Path

import pytest


@pytest.fixture
def mockrules():
  '''Provides a path to test rules resources.'''
  return Path(__file__).parent.joinpath('resources', 'rules')

@pytest.fixture
def mockinvalidrules():
  '''Provides a path to test rules resources.'''
  return Path(__file__).parent.joinpath('resources', 'invalid-rules')
