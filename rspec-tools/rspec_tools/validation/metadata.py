import json
from pathlib import Path
from typing import Optional, Final
from functools import cache

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule

DEFAULT_SCHEMA_PATH: Final[Path] = Path(__file__).parent.joinpath('rule-metadata-schema.json')

@cache
def get_json_schema():
  return json.loads(DEFAULT_SCHEMA_PATH.read_bytes())

def validate_metadata(rule_language: LanguageSpecificRule):
  validate_schema(rule_language)
  validate_status(rule_language)

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
    raise RuleValidationError(f'ERROR Rule {rule_language.id} has invalid metadata:' 
      f'status can\'t be "{status}" for a rule with the replacement rule(s)')

def has_replacement_rules(rule_language: LanguageSpecificRule):
  meta = rule_language.metadata
  return 'extra' in meta and 'replacementRules' in meta.get('extra') and len(meta.get('extra').get('replacementRules')) > 0

__all__=['validate_metadata']