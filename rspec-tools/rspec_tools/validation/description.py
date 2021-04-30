import json
from bs4 import BeautifulSoup
from typing import Final

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule

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
