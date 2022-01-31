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
  for h2 in descr.findAll('h2'):
    name = h2.text.strip()
    if name not in ACCEPTED_SECTION_NAMES:
      raise RuleValidationError(f'Rule {rule_language.id} has unconventional header "{name}"')

def validate_section_levels(rule_language: LanguageSpecificRule):
  h1 = rule_language.description.find('h1')
  if h1 is not None:
    name = h1.text.strip()
    raise RuleValidationError(f'Rule {rule_language.id} has level-0 header "{name}"')
