import os
import argparse
import json


def load_json(file):
  with open(file) as json_file:
    return json.load(json_file) 

def get_rules_json(path,languages):
  print(f"Getting rules from {os.getcwd()} {path}")
  for filename in os.listdir(path):
    if filename.endswith(".json") and not filename.startswith("Sonar_way"):
        rule=load_json(os.path.join(path, filename))
        dump_rule(filename[:-5],rule,languages)
    else:
        continue


def dump_rule(name,rule,languages):
  if "compatibleLanguages" in rule:
    for language in rule['compatibleLanguages']:
      store_rule(name,rule,language)
  else:
    for language in languages:
      store_rule(name,rule,language)
  
def store_rule(name,rule,language):
  record={
    f"{name}": f"{version}",
  }
  if language not in rules.keys():
    print(f"create entry for {language}")
    rules[language] = []
  if record in rules[language]:
    print(f"{record} alread in {language}")
  else:
    rules[language].append(record)  
  

def dump_rules(repo):
  print(f"dumping rules")
  os.chdir(repo)
  sonarpedia = load_json('sonarpedia.json')
  path=sonarpedia['rules-metadata-path']
  languages=sonarpedia['languages']
  get_rules_json(path,languages)
  with open(f"../{rules_filename}", 'w') as outfile:
    json.dump(rules, outfile)


def main():
  parser = argparse.ArgumentParser(description='rules coverage')
  parser.add_argument('command', nargs='+', help='see code for help')  
  args = parser.parse_args()

  global version
  global rules
  global rules_filename
  version=args.command[1]
  rules_filename='covered_rules.json'
  if os.path.exists(rules_filename):
    print("rules already exists")
    rules=load_json(rules_filename)
  else:
    rules={}
  dump_rules(args.command[0])

if __name__ == '__main__':
  main()
