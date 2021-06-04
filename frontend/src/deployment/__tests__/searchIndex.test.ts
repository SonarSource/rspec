import path from 'path';
import lunr from 'lunr';

import { buildSearchIndex, buildIndexStore, DESCRIPTION_SPLIT_REGEX } from '../searchIndex';


describe('index store generation', () => {
  test('merges rules metadata', () => {
    const rulesPath = path.join(__dirname, 'resources', 'plugin_rules');
    const [indexStore, _] = buildIndexStore(rulesPath);
    const ruleS3457 = indexStore['S3457'];

    expect(ruleS3457).toMatchObject({
      id: 'S3457',
      type: 'CODE_SMELL',
      languages: ['cfamily', 'csharp', 'java', 'python'],
      tags: ['cert', 'clumsy', 'confusing'],
      severities: ['Major', 'Minor'],
      qualityProfiles: ['MISRA C++ 2008 recommended', 'Sonar way'],
    });
  });

  test('stores description words', () => {
    const rulesPath = path.join(__dirname, 'resources', 'plugin_rules');
    const [indexStore, _] = buildIndexStore(rulesPath);
    const ruleS3457 = indexStore['S3457'];

    const expectedWords = [
      ...'Because printf-style format strings are'.split(DESCRIPTION_SPLIT_REGEX),
      ...'Formatting strings, either with the % operator or'.split(DESCRIPTION_SPLIT_REGEX)
    ];

    expect(ruleS3457.descriptions).toEqual(expect.arrayContaining(expectedWords));
  });

  test('collect all tags', () => {
    const rulesPath = path.join(__dirname, 'resources', 'plugin_rules');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.tags).toEqual({"based-on-misra": 1,
                                     "cert": 4,
                                     "clumsy": 4,
                                     "confusing": 4,
                                     "lock-in": 1});
  });
  test('collect all languages', () => {
    const rulesPath = path.join(__dirname, 'resources', 'plugin_rules');
    const [_, aggregates] = buildIndexStore(rulesPath);
    expect(aggregates.langs).toEqual({"cfamily": 2,
                                      "csharp": 1,
                                      "java": 1,
                                      "python": 1});
  });
});

describe('search index enables search by title and description words', () => {
  test('searches in rule description', () => {
    const searchIndex = createIndex();
    const searchesS3457 = search(searchIndex, 'Because printf-style format', 'descriptions');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = search(searchIndex, 'Signal handling contains', 'descriptions');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = search(searchIndex, 'Unknown description', 'descriptions');
    expect(searchesUnknown).toHaveLength(0);

    const searchesBothRules = search(searchIndex, 'Noncompliant Code Example', 'descriptions');
    expect(searchesBothRules.sort()).toEqual(['S3457', 'S987'].sort());
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

  test('searches in rule tags', () => {
    const searchIndex = createIndex();
    const searchesS3457 = search(searchIndex, 'cert', 'tags');
    expect(searchesS3457).toEqual(['S3457']);

    const searchesS987 = search(searchIndex, 'based-on-misra', 'tags');
    expect(searchesS987).toEqual(['S987']);

    const searchesUnknown = search(searchIndex, 'unknown tag', 'tags');
    expect(searchesUnknown).toHaveLength(0);
  });

  function createIndex() {
    const rulesPath = path.join(__dirname, 'resources', 'plugin_rules');
    const [indexStore, _] = buildIndexStore(rulesPath);

    // Hack to avoid warnings when 'selectivePipeline' is already registered
    if ('selectivePipeline' in (lunr.Pipeline as any).registeredFunctions) {
      delete (lunr.Pipeline as any).registeredFunctions['selectivePipeline']
    }
    return buildSearchIndex(indexStore);
  }
  
  function search(index: lunr.Index, query: string, field: string): string[] {
    const hits = index.query(q => {
      if (field === 'titles' || field === 'descriptions') {
        lunr.tokenizer(query).forEach(token => {
          q.term(token, {fields: [field], presence: lunr.Query.presence.REQUIRED})
        })
      } else if (field === 'tags') {
        q.term(query, {
          fields: ['tags'],
          presence: lunr.Query.presence.REQUIRED,
          usePipeline: false
        });
      }
    });
    return hits.map(({ ref }) => ref)
  }
});
