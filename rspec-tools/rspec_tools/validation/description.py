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
                                            'Noncompliant Code Example.',
                                            'Noncompliant Code Example:',
                                            'Noncompliant Code Examples',
                                            'NonCompliant Code Example',
                                            'Compliant Solution',
                                            'Compliant Solutions',
                                            'Compliant solution',
                                            'Compliant Solution:',
                                            'Compliant Example',
                                            'Compliant Code Example',
                                            'Compliant',
                                            'See',
                                            'See:',
                                            'See also',
                                            'See Also',
                                            'Exceptions',
                                            'Sensitive Code Example',
                                            'Sensitive Code Examples',
                                            'Ask Yourself Whether',
                                            'Recommended Secure Coding Practices',
                                            'Deprecated']

def validate_section_names(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  for h2 in descr.findAll('h2'):
    name = h2.text.strip()
    if name not in ACCEPTED_SECTION_NAMES:
      raise RuleValidationError(f'Rule {rule_language.id} has unconventional header "{name}"')

__all__=['validate_metadata']
