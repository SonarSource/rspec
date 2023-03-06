from bs4 import BeautifulSoup
from pathlib import Path
from typing import Final
from collections import Counter

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule
from rspec_tools.utils import LANG_TO_SOURCE

import re

def read_file(path):
  SECTION_NAMES_PATH = Path(__file__).parent.parent.parent.parent.joinpath(path)
  return SECTION_NAMES_PATH.read_text(encoding='utf-8').split('\n')

def parse_names(path):
  SECTION_NAMES_FILE = read_file(path)
  return [s.replace('* ', '').strip() for s in SECTION_NAMES_FILE if s.strip()]

HOW_TO_FIX_IT = 'How to fix it'
HOW_TO_FIX_IT_REGEX = re.compile(HOW_TO_FIX_IT)

def parse_education_section_names(path):
  education_format_file = read_file(path)
  sections = set()
  optional_sections = set()
  how_to_fix_it_subsections = set()
  resources_subsections = set()
  is_in_how_to_fix = False
  is_in_resources = False
  for line in EDUCATION_FORMAT_FILE:
    if line.startswith('== '):
      section = line.replace('== ', '').strip()
      if section.endswith('(optional)'):
        section = section.replace(' (optional)', '')
        optional_sections.add(section)
      if not section.startswith(HOW_TO_FIX_IT):
        sections.add(section)
      if section.startswith(HOW_TO_FIX_IT):
        is_in_how_to_fix = True
      if section == 'Resources':
        is_in_how_to_fix = False
        is_in_resources = True
    if line.startswith('=== '):
      if is_in_how_to_fix:
        section = line.replace('=== ', '').strip()
        how_to_fix_it_subsections.add(section)
      if is_in_resources:
        section = line.replace('=== ', '').strip()
        resources_subsections.add(section)
  return [
    sections,
    optional_sections,
    how_to_fix_it_subsections,
    resources_subsections
  ]

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
ACCEPTED_ALL_SECTION_NAMES: Final[list[str]] = parse_names('docs/header_names/all_section_names.adoc')
# The list of all the framework names currently accepted by the script.
ACCEPTED_FRAMEWORK_NAMES: Final[list[str]] = parse_names('docs/header_names/allowed_framework_names.adoc')

[
  # all but the "how to fix it" ones which are dynamic
  ACCEPTED_EDUCATION_SECTION_NAMES,
  OPTIONAL_EDUCATION_SECTION_NAMES,
  ACCEPTED_HOW_TO_FIX_IT_SUBSECTIONS_NAMES,
  ACCEPTED_RESOURCES_SUBSECTION_NAMES
  ] = parse_education_section_names('docs/header_names/education_format_example.adoc')

def intersection(lst1, lst2):
  lst3 = [value for value in lst1 if value in lst2]
  return lst3
def difference(lst1, lst2):
  return list(set(lst1) - set(lst2))

def validate_section_names(rule_language: LanguageSpecificRule):
  """Validates all h2-level section names BUT "How to fix it..." ones
  """

  descr = rule_language.description
  h2_titles = list(map(lambda x: x.text.strip(), descr.find_all('h2')))

  education_titles = intersection(h2_titles, ACCEPTED_EDUCATION_SECTION_NAMES)
  if education_titles:
    # we're using the education format
    validate_how_to_fix_it_sections_names(rule_language, h2_titles)
    missing_titles = difference(ACCEPTED_EDUCATION_SECTION_NAMES, education_titles)
    if difference(missing_titles, OPTIONAL_EDUCATION_SECTION_NAMES):
      # when using the progressive education format, we need to have all its mandatory titles
      raise RuleValidationError(f'Rule {rule_language.id} is missing the "{missing_titles[0]}" section')
  for title in h2_titles:
    if title not in ACCEPTED_ALL_SECTION_NAMES and not HOW_TO_FIX_IT_REGEX.match(title):
      raise RuleValidationError(f'Rule {rule_language.id} has an unconventional header "{title}"')

def validate_how_to_fix_it_sections_names(rule_language: LanguageSpecificRule, h2_titles: list[str]):
  how_to_fix_it_sections = [ s for s in h2_titles if HOW_TO_FIX_IT_REGEX.match(s) ]
  if len(how_to_fix_it_sections) > 6:
    raise RuleValidationError(f'Rule {rule_language.id} has more than 6 "How to fix it" sections. Please ensure this limit can be increased with PM/UX teams')
  if not how_to_fix_it_sections:
    raise RuleValidationError(f'Rule {rule_language.id} is missing a "How to fix it" section')
  if f'{HOW_TO_FIX_IT}?' in how_to_fix_it_sections and len(how_to_fix_it_sections) > 1:
    raise RuleValidationError(f'Rule {rule_language.id} is mixing "{HOW_TO_FIX_IT}?" with "How to fix it in FRAMEWORK NAME" sections. Either use a single "How to fix it?" or one or more "How to fix it in FRAMEWORK"')
  framework_sections_seen = set()
  for section_name in how_to_fix_it_sections:
    validate_how_to_fix_it_framework(section_name, rule_language, framework_sections_seen)

def validate_how_to_fix_it_subsections(rule_language: LanguageSpecificRule):
  descr = rule_language.description

  how_to_fix_it_sections = descr.find_all('h2', string=HOW_TO_FIX_IT_REGEX)
  for section in how_to_fix_it_sections:
    section_name = section.text.strip()
    titles = collect_titles(section, 3)
    subsections_seen = set()
    for title in titles:
      name = title.text.strip()
      if name not in ACCEPTED_HOW_TO_FIX_IT_SUBSECTIONS_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has a subsection with an unallowed name in the "{section_name}" section: "{name}"')
      if name in subsections_seen:
        raise RuleValidationError(f'Rule {rule_language.id} has duplicate subsections in the "{section_name}" section. There are 2 occurences of "{name}"')
      subsections_seen.add(name)

def validate_how_to_fix_it_framework(section_name, rule_language, framework_sections_seen):
  result = re.search('How to fix it in (?:(?:an|a|the)\\s)?(.*)', section_name)
  if result is not None:
    current_framework = result.group(1)
    if current_framework not in ACCEPTED_FRAMEWORK_NAMES:
      raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" section for an unsupported framework: "{result.group(1)}"')
    if section_name in framework_sections_seen:
      raise RuleValidationError(f'Rule {rule_language.id} has duplicate "How to fix it" sections for the {current_framework} framework. There are 2 occurences of "{section_name}"')
    framework_sections_seen.add(section_name)
  elif section_name == 'How to fix it?':
    framework_sections_seen.add(section_name)
  else:
    raise RuleValidationError(f'Rule {rule_language.id} has a "How to fix it" section with an unsupported format: "{section_name}". Either use "How to fix it?" or "How to fix it in FRAMEWORK NAME"')

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

  current = node.next_sibling
  nodes = []
  while(current is not None):
    if hasattr(current, 'find_all'):
      nodes = nodes + current.find_all(f'h{level}')
    current = current.next_sibling
  return nodes

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
