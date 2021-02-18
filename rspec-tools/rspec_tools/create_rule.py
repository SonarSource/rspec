from git import Repo
from github import Github
from github.PullRequest import PullRequest
from pathlib import Path
from typing import Final, Iterable, Optional
from contextlib import contextmanager

from rspec_tools.utils import copy_directory_content

def build_github_repository_url(token):
  'Builds the rspec repository url'
  return f'https://{token}@github.com/SonarSource/rspec.git'

def extract_repository_name(url):
  url_end = url.split('/')[-2:]
  return '/'.join(url_end).removesuffix('.git')

class RuleCreator:
  ''' Create a new Rule in a repository following the official Github 'rspec' repository structure.'''
  MASTER_BRANCH: Final[str] = 'master'
  ID_COUNTER_BRANCH: Final[str] = 'rspec-id-counter'
  ID_COUNTER_FILENAME: Final[str] = 'next_rspec_id.txt'
  TEMPLATE_PATH: Final[Path] = Path(__file__).parent.parent.joinpath('rspec_template')

  repository: Final[Repo]
  origin_url: Final[str]

  def __init__(self, repository_url: str, clone_directory: str, configuration: dict[str, str]):
    self.repository = Repo.clone_from(repository_url, clone_directory)
    self.origin_url = repository_url

    # create local branches tracking remote ones
    for branch in [self.MASTER_BRANCH, self.ID_COUNTER_BRANCH]:
      self.repository.remote().fetch(branch)
      self.repository.git.checkout('-B', branch, f'origin/{branch}')

    # update repository config
    with self.repository.config_writer() as config_writer:
      for key, value in configuration.items():
        split_key = key.split('.')
        config_writer.set_value(*split_key, value)
    

  def reserve_rule_number(self) -> int:
    '''Reserve an id on the id counter branch of the repository.'''
    with self._current_git_branch(self.ID_COUNTER_BRANCH):
      counter_file_path = Path(self.repository.working_dir).joinpath(self.ID_COUNTER_FILENAME)
      counter = int(counter_file_path.read_text())
      counter_file_path.write_text(str(counter + 1))
      
      self.repository.index.add([str(counter_file_path)])
      self.repository.index.commit('Increment RSPEC ID counter')

    origin = self.repository.remote(name='origin')
    origin.push()
    return counter

  def create_new_rule_branch(self, rule_number: int, languages: Iterable[str]) -> str:
    '''Create all the files required for a new rule.'''
    branch_name = f'add-RSPEC-S{rule_number}'
    with self._current_git_branch(self.MASTER_BRANCH, branch_name):
      repo_dir = Path(self.repository.working_dir)
      rule_dir = repo_dir.joinpath('rules', f'S{rule_number}')
      rule_dir.mkdir()
      common_template = self.TEMPLATE_PATH.joinpath('common')
      lang_specific_template = self.TEMPLATE_PATH.joinpath('language_specific')
      copy_directory_content(common_template, rule_dir)

      for lang in languages:
        lang_dir = rule_dir.joinpath(lang)
        lang_dir.mkdir()
        copy_directory_content(lang_specific_template, lang_dir)
      
      for rule_item in rule_dir.glob('**/*'):
        if rule_item.is_file():
          template_content = rule_item.read_text()
          final_content = template_content.replace('${RSPEC_ID}', str(rule_number))
          rule_item.write_text(final_content)
      self.repository.git.add('--all')
      self.repository.index.commit(f'Create rule S{rule_number}')

    origin = self.repository.remote(name='origin')
    origin.push(f'refs/heads/{branch_name}:refs/heads/{branch_name}')
    return branch_name
  
  def create_new_rule_pull_request(self, token: str, rule_number: int, languages: Iterable[str]) -> PullRequest:
    branch_name = self.create_new_rule_branch(rule_number, languages)
    repository_url = extract_repository_name(self.origin_url)
    github = Github(token)
    github_repo = github.get_repo(repository_url)
    return github_repo.create_pull(
      title=f'Create rule S{rule_number}', body='', head=branch_name, base=self.MASTER_BRANCH,
      draft=True, maintainer_can_modify=True
    )

  @contextmanager
  def _current_git_branch(self, base_branch: str, new_branch: Optional[str] = None):
    '''Checkout a given branch before yielding, then revert to the previous branch.'''
    past_branch = self.repository.active_branch
    try:
      self.repository.git.checkout(base_branch)
      origin = self.repository.remote(name='origin')
      origin.pull()
      if new_branch is not None:
        self.repository.git.checkout('-B', new_branch)
      yield
    finally:
      self.repository.git.checkout(past_branch)