import path from 'path';
import lunr from 'lunr';

import { buildSearchIndex, buildIndexStore, DESCRIPTION_SPLIT_REGEX } from '../searchIndex';
import { withTestDir, createFiles } from '../testutils';
import { IndexStore } from '../../types/IndexStore';


describe('index store generation', () => {
  test('merges rules metadata', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    const ruleS3457 = indexStore['S3457'];

    expect(ruleS3457).toMatchObject({
      id: 'S3457',
      types: ['CODE_SMELL'],
      supportedLanguages: [
        { "name": "cfamily", "status": "ready", },
        { "name": "csharp", "status": "ready", },
        { "name": "default", "status": "ready", },
        { "name": "java", "status": "closed", },
        { "name": "python", "status": "deprecated", }
      ],
      tags: ['cert', 'clumsy', 'confusing'],
      severities: ['Major', 'Minor'],
      qualityProfiles: ['MISRA C++ 2008 recommended', 'Sonar way'],
    });
  });

  test('stores description words', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    const ruleS3457 = indexStore['S3457'];

    const expectedWords = [
      ...'Because printf-style format strings are'.split(DESCRIPTION_SPLIT_REGEX),
      ...'Formatting strings, either with the % operator or'.split(DESCRIPTION_SPLIT_REGEX)
    ];

    expect(ruleS3457.descriptions).toEqual(expect.arrayContaining(expectedWords));
  });

  test('computes types correctly', () => {
    return withTestDir(async rulesPath => {
      createFiles(rulesPath, {
        'S100/default-metadata.json': JSON.stringify({
          title: 'Rule S100',
          type: 'CODE_SMELL',
        }),
        'S100/default-description.html': 'Description',
        'S100/java-metadata.json': JSON.stringify({
          title: 'Java Rule S100',
          type: 'CODE_SMELL',
        }),
        'S100/java-description.html': 'Description',

        'S101/default-metadata.json': JSON.stringify({
          title: 'Rule S101',
          type: 'CODE_SMELL',
        }),
        'S101/default-description.html': 'Description',
        'S101/java-metadata.json': JSON.stringify({
          title: 'Java Rule S101',
          type: 'CODE_SMELL',
        }),
        'S101/java-description.html': 'Description',
        'S101/python-metadata.json': JSON.stringify({
          title: 'Rule S101',
          type: 'VULNERABILITY',
        }),
        'S101/python-description.html': 'Description',
        'S101/cfamily-metadata.json': JSON.stringify({
          title: 'Rule S101',
          type: 'BUG',
        }),
        'S101/cfamily-description.html': 'Description',

        'S501/default-metadata.json': JSON.stringify({
          title: 'Rule S501',
          type: 'CODE_SMELL',
        }),
        'S501/default-description.html': 'Not implemented by any language',
      });

      const [indexStore, aggregates] = buildIndexStore(rulesPath);
      expect(aggregates.langs).toEqual({ 'cfamily': 1, 'default': 3, 'java': 2, 'python': 1 });

      const ruleS100 = indexStore['S100'];
      expect(ruleS100.types.sort()).toEqual(['CODE_SMELL']);

      const ruleS101 = indexStore['S101'];
      expect(ruleS101.types.sort()).toEqual(['BUG', 'CODE_SMELL', 'VULNERABILITY']);

      const ruleS501 = indexStore['S501'];
      expect(ruleS501.types.sort()).toEqual(['CODE_SMELL']);

      const searchIndex = createIndex(indexStore);

      expect(searchIndex.search('S501')).toHaveLength(1);
      expect(searchIndex.search('titles:S501')).toHaveLength(1);
      expect(searchIndex.search('titles:*')).toHaveLength(3);
      expect(searchIndex.search('types:*')).toHaveLength(3);

      // For types, the wildcard in the search query is required to succeed!
      // This may be related to how tokenization is handled (or not done for arrays),
      // but the actual reason doesn't matter for this test.
      expect(searchIndex.search('BUG')).toHaveLength(1);
      expect(searchIndex.search('types:BUG')).toHaveLength(1);
      expect(searchIndex.search('*SMELL')).toHaveLength(3);
      expect(searchIndex.search('types:*SMELL')).toHaveLength(3);
      expect(searchIndex.search('*VULNERABILITY')).toHaveLength(1);
      expect(searchIndex.search('types:*VULNERABILITY')).toHaveLength(1);

      const bugyRules = tokenizedSearch(searchIndex, 'BUG', 'types').sort();
      expect(bugyRules).toEqual(['S101']);
      const smellyRulesFuzzy = tokenizedSearch(searchIndex, '*SMELL*', 'types').sort();
      expect(smellyRulesFuzzy).toEqual(['S100', 'S101', 'S501']);
      const vulnerabilityRulesFuzzy = tokenizedSearch(searchIndex, 'VULNERABILITY*', 'types').sort();
      expect(vulnerabilityRulesFuzzy).toEqual(['S101']);
      const smellyRules = tokenizedSearch(searchIndex, 'CODE_SMELL*', 'types').sort();
      expect(smellyRules).toEqual(['S100', 'S101', 'S501']);

      expect(searchNormalizedField(searchIndex, '*', 'types').sort()).toEqual(['S100', 'S101', 'S501']);
      expect(searchNormalizedField(searchIndex, 'BUG', 'types').sort()).toEqual(['S101']);
      expect(searchNormalizedField(searchIndex, 'CODE_SMELL', 'types').sort()).toEqual(['S100', 'S101', 'S501']);
      expect(searchNormalizedField(searchIndex, 'VULNERABILITY', 'types').sort()).toEqual(['S101']);
    });
  });

  test('collects all tags', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.tags).toEqual({"based-on-misra": 1,
                                     "cert": 2,
                                     "clumsy": 2,
                                     "confusing": 1,
                                     "lock-in": 1,
                                     "misra-c++2008": 1,
                                     "pitfall": 1
                                    });
  });

  test('collects all languages', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.langs).toEqual({"cfamily": 3,
                                      "csharp": 1,
                                      "default": 3,
                                      "java": 1,
                                      "python": 1});
  });

  test('collects all rule keys', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    expect(indexStore['S3457'].all_keys).toEqual(['RSPEC-3457', 'S3457']);
    expect(indexStore['S1000'].all_keys).toEqual(['RSPEC-1000', 'S1000', 'UnnamedNamespaceInHeader']);
    expect(indexStore['S987'].all_keys).toEqual(['PPIncludeSignal', 'RSPEC-987', 'S987']);
  });

  test('collects all quality profiles', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.qualityProfiles).toEqual({
      "MISRA C++ 2008 recommended": 2,
      "Sonar way": 2});
  });
});

describe('search index enables search by title and description words', () => {
  test('searches in rule keys', () => {
    const searchIndex = createIndex();
    const searchesS3457 = tokenizedSearch(searchIndex, 'S3457', 'all_keys');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = tokenizedSearch(searchIndex, 'ppincludesignal', 'all_keys');
    expect(searchesS987).toEqual(['S987']);

    const searchesS1000 = tokenizedSearch(searchIndex, 'UnnamedNamespaceInHeader', 'all_keys');
    expect(searchesS1000).toEqual(['S1000']);
  });

  test('searches in rule description', () => {
    const searchIndex = createIndex();
    const searchesS3457 = tokenizedSearch(searchIndex, 'Because printf-style format', 'descriptions');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = tokenizedSearch(searchIndex, 'Signal handling contains', 'descriptions');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = tokenizedSearch(searchIndex, 'Unknown description', 'descriptions');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = tokenizedSearch(searchIndex, 'Noncompliant Code Example', 'descriptions');
    expect(searchesBothRules.sort()).toEqual(['S1000', 'S3457', 'S987'].sort());
  });

  test('searches in rule title', () => {
    const searchIndex = createIndex();
    const searchesS3457 = tokenizedSearch(searchIndex, 'Composite format strings', 'titles');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = tokenizedSearch(searchIndex, 'signal.h used', 'titles');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = tokenizedSearch(searchIndex, 'unknown title', 'titles');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = tokenizedSearch(searchIndex, 'be should', 'titles');
    expect(searchesBothRules.sort()).toEqual(['S3457', 'S987'].sort());
  });
});

describe('search index enables search by tags, quality profiles and languages', () => {

  test('searches in rule tags', () => {
    const searchIndex = createIndex();
    const searchesS3457 = searchExactField(searchIndex, 'cert', 'tags');
    expect(searchesS3457).toHaveLength(2);
    expect(searchesS3457).toContain('S1000');
    expect(searchesS3457).toContain('S3457');

    const searchesS987 = searchExactField(searchIndex, 'based-on-misra', 'tags');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = searchExactField(searchIndex, 'unknown tag', 'tags');
    expect(searchesUnknown).toHaveLength(0);
  });

  test('searches in rule quality profiles', () => {
    const searchIndex = createIndex();
    const searchesSonarWay = searchExactField(searchIndex, 'sonar way', 'qualityProfiles');
    expect(searchesSonarWay).toEqual(['S1000', 'S3457']);

    const filtersAll = searchExactField(searchIndex, 'non-existent', 'qualityProfiles');
    expect(filtersAll).toEqual([]);
  });

  test('filter per language', () => {
    const searchIndex = createIndex();
    const csharpRules = searchExactField(searchIndex, 'csharp', 'languages');
    expect(csharpRules).toEqual(['S3457']);

    const cfamilyRules = searchExactField(searchIndex, 'cfamily', 'languages');
    expect(cfamilyRules.sort()).toEqual(['S987', 'S1000', 'S3457'].sort());
  });
});

function createIndex(ruleIndexStore?: IndexStore) {
  if (!ruleIndexStore) {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    ruleIndexStore = indexStore;
  }

  // Hack to avoid warnings when 'selectivePipeline' is already registered
  if ('selectivePipeline' in (lunr.Pipeline as any).registeredFunctions) {
    delete (lunr.Pipeline as any).registeredFunctions['selectivePipeline']
  }
  return buildSearchIndex(ruleIndexStore);
}

// These search functions mimic the behaviors of useSearch.ts.

function tokenizedSearch(index: lunr.Index, query: string, field: string): string[] {
  const hits = index.query(q => {
    lunr.tokenizer(query).forEach(token => {
      q.term(token, {
        fields: [field],
        presence: lunr.Query.presence.REQUIRED
      })
    })
  });
  return hits.map(({ ref }) => ref)
}

function searchExactField(index: lunr.Index, query: string, field: string): string[] {
  const hits = index.query(q => {
    q.term(query, {
      fields: [field],
      presence: lunr.Query.presence.REQUIRED,
      usePipeline: false
    });
  });
  return hits.map(({ ref }) => ref)
}

function searchNormalizedField(index: lunr.Index, query: string, field: string): string[] {
  const hits = index.query(q => {
    q.term(query.toLowerCase(), {
      fields: [field],
      presence: lunr.Query.presence.REQUIRED,
      usePipeline: false
    });
  });
  return hits.map(({ ref }) => ref)
}
