export type Status = 'ready' | 'beta' | 'closed' | 'deprecated' | 'superseded';

export interface LanguageSupport {
  name: string,
  status: Status
}

export type Version = string | { since: string, until: string };

export type Mapper = ((key: string, value: Version) => JSX.Element);

export type Coverage = string | JSX.Element[];

export default interface RuleMetadata {
  title: string,
  languagesSupport: LanguageSupport[],
  allKeys: string[],
  branch: string,
  defaultQualityProfiles: string[],
  prUrl?: string
}
