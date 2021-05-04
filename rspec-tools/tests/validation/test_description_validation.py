from pathlib import Path

from unittest.mock import patch, PropertyMock
import pytest
from rspec_tools.errors import RuleValidationError
from copy import deepcopy

from rspec_tools.rules import LanguageSpecificRule, RulesRepository
from rspec_tools.validation.description import validate_section_names

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
