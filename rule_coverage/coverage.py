import os
import sys
import argparse
import json
from git import Repo
from git import Git
from pathlib import Path

REPOS=['sonar-abap','sonar-cpp','sonar-cobol','sonar-dotnet','sonar-css','sonar-flex','slang-enterprise','sonar-java','SonarJS','sonar-php','sonar-pli','sonar-plsql','sonar-python','sonar-rpg','sonar-swift','sonar-tsql','sonar-vb','sonar-html','sonar-xml','sonar-kotlin', 'sonar-secrets', 'sonar-security']

CANONICAL_NAMES={
  'JS': 'JAVASCRIPT',
  'TS': 'TYPESCRIPT',
  'WEB': 'HTML'
}

RULES_FILENAME='covered_rules.json'

def load_json(file):
  with open(file) as json_file:
    return json.load(json_file)

# repoAndVersion uniquely identifies the analyzer and version implementing
# the rule for the given languages.
# Rule implementations for some langauges are spread across multiple repositories
# for example sonar-java and sonar-security for Java.
# We use repoAndVersion to avoid confusion between version of different analyzers.
def get_rules_json(path, languages, repoAndVersion):
  print(f"Getting rules from {os.getcwd()} {path} for {repoAndVersion}")
  for filename in os.listdir(path):
    if filename.endswith(".json") and not filename.startswith("Sonar_way"):
        rule=load_json(os.path.join(path, filename))
        dump_rule(filename[:-5], rule, languages, repoAndVersion)
    else:
        continue

def canonicalize(language):
  if language in CANONICAL_NAMES:
    return CANONICAL_NAMES[language]
  return language

def dump_rule(ruleId, rule, languages, repoAndVersion):
  if "compatibleLanguages" in rule:
    for language in rule['compatibleLanguages']:
      store_rule(ruleId, language, repoAndVersion)
  else:
    for language in languages:
      store_rule(ruleId, language, repoAndVersion)

def store_rule(ruleId, language, repoAndVersion):
  language = canonicalize(language)
  global rules
  if language not in rules:
    print(f"create entry for {language}")
    rules[language] = {}
  if '_' in ruleId:
      ruleId=ruleId[:ruleId.find('_')]
  if ruleId not in rules[language]:
    rules[language][ruleId] = {'since': repoAndVersion, 'until': repoAndVersion}
  elif type(rules[language][ruleId]) == dict:
    rules[language][ruleId]['until'] = repoAndVersion
  else:
    rules[language][ruleId] = {'since': rules[language][ruleId], 'until': repoAndVersion}

def simplify_spec_for_rules_that_are_still_supported():
  ''' Represent covered range for rules that are still active as a single string holding "since" value.
  Assumes the rules that are still active have "until" set to "master" branch, which happens if
  "master" is scanned last after all the tagged versions.'''
  global rules
  for language, lang_rules in rules.items():
    for rule, version in lang_rules.items():
      if type(version) == dict and version['until'].endswith(' master'):
        lang_rules[rule] = version['since']

def dump_rules(repo, version):
  for sp_file in Path('.').rglob('sonarpedia.json'):
    print(sp_file)
    sonarpedia_path=sp_file.parents[0]
    sonarpedia = load_json(sp_file)
    path=str(sonarpedia_path) + '/' + sonarpedia['rules-metadata-path'].replace('\\', '/')
    languages=sonarpedia['languages']
    simplify_spec_for_rules_that_are_still_supported()
    get_rules_json(path, languages, repo + ' ' + version)
    with open(f"../{RULES_FILENAME}", 'w') as outfile:
      json.dump(rules, outfile, indent=2, sort_keys=True)

def checkout_repo(repo):
  token=os.getenv('GITHUB_TOKEN')
  if not token:
    git_url=f"git@github.com:SonarSource/{repo}"
  else:
    git_url=f"https://{token}@github.com/SonarSource/{repo}"
  git_repo=None
  g=Git(repo)
  if not os.path.exists(repo):
    return Repo.clone_from(git_url, repo)
  else:
    return Repo(repo)

def scan_all_versions(repo):
  git_repo = checkout_repo(repo)
  tags = git_repo.tags
  tags.sort(key = lambda t: t.commit.committed_date)
  versions = [tag.name for tag in tags]
  for version in versions:
    if not '-' in version:
      print(f"{repo} {version}")
      scan_version(repo, version)
  scan_version(repo, 'master')

def scan_version(repo, version):
  r = checkout_repo(repo)
  g = Git(repo)
  os.chdir(repo)
  try:
    r.head.reference = r.commit(version)
    r.head.reset(index=True, working_tree=True)
    g.checkout(version)
    dump_rules(repo, version)
  except Exception as e:
    print(f"{repo} {version} checkout failed, resetting and cleaning: {e}")
  os.chdir('..')

def main():
  parser = argparse.ArgumentParser(description='rules coverage')
  parser.add_argument('command', nargs='+', help='see code for help')
  args = parser.parse_args()

  global rules
  if os.path.exists(RULES_FILENAME):
    rules=load_json(RULES_FILENAME)
  else:
    rules={}

  if args.command[0] == "batchall":
    print(f"batch mode for {REPOS}")
    for repo in REPOS:
      scan_all_versions(repo)
  elif args.command[0] == "batch":
    repo=args.command[1]
    print(f"batch mode for {repo}")
    scan_all_versions(repo)
  else:
    repo=args.command[0]
    version=args.command[1]
    print(f"checking {repo} version {version}")
    scan_version(repo, version)

if __name__ == '__main__':
  main()
