
import json
from pathlib import Path
from typing import Final, Generator, Iterable, Optional


METADATA_FILE_NAME: Final[str] = 'metadata.json'

class RuleLanguage:
  language_path: Final[Path]
  rule: 'Rule'
  __metadata: Optional[dict] = None

  def __init__(self, language_path: Path, rule: 'Rule'):
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
    lang_metadata = json.loads(metadata_path.read_bytes())
    self.__metadata = self.rule.generic_metadata | lang_metadata
    return self.__metadata


class Rule:
  rule_path: Final[Path]
  __generic_metadata: Optional[dict] = None

  def __init__(self, rule_path: Path):
    self.rule_path = rule_path

  @property
  def id(self) -> str:
    return self.rule_path.name

  @property
  def languages(self) -> Generator[RuleLanguage, None, None]:
    return (RuleLanguage(child, self) for child in self.rule_path.iterdir() if child.is_dir())
  
  def get_language(self, language: str) -> RuleLanguage:
    return RuleLanguage(self.rule_path.joinpath(language), self)

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

  def __init__(self, *, rules_path: Path=DEFAULT_RULES_PATH):
    print(rules_path.absolute().__str__())
    self.rules_path = rules_path

  @property
  def rules(self) -> Generator[Rule, None, None]:
    return (Rule(child) for child in self.rules_path.glob('S*') if child.is_dir())
    
  def get_rule(self, ruleid: str):
    return Rule(self.rules_path.joinpath(ruleid))