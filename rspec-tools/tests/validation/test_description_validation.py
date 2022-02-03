from pathlib import Path

from unittest.mock import patch, PropertyMock
import pytest
import re
from rspec_tools.errors import RuleValidationError
from copy import deepcopy

from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.description import validate_section_names, validate_section_levels, validate_parameters, validate_source_language

@pytest.fixture
def rule_language(mockrules: Path):
  def _rule_language(rule_id, language):
    rule = RulesRepository(rules_path=mockrules).get_rule(rule_id)
    return rule.get_language(language)
  return _rule_language

@pytest.fixture
def invalid_rule(mockinvalidrules: Path):
  def _invalid_rule(rule_id, language):
    rule = RulesRepository(rules_path=mockinvalidrules).get_rule(rule_id)
    return rule.get_language(language)
  return _invalid_rule

def test_valid_sections_passes_validation(rule_language):
  '''Check that description with standard sections is considered valid.'''
  validate_section_names(rule_language('S100', 'cfamily'))

def test_unexpected_section_fails_validation(invalid_rule):
  rule = invalid_rule('S100', 'cfamily')
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule.id} has unconventional header "Invalid header"'):
    validate_section_names(rule)

def test_valid_section_levels_passes_validation(rule_language):
  '''Check that description with correct formatting is considered valid.'''
  validate_section_levels(rule_language('S100', 'cfamily'))

def test_level_0_section_fails_validation(invalid_rule):
  rule = invalid_rule('S100', 'cfamily')
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule.id} has level-0 header "Invalid header level"'):
    validate_section_levels(rule)

def test_parameters_passes_validation(rule_language):
  '''Check that correctly formed parameters are considered valid.'''
  validate_parameters(rule_language('S100', 'cfamily'))

def test_parameters_fails_validation_missing_block(invalid_rule):
  '''Check that description with unexpected tag breaks validation.'''
  rule = invalid_rule('S100', 'cfamily')
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule.id} should use `\*\*\*\*` blocks for each parameter'):
    validate_parameters(rule)

def test_parameters_fails_validation_missing_title(invalid_rule):
  rule = invalid_rule('S100', 'csharp')
  '''Check that parameters without key as title breaks validation.'''
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule.id} should have a parameter name declared with `.name` before the bock, for each parameter'):
    validate_parameters(rule)

def test_parameters_fails_validation_missing_description(invalid_rule):
  rule = invalid_rule('S100', 'java')
  '''Check that parameters without any description break validation.'''
  with pytest.raises(RuleValidationError, match=fr'^Rule {rule.id} should have a description for each parameter'):
    validate_parameters(rule)

def test_valid_source_declaration_validation(rule_language):
  '''Check that declaring a language for sources is considered valid.'''
  # cpp and text
  validate_source_language(rule_language('S100', 'cfamily'))
  # javascript and no source
  validate_source_language(rule_language('S100', 'csharp'))

def test_missing_source_language_fails_validation(invalid_rule):
  '''Check that forgetting the language for sources breaks validation'''
  rule = invalid_rule('S100', 'cfamily')
  with pytest.raises(RuleValidationError, match=re.escape(f'Rule {rule.id} has non highlighted code example in section "Noncompliant Code Example".\nUse [source,cpp] or [source,text] before the opening \'----\'.')):
    validate_source_language(rule)

def test_wrong_source_language_fails_validation(invalid_rule):
  '''Check that forgetting the language for sources breaks validation'''
  rule = invalid_rule('S100', 'csharp')
  with pytest.raises(RuleValidationError, match=re.escape(f'Rule {rule.id} has unknown language "csharp" in code example in section "Noncompliant Code Example".\nAre you looking for "cs"?')):
    validate_source_language(rule)
