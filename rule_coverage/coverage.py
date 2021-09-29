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
  ruleId = filename[:-5]
  if '_' in ruleId:
    return ruleId[:ruleId.find('_')]
  else:
    return ruleId

def rule_languages(rule, languages):
  '''
  Some analyzers, like SonarJS and sonar-cpp handle multiple languages
  by the same rule implementation. They add a special field "compatibleLanguages"
  to the rule metadata to specify which languges each implementation is applicable to.
  '''
  if "compatibleLanguages" in rule:
    return rule["compatibleLanguages"]
  else:
    return languages

def get_implemented_rules(path, languages):
  implemented_rules = {}
  for lang in languages:
    implemented_rules[lang] = []
  for filename in os.listdir(path):
    if filename.endswith(".json") and not filename.startswith("Sonar_way"):
        rule = load_json(os.path.join(path, filename))
        ruleId = get_rule_id(filename)
        for language in rule_languages(rule, languages):
          if language not in implemented_rules:
            implemented_rules[language] = []
          implemented_rules[language].append(ruleId)
    else:
        continue
  return implemented_rules

# analyzer+version uniquely identifies the analyzer and version implementing
# the rule for the given languages.
# Rule implementations for some langauges are spread across multiple repositories
# for example sonar-java and sonar-security for Java.
# We use analyzer+version to avoid confusion between versions of different analyzers.
def add_analyzer_version(analyzer, version, implemented_rules, coverage):
  repoAndVersion = analyzer + ' ' + version
  lastVersion = version == 'master'
  for language in implemented_rules:
    implemented_rules_for_lang = implemented_rules[language]
    language = canonicalize(language)
    if language not in coverage:
      print(f"Create entry for {language}")
      coverage[language] = {}
    for ruleId in implemented_rules_for_lang:
      if lastVersion:
        if ruleId not in coverage[language]:
          coverage[language][ruleId] = repoAndVersion
        elif type(coverage[language][ruleId]) == dict:
          coverage[language][ruleId] = coverage[language][ruleId]['since']
      else:
        if ruleId not in coverage[language]:
          coverage[language][ruleId] = {'since': repoAndVersion, 'until': repoAndVersion}
        elif type(coverage[language][ruleId]) == dict:
          coverage[language][ruleId]['until'] = repoAndVersion
        else:
          coverage[language][ruleId] = {'since': coverage[language][ruleId], 'until': repoAndVersion}

def canonicalize(language):
  if language in CANONICAL_NAMES:
    return CANONICAL_NAMES[language]
  return language

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
    add_analyzer_version(repo, version, implemented_rules, coverage)
  except Exception as e:
    print(f"{repo} {version} checkout failed: {e}")
  os.chdir('..')

def load_coverage(filename):
  if os.path.exists(filename):
    return load_json(filename)
  else:
    return {}

def store_coverage(filename, coverage):
  with open(filename, 'w') as outfile:
    json.dump(coverage, outfile, indent=2, sort_keys=True)

def main():
  parser = argparse.ArgumentParser(description='rules coverage')
  parser.add_argument('command', nargs='+', help='see code for help')
  args = parser.parse_args()

  RULES_FILENAME = 'covered_rules.json'

  coverage = load_coverage(RULES_FILENAME)

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

  store_coverage(RULES_FILENAME, coverage)

if __name__ == '__main__':
  main()
