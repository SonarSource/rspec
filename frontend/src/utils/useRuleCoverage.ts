import { useFetch } from './useFetch';

type RuleCoverage = Record<string, Record<string, string>>;

export function useRuleCoverage() {

  const coveredRulesUrl = `${process.env.PUBLIC_URL}/covered_rules.json`;
  const [coveredRules, coveredRulesError, coveredRulesIsLoading] = useFetch<RuleCoverage>(coveredRulesUrl);
  const languageToSonarpedia = new Map<string, string[]>(Object.entries({
    'abap': ['ABAP'],
    'apex': ['APEX'],
    'cfamily': ['CPP', 'C', 'OBJC'],
    'cobol': ['COBOL'],
    'csharp': ['CSH'],
    'vbnet': ['VBNET'],
    'css': ['CSS'],
    'flex': ['FLEX'],
    'kotlin': ['KOTLIN'],
    'scala': ['SCALA'],
    'ruby': ['RUBY'],
    'go': ['GO'],
    'java': ['JAVA'],
    'javascript': ['JAVASCRIPT', 'JS', 'TYPESCRIPT'],
    'php': ['PHP'],
    'pli': ['PLI'],
    'plsql': ['PLSQL'],
    'python': ['PY'],
    'rpg': ['RPG'],
    'secrets': ['SECRETS'],
    'swift': ['SWIFT'],
    'tsql': ['TSQL'],
    'vb6': ['VB'],
    'WEB': ['WEB'],
    'xml': ['XML'],
    'html': ['HTML'],
    'cloudformation': ['CLOUDFORMATION'],
    'terraform': ['TERRAFORM']
  }));
  const allLanguageKeys = collectAllLanguageKeys();

  function collectAllLanguageKeys() {
    let ret = new Set<string>();
    languageToSonarpedia.forEach((sonarpediaKeys, lang) => {
      sonarpediaKeys.forEach(key => ret.add(key));
    });
    return Array.from(ret);
  }

  function ruleCoverageForSonarpediaKeys(sonarpediaKeys: string[], ruleKeys: string[], mapper: any) {
    if (coveredRulesError) {
      return 'Failed Loading';
    }
    if (coveredRulesIsLoading) {
      return 'Loading';
    }
    if (!coveredRules) {
      throw new Error('coveredRules is empty');
    }
    const result: any[] = [];
    sonarpediaKeys.forEach(sonarpediaKey => {
      ruleKeys.forEach(ruleKey => {
        if (sonarpediaKey in coveredRules &&
          ruleKey in coveredRules[sonarpediaKey]) {
          result.push(mapper(sonarpediaKey, coveredRules[sonarpediaKey][ruleKey]))
        }
      });
    });
    if (result.length > 0) {
      return result;
    } else {
      return 'Not Covered';
    }
  }

  function ruleCoverage(language: string, ruleKeys: string[], mapper: any) {
    const languageKeys = languageToSonarpedia.get(language);
    if (!languageKeys) {
      return 'Nonsupported language';
    }
    return ruleCoverageForSonarpediaKeys(languageKeys, ruleKeys, mapper);
  }

  function allLangsRuleCoverage(ruleKeys: string[], mapper: any) {
    return ruleCoverageForSonarpediaKeys(allLanguageKeys, ruleKeys, mapper);
  }

  return {ruleCoverage, allLangsRuleCoverage};
}
