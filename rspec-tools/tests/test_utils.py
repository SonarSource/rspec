from rspec_tools.errors import InvalidArgumentError
from rspec_tools.utils import parse_and_validate_language_list, load_valid_languages, get_mapped_languages, get_labels_for_languages, resolve_rule, validate_language, get_label_for_language
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

def test_resolve_rule():
  assert resolve_rule('S100') == 100
  assert resolve_rule('S1234') == 1234
  with pytest.raises(InvalidArgumentError):
    resolve_rule('S12')
  with pytest.raises(InvalidArgumentError):
    resolve_rule('12')
  with pytest.raises(InvalidArgumentError):
    resolve_rule('SS13')
  with pytest.raises(InvalidArgumentError):
    resolve_rule('RSPEC-1343')
  with pytest.raises(InvalidArgumentError):
    resolve_rule(' S1343 ')
  with pytest.raises(InvalidArgumentError):
    resolve_rule('SXXXX')
  with pytest.raises(InvalidArgumentError):
    resolve_rule('S90000')

def test_label_for_language():
  assert get_label_for_language('java') == 'java'

def test_validate_language():
  validate_language('java')
  with pytest.raises(InvalidArgumentError):
    validate_language('russian')
