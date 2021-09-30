import os
import sys
import argparse
import json
from git import Repo
from git import Git
from pathlib import Path

REPOS = ['sonar-abap','sonar-cpp','sonar-cobol','sonar-dotnet','sonar-css','sonar-flex','slang-enterprise','sonar-java','SonarJS','sonar-php','sonar-pli','sonar-plsql','sonar-python','sonar-rpg','sonar-swift','sonar-tsql','sonar-vb','sonar-html','sonar-xml','sonar-kotlin', 'sonar-secrets', 'sonar-security']

CANONICAL_NAMES = {
  'JS': 'JAVASCRIPT',
  'TS': 'TYPESCRIPT',
  'WEB': 'HTML'
}

def load_json(file):
  with open(file) as json_file:
    return json.load(json_file)

def get_rule_id(filename):
  rule_id = filename[:-5]
  if '_' in rule_id:
    return rule_id[:rule_id.find('_')]
  else:
    return rule_id

def compatible_languages(rule, languages_from_sonarpedia):
  '''
  Some analyzers, like SonarJS and sonar-cpp handle multiple languages
  by the same rule implementation. They add a special field "compatibleLanguages"
  to the rule metadata to specify which languges each implementation is applicable to.
  By default, the rule is applicable to all languages declared in sonarpedia.
  '''
  if "compatibleLanguages" in rule:
    return rule["compatibleLanguages"]
  else:
    return languages_from_sonarpedia

def get_implemented_rules(path, languages_from_sonarpedia):
  implemented_rules = {}
  for lang in languages_from_sonarpedia:
    implemented_rules[lang] = []
  for filename in os.listdir(path):
    if filename.endswith(".json") and not filename.startswith("Sonar_way"):
        rule = load_json(os.path.join(path, filename))
        rule_id = get_rule_id(filename)
        for language in compatible_languages(rule, languages_from_sonarpedia):
          if language not in implemented_rules:
            implemented_rules[language] = []
          implemented_rules[language].append(rule_id)
    else:
        continue
  return implemented_rules

def canonicalize(language):
  if language in CANONICAL_NAMES:
    return CANONICAL_NAMES[language]
  return language

class Coverage:
  '''Keep and update the coverage DB: lang*rule_id -> analyzer version'''
  def __init__(self, filename):
    self.rules = {}
    if os.path.exists(filename):
      self.rules = load_json(filename)

  def save_to_file(self, filename):
    with open(filename, 'w') as outfile:
      json.dump(self.rules, outfile, indent=2, sort_keys=True)

  def _rule_implemented_for_intermediate_version(self, rule_id, language, repo_and_version):
    if rule_id not in self.rules[language]:
      self.rules[language][rule_id] = {'since': repo_and_version, 'until': repo_and_version}
    elif type(self.rules[language][rule_id]) == dict:
      self.rules[language][rule_id]['until'] = repo_and_version
    else:
      self.rules[language][rule_id] = {'since': self.rules[language][rule_id], 'until': repo_and_version}

  def _rule_implemented_for_last_version(self, rule_id, language, repo_and_version):
    if rule_id not in self.rules[language]:
      self.rules[language][rule_id] = repo_and_version
    elif type(self.rules[language][rule_id]) == dict:
      self.rules[language][rule_id] = self.rules[language][rule_id]['since']

  def rule_implemented(self, rule_id, language, analyzer, version):
    repo_and_version = analyzer + ' ' + version
    language = canonicalize(language)

    if language not in self.rules:
      print(f"Create entry for {language}")
      self.rules[language] = {}

    if version == 'master':
      self._rule_implemented_for_last_version(rule_id, language, repo_and_version)
    else:
      self._rule_implemented_for_intermediate_version(rule_id, language, repo_and_version)

  # analyzer+version uniquely identifies the analyzer and version implementing
  # the rule for the given languages.
  # Rule implementations for some languages are spread across multiple repositories
  # for example sonar-java and sonar-security for Java.
  # We use analyzer+version to avoid confusion between versions of different analyzers.
  def add_analyzer_version(self, analyzer, version, implemented_rules_per_language):
    for language in implemented_rules_per_language:
      for rule_id in implemented_rules_per_language[language]:
        self.rule_implemented(rule_id, language, analyzer, version)

def all_implemented_rules():
  implemented_rules = {}
  for sp_file in Path('.').rglob('sonarpedia.json'):
    print(sp_file)
    sonarpedia_path=sp_file.parents[0]
    sonarpedia = load_json(sp_file)
    path = str(sonarpedia_path) + '/' + sonarpedia['rules-metadata-path'].replace('\\', '/')
    languages = sonarpedia['languages']
    implemented_rules.update(get_implemented_rules(path, languages))
  return implemented_rules

def checkout_repo(repo):
  token=os.getenv('GITHUB_TOKEN')
  git_url=f"git@github.com:SonarSource/{repo}"
  if token:
    git_url=f"https://{token}@github.com/SonarSource/{repo}"
  g=Git(repo)
  if not os.path.exists(repo):
    return Repo.clone_from(git_url, repo)
  else:
    return Repo(repo)

def scan_all_versions(repo, coverage):
  git_repo = checkout_repo(repo)
  tags = git_repo.tags
  tags.sort(key = lambda t: t.commit.committed_date)
  versions = [tag.name for tag in tags if '-' not in tag.name]
  for version in versions:
    scan_version(repo, version, coverage)
  scan_version(repo, 'master', coverage)

def scan_version(repo, version, coverage):
  print(f"{repo} {version}")
  r = checkout_repo(repo)
  g = Git(repo)
  os.chdir(repo)
  try:
    r.head.reference = r.commit(version)
    r.head.reset(index=True, working_tree=True)
    g.checkout(version)
    implemented_rules = all_implemented_rules()
    coverage.add_analyzer_version(repo, version, implemented_rules)
  except Exception as e:
    print(f"{repo} {version} checkout failed: {e}")
  os.chdir('..')

def main():
  parser = argparse.ArgumentParser(description='rules coverage')
  parser.add_argument('command', nargs='+', help='see code for help')
  args = parser.parse_args()

  RULES_FILENAME = 'covered_rules.json'
  coverage = Coverage(RULES_FILENAME)

  if args.command[0] == "batchall":
    print(f"batch mode for {REPOS}")
    for repo in REPOS:
      scan_all_versions(repo, coverage)
  elif args.command[0] == "batch":
    repo=args.command[1]
    print(f"batch mode for {repo}")
    scan_all_versions(repo, coverage)
  else:
    repo=args.command[0]
    version=args.command[1]
    print(f"checking {repo} version {version}")
    scan_version(repo, version, coverage)

  coverage.save_to_file(RULES_FILENAME)

if __name__ == '__main__':
  main()
