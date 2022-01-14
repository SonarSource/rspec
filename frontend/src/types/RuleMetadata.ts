export type Status = 'default'|'ready'|'closed'|'deprecated'|'superseded';

export interface LanguageSupport {
  name: string,
  status: Status
}

export default interface RuleMetadata {
  title: string,
  languagesSupport: LanguageSupport[],
  allKeys: string[],
  branch: string,
  prUrl?: string
}
