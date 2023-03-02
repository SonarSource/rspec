from bs4 import BeautifulSoup
from pathlib import Path
from typing import Final

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule
from rspec_tools.utils import LANG_TO_SOURCE

import re

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
SECTION_NAMES_PATH = Path(__file__).parent.parent.parent.parent.joinpath('docs/section_names.adoc')
SECTION_NAMES_FILE = SECTION_NAMES_PATH.read_text(encoding='utf-8').split('\n')
ACCEPTED_SECTION_NAMES: Final[list[str]] = [s.replace('* ', '').strip() for s in SECTION_NAMES_FILE if s.strip()]
# The list of all the framework names currently accepted by the script.
FRAMEWORK_NAMES_PATH = Path(__file__).parent.parent.parent.parent.joinpath('docs/allowed_framework_names.adoc')
FRAMEWORK_NAMES_FILE = FRAMEWORK_NAMES_PATH.read_text(encoding='utf-8').split('\n')
ACCEPTED_FRAMEWORK_NAMES: Final[list[str]] = [s.replace('* ', '').strip() for s in FRAMEWORK_NAMES_FILE if s.strip()]

def validate_section_names(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  for h2 in descr.find_all('h2'):
    name = h2.text.strip()
    if name not in ACCEPTED_SECTION_NAMES:
      raise RuleValidationError(f'Rule {rule_language.id} has unconventional header "{name}"')

def validate_how_to_fix_it_subsections(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  frameworks_counter = 0

  for h3 in descr.find_all('h3'):
    name = h3.text.strip()
    # It is important that the Regex here matches the one used by the analyzers when loading the rules content
    result = re.search('How to fix it in (?:(?:an|a|the)\\s)?(.*)', name)
    if result is not None:
      if result.group(1) not in ACCEPTED_FRAMEWORK_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" section for an unsupported framework: "{result.group(1)}"')
      else:
        frameworks_counter += 1

  how_to_fix_it_section = descr.find('h2', string='How to fix it?')
  if how_to_fix_it_section is not None:
    if frameworks_counter == 0:
      raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" section but is missing subsections related to frameworks')
    if frameworks_counter > 6:
      raise RuleValidationError(f'Rule {rule_language.id} has more than 6 "How to fix it" subsections. Please ensure this limit can be increased with PM/UX teams')
  elif frameworks_counter > 0:
    raise RuleValidationError(f'Rule {rule_language.id} has "How to fix it" subsections for frameworks outside a defined "How to fix it?" section')

def validate_section_levels(rule_language: LanguageSpecificRule):
  h1 = rule_language.description.find('h1')
  if h1 is not None:
    name = h1.text.strip()
    raise RuleValidationError(f'Rule {rule_language.id} has level-0 header "{name}"')

def validate_one_parameter(child, id):
  if child.name != 'div' or child['class'][0] != 'sidebarblock':
    raise RuleValidationError(f'Rule {id} should use `****` blocks for each parameter')
  for div_child in child.children:
    if div_child.name is not None:
      if div_child['class'][0] != 'content':
        raise RuleValidationError(f'Rule {id} should use `****` blocks for each parameter')
      if div_child.p is None:
        raise RuleValidationError(f'Rule {id} should have a description for each parameter')
      if div_child.find('div', 'title') is None:
        raise RuleValidationError(f'Rule {id} should have a parameter name declared with `.name` before the bock, for each parameter')

def validate_parameters(rule_language: LanguageSpecificRule):
  for h3 in rule_language.description.find_all('h3'):
    name = h3.text.strip()
    if name == 'Parameters':
      for child in h3.parent.children:
        if child.name is None or child == h3 or child.name == 'hr':
          continue
        validate_one_parameter(child, rule_language.id)

def highlight_name(rule_language: LanguageSpecificRule):
  if (rule_language.language in LANG_TO_SOURCE):
    return LANG_TO_SOURCE[rule_language.language]
  return rule_language.language

def known_highlight(language):
  return language in LANG_TO_SOURCE.values()

def validate_source_language(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  for h2 in descr.findAll('h2'):
    name = h2.text.strip()
    if name.startswith('Compliant') or name.startswith('Noncompliant'):
      for pre in h2.parent.find_all('pre'):
        if not pre.has_attr('class') or pre['class'][0] != u'highlight' or not pre.code or not pre.code.has_attr('data-lang'):
          raise RuleValidationError(f'''Rule {rule_language.id} has non highlighted code example in section "{name}".
Use [source,{highlight_name(rule_language)}] or [source,text] before the opening '----'.''')
        elif not known_highlight(pre.code['data-lang']):
          raise RuleValidationError(f'''Rule {rule_language.id} has unknown language "{pre.code['data-lang']}" in code example in section "{name}".
Are you looking for "{highlight_name(rule_language)}"?''')
