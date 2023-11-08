import path from 'path';
import lunr from 'lunr';

import { buildSearchIndex, buildIndexStore, DESCRIPTION_SPLIT_REGEX } from '../searchIndex';
import { withTestDir, createFiles } from '../testutils';
import { IndexStore } from '../../types/IndexStore';
import {
  addFilterForKeysTitlesDescriptions, addFilterForLanguages,
  addFilterForQualityProfiles, addFilterForTags, addFilterForTypes
} from '../../utils/useSearch';

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
      qualityProfiles: ['Sonar way'],
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

      expect(findRulesByType(searchIndex, '*').sort()).toEqual(['S100', 'S101', 'S501']);
      expect(findRulesByType(searchIndex, 'BUG').sort()).toEqual(['S101']);
      expect(findRulesByType(searchIndex, 'CODE_SMELL').sort()).toEqual(['S100', 'S101', 'S501']);
      expect(findRulesByType(searchIndex, 'VULNERABILITY').sort()).toEqual(['S101']);
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
                                     "misra": 1,
                                     "misra-c++2008": 1,
                                     "pitfall": 1
                                    });
  });

  test('collects all languages', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.langs).toEqual({"cfamily": 4,
                                      "csharp": 1,
                                      "default": 5,
                                      "java": 2,
                                      "python": 1});
  });

  test('collects all rule keys', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    expect(indexStore['S3457'].all_keys).toEqual(['RSPEC-3457', 'S3457']);
    expect(indexStore['S1000'].all_keys).toEqual(['RSPEC-1000', 'S1000', 'UnnamedNamespaceInHeader']);
    expect(indexStore['S987'].all_keys).toEqual(['ALegacyKey', 'PPIncludeSignal', 'RSPEC-987', 'S987']);
  });

  test('collects all quality profiles', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.qualityProfiles).toEqual({
      "Sonar way": 3});
  });
});

describe('search index enables search by title and description words', () => {
  test('searches in rule keys', () => {
    const searchIndex = createIndex();
    const searchesS3457 = findRuleByQuery(searchIndex, 'S3457');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = findRuleByQuery(searchIndex, 'pPIncLuDeSiGNal');
    expect(searchesS987).toEqual(['S987']);

    const searchesByLegacy = findRuleByQuery(searchIndex, 'aLegacyKey');
    expect(searchesByLegacy).toEqual(['S987']);

    const searchesS1000 = findRuleByQuery(searchIndex, 'UnnamedNamespaceInHeader');
    expect(searchesS1000).toEqual(['S1000']);
  });

  test('searches in rule description', () => {
    const searchIndex = createIndex();
    const searchesS3457 = findRuleByQuery(searchIndex, 'Because printf-style format');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = findRuleByQuery(searchIndex, 'Signal handling contains');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = findRuleByQuery(searchIndex, 'Unknown description');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = findRuleByQuery(searchIndex, 'Noncompliant Code Example');
    expect(searchesBothRules).toEqual(['S1000', 'S3457', 'S987'].sort());

    const searchesRuleMentions = findRuleByQuery(searchIndex, 'S1000');
    expect(searchesRuleMentions).toEqual(['S987', 'S1000'].sort());
  });

  test('searches in rule title', () => {
    const searchIndex = createIndex();
    const searchesS3457 = findRuleByQuery(searchIndex, 'Composite format strings');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = findRuleByQuery(searchIndex, 'signal.h used');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = findRuleByQuery(searchIndex, 'unknown title');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = findRuleByQuery(searchIndex, 'should be used');
    expect(searchesBothRules).toEqual(['S1007', 'S3457', 'S987'].sort());
  });
});

describe('search index enables search by tags, quality profiles and languages', () => {

  test('searches in rule tags', () => {
    const searchIndex = createIndex();
    const searchesS3457 = findRulesByTags(searchIndex, ['cert']);
    expect(searchesS3457).toHaveLength(2);
    expect(searchesS3457).toContain('S1000');
    expect(searchesS3457).toContain('S3457');

    const searchesS987 = findRulesByTags(searchIndex, ['based-on-misra', 'lock-in']);
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = findRulesByTags(searchIndex, ['unknown tag']);
    expect(searchesUnknown).toHaveLength(0);
  });

  test('searches in rule quality profiles', () => {
    const searchIndex = createIndex();
    const searchesSonarWay = findRulesByProfile(searchIndex, 'sonar way');
    expect(searchesSonarWay.sort()).toEqual(['S1000', 'S3457', 'S3649']);

    const filtersAll = findRulesByProfile(searchIndex, 'non-existent');
    expect(filtersAll).toEqual([]);
  });

  test('filter per language', () => {
    const searchIndex = createIndex();
    const csharpRules = findRulesByLanguage(searchIndex, 'csharp');
    expect(csharpRules).toEqual(['S3457']);

    const cfamilyRules = findRulesByLanguage(searchIndex, 'cfamily');
    expect(cfamilyRules.sort()).toEqual(['S987', 'S1000', 'S1007', 'S3457'].sort());
  });
});

function createIndex(ruleIndexStore?: IndexStore) {
  if (!ruleIndexStore) {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    ruleIndexStore = indexStore;
  }

  return buildSearchIndex(ruleIndexStore);
}

afterEach(() => {
  // Hack to avoid warnings when 'selectivePipeline' is already registered
  if ('selectivePipeline' in (lunr.Pipeline as any).registeredFunctions) {
    delete (lunr.Pipeline as any).registeredFunctions['selectivePipeline'];
  }
});

function findRules<QueryParam>(
  index: lunr.Index,
  filter: (q: lunr.Query, param: QueryParam) => void,
  param: QueryParam
): string[] {
  const hits = index.query(q => filter(q, param));
  return hits.map(({ ref }) => ref);
}

function findRulesByType(index: lunr.Index, type: string): string[] {
  return findRules(index, addFilterForTypes, type);
}

function findRulesByTags(index: lunr.Index, tags: string[]): string[] {
  return findRules(index, addFilterForTags, tags);
}

function findRulesByLanguage(index: lunr.Index, language: string): string[] {
  return findRules(index, addFilterForLanguages, language);
}

function findRulesByProfile(index: lunr.Index, profile: string): string[] {
  return findRules(index, addFilterForQualityProfiles, [profile]);
}

function findRuleByQuery(index: lunr.Index, query: string): string[] {
  const rules = findRules(index, addFilterForKeysTitlesDescriptions, query);
  return rules.sort();
}
