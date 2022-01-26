import json
from bs4 import BeautifulSoup
from typing import Final

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
ACCEPTED_SECTION_NAMES: Final[list[str]] = ['Noncompliant Code Example',
                                            'Compliant Solution',
                                            'See',
                                            'See Also',
                                            'Exceptions',
                                            'Sensitive Code Example',
                                            'Ask Yourself Whether',
                                            'Recommended Secure Coding Practices',
                                            'Deprecated']

def validate_section_names(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  for h2 in descr.find_all('h2'):
    name = h2.text.strip()
    if name not in ACCEPTED_SECTION_NAMES:
      raise RuleValidationError(f'Rule {rule_language.id} has unconventional header "{name}"')

def validate_section_levels(rule_language: LanguageSpecificRule):
  h1 = rule_language.description.find('h1')
  if h1 is not None:
    name = h1.text.strip()
    raise RuleValidationError(f'Rule {rule_language.id} has level-0 header "{name}"')

def validate_one_parameter(child, id):
  if child.name != 'div' or child['class'][0] != 'dlist':
    raise RuleValidationError(f'Rule {id} should use labeled lists for parameters')
  for divChild in child.children:
    if divChild.name is not None:
      if divChild.name != 'dl':
        raise RuleValidationError(f'Rule {id} should use labeled lists for parameters')
      for param in divChild.children:
        if param.name == 'dt' and param.strong == None:
          raise RuleValidationError(f'Rule {id} should write parameter name {param.text} in bold')

def validate_parameters(rule_language: LanguageSpecificRule):
  for h3 in rule_language.description.find_all('h3'):
    name = h3.text.strip()
    if name == 'Parameters':
      for child in h3.parent.children:
        if child.name is None or child == h3 or child.name == 'hr':
          continue
        validate_one_parameter(child, rule_language.id)
