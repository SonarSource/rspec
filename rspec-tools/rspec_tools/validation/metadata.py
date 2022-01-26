import json
from pathlib import Path
from typing import Final, List
from functools import cache

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import GenericRule, LanguageSpecificRule

DEFAULT_SCHEMA_PATH: Final[Path] = Path(__file__).parent.joinpath('rule-metadata-schema.json')

# Closed rules with no languages were imported when the migration from Jira was done.
# These rules are allowed to have no language specialization in order to keep them for posterity.
RULES_WITH_NO_LANGUAGES = [
  'S137',
  'S501',
  'S502',
  'S502',
  'S789',
  'S857',
  'S866',
  'S882',
  'S908',
  'S911',
  'S913',
  'S914',
  'S918',
  'S921',
  'S974',
  'S975',
  'S1076',
  'S1078',
  'S1127',
  'S1173',
  'S1212',
  'S1230',
  'S1294',
  'S1318',
  'S1513',
  'S1518',
  'S1519',
  'S1520',
  'S1521',
  'S1538',
  'S1646',
  'S1701',
  'S1724',
  'S1730',
  'S1746',
  'S1802',
  'S1815',
  'S1825',
  'S1826',
  'S1847',
  'S1873',
  'S1924',
  'S1925',
  'S1956',
  'S2098',
  'S2128',
  'S2192',
  'S2215',
  'S2336',
  'S2337',
  'S2338',
  'S2341',
  'S2371',
  'S2385',
  'S2732',
  'S2735',
  'S2736',
  'S2848',
  'S2916',
  'S2987',
  'S2988',
  'S2998',
  'S3223',
  'S3354',
  'S3746',
  'S4805',
]

@cache
def get_json_schema():
  return json.loads(DEFAULT_SCHEMA_PATH.read_bytes())

def validate_metadata(rule_language: LanguageSpecificRule):
  validate_schema(rule_language)
  validate_status(rule_language)
  validate_security_standards(rule_language)


def validate_rule_metadata(rule: GenericRule):
  '''In addition to the test carried out by validate_metadata for each language specification,
     a rule must have at least one language (unless it is part of the list of exception).
  '''
  specializations = list(rule.specializations)
  if rule.id in RULES_WITH_NO_LANGUAGES:
    if specializations:
      # When this triggers, ask yourself whether the rule should be removed from RULES_WITH_NO_LANGUAGES
      raise RuleValidationError(f'Rule {rule.id} should have no specializations')

    if rule.generic_metadata.get('status', None) not in ['closed', 'deprecated']:
      raise RuleValidationError(f'Rule {rule.id} should be closed or deprecated')

    # Nothing else to do.
    return

  if not specializations:
    raise RuleValidationError(f'Rule {rule.id} has no language-specific data')

  errors: List[str] = []
  for language_rule in specializations:
    try:
      validate_metadata(language_rule)
    except RuleValidationError as e:
      errors.append(str(e))

  if errors:
    raise RuleValidationError(f'Rule {rule.id} failed validation for these reasons:\n - ' + '\n - '.join(errors))


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