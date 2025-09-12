
import fs from 'fs';
import path from 'path';

import { stripHtml } from 'string-strip-html';
import lunr, { Token } from 'lunr';

import { IndexedRule, IndexStore, Severity, Type, IndexAggregates } from '../types/IndexStore';
import { logger as rootLogger } from './deploymentLogger';
import { LanguageSupport } from '../types/RuleMetadata';

const logger = rootLogger.child({ source: path.basename(__filename) })


export const DESCRIPTION_SPLIT_REGEX = /[\s,.:;!?()"'-+*/\\%#]+/;

export interface IndexedRuleWithDescription extends IndexedRule {
  descriptions?: Array<string>;
}

function buildOneRuleRecord(allLanguages: string[], rulesPath: string, ruleDir: string) {

  const types = new Set<Type>();
  const severities = new Set<Severity>();
  const allKeys = new Set<string>([ruleDir]);
  const titles = new Set<string>();
  const tags = new Set<string>();
  const qualityProfiles = new Set<string>();
  const descriptions = new Set<string>();
  const supportedLanguages : LanguageSupport[] = [];
  let prUrl = undefined;

  allLanguages.forEach((lang) => {
    // extract every word of every description of this rule
    const descriptionPath = path.join(rulesPath, ruleDir, `${lang}-description.html`);
    const descriptionStr = fs.readFileSync(descriptionPath).toString();
    // Remove HTML tags from the description, extract unique words and normalize them.
    // This reduces a bit the footprint of descriptions in the index.
    const descriptionWords = stripHtml(descriptionStr).result.split(DESCRIPTION_SPLIT_REGEX)
    descriptionWords.forEach((word) => descriptions.add(word));

    // merge metadata fields of every version of this rule in a single indexed record
    const metadataPath = path.join(rulesPath, ruleDir, `${lang}-metadata.json`);
    const metadataStr = fs.readFileSync(metadataPath).toString();
    const metadata = JSON.parse(metadataStr);

    if (metadata.prUrl) {
      prUrl = metadata.prUrl;
    }
    allKeys.add(metadata.sqKey);
    allKeys.add(metadata.ruleSpecification);
    metadata.extra?.legacyKeys?.forEach((legacyKey: string) => allKeys.add(legacyKey));
    titles.add(metadata.title);
    types.add(metadata.type);
    severities.add(metadata.defaultSeverity as Severity);
    supportedLanguages.push({name: lang, status: metadata.status});
    if (metadata.tags) {
      for (const tag of metadata.tags) {
        tags.add(tag);
      }
    }
    if (metadata.defaultQualityProfiles) {
      for (const qualityProfile of metadata.defaultQualityProfiles) {
        qualityProfiles.add(qualityProfile);
      }
    }
  });
  return {
    types,
    severities,
    allKeys,
    titles,
    supportedLanguages,
    tags,
    qualityProfiles,
    descriptions,
    prUrl
  };
}

function buildOneRuleIndexedRecord(rulesPath: string, ruleDir: string)
  : [string, IndexedRuleWithDescription] | null {

  const allLanguages = fs.readdirSync(path.join(rulesPath, ruleDir))
    .filter((fileName) => fileName.endsWith('-metadata.json'))
    .map((fileName) => (fileName.split('-')[0]));

  const record = buildOneRuleRecord(allLanguages, rulesPath, ruleDir);

  if (allLanguages.length < 1) {
    logger.error(`No languages found for rule ${ruleDir}, at least 1 is required`);
    return null;
  }
  if (record.types.size < 1) {
    logger.error(
      `${record.types.size} type(s) found for rule ${ruleDir}, 1 is required: ${JSON.stringify(record.types)}`);
    return null;
  }
  if (record.severities.size < 1) {
    logger.error(`No severity found for rule ${ruleDir}, at least 1 is required`);
    return null;
  }

  const indexedRecord: IndexedRuleWithDescription = {
    id: ruleDir,
    supportedLanguages: Array.from(record.supportedLanguages).sort((a, b) => a.name.localeCompare(b.name)),
    types: Array.from(record.types).sort((a, b) => a.localeCompare(b)),
    severities: Array.from(record.severities).sort((a, b) => a.localeCompare(b)),
    all_keys: Array.from(record.allKeys).sort((a, b) => a.localeCompare(b)),
    titles: Array.from(record.titles).sort((a, b) => a.localeCompare(b)),
    tags: Array.from(record.tags).sort((a, b) => a.localeCompare(b)),
    qualityProfiles: Array.from(record.qualityProfiles).sort((a, b) => a.localeCompare(b)),
    descriptions: Array.from(record.descriptions).sort((a, b) => a.localeCompare(b)),
    prUrl: record.prUrl
  }

  return [ruleDir, indexedRecord];
}

function buildIndexAggregates(indexedRecords: [string, IndexedRuleWithDescription][]): IndexAggregates {
  const aggregates: IndexAggregates = { langs: {}, tags: {}, qualityProfiles: {} };

  indexedRecords.forEach(record => {
    record[1].qualityProfiles.forEach((qualityProfile) => {
      if (qualityProfile in aggregates.qualityProfiles) {
        aggregates.qualityProfiles[qualityProfile] += 1;
      } else {
        aggregates.qualityProfiles[qualityProfile] = 1;
      }
    });
    record[1].supportedLanguages.forEach(lang => {
      if (lang.name in aggregates.langs) {
        aggregates.langs[lang.name] += 1;
      } else {
        aggregates.langs[lang.name] = 1;
      }
    });
    record[1].tags.forEach((tag) => {
      if (tag in aggregates.tags) {
        aggregates.tags[tag] += 1;
      } else {
        aggregates.tags[tag] = 1;
      }
    });
  });
  return aggregates;
}

/**
 * Create the index store. This store is indexed by lunr and later used by the frontend.
 * Whenever the lunr index finds something it returns IDs. The frontend will look at
 * metadata corresponding to this ID in the index store.
 * @param rulesPath Path to the directory containing aggregated metadata and rules
 *                  descriptions in HTML format.
 */
export function buildIndexStore(rulesPath: string):[Record<string,IndexedRuleWithDescription>, IndexAggregates] {
  const ruleDirs = fs.readdirSync(rulesPath).filter((fileName) => {
    const fullpath = path.join(rulesPath, fileName);
    return fs.lstatSync(fullpath).isDirectory();
  });
  const indexedRecords = ruleDirs.map((ruleDir) => buildOneRuleIndexedRecord(rulesPath, ruleDir));
  const filteredRecords = indexedRecords.filter((value) => value !== null) as [string, IndexedRuleWithDescription][];
  return [Object.fromEntries(filteredRecords), buildIndexAggregates(filteredRecords)];
}

/**
 * Create a lunr search index from the provided index store.
 * @param ruleIndexStore index store to index with lunr.
 */
export function buildSearchIndex(ruleIndexStore: IndexStore) {
  function selectivePipeline(token: Token) {
    // Lunr documentation shows that we can use the "metadata" property, but
    // it is not declared in the Token class. Thus we cast as any here.
    const fields = (token as any).metadata["fields"];
    // process only titles and descriptions
    if (fields.includes('all_keys') || fields.includes('titles') || fields.includes('descriptions')) {
      // We don't use the stopword filter to allow words such as "do", "while", "for"
      const trimmed = lunr.trimmer(token);
      return lunr.stemmer(trimmed);
    }
    return token;
  }

  lunr.Pipeline.registerFunction(selectivePipeline, 'selectivePipeline');

  return lunr(function () {
    // Set our own token processing pipeline
    this.pipeline.reset();
    this.pipeline.add(selectivePipeline);

    this.ref('id');
    this.field('titles', { extractor: (doc) => (doc as IndexedRule).titles.join('\n') });
    this.field('types');
    this.field('languages', { extractor: (doc) => (doc as IndexedRule).supportedLanguages.map(lang => lang.name) });
    this.field('defaultSeverity');
    this.field('tags');
    this.field('qualityProfiles');
    this.field('descriptions');
    this.field('all_keys');

    for (const searchRecord of Object.values(ruleIndexStore)) {
      this.add(searchRecord);
    }
  })
}

/**
 * Read rules from provided directory, create the corresponding index store
 * and search index and finally write both of them back in the rules directory.
 * @param rulesPath Path to the directory containing aggregated metadata and rules
 *                  descriptions in HTML format.
 */
export function createIndexFiles(rulesPath: string) {
  const [indexStore, indexAggregates] = buildIndexStore(rulesPath);
  const searchIndex = buildSearchIndex(indexStore);
  const searchIndexJson = JSON.stringify(searchIndex);
  const searchIndexPath = path.join(rulesPath, "rule-index.json");
  fs.writeFileSync(searchIndexPath, searchIndexJson, {encoding: 'utf8', flag: 'w'});
  // Remove the descriptions as they are only interesting for indexing
  for (const rule of Object.values(indexStore)) {
      delete rule.descriptions;
  }
  const indexStoreJson = JSON.stringify(indexStore);
  const indexStorePath = path.join(rulesPath, "rule-index-store.json")
  fs.writeFileSync(indexStorePath, indexStoreJson, {encoding: 'utf8', flag: 'w'});

  const aggregatesJson = JSON.stringify(indexAggregates);
  const aggregatesPath = path.join(rulesPath, "rule-index-aggregates.json");
  fs.writeFileSync(aggregatesPath, aggregatesJson, {encoding: 'utf8', flag: 'w'});
}
