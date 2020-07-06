import os
import sys
import argparse
import json
from git import Repo
from git import Git


def load_json(file):
  with open(file) as json_file:
    return json.load(json_file) 

def get_rules_json(path,languages,version):
  print(f"Getting rules from {os.getcwd()} {path}")
  for filename in os.listdir(path):
    if filename.endswith(".json") and not filename.startswith("Sonar_way"):
        rule=load_json(os.path.join(path, filename))
        dump_rule(filename[:-5],rule,languages,version)
    else:
        continue


def dump_rule(name,rule,languages,version):
  if "compatibleLanguages" in rule:
    for language in rule['compatibleLanguages']:
      store_rule(name,rule,language,version)
  else:
    for language in languages:
      store_rule(name,rule,language,version)
  
def store_rule(name,rule,language,version):
  if language not in rules:
    print(f"create entry for {language}")
    rules[language] = {}
  if name not in rules[language]:
    rules[language][name]=version
  
def dump_rules(repo,version):
  sp_file='sonarpedia.json'
  if os.path.exists(sp_file):
    sonarpedia = load_json(sp_file)
    path=sonarpedia['rules-metadata-path']
    languages=sonarpedia['languages']
    get_rules_json(path,languages,version)
    with open(f"../{rules_filename}", 'w') as outfile:
      json.dump(rules, outfile)
  else:
    print(f"no {sp_file} file")

def checkout(repo,version):
  git_url=f"git@github.com:SonarSource/{repo}"
  git_repo=None
  g=Git(repo)
  if not os.path.exists(repo):
    git_repo=Repo.clone_from(git_url, repo)
  else:
    git_repo=Repo(repo)
  os.chdir(repo)
  for tag in git_repo.tags:
    if not '-' in tag.name:
      print(f"{tag.name}")
      g.checkout(tag.name)
      dump_rules(repo,tag.name)
  #g=Git(repo)
  #g.checkout(version)

def main():
  parser = argparse.ArgumentParser(description='rules coverage')
  parser.add_argument('command', nargs='+', help='see code for help')  
  args = parser.parse_args()

  global rules
  global rules_filename
  version=args.command[1]
  rules_filename='covered_rules.json'
  if os.path.exists(rules_filename):
    rules=load_json(rules_filename)
  else:
    rules={}
  repo=args.command[0]

  checkout(repo,version)
  #dump_rules(repo,version)

if __name__ == '__main__':
  main()
