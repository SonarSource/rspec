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
  schema = get_json_schema()
  try:
    validate(instance=rule_language.metadata, schema=schema)
  except ValidationError as e:
    path = f'in {e.path[-1]}' if e.path else ''
    raise RuleValidationError(f'Rule {rule_language.id} has invalid metadata {path}: {e.message}') from e


__all__=['validate_metadata']