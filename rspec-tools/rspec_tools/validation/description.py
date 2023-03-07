from bs4 import BeautifulSoup
from pathlib import Path
from typing import Final
from collections import Counter

from rspec_tools.errors import RuleValidationError
from rspec_tools.rules import LanguageSpecificRule
from rspec_tools.utils import LANG_TO_SOURCE

import re

def read_file(path):
  section_names_path = Path(__file__).parent.parent.parent.parent.joinpath(path)
  return section_names_path.read_text(encoding='utf-8').split('\n')

def parse_names(path):
  section_names_path = read_file(path)
  return [s.replace('* ', '').strip() for s in section_names_path if s.strip()]

HOW_TO_FIX_IT = 'How to fix it'
HOW_TO_FIX_IT_REGEX = re.compile(HOW_TO_FIX_IT)

def parse_education_section_names(path):
  education_format_file = read_file(path)
  sections = {}
  optional_sections = {}
  current_map = sections
  current_section_name = ''
  subsections = {}
  current_subsection_name = ''
  for line in education_format_file:
    if line.startswith('== '):
      section = line.replace('== ', '').strip()
      if section.endswith('(optional)'):
        section = section.replace(' (optional)', '')
        current_map = optional_sections
      else:
        current_map = sections
      if section.startswith(HOW_TO_FIX_IT):
        # we store "How to fix it" and "How to fix it in ..." together
        section = HOW_TO_FIX_IT
      else:
        if section in current_map:
          raise RuleValidationError(f'Section {section} is mentionned more than once in the specification file')
      current_section_name = section
      current_map[section] = set()
    if line.startswith('=== '):
      subsection = line.replace('=== ', '').strip()
      current_map[current_section_name].add(subsection)
      current_subsection_name = subsection
    if line.startswith('==== '):
      sub_subsection_name = line.replace('=== ', '').strip()
      if current_subsection_name not in subsections:
        subsections[current_subsection_name] = set()
      subsections[current_subsection_name].add(sub_subsection_name)
  return [
    sections,
    optional_sections,
    subsections,
  ]

# The list of all the sections currently accepted by the script.
# The list includes multiple variants for each title because they all occur
# in the migrated RSPECs.
# Further work required to shorten the list by renaming the sections in some RSPECS
# to keep only on version for each title.
LEGACY_SECTION_NAMES: Final[list[str]] = parse_names('docs/header_names/legacy_section_names.adoc')
# The list of all the framework names currently accepted by the script.
ACCEPTED_FRAMEWORK_NAMES: Final[list[str]] = parse_names('docs/header_names/allowed_framework_names.adoc')

[
  SECTIONS,
  OPTIONAL_SECTIONS,
  SUBSECTIONS,
  ] = parse_education_section_names('docs/header_names/education_format_names.adoc')



def intersection(lst1, lst2):
  return list(set(lst1).intersection(lst2))
def difference(lst1, lst2):
  return list(set(lst1) - set(lst2))

def validate_section_names(rule_language: LanguageSpecificRule):
  """Validates all h2-level section names"""

  descr = rule_language.description
  h2_titles = list(map(lambda x: x.text.strip(), descr.find_all('h2')))

  education_titles = intersection(h2_titles, list(SECTIONS.keys()) + list(OPTIONAL_SECTIONS.keys()))
  if education_titles:
    # we're using the education format
    validate_how_to_fix_it_sections_names(rule_language, h2_titles)
    missing_titles = difference(list(SECTIONS.keys()), education_titles)
    # we handled "how to fix it" sections above
    missing_titles_without_how_to_fix_its = [ s for s in missing_titles if not HOW_TO_FIX_IT_REGEX.match(s)]
    if missing_titles_without_how_to_fix_its:
      # when using the progressive education format, we need to have all its mandatory titles
      raise RuleValidationError(f'Rule {rule_language.id} is missing the "{missing_titles_without_how_to_fix_its[0]}" section')
  else:
    # we're using the legacy format
    for title in h2_titles:
      if title not in LEGACY_SECTION_NAMES:
        raise RuleValidationError(f'Rule {rule_language.id} has an unconventional header "{title}"')

def validate_how_to_fix_it_sections_names(rule_language: LanguageSpecificRule, h2_titles: list[str]):
  how_to_fix_it_sections = [ s for s in h2_titles if HOW_TO_FIX_IT_REGEX.match(s) ]
  if len(how_to_fix_it_sections) > 6:
    raise RuleValidationError(f'Rule {rule_language.id} has more than 6 "{HOW_TO_FIX_IT}" sections. Please ensure this limit can be increased with PM/UX teams')
  if not how_to_fix_it_sections:
    raise RuleValidationError(f'Rule {rule_language.id} is missing a "{HOW_TO_FIX_IT}" section')
  if HOW_TO_FIX_IT in how_to_fix_it_sections and len(how_to_fix_it_sections) > 1:
    raise RuleValidationError(f'Rule {rule_language.id} is mixing "{HOW_TO_FIX_IT}" with "How to fix it in FRAMEWORK NAME" sections. Either use a single "{HOW_TO_FIX_IT}" or one or more "How to fix it in FRAMEWORK"')
  duplicate_names = [x for x in how_to_fix_it_sections if how_to_fix_it_sections.count(x) > 1] # O(n*n) is fine, given n <= 6
  if 0 < len(duplicate_names):
    raise RuleValidationError(f'Rule {rule_language.id} has duplicate "{HOW_TO_FIX_IT}" sections {set(duplicate_names)}')
  for section_name in how_to_fix_it_sections:
    validate_how_to_fix_it_framework(section_name, rule_language)

def validate_how_to_fix_it_framework(section_name, rule_language):
  result = re.search('How to fix it in (?:(?:an|a|the)\\s)?(.*)', section_name)
  if result is not None:
    current_framework = result.group(1)
    if current_framework not in ACCEPTED_FRAMEWORK_NAMES:
      raise RuleValidationError(f'Rule {rule_language.id} has a "{HOW_TO_FIX_IT}" section for an unsupported framework: "{result.group(1)}"')
  elif section_name != HOW_TO_FIX_IT:
    raise RuleValidationError(f'Rule {rule_language.id} has a "{HOW_TO_FIX_IT}" section with an unsupported format: "{section_name}". Either use "{HOW_TO_FIX_IT}" or "How to fix it in FRAMEWORK NAME"')

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

def validate_subsections(rule_language: LanguageSpecificRule):
  for optional_section in list(OPTIONAL_SECTIONS.keys()):
    validate_subsections_for_section(rule_language, optional_section, OPTIONAL_SECTIONS[optional_section])
  for mandatory_section in list(SECTIONS.keys()):
    if mandatory_section == HOW_TO_FIX_IT:
      validate_subsections_for_section(rule_language, mandatory_section, SECTIONS[mandatory_section], 3, HOW_TO_FIX_IT_REGEX)
    else:
      validate_subsections_for_section(rule_language, mandatory_section, SECTIONS[mandatory_section])
  for subsection_with_sub_subsection in list(SUBSECTIONS.keys()):
    validate_subsections_for_section(rule_language, subsection_with_sub_subsection, SUBSECTIONS[subsection_with_sub_subsection], 4)

def validate_subsections_for_section(rule_language: LanguageSpecificRule, section_name: str, allowed_subsections: set[str], level = 3, section_regex = None):
  if not section_regex:
    section_regex = section_name
  descr = rule_language.description
  top_level_section = descr.find(f'h{level-1}', string=section_regex)
  if top_level_section is not None:
    titles = collect_titles(top_level_section, level)
    subsections_seen = set()
    for title in titles:
      name = title.text.strip()
      if name not in allowed_subsections:
        raise RuleValidationError(f'Rule {rule_language.id} has a "{section_name}" subsection with an unallowed name: "{name}"')
      if name in subsections_seen:
        raise RuleValidationError(f'Rule {rule_language.id} has duplicate "{section_name}" subsections. There are 2 occurences of "{name}"')
      subsections_seen.add(name)
