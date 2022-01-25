import json
from pathlib import Path
from typing import Optional, Final
from functools import cache

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import GenericRule, LanguageSpecificRule

DEFAULT_SCHEMA_PATH: Final[Path] = Path(__file__).parent.joinpath('rule-metadata-schema.json')

@cache
def get_json_schema():
  return json.loads(DEFAULT_SCHEMA_PATH.read_bytes())

def validate_metadata(rule_language: LanguageSpecificRule):
  validate_schema(rule_language)
  validate_status(rule_language)
  validate_security_standards(rule_language)

def validate_metadata_of_modified_rule(rule: GenericRule):
  '''In addition to the test carried out by validate_metadata, a modified rule:
     - must have at least one language
  '''
  specializations = list(rule.specializations)
  if len(specializations) == 0:
    raise RuleValidationError(f'Rule {rule.id} has no language-specific data')

  for language_rule in specializations:
    validate_metadata(language_rule)

def validate_schema(rule_language: LanguageSpecificRule):
  schema = get_json_schema()
  try:
    validate(instance=rule_language.metadata, schema=schema)
  except ValidationError as e:
    path = f'in {e.path[-1]}' if e.path else ''
    raise RuleValidationError(f'Rule {rule_language.id} has invalid metadata {path}: {e.message}') from e

def validate_status(rule_language: LanguageSpecificRule):
  status = rule_language.metadata.get('status')
  if has_replacement_rules(rule_language) and status in ["beta", "ready"]:
    raise RuleValidationError(f'Rule {rule_language.id} has invalid metadata:'
      f' status can\'t be "{status}" for a rule with replacement rule(s)')


def validate_security_standards(rule_language: LanguageSpecificRule):
  rule = rule_language.rule
  if 'securityStandards' in rule.generic_metadata.keys() and 'securityStandards' in rule_language.metadata:
    missing_standards = []
    rule_language_standards = rule_language.metadata['securityStandards']
    for standard in rule.generic_metadata['securityStandards'].keys():
      if standard not in rule_language_standards:
        missing_standards.append(standard)
    
    if len(missing_standards) > 0:
      raise RuleValidationError(f'Rule {rule_language.id} has invalid metadata:'
        f' securityStandard should contain {missing_standards}')
      



def has_replacement_rules(rule_language: LanguageSpecificRule):
  meta = rule_language.metadata
  return 'extra' in meta and 'replacementRules' in meta.get('extra') and len(meta.get('extra').get('replacementRules')) > 0

__all__=['validate_metadata']