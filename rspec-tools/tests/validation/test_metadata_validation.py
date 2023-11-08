from pathlib import Path

from unittest.mock import patch, PropertyMock
import pytest
import re
from rspec_tools.errors import RuleValidationError
from copy import deepcopy

from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.metadata import validate_rule_specialization_metadata, validate_rule_metadata

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
  validate_rule_specialization_metadata(rule_language)


@patch('rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES', [])
def test_rule_with_no_language(invalid_rules: RulesRepository):
  s501 = invalid_rules.get_rule('S501')
  with pytest.raises(RuleValidationError, match=fr'^Rule S501 has no language-specific data'):
    validate_rule_metadata(s501)


@patch('rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES', ['S501'])
def test_rule_with_no_language_in_exception_list(invalid_rules: RulesRepository):
  s501 = invalid_rules.get_rule('S501')
  validate_rule_metadata(s501)
  with patch.dict(s501.generic_metadata, [('status', 'deprecated')]):
    validate_rule_metadata(s501)


@patch('rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES', ['S501'])
def test_open_rule_with_no_language_in_exception_list(invalid_rules: RulesRepository):
  s501 = invalid_rules.get_rule('S501')
  with pytest.raises(RuleValidationError, match=fr'^Rule S501 should be closed or deprecated'):
    with patch.dict(s501.generic_metadata, [('status', 'ready')]):
      validate_rule_metadata(s501)


@patch('rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES', ['S120'])
def test_rule_expected_to_have_no_language(mockrules: Path):
  valid_rule = RulesRepository(rules_path=mockrules).get_rule('S120')
  with pytest.raises(RuleValidationError, match=fr'^Rule S120 should have no specializations'):
    validate_rule_metadata(valid_rule)


@patch('rspec_tools.validation.metadata.RULES_WITH_NO_LANGUAGES', [])
def test_rule_with_invalid_language(invalid_rules: RulesRepository):
  s502 = invalid_rules.get_rule('S502')
  with pytest.raises(RuleValidationError, match=fr'^Rule S502 failed validation for these reasons:\n - Rule scala:S502 has invalid metadata'):
    validate_rule_metadata(s502)

def test_rule_with_invalid_education_principles(invalid_rules: RulesRepository):
  s503 = invalid_rules.get_rule('S503')
  with pytest.raises(RuleValidationError, match=re.escape("Rule S503 failed validation for these reasons:\n - Rule scala:S503 has invalid metadata in 0: 'invalid' is not one of ['defense_in_depth', 'never_trust_user_input']")):
    validate_rule_metadata(s503)


def test_rule_with_no_impacts(invalid_rules: RulesRepository):
  s504 = invalid_rules.get_rule('S504')
  with pytest.raises(RuleValidationError, match=re.escape("Rule S504 failed validation for these reasons:\n - Rule scala:S504 has invalid metadata in impacts: {} does not have enough properties")):
    validate_rule_metadata(s504)


def test_rule_with_invalid_impacts(invalid_rules: RulesRepository):
  s505 = invalid_rules.get_rule('S505')
  with pytest.raises(RuleValidationError, match=re.escape("Rule S505 failed validation for these reasons:\n - Rule scala:S505 has invalid metadata in impacts: Additional properties are not allowed ('INVALID' was unexpected)")):
    validate_rule_metadata(s505)


def test_rule_with_invalid_impact_level(invalid_rules: RulesRepository):
  s506 = invalid_rules.get_rule('S506')
  with pytest.raises(RuleValidationError, match=re.escape("Rule S506 failed validation for these reasons:\n - Rule scala:S506 has invalid metadata in MAINTAINABILITY: 'INVALID' is not one of ['LOW', 'MEDIUM', 'HIGH']")):
    validate_rule_metadata(s506)


def test_rule_with_invalid_attribute(invalid_rules: RulesRepository):
  s507 = invalid_rules.get_rule('S507')
  with pytest.raises(RuleValidationError, match=re.escape("Rule S507 failed validation for these reasons:\n - Rule scala:S507 has invalid metadata in attribute: 'INVALID' is not one of ['FORMATTED', 'CONVENTIONAL', 'IDENTIFIABLE', 'CLEAR', 'LOGICAL', 'COMPLETE', 'EFFICIENT', 'FOCUSED', 'DISTINCT', 'MODULAR', 'TESTED', 'LAWFUL', 'TRUSTWORTHY', 'RESPECTFUL']")):
    validate_rule_metadata(s507)


def test_rule_with_unicode_in_metadata(invalid_rules: RulesRepository):
  s4225 = invalid_rules.get_rule('S4225')
  with pytest.raises(UnicodeDecodeError, match=fr'ascii'):
    validate_rule_metadata(s4225)

def test_rule_that_is_fully_valid(mockrules: Path):
  valid_rule = RulesRepository(rules_path=mockrules).get_rule('S120')
  validate_rule_metadata(valid_rule)


def test_missing_required_property_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  del invalid_metadata['title']
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_rule_specialization_metadata(rule_language)


def test_invalid_remediation_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  invalid_metadata['remediation']["func"] = 42
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_rule_specialization_metadata(rule_language)


def test_adding_properties_fails_validation(rule_language: LanguageSpecificRule):
  metadata = deepcopy(rule_language.metadata)
  metadata['unknown'] = 42
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = metadata
      validate_rule_specialization_metadata(rule_language)


def test_ready_rule_with_replacement_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  invalid_metadata['extra'] = { 'replacementRules': [ 'RSPEC-1234', 'RSPEC-5678' ]}
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata: status'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_rule_specialization_metadata(rule_language)


def test_deprecated_rule_with_replacement_passes_validation(rule_language: LanguageSpecificRule):
  metadata = deepcopy(rule_language.metadata)
  metadata['extra'] = { 'replacementRules': [ 'RSPEC-1234' ]}
  metadata['status'] = 'deprecated'
  with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
    mock.return_value = metadata
    validate_rule_specialization_metadata(rule_language)


def test_rule_with_incomplete_list_of_security_standard_fails_validation(rule_language: LanguageSpecificRule):
  invalid_metadata = deepcopy(rule_language.metadata)
  # "OWASP Top 10 2021", defined in the generic metadata is missing
  invalid_metadata['securityStandards'] = {'ASVS 4.0': [], 'OWASP': [], 'CERT': []}
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata: securityStandard'):
    with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_metadata
      validate_rule_specialization_metadata(rule_language)


def test_rule_with_complete_list_of_security_standard_passes_validation(rule_language: LanguageSpecificRule):
  metadata = deepcopy(rule_language.metadata)
  metadata['securityStandards'] = {'ASVS 4.0': [], 'OWASP': [], "OWASP Top 10 2021": []}
  with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
    mock.return_value = metadata
    validate_rule_specialization_metadata(rule_language)

def test_rule_with_invalid_format_for_security_standard_items_fails_validation(rule_language: LanguageSpecificRule):
  invalid_security_standards_items = {
    'OWASP': ['B1', 'AAA123', 'A0', ' A1', 'Not covered', ''],
    'OWASP Top 10 2021': ['B1', 'AAA123', 'A0',  ' A1', 'Not covered', ''],
    'OWASP Mobile': ['B1', 'MMM123', 'M0', ' M1', 'Not covered', ''],
    'PCI DSS 3.2': ['2.1.A', '2.1.1 ', 'Not covered', ''],
    'PCI DSS 4.0': ['2.1.A', '2.1.1 ', 'Not covered', ''],
    'CIS': ['2.1.A', '"2.1.1 ', 'Not covered', ''],
    'HIPAA': ['Not covered', ''],
    'CERT': ['MSC13-C', 'MSC13-C. ', 'Not covered', ''],
    'MASVS': ['MSTG-CRYPTO-A', 'MSTG-CRYPTO-6 ', 'Not covered', ''],
    'ASVS 4.0': ['A.1.2', ' 1.1.1', 'Not covered', '']
  }

  for security_standard in invalid_security_standards_items:
    for item in invalid_security_standards_items[security_standard]:
      invalid_metadata = deepcopy(rule_language.metadata)
      invalid_metadata['securityStandards'] = { security_standard: [item] }
      with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has invalid metadata in 0: \'{item}\' does not match'):
        with patch.object(LanguageSpecificRule, 'metadata', new_callable=PropertyMock) as mock:
          mock.return_value = invalid_metadata
          validate_rule_specialization_metadata(rule_language)
