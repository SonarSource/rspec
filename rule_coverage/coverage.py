import os
import sys
import argparse
import json
from git import Repo
from git import Git
from pathlib import Path

repos=['sonar-abap','sonar-cpp','sonar-cobol','sonar-dotnet','sonar-css','sonar-flex','slang-enterprise','sonar-java','SonarJS','sonar-php','sonar-pli','sonar-plsql','sonar-python','sonar-rpg','sonar-swift','sonar-tsql','sonar-vb','sonar-html','sonar-xml','sonar-kotlin', 'sonar-secrets', 'sonar-security']

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


def dump_rule(name, rule, languages, repoAndVersion):
  if "compatibleLanguages" in rule:
    for language in rule['compatibleLanguages']:
      store_rule(name, rule, language, repoAndVersion)
  else:
    for language in languages:
      store_rule(name, rule, language, repoAndVersion)

def store_rule(name, rule, language, repoAndVersion):
  if language not in rules:
    print(f"create entry for {language}")
    rules[language] = {}
  if '_' in name:
      name=name[:name.find('_')]
  if name not in rules[language]:
    rules[language][name] = repoAndVersion

def dump_rules(repo, version):
  for sp_file in Path('.').rglob('sonarpedia.json'):
    print(sp_file)
    sonarpedia_path=sp_file.parents[0]
    sonarpedia = load_json(sp_file)
    path=str(sonarpedia_path) + '/' + sonarpedia['rules-metadata-path'].replace('\\', '/')
    languages=sonarpedia['languages']
    get_rules_json(path, languages, repo + ' ' + version)
    with open(f"../{rules_filename}", 'w') as outfile:
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
  versions = [tag.name for tag in git_repo.tags]
  for version in versions:
    if not '-' in version:
      print(f"{repo} {version}")
      scan_version(repo, version, version)
  scan_version(repo, 'master', 'nightly')

def scan_version(repo, version, version_name):
  g=Git(repo)
  os.chdir(repo)
  try:
    g.checkout(version)
    dump_rules(repo, version_name)
  except Exception:
    print(f"{repo} {version} checkout failed, resetting and cleaning")
    g.reset('--hard', version)
    g.clean('-xfd')
  os.chdir('..')

def main():
  parser = argparse.ArgumentParser(description='rules coverage')
  parser.add_argument('command', nargs='+', help='see code for help')
  args = parser.parse_args()

  global rules
  global rules_filename
  rules_filename='covered_rules.json'
  if os.path.exists(rules_filename):
    rules=load_json(rules_filename)
  else:
    rules={}

  if args.command[0] == "batchall":
    print(f"batch mode for {repos}")
    for repo in repos:
      scan_all_versions(repo)
  elif args.command[0] == "batch":
    repo=args.command[1]
    print(f"batch mode for {repo}")
    scan_all_versions(repo)
  else:
    repo=args.command[0]
    version=args.command[1]
    print(f"checking {repo} version {version}")
    checkout_repo(repo)
    scan_version(repo, version, version)

if __name__ == '__main__':
  main()
