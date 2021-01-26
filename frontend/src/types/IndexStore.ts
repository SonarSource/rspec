export interface IndexedRule {
    id: number;
    languages: string[];
    // FIXME: type, defaultSeverity should never be null but the index generation has a bug
    type: 'BUG'|'CODE_SMELL'|'VULNERABILITY'|'SECURITY_HOTSPOT'|null;
    defaultSeverity: 'Blocker'|'Critical'|'Major'|'Minor'|'Info'|null,
    // FIXME: titles should be a list instead of being a concatenation of titles.
    titles: string,
    tags: string[],
    // FIXME: quality profiles seem to always be empty
    qualityProfiles: string[]
}

export type IndexStore = Record<string, IndexedRule>