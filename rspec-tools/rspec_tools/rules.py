
import json
from pathlib import Path
from typing import Final, Generator, Iterable, Optional
from bs4 import BeautifulSoup
from rspec_tools.errors import RuleNotFoundError


METADATA_FILE_NAME: Final[str] = 'metadata.json'
DESCRIPTION_FILE_NAME: Final[str] = 'rule.html'

class LanguageSpecificRule:
  language_path: Final[Path]
  rule: 'GenericRule'
  __metadata: Optional[dict] = None
  __description: Optional[object] = None

  def __init__(self, language_path: Path, rule: 'GenericRule'):
    self.language_path = language_path
    self.rule = rule

  @property
  def language(self):
    return self.language_path.name

  @property
  def id(self):
    return f'{self.language}:{self.rule.id}'

  @property
  def metadata(self):
    if self.__metadata is not None:
      return self.__metadata
    metadata_path = self.language_path.joinpath(METADATA_FILE_NAME)
    try:
      lang_metadata = json.loads(metadata_path.read_bytes())
    except:
      print('Failed to parse ', metadata_path)
      raise

    self.__metadata = self.rule.generic_metadata | lang_metadata
    return self.__metadata

  @property
  def description(self):
    if self.__description is not None:
      return self.__description
    description_path = self.language_path.joinpath(DESCRIPTION_FILE_NAME)
    soup = BeautifulSoup(description_path.read_bytes(),features="html.parser")
    self.__description = soup
    return self.__description

class GenericRule:
  rule_path: Final[Path]
  __generic_metadata: Optional[dict] = None

  def __init__(self, rule_path: Path):
    self.rule_path = rule_path

  @property
  def id(self) -> str:
    return self.rule_path.name

  @property
  def specializations(self) -> Generator[LanguageSpecificRule, None, None]:
    return (LanguageSpecificRule(child, self) for child in self.rule_path.iterdir() if child.is_dir())
  
  def get_language(self, language: str) -> LanguageSpecificRule:
    return LanguageSpecificRule(self.rule_path.joinpath(language), self)

  @property
  def generic_metadata(self):
    if self.__generic_metadata is not None:
      return self.__generic_metadata
    metadata_path = self.rule_path.joinpath(METADATA_FILE_NAME)
    self.__generic_metadata = json.loads(metadata_path.read_bytes())
    return self.__generic_metadata


class RulesRepository:
  DEFAULT_RULES_PATH: Final[Path] = Path(__file__).parent.parent.parent.joinpath('rules')

  rules_path: Final[Path]

  def __init__(self, rules_path: Path=DEFAULT_RULES_PATH):
    self.rules_path = rules_path

  @property
  def rules(self) -> Generator[GenericRule, None, None]:
    return (GenericRule(child) for child in self.rules_path.glob('S*') if child.is_dir())
    
  def get_rule(self, ruleid: str):
    rulepath = self.rules_path.joinpath(ruleid)
    if not rulepath.is_dir():
      raise RuleNotFoundError('Cannot find rule ' + ruleid + ' in ' + str(self.rules_path))
    return GenericRule(self.rules_path.joinpath(ruleid))
