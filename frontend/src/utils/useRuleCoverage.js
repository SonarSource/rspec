import { useFetch } from './useFetch';

export function useRuleCoverage() {

  const coveredRulesUrl = `${process.env.PUBLIC_URL}/covered_rules.json`;
  const [coveredRules, coveredRulesError, coveredRulesIsLoading] = useFetch(coveredRulesUrl);
  const languageToSonarpedia = {
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
    'swift': ['SWIFT'],
    'tsql': ['TSQL'],
    'vb6': ['VB'],
    'WEB': ['WEB'],
    'xml': ['XML']
  };
  function ruleCoverage(language, ruleKeys, mapper) {
    if (coveredRulesError) {
      return 'Failed Loading';
    }
    if (coveredRulesIsLoading) {
      return 'Loading';
    }
    // return "FIXME"
    const result = [];
    // const keys = coveredRules.keys;
    languageToSonarpedia[language].forEach(sonarpediaKey => {
      ruleKeys.forEach(ruleKey => {
        if (ruleKey in coveredRules[sonarpediaKey]) {
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

  return ruleCoverage;
}