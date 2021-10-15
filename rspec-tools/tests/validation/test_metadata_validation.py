from pathlib import Path

from unittest.mock import patch, PropertyMock
import pytest
from rspec_tools.errors import RuleValidationError
from copy import deepcopy

from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.metadata import validate_metadata

@pytest.fixture
def rule_language(mockrules: Path):
    rule = RulesRepository(rules_path=mockrules).get_rule('S100')
    return rule.get_language('kotlin')

def test_valid_metadata_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that language metadata are correctly overriden.'''
  validate_metadata(rule_language)


def test_missing_required_property_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  del invalid_metadata['title']
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_metadata(rule_language)


def test_invalid_remediation_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  invalid_metadata['remediation']["func"] = 42
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_metadata(rule_language)


def test_adding_properties_fails_validation(rule_language: LanguageSpecificRule):
  metadata = deepcopy(rule_language.metadata)
  metadata['unknown'] = 42
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = metadata
      validate_metadata(rule_language)


def test_ready_rule_with_replacement_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  invalid_metadata['extra'] = { 'replacementRules': [ 'RSPEC-1234', 'RSPEC-5678' ]}
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata: status'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_metadata(rule_language)


def test_deprecated_rule_with_replacement_passes_validation(rule_language: LanguageSpecificRule):
  metadata = deepcopy(rule_language.metadata)
  metadata['extra'] = { 'replacementRules': [ 'RSPEC-1234' ]}
  metadata['status'] = 'deprecated'
  with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
    mock.return_value = metadata
    validate_metadata(rule_language)
