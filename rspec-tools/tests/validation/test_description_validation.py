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

def test_valid_sections_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that description with standard sections is considered valid.'''
  validate_section_names(rule_language)

def test_unexpected_section_fails_validation(rule_language: LanguageSpecificRule):
  '''Check that unconventional section header breaks validation.'''
  invalid_description = deepcopy(rule_language.description)
  invalid_header = invalid_description.new_tag('h2')
  invalid_header.string = 'Invalid header'
  invalid_description.body.insert(1, invalid_header)
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has unconventional header "Invalid header"'):
    with patch.object(LanguageSpecificRule, 'description', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_description
      validate_section_names(rule_language)

def test_valid_section_levels_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that description with correct formatting is considered valid.'''
  validate_section_levels(rule_language)

def test_level_0_section_fails_validation(rule_language: LanguageSpecificRule):
  '''Check that level-0 section header breaks validation.'''
  invalid_description = deepcopy(rule_language.description)
  invalid_header = invalid_description.new_tag('h1')
  invalid_header.string = 'Invalid header level'
  invalid_description.body.insert(1, invalid_header)
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} has level-0 header "Invalid header level"'):
    with patch.object(LanguageSpecificRule, 'description', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_description
      validate_section_levels(rule_language)

def test_parameters_passes_validation(rule_language: LanguageSpecificRule):
  '''Check that correctly formed parameters are considered valid.'''
  validate_parameters(rule_language)

def test_parameters_fails_validation_on_list(rule_language: LanguageSpecificRule):
  '''Check that description with unexpected tag breaks validation.'''
  invalid_description = deepcopy(rule_language.description)
  invalid_param = invalid_description.new_tag('p')
  for h3 in invalid_description.find_all('h3'):
    name = h3.text.strip()
    if name == 'Parameters':
      h3.parent.insert(2, invalid_param)
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule_language.id} should use labeled lists for parameters'):
    with patch.object(LanguageSpecificRule, 'description', new_callable=PropertyMock) as mock:
      mock.return_value = invalid_description
      validate_parameters(rule_language)

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
