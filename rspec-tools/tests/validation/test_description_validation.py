from pathlib import Path

from unittest.mock import patch, PropertyMock
import pytest
import re
from rspec_tools.errors import RuleValidationError
from copy import deepcopy

from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.description import validate_section_names, validate_section_levels, validate_parameters

@pytest.fixture
def rule_language(mockrules: Path):
  rule = RulesRepository(rules_path=mockrules).get_rule('S100')
  return rule.get_language('cfamily')

@pytest.fixture
def invalid_rule(mockinvalidrules: Path):
  rule = RulesRepository(rules_path=mockinvalidrules).get_rule('S100')
  return rule.get_language('cfamily')

def test_valid_sections_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that description with standard sections is considered valid.'''
  validate_section_names(rule_language)

def test_unexpected_section_fails_validation(invalid_rule: LanguageSpecificRule):
  with pytest.raises(RuleValidationError, match=fr'^Rule {invalid_rule.id} has unconventional header "Invalid header"'):
    validate_section_names(invalid_rule)

def test_valid_section_levels_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that description with correct formatting is considered valid.'''
  validate_section_levels(rule_language)

def test_level_0_section_fails_validation(invalid_rule: LanguageSpecificRule):
  with pytest.raises(RuleValidationError, match=fr'^Rule {invalid_rule.id} has level-0 header "Invalid header level"'):
    validate_section_levels(invalid_rule)

def test_parameters_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that correctly formed parameters are considered valid.'''
  validate_parameters(rule_language)

def test_parameters_fails_validation_on_list(invalid_rule: LanguageSpecificRule):
  '''Check that description with unexpected tag breaks validation.'''
  with pytest.raises(RuleValidationError, match=fr'^Rule {invalid_rule.id} should use labeled lists for parameters'):
    validate_parameters(invalid_rule)

def test_parameters_fails_validation_on_font(rule_language: LanguageSpecificRule):
  '''Check that description with key not bold breaks validation.'''
  invalid_description = deepcopy(rule_language.description)
  for h3 in invalid_description.find_all('h3'):
    name = h3.text.strip()
    if name == 'Parameters':
      label = h3.parent.strong.parent
      h3.parent.strong.extract()
      label.insert(0, 'format')
      param_desc = re.escape(label.text)
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} should write parameter name {param_desc} in bold'):
    with patch.object(LanguageSpecificRule, 'description', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_description
      validate_parameters(rule_language)
