import {LanguageSupport} from './RuleMetadata';

export type Severity = 'Blocker'|'Critical'|'Major'|'Minor'|'Info';
export type Type = 'BUG'|'CODE_SMELL'|'VULNERABILITY'|'SECURITY_HOTSPOT';

export interface IndexedRule {
    id: string;
    supportedLanguages: LanguageSupport[];
    // FIXME: type, defaultSeverity should never be null but the index generation has a bug
    types: Type[];
    severities: Severity[];
    all_keys: string[];
    titles: string[];
    tags: string[];
    qualityProfiles: string[];
    prUrl?: string;
}

export type IndexStore = Record<string, IndexedRule>

export interface IndexAggregates {
    langs: { [id: string]: number };
    tags: { [id: string]: number };
    qualityProfiles: { [id: string]: number };
}
