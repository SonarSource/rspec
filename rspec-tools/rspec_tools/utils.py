from rspec_tools.errors import InvalidArgumentError
from pathlib import Path
import shutil

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
                 'solidity': 'solidity',
                 'swift': 'swift',
                 'tsql': 'tsql',
                 'vb6': 'vb6',
                 'vbnet': 'dotnet',
                 'cloudformation': 'iac',
                 'terraform': 'iac',
                 'xml': 'xml',
}

def copy_directory_content(src:Path, dest:Path):
  for item in src.iterdir():
    if (item.is_dir()):
      shutil.copytree(item, dest)
    else:
      shutil.copy2(item, dest)

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

def parse_and_validate_language_list(languages):
  lang_list = [lang.strip() for lang in languages.split(',')]
  if len(languages.strip()) == 0 or len(lang_list) == 0:
    raise InvalidArgumentError('Invalid argument for "languages". At least one language should be provided.')
  valid_langs = load_valid_languages()
  for lang in lang_list:
    if lang not in valid_langs:
      raise InvalidArgumentError(f"Unsupported language: \"{lang}\". See {SUPPORTED_LANGUAGES_FILENAME} for the list of supported languages.")
  return lang_list

def get_labels_for_languages(lang_list):
  labels = [LANG_TO_LABEL[lang] for lang in lang_list]
  return list(set(labels))

