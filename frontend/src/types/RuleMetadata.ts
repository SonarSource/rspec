export type Status = 'ready' | 'beta' | 'closed' | 'deprecated' | 'superseded';

export interface LanguageSupport {
  name: string,
  status: Status
}

export type Version = string | { since: string, until: string };

export default interface RuleMetadata {
  title: string,
  languagesSupport: LanguageSupport[],
  allKeys: string[],
  branch: string,
  prUrl?: string
}
