from rspec_tools.errors import InvalidArgumentError
from pathlib import Path
from typing import List
import shutil
import re
import tempfile
import json
import contextlib
import os

SUPPORTED_LANGUAGES_FILENAME = '../supported_languages.adoc'
LANG_TO_LABEL = {'abap': 'abap',
                 'apex': 'slang',
                 'cfamily': 'cfamily',
                 'cobol': 'cobol',
                 'csharp': 'dotnet',
                 'css': 'css',
                 'flex': 'flex',
                 'go': 'slang',
                 'html': 'html',
                 'java': 'java',
                 'javascript': 'jsts',
                 'kotlin': 'kotlin',
                 'php': 'php',
                 'pli': 'pli',
                 'plsql': 'plsql',
                 'python': 'python',
                 'rpg': 'rpg',
                 'ruby': 'slang',
                 'rust': 'rust',
                 'scala': 'slang',
                 'secrets': 'secrets',
                 'solidity': 'solidity',
                 'swift': 'swift',
                 'text': 'text',
                 'tsql': 'tsql',
                 'vb6': 'vb6',
                 'vbnet': 'dotnet',
                 'cloudformation': 'iac',
                 'terraform': 'iac',
                 'xml': 'xml',
}

LANG_TO_SOURCE = {
    # languages with syntax coloring in highlight.js
    'abap': 'abap',
    'cfamily': 'cpp',
    'csharp': 'csharp',
    'css': 'css',
    'go': 'go',
    'html': 'html',
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
    'terraform': 'terraform',
    'tsql': 'sql',
    'vbnet': 'vbnet',
    'xml': 'xml',
    'c': 'c',
    'objectivec': 'objectivec',
    'vb': 'vb',
    # these languages are not supported by highlight.js as the moment:
    'apex': 'apex',
    'cloudformation': 'cloudformation',
    'cobol': 'cobol',
    'flex': 'flex',
    'pli': 'pli',
    'rpg': 'rpg',
    'text': 'text',
    'vb6': 'vb6'
}

METADATA_FILE = 'metadata.json'

def copy_directory_content(src:Path, dest:Path):
  for item in src.iterdir():
    if (item.is_dir()):
      shutil.copytree(item, dest)
    else:
      shutil.copy2(item, dest)

def swap_metadata_files(dir1:Path, dir2:Path):
  meta1 = dir1.joinpath(METADATA_FILE)
  meta2 = dir2.joinpath(METADATA_FILE)
  with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir).joinpath(METADATA_FILE)
    shutil.copy2(meta1, tmp)
    shutil.copy2(meta2, meta1)
    shutil.copy2(tmp, meta2)

def is_empty_metadata(rule_dir:Path):
  with open(rule_dir.joinpath(METADATA_FILE), 'r') as meta:
    return not json.load(meta)

def load_valid_languages():
  with open(SUPPORTED_LANGUAGES_FILENAME, 'r') as supported_langs_file:
    supported_langs = supported_langs_file.read()
    supported_langs = supported_langs.replace(' or', '')
    supported_langs = supported_langs.replace('`', '')
    supported_langs = supported_langs.replace(' ', '')
    supported_langs = supported_langs.replace('\n', '')
    return supported_langs.split(',')

def get_mapped_languages():
  '''Get all the languages we have a label for.
  Necessary to make sure all valid languages are mapped (see test_utils.py).'''
  return LANG_TO_LABEL.keys();

def _validate_languages(languages: List[str]):
  valid_langs = load_valid_languages()
  for lang in languages:
    if lang not in valid_langs:
      raise InvalidArgumentError(f"Unsupported language: \"{lang}\". See {SUPPORTED_LANGUAGES_FILENAME} for the list of supported languages.")

def parse_and_validate_language_list(languages):
  lang_list = [lang.strip() for lang in languages.split(',')]
  if len(languages.strip()) == 0 or len(lang_list) == 0:
    raise InvalidArgumentError('Invalid argument for "languages". At least one language should be provided.')
  _validate_languages(lang_list)
  return lang_list

def validate_language(language):
  _validate_languages([language])

def get_labels_for_languages(lang_list):
  labels = [LANG_TO_LABEL[lang] for lang in lang_list]
  return list(set(labels))

def get_label_for_language(language: str) -> str:
  return LANG_TO_LABEL[language]

def resolve_rule(rule_id: str) -> int:
  m = re.search('^S([0-9]{3,4})$', rule_id)
  if not m:
    raise InvalidArgumentError(f"Unrecognized rule id format: \"{rule_id}\". Rule id must start with an \"S\" followed by 3 or 4 digits.")
  else:
    return int(m.group(1))

def load_json(file):
  with open(file) as json_file:
    return json.load(json_file)

@contextlib.contextmanager
def pushd(new_dir):
  previous_dir = os.getcwd()
  os.chdir(new_dir)
  try:
    yield
  finally:
    os.chdir(previous_dir)
