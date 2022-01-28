import json
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Final

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
SECTION_NAMES_PATH = Path(__file__).parent.parent.parent.parent.joinpath('docs/section_names.adoc')
SECTION_NAMES_FILE = SECTION_NAMES_PATH.read_text(encoding='utf-8').split('\n')
ACCEPTED_SECTION_NAMES: Final[list[str]] = [s.replace('* ', '').strip() for s in SECTION_NAMES_FILE if s.strip()]
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

HIGHLIGHTED_LANGUAGES = {'cfamily': 'cpp',
                         'csharp': 'cs',
                         'css': 'css',
                         'go': 'go',
                         'java': 'java',
                         'javascript': 'javascript',
                         'kotlin': 'kotlin',
                         'php': 'php',
                         'plsql': 'sql',
                         'python': 'python',
                         'ruby': 'ruby',
                         'rust': 'rust',
                         'scala': 'scala',
                         'swift': 'swift',
                         'tsql': 'sql',
                         'xml': 'xml'
                         }

def validate_source_language(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  if rule_language.language in HIGHLIGHTED_LANGUAGES.keys():
    for h2 in descr.findAll('h2'):
      name = h2.text.strip()
      if name.startswith('Compliant') or name.startswith('Noncompliant'):
        pre = h2.parent.pre
        if not pre.has_attr('class') or pre['class'][0] != u'highlight':
          raise RuleValidationError(f'''Rule {rule_language.id} has non highlighted code example in section "{name}".
Use [source,{HIGHLIGHTED_LANGUAGES[rule_language.language]}] or [source,text] before the opening '----'.''')
