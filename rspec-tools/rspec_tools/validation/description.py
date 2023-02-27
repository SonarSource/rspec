from bs4 import BeautifulSoup
from pathlib import Path
from typing import Final
from collections import Counter

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule
from rspec_tools.utils import LANG_TO_SOURCE

import re

def parse_names(path):
  SECTION_NAMES_PATH = Path(__file__).parent.parent.parent.parent.joinpath(path)
  SECTION_NAMES_FILE = SECTION_NAMES_PATH.read_text(encoding='utf-8').split('\n')
  return [s.replace('* ', '').strip() for s in SECTION_NAMES_FILE if s.strip()]

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
ACCEPTED_ALL_SECTION_NAMES: Final[list[str]] = parse_names('docs/all_section_names.adoc')
ACCEPTED_PROGRESSIVE_EDUCATION_SECTION_NAMES: Final[list[str]] = parse_names('docs/progressive_education_section_names.adoc')
# The list of all the framework names currently accepted by the script.
ACCEPTED_FRAMEWORK_NAMES: Final[list[str]] = parse_names('docs/allowed_framework_names.adoc')
# The list of all the "How to fix it?" subsection names accepted by the script.
ACCEPTED_HOW_TO_FIX_IT_SUBSECTIONS_NAMES: Final[list[str]] = parse_names('docs/how_to_fix_it_subsection_names.adoc')
# the list of all the "Resources" subsection names accepted by the script.
ACCEPTED_RESOURCES_SUBSECTION_NAMES: Final[list[str]] = parse_names('docs/resources_subsection_names.adoc')

def intersection(lst1, lst2):
  lst3 = [value for value in lst1 if value in lst2]
  return lst3
def difference(lst1, lst2):
  return list(set(lst1) - set(lst2))

def validate_section_names(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  h2_titles = list(map(lambda x: x.text.strip(), descr.find_all('h2')))

  progressive_education_titles = intersection(h2_titles, ACCEPTED_PROGRESSIVE_EDUCATION_SECTION_NAMES)
  if progressive_education_titles:
    # we're using the progressive education format
    missing_titles = difference(ACCEPTED_PROGRESSIVE_EDUCATION_SECTION_NAMES, progressive_education_titles)
    if missing_titles:
      # when using the progressive education format, we need to have all its titles
      raise RuleValidationError(f'Rule {rule_language.id} is missing the "{missing_titles[0]}" section')
  else:
    for title in h2_titles:
      if title not in ACCEPTED_ALL_SECTION_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has unconventional header "{title}"')

def validate_how_to_fix_it_subsections(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  frameworks_counter = 0

  how_to_fix_it_section = descr.find('h2', string='How to fix it?')
  if how_to_fix_it_section is not None:
    titles = collect_titles(how_to_fix_it_section, 3)
    frameworks_counter = validate_how_to_fix_it_subsections_titles(titles, rule_language)
    if frameworks_counter == 0:
      raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" section but is missing subsections related to frameworks')
    if frameworks_counter > 6:
      raise RuleValidationError(f'Rule {rule_language.id} has more than 6 "How to fix it" subsections. Please ensure this limit can be increased with PM/UX teams')

def validate_how_to_fix_it_subsections_titles(titles, rule_language):
  is_in_framework = False
  current_framework = ''
  frameworks_counter = 0
  framework_subsections_seen = set()
  for title in titles:
    name = title.text.strip()
    result = re.search('How to fix it in (?:(?:an|a|the)\\s)?(.*)', name)
    if result is not None:
      current_framework = result.group(1)
      if current_framework not in ACCEPTED_FRAMEWORK_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" section for an unsupported framework: "{result.group(1)}"')
      is_in_framework = True
      frameworks_counter += 1
      framework_subsections_seen = set()
    else:
      if not is_in_framework:
        raise RuleValidationError(f'Rule {rule_language.id} has subsections outside of a "How to fix it" section')
      if name not in ACCEPTED_HOW_TO_FIX_IT_SUBSECTIONS_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" subsection with an unallowed name for the ${current_framework} framework')
      if name in framework_subsections_seen:
        raise RuleValidationError(f'Rule {rule_language.id} has duplicate "How to fix it" subsections for the ${current_framework} framework. There are 2 occurences of "{name}"')
      framework_subsections_seen.add(name)
  return frameworks_counter

def collect_titles(node, level):
  """Collects all the titles of a given level starting from the provided node

  The goal of this function is to extract titles from the extra HTML tags
  that are produced when the HTML file is produced from the ASCIIdoc.
  The titles are collected in the order in which they appear.

  Args:
      node (BeautifulSoup): BeautifulSoup object
      level (int): the level of title we are looking for

  Returns:
      list[BeautifulSoup]: List of nodes that were found.
  """

  current = node
  nodes = []
  while(current is not None):
    dfs(nodes, current, level)
    current = current.next_sibling
  return nodes

def dfs(collector, node, level):
  if node.name == f'h{level}':
    collector.append(node)
  if hasattr(node, 'children'):
    for child in node.children:
      dfs(collector, child, level)

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

def validate_resources_subsections(rule_language: LanguageSpecificRule):
  descr = rule_language.description
  resources_section = descr.find('h2', string='Resources')
  if resources_section is not None:
    titles = collect_titles(resources_section, 3)
    subsections_seen = set()
    for title in titles:
      name = title.text.strip()
      if name not in ACCEPTED_RESOURCES_SUBSECTION_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has a "Resources" subsection with an unallowed name: "{name}"')
      if name in subsections_seen:
        raise RuleValidationError(f'Rule {rule_language.id} has duplicate "Resources" subsections. There are 2 occurences of "{name}"')
      subsections_seen.add(name)
