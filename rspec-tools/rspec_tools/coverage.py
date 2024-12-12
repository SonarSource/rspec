import collections
import json
import os
import re
import sys
from pathlib import Path

from git import Git, Repo
from rspec_tools.utils import load_json, pushd

REPOS = [
  'sonar-abap',
  'sonar-apex',
  'sonar-architecture',
  'sonar-cobol',
  'sonar-cpp',
  'sonar-dart',
  'sonar-dataflow-bug-detection',
  'sonar-dotnet-enterprise',
  'sonar-flex',
  'sonar-go',
  'sonar-html',
  'sonar-iac-enterprise',
  'sonar-java',
  'SonarJS',
  'sonar-kotlin',
  'sonar-php',
  'sonar-pli',
  'sonar-plsql',
  'sonar-python',
  'sonar-rpg',
  'sonar-ruby',
  'sonar-scala',
  'sonar-security',
  'sonar-swift',
  'sonar-text-enterprise',
  'sonar-tsql',
  'sonar-vb',
  'sonar-xml'
]

CANONICAL_NAMES = {
  'CLOUD_FORMATION': 'CLOUDFORMATION',
  'JS': 'JAVASCRIPT',
  'TS': 'TYPESCRIPT',
  'WEB': 'HTML'
}


RULES_FILENAME = 'covered_rules.json'

DEPENDENCY_RE = re.compile(r'\s*dependency\s+\'(com|org)\.sonarsource\.([\w-]+):([\w-]+):(\d+(\.\d+)+)\'')

BUNDLED_SIMPLE = r'[\'"](com|org)\.sonarsource\.([\w.-]+):([\w-]+)[\'"]'
BUNDLED_MULTI = r'\(\s*group:\s*[\'"]([\w.-]+)[\'"],\s*name:\s*[\'"]([\w-]+)[\'"],\s*classifier:\s*[\'"][\w-]+\'\s*\)'
BUNDLED_RE = re.compile(rf'\s*bundledPlugin\s+({BUNDLED_SIMPLE}|{BUNDLED_MULTI})')


def get_rule_id(filename):
  rule_id = filename[:-5]
  return rule_id.removesuffix('_abap').removesuffix('_java')


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
    if filename.endswith(".json") and 'profile' not in filename:
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

def read_all_alternative_keys(metadata):
  ret = []
  if 'sqKey' in metadata:
    ret.append(metadata['sqKey'])
  if 'ruleSpecification' in metadata:
    ret.append(metadata['ruleSpecification'])
  if 'extra' in metadata and 'legacyKeys' in metadata['extra']:
    ret.extend(metadata['extra']['legacyKeys'])
  return ret

def read_canonical_rule_ids(rules_dir):
  '''
  Map all the keys identifying a rule to its modern key (which is also its directory name).
  '''
  print('Collecting the rule-id synonyms from ' + str(rules_dir))
  canonical_id = {}
  rule_dirs = [entry for entry in os.scandir(rules_dir) if entry.is_dir()]
  for rule_dir in rule_dirs:
    for metadata_path in Path(rule_dir).rglob('metadata.json'):
      for alternative_key in read_all_alternative_keys(load_json(metadata_path)):
        canonical_id[alternative_key] = rule_dir.name
  return canonical_id

class Coverage:
  '''Keep and update the coverage DB: lang*rule_id -> analyzer version'''
  def __init__(self, filename, rules_dir):
    self.rules = {}
    self.canonical_ids = read_canonical_rule_ids(rules_dir)
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
    if rule_id in self.canonical_ids:
      rule_id = self.canonical_ids[rule_id]

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
  implemented_rules = collections.defaultdict(list)
  for sp_file in Path('.').rglob('sonarpedia.json'):
    print(sp_file)
    sonarpedia_path=sp_file.parents[0]
    try:
      sonarpedia = load_json(sp_file)
      path = str(sonarpedia_path) + '/' + sonarpedia['rules-metadata-path'].replace('\\', '/')
      languages = sonarpedia['languages']

      implemented_rules_in_path = get_implemented_rules(path, languages)
      for lang, rules in implemented_rules_in_path.items():
        implemented_rules[lang] += rules
    except Exception as e:
      print(f"failed to collect implemented rules for {sp_file}: {e}")
      continue
  return implemented_rules

def checkout_repo(repo):
  git_url=f"https://github.com/SonarSource/{repo}"
  token=os.getenv('GITHUB_TOKEN')
  if token:
    git_url=f"https://oauth2:{token}@github.com/SonarSource/{repo}"
  if not os.path.exists(repo):
    return Repo.clone_from(git_url, repo)
  else:
    return Repo(repo)


VERSION_RE = re.compile(r'\d[\d\.]+')
def is_version_tag(name):
  return bool(re.fullmatch(VERSION_RE, name))


def comparable_version(key):
  v = key.removeprefix('sqcb-').removeprefix('sqs-')
  if not is_version_tag(v):
    if v == 'master':
      return [0]
    else:
      sys.exit(f'Unexpected version {key}')
  return list(map(int, v.split('.')))


def collect_coverage_for_all_versions(repo, coverage):
  git_repo = checkout_repo(repo)
  tags = git_repo.tags
  versions = [tag.name for tag in tags if is_version_tag(tag.name)]
  versions.sort(key = comparable_version)
  for version in versions:
    collect_coverage_for_version(repo, git_repo, version, coverage)
  collect_coverage_for_version(repo, git_repo, 'master', coverage)

def collect_coverage_for_version(repo_name, git_repo, version, coverage):
  g = Git(git_repo)
  print(f"{repo_name} {version}")
  repo_dir = git_repo.working_tree_dir
  try:
    with pushd(repo_dir):
      git_repo.head.reference = git_repo.commit(version)
      git_repo.head.reset(index=True, working_tree=True)
      g.checkout(version)
      implemented_rules = all_implemented_rules()
      coverage.add_analyzer_version(repo_name, version, implemented_rules)
  except Exception as e:
    print(f"{repo_name} {version} checkout failed: {e}")
    raise

def update_coverage_for_all_repos(rules_dir):
  print(f"batch mode for {REPOS}")
  coverage = Coverage(RULES_FILENAME, rules_dir)
  for repo in REPOS:
    collect_coverage_for_all_versions(repo, coverage)
  coverage.save_to_file(RULES_FILENAME)

def update_coverage_for_repo(repo, rules_dir):
  print(f"batch mode for {repo}")
  coverage = Coverage(RULES_FILENAME, rules_dir)
  collect_coverage_for_all_versions(repo, coverage)
  coverage.save_to_file(RULES_FILENAME)

def update_coverage_for_repo_version(repo, version, rules_dir):
  print(f"checking {repo} version {version}")
  coverage = Coverage(RULES_FILENAME, rules_dir)
  git_repo = checkout_repo(repo)
  collect_coverage_for_version(repo, git_repo, version, coverage)
  coverage.save_to_file(RULES_FILENAME)


def get_plugin_versions(git_repo, version):
  g = Git(git_repo)
  repo_dir = git_repo.working_tree_dir
  try:
    with pushd(repo_dir):
      content = g.show(f'{version}:build.gradle')
      versions = {}
      for m in re.findall(DEPENDENCY_RE, content):
        versions[m[2]] = m[3]
      return versions
  except Exception as e:
    print(f"Sonar Enterprise {version} checkout failed: {e}")
    raise

def get_packaged_plugins(git_repo):
  g = Git(git_repo)
  repo_dir = git_repo.working_tree_dir
  with pushd(repo_dir):
    BUNDLES= {'Community Build': 'sonar-application/bundled_plugins.gradle',
              'Datacenter': 'private/edition-datacenter/bundled_plugins.gradle',
              'Developer': 'private/edition-developer/bundled_plugins.gradle',
              'Enterprise': 'private/edition-enterprise/bundled_plugins.gradle'}
    bundle_map = {}
    for key, bundle in BUNDLES.items():
      bundle_map[key] = []
      content = g.show(f'master:{bundle}')
      for m in re.findall(BUNDLED_RE, content):
        if m[3] != '':
          bundle_map[key].append(m[3])
        else:
          bundle_map[key].append(m[5])
    return bundle_map

def lowest_cb(plugin_versions, plugin, version):
  tags = list(filter(lambda k: not k.startswith('sqs-'), plugin_versions.keys()))
  tags.sort(key = comparable_version)
  for t in tags:
    if plugin in plugin_versions[t]:
      pvv = plugin_versions[t][plugin]
      if comparable_version(pvv) >= comparable_version(version):
        return t
  return None


def lowest_server(plugin_versions, plugin, version):
  tags = list(filter(lambda k: not k.startswith('sqcb-'), plugin_versions.keys()))
  tags.sort(key = comparable_version)
  for t in tags:
    if plugin in plugin_versions[t]:
      pvv = plugin_versions[t][plugin]
      if comparable_version(pvv) >= comparable_version(version):
        return t
  return None


def build_rule_per_product(rules_dir, bundle_map, plugin_versions):
  coverage = Coverage(RULES_FILENAME, rules_dir)
  rule_per_product = {}
  repo_plugin_mapping = load_json(os.path.join(Path(__file__).parent, 'repo_plugin_mapping.json'))
  for lang, rules in coverage.rules.items():
    for rule, version in rules.items():
      if isinstance(version, str):
        if rule not in rule_per_product:
          rule_per_product[rule] = {}
        if lang not in rule_per_product[rule]:
          rule_per_product[rule][lang] = {}
        target_repo, v = version.split(' ')
        if lang not in repo_plugin_mapping or target_repo not in repo_plugin_mapping[lang]:
          print(f"Couldn't find the corresponding plugin name for {lang} - {target_repo}")
          continue
        plugin = repo_plugin_mapping[lang][target_repo]
        if plugin in bundle_map['Community Build']:
          rule_per_product[rule][lang]['SonarQube Community Build'] = lowest_cb(plugin_versions, plugin, v)
          rule_per_product[rule][lang]['SonarQube Server'] = {
            'Developer': lowest_server(plugin_versions, plugin, v)
            }
        elif plugin in bundle_map['Developer']:
          rule_per_product[rule][lang]['SonarQube Server'] = {
            'Developer': lowest_server(plugin_versions, plugin, v)}
        elif plugin in bundle_map['Enterprise']:
          rule_per_product[rule][lang]['SonarQube Server'] = {
            'Enterprise': lowest_server(plugin_versions, plugin, v)}
        elif plugin in bundle_map['Datacenter']:
          rule_per_product[rule][lang]['SonarQube Server'] = {
            'Datacenter': lowest_server(plugin_versions, plugin, v)
          }
        else:
          print(f'Couldnt find plugin {plugin}')
  with open('rule_product_mapping.json', 'w', encoding='utf-8') as outfile:
    json.dump(rule_per_product, outfile, indent=2, sort_keys=True)


def is_interesting_version(version):
  if version.startswith('sqs-'):
    # Sonarqube Server Release
    return True
  if version.startswith('sqcb-'):
    # Sonarqube Community Build Release
    return True
  if not is_version_tag(version):
    # Non official version
    return False
  try:
    # Official release before Dec 2024
    major = int(version[:version.find('.')])
  except ValueError:
    return False
  return major >= 8

def collect_coverage_per_product(rules_dir):
  git_repo = checkout_repo('sonar-enterprise')
  bundle_map = get_packaged_plugins(git_repo)
  tags = git_repo.tags
  tags.sort(key = lambda t: t.commit.committed_date)
  versions = [tag.name for tag in tags if is_interesting_version(tag.name)]
  plugin_versions = {}
  for version in versions:
    plugin_versions[version] = get_plugin_versions(git_repo, version)
  build_rule_per_product(rules_dir, bundle_map, plugin_versions)
