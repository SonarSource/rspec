import re
from pathlib import Path

import pytest
from rspec_tools.validation.sanitize_asciidoc import sanitize_asciidoc

def test_unbalanced_single_backquotes(mockinvalidasciidoc: Path):
  '''Check that we detect unbalanced single backquotes.'''
  path = mockinvalidasciidoc / 'unbalanced_single_backquotes.adoc'
  assert sanitize_asciidoc(path) == 1


def test_unbalanced_double_backquotes(mockinvalidasciidoc: Path):
  '''Check that we detect unbalanced double backquotes.'''
  path = mockinvalidasciidoc / 'unbalanced_double_backquotes.adoc'
  assert sanitize_asciidoc(path) == 1


def test_triple_backquote(mockinvalidasciidoc: Path):
  '''Check that we detect triple backquotes.'''
  path = mockinvalidasciidoc / 'triple_backquotes.adoc'
  assert sanitize_asciidoc(path) == 1


def test_unprotected_formatting(mockinvalidasciidoc: Path):
  '''Check that we detect unprotected formatting tags.'''
  path = mockinvalidasciidoc / 'unprotected_formatting.adoc'
  assert sanitize_asciidoc(path) == 4


def test_unprotected_formatting_with_plusses(mockinvalidasciidoc: Path):
  '''Check that we detect unprotected formatting tags even when there are plusses.'''
  path = mockinvalidasciidoc / 'unprotected_formatting_with_plusses.adoc'
  assert sanitize_asciidoc(path) == 1


def test_unclosed_ifdef(mockinvalidasciidoc: Path):
  '''Check that we detect unclosed ifdef'''
  path = mockinvalidasciidoc / 'unclosed_ifdef.adoc'
  assert sanitize_asciidoc(path) == 1


def test_close_unopened_ifdef(mockinvalidasciidoc: Path):
  '''Check that we detect calls to endif without a ifdef'''
  path = mockinvalidasciidoc / 'close_unopened_ifdef.adoc'
  assert sanitize_asciidoc(path) == 1


def test_two_ifdef(mockinvalidasciidoc: Path):
  '''Check that we detect too many ifdef'''
  path = mockinvalidasciidoc / 'two_ifdef.adoc'
  assert sanitize_asciidoc(path) == 1


def test_vscode_ifdef(mockinvalidasciidoc: Path):
  '''Check that we detect ifdef with VSCode flags'''
  path = mockinvalidasciidoc / 'vscode_ifdef.adoc'
  # We will get 2 errors:
  # * Don't use VS Code flags
  # * Wrong corresponding endif
  assert sanitize_asciidoc(path) == 2


def test_wrong_ifdef(mockinvalidasciidoc: Path):
  '''Check that we detect ifdef with invalid form'''
  path = mockinvalidasciidoc / 'wrong_ifdef.adoc'
  assert sanitize_asciidoc(path) == 1


def test_wrong_endif(mockinvalidasciidoc: Path):
  '''Check that we detect endif with invalid form'''
  path = mockinvalidasciidoc / 'wrong_endif.adoc'
  assert sanitize_asciidoc(path) == 1


def test_include_stuck_before(mockinvalidasciidoc: Path):
  '''Check that we detect when an include has no empty line before'''
  path = mockinvalidasciidoc / 'include_stuck_before.adoc'
  assert sanitize_asciidoc(path) == 1


def test_include_stuck_after(mockinvalidasciidoc: Path):
  '''Check that we detect when an include has no empty line after'''
  path = mockinvalidasciidoc / 'include_stuck_after.adoc'
  assert sanitize_asciidoc(path) == 1


def test_two_stuck_includes(mockinvalidasciidoc: Path):
  '''Check that we detect when two includes are stuck together'''
  path = mockinvalidasciidoc / 'two_stuck_includes.adoc'
  assert sanitize_asciidoc(path) == 1


def test_correctly_sanitized(mockasciidoc: Path):
  '''Check that we raise no issue on correctly sanitized asciidoc'''
  path = mockasciidoc / 'valid.adoc'
  assert sanitize_asciidoc(path) == 0
