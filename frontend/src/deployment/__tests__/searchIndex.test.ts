import path from 'path';
import lunr from 'lunr';

import { buildSearchIndex, buildIndexStore, DESCRIPTION_SPLIT_REGEX } from '../searchIndex';


describe('index store generation', () => {
  test('merges rules metadata', () => {
    const rulesPath = path.join(__dirname, 'resources', 'metadata');
    const [indexStore, _] = buildIndexStore(rulesPath);
    const ruleS3457 = indexStore['S3457'];

    expect(ruleS3457).toMatchObject({
      id: 'S3457',
      type: 'CODE_SMELL',
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

function createIndex() {
  const rulesPath = path.join(__dirname, 'resources', 'metadata');
  const [indexStore, _] = buildIndexStore(rulesPath);

  // Hack to avoid warnings when 'selectivePipeline' is already registered
  if ('selectivePipeline' in (lunr.Pipeline as any).registeredFunctions) {
    delete (lunr.Pipeline as any).registeredFunctions['selectivePipeline']
  }
  return buildSearchIndex(indexStore);
}


describe('search index enables search by title and description words', () => {
  test('searches in rule keys', () => {
    const searchIndex = createIndex();
    const searchesS3457 = search(searchIndex, 'S3457', 'all_keys');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = search(searchIndex, 'ppincludesignal', 'all_keys');
    expect(searchesS987).toEqual(['S987']);

    const searchesS1000 = search(searchIndex, 'UnnamedNamespaceInHeader', 'all_keys');
    expect(searchesS1000).toEqual(['S1000']);
  });

  test('searches in rule description', () => {
    const searchIndex = createIndex();
    const searchesS3457 = search(searchIndex, 'Because printf-style format', 'descriptions');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = search(searchIndex, 'Signal handling contains', 'descriptions');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = search(searchIndex, 'Unknown description', 'descriptions');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = search(searchIndex, 'Noncompliant Code Example', 'descriptions');
    expect(searchesBothRules.sort()).toEqual(['S1000', 'S3457', 'S987'].sort());
  });

  test('searches in rule title', () => {
    const searchIndex = createIndex();
    const searchesS3457 = search(searchIndex, 'Composite format strings', 'titles');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = search(searchIndex, 'signal.h used', 'titles');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = search(searchIndex, 'unknown title', 'titles');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = search(searchIndex, 'be should', 'titles');
    expect(searchesBothRules.sort()).toEqual(['S3457', 'S987'].sort());
  });

  function search(index: lunr.Index, query: string, field: string): string[] {
    const hits = index.query(q => {
      lunr.tokenizer(query).forEach(token => {
        q.term(token, {fields: [field], presence: lunr.Query.presence.REQUIRED})
      })
    });
    return hits.map(({ ref }) => ref)
  }
});

describe('search index enables search by tags, quality profiles and languages', () => {

  test('searches in rule tags', () => {
    const searchIndex = createIndex();
    const searchesS3457 = search(searchIndex, 'cert', 'tags');
    expect(searchesS3457).toHaveLength(2);
    expect(searchesS3457).toContain('S1000');
    expect(searchesS3457).toContain('S3457');

    const searchesS987 = search(searchIndex, 'based-on-misra', 'tags');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = search(searchIndex, 'unknown tag', 'tags');
    expect(searchesUnknown).toHaveLength(0);
  });

  test('searches in rule quality profiles', () => {
    const searchIndex = createIndex();
    const searchesSonarWay = search(searchIndex, 'sonar way', 'qualityProfiles');
    expect(searchesSonarWay).toEqual(['S1000', 'S3457']);

    const filtersAll = search(searchIndex, 'non-existent', 'qualityProfiles');
    expect(filtersAll).toEqual([]);
  });

  test('filter per language', () => {
    const searchIndex = createIndex();
    const csharpRules = search(searchIndex, 'csharp', 'languages');
    expect(csharpRules).toEqual(['S3457']);

    const cfamilyRules = search(searchIndex, 'cfamily', 'languages');
    expect(cfamilyRules.sort()).toEqual(['S987', 'S1000', 'S3457'].sort());
  });

  function search(index: lunr.Index, query: string, field: string): string[] {
    const hits = index.query(q => {
      q.term(query, {
        fields: [field],
        presence: lunr.Query.presence.REQUIRED,
        usePipeline: false
      });
    });
    return hits.map(({ ref }) => ref)
  }
});
