from pathlib import Path

from unittest.mock import patch, PropertyMock
import pytest
from rspec_tools.errors import RuleValidationError
from copy import deepcopy

from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.metadata import validate_metadata, validate_metadata_of_modified_rule

@pytest.fixture
def rule_language(mockrules: Path):
  rule = RulesRepository(rules_path=mockrules).get_rule('S100')
  return rule.get_language('kotlin')


@pytest.fixture
def invalid_rules():
  invalid_rules_path = Path(__file__).parent.parent.joinpath('resources', 'invalid-rules')
  return RulesRepository(rules_path=invalid_rules_path)


def test_valid_metadata_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that language metadata are correctly overridden.'''
  validate_metadata(rule_language)


def test_modified_rule_with_no_language(invalid_rules: RulesRepository):
  s501 = invalid_rules.get_rule('S501')
  with pytest.raises(RuleValidationError, match=fr'^Rule S501 has no language-specific data'):
    validate_metadata_of_modified_rule(s501)


def test_modified_rule_with_invalid_language(invalid_rules: RulesRepository):
  s502 = invalid_rules.get_rule('S502')
  with pytest.raises(RuleValidationError, match=fr'^Rule scala:S502 has invalid metadata'):
    validate_metadata_of_modified_rule(s502)


def test_modified_rule_that_is_fully_valid(mockrules: Path):
  valid_rule = RulesRepository(rules_path=mockrules).get_rule('S120')
  validate_metadata_of_modified_rule(valid_rule)


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


def test_rule_with_incomplete_list_of_security_standard_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  # "OWASP Top 10 2021", defined in the generic metadata is missing
  invalid_metadata['securityStandards'] = {'ASVS 4': [], 'OWASP': [], 'CERT': []}
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata: securityStandard'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_metadata(rule_language)


def test_rule_with_complete_list_of_security_standard_passes_validation(rule_language: LanguageSpecificRule):
  metadata = deepcopy(rule_language.metadata)
  metadata['securityStandards'] = {'ASVS 4': [], 'OWASP': [], "OWASP Top 10 2021": []}
  with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
    mock.return_value = metadata
    validate_metadata(rule_language)