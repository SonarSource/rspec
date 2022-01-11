import {Status} from './IndexStore'

export interface Language {
  name: string,
  status: Status
}

export default interface RuleMetadata {
  title: string,
  all_languages: Language[],
  allKeys: string[],
  branch: string,
  prUrl?: string
}
