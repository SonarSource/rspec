import { useFetch } from './useFetch';

export type RuleCoverage = Record<string, Record<string, string>>;

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

export function useRuleCoverage() {
  const coveredRulesUrl = `${process.env.PUBLIC_URL}/covered_rules.json`;
  const [coveredRules, coveredRulesError, coveredRulesIsLoading] = useFetch<RuleCoverage>(coveredRulesUrl);

  function ruleCoverageForSonarpediaKeys(languageKeys: string[], ruleKeys: string[], mapper: any) {
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
    languageKeys.forEach(language => {
      ruleKeys.forEach(ruleKey => {
        if (language in coveredRules && ruleKey in coveredRules[language]) {
          result.push(mapper(language, coveredRules[language][ruleKey]))
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
    const allLanguageKeys = Array.from(languageToSonarpedia.keys());
    return ruleCoverageForSonarpediaKeys(allLanguageKeys, ruleKeys, mapper);
  }

  function isLanguageCovered(language: string, ruleKeys: string[]): boolean {
    const languageKeys = languageToSonarpedia.get(language);
    if (!languageKeys) {
      return false;
    }
    if (coveredRulesError || coveredRulesIsLoading) {
      return false;
    }
    if (!coveredRules) {
      throw new Error('coveredRules is empty');
    }
    return !!languageKeys.find(lang => 
      ruleKeys.find(ruleKey => lang in coveredRules && ruleKey in coveredRules[lang])
    );
  }

  return {ruleCoverage, allLangsRuleCoverage, isLanguageCovered};
}
