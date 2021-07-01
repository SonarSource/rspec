import os
import sys
import argparse
import json
from git import Repo
from git import Git
from pathlib import Path

repos=['sonar-abap','sonar-cpp','sonar-cobol','sonar-dotnet','sonar-css','sonar-flex','slang-enterprise','sonar-java','SonarJS','sonar-php','sonar-pli','sonar-plsql','sonar-python','sonar-rpg','sonar-swift','sonar-tsql','sonar-vb','sonar-html','sonar-xml','sonar-kotlin', 'sonar-secrets']
#repos=['sonar-php','sonar-pli','sonar-plsql','sonar-python','sonar-rpg','sonar-swift','sonar-tsql','sonar-vb','sonar-html','sonar-xml']

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
  if '_' in name:
      name=name[:name.find('_')]
  if name not in rules[language]:
    rules[language][name]=version
  
def dump_rules(repo,version):
  for sp_file in Path('.').rglob('sonarpedia.json'):
    print(sp_file)
    sonarpedia_path=sp_file.parents[0]
    sonarpedia = load_json(sp_file)
    path=str(sonarpedia_path)+'/'+sonarpedia['rules-metadata-path'].replace('\\','/')
    languages=sonarpedia['languages']
    get_rules_json(path,languages,version)
    with open(f"../{rules_filename}", 'w') as outfile:
      json.dump(rules, outfile, indent=2)
  
def checkout(repo,version,batch_mode):
  token=os.getenv('GITHUB_TOKEN')
  if not token:
    git_url=f"git@github.com:SonarSource/{repo}"
  else:
    git_url=f"https://{token}@github.com/SonarSource/{repo}"
  git_repo=None
  g=Git(repo)
  if not os.path.exists(repo):
    git_repo=Repo.clone_from(git_url, repo)
  else:
    git_repo=Repo(repo)
  if batch_mode:
    os.chdir(repo)  
    for tag in git_repo.tags:
      if not '-' in tag.name:
        print(f"{repo} {tag.name}")
        try:
          g.checkout(tag.name)
        except Exception:
          print("checkout failed, resetting and cleaning")
          g.reset('--hard',tag)
          g.clean('-xfd')
        dump_rules(repo,tag.name)
    os.chdir('..')
  else:
    g=Git(repo)
    g.checkout(version)
    os.chdir(repo)
  
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
      checkout(repo,None,True)
  elif args.command[0] == "batch":
    repo=args.command[1]
    print(f"batch mode for {repo}")
    checkout(repo,None,True)
  else: 
    repo=args.command[0]
    version=args.command[1]
    print(f"checking {repo} version {version}")
    checkout(repo,version,False)
    dump_rules(repo,version)

if __name__ == '__main__':
  main()
