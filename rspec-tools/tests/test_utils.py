from rspec_tools.errors import InvalidArgumentError
from rspec_tools.utils import parse_and_validate_language_list, load_valid_languages, get_mapped_languages, get_labels_for_languages
import pytest

def test_fails_when_no_languages_listed():
  '''Test that language validation fails on empty list.'''
  with pytest.raises(InvalidArgumentError):
      parse_and_validate_language_list('')
  with pytest.raises(InvalidArgumentError):
      parse_and_validate_language_list('     ')

def test_fails_for_non_language():
  '''Test that language validation fails on unexpected langauge.'''
  with pytest.raises(InvalidArgumentError):
    parse_and_validate_language_list('abracadabra')
  with pytest.raises(InvalidArgumentError):
    parse_and_validate_language_list('java,abra,cadabra')

def test_parses_the_language_list():
  lang_list = ['php', 'javascript', 'cfamily']
  lang_str = '  php,javascript, cfamily'
  assert parse_and_validate_language_list(lang_str) == lang_list

def test_valid_languages_contains_java():
  assert 'java' in load_valid_languages()

def test_valid_and_mapped_languages_equivalent():
  assert set(get_mapped_languages()) == set(load_valid_languages())

def test_labels_for_languages():
  lang_list = ['java', 'apex', 'cfamily', 'ruby']
  labels = ['java', 'slang', 'cfamily']
  assert set(get_labels_for_languages(lang_list)) == set(labels)
