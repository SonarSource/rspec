export type Severity = 'Blocker'|'Critical'|'Major'|'Minor'|'Info';

export interface IndexedRule {
    id: string;
    languages: string[];
    // FIXME: type, defaultSeverity should never be null but the index generation has a bug
    type: 'BUG'|'CODE_SMELL'|'VULNERABILITY'|'SECURITY_HOTSPOT';
    severities: Severity[],
    titles: string[],
    tags: string[],
    // FIXME: quality profiles seem to always be empty
    qualityProfiles: string[],
    prUrl?: string
}

export type IndexStore = Record<string, IndexedRule>
