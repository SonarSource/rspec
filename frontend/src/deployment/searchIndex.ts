
import fs from 'fs';
import path from 'path';

import { stripHtml } from 'string-strip-html';
import lunr, { Token } from 'lunr';

import { IndexedRule, IndexStore, Severity, Status, IndexAggregates } from '../types/IndexStore';
import { logger as rootLogger } from './deploymentLogger';

const logger = rootLogger.child({ source: path.basename(__filename) })


export const DESCRIPTION_SPLIT_REGEX = /[\s,.:;!?()"'-+*/\\%#]+/;

export interface IndexedRuleWithDescription extends IndexedRule {
  descriptions?: Array<string>;
}

/**
 * Create the index store. This store is indexed by lunr and later used by the frontend.
 * Whenever the lunr index finds something it returns IDs. The frontend will look at
 * metadata corresponding to this ID in the index store.
 * @param rulesPath Path to the directory containing aggregated metadata and rules
 *                  descriptions in HTML format.
 */
export function buildIndexStore(rulesPath: string):[Record<string,IndexedRuleWithDescription>, IndexAggregates] {
  let ruleDirs = fs.readdirSync(rulesPath).filter((fileName) => {
    const fullpath = path.join(rulesPath, fileName);
    return fs.lstatSync(fullpath).isDirectory();
  });
  let allTags: { [id: string]: number } = {};
  let allLangs: { [id: string]: number } = {};
  let allQualityProfiles: { [id: string]: number } = {};
  const indexedRecords = ruleDirs.map<[string, IndexedRuleWithDescription] | null>((ruleDir) => {
    const allLanguages = fs.readdirSync(path.join(rulesPath, ruleDir))
                            .filter((fileName) => fileName.endsWith('-metadata.json'))
                            .map((fileName) => fileName.split('-')[0]);

    let types = new Set<string>();
    let severities = new Set<Severity>();
    let statuses = new Array<Status>();
    const all_keys = new Set<string>([ruleDir]);
    const titles = new Set<string>();
    const tags = new Set<string>();
    const qualityProfiles = new Set<string>();
    const descriptions = new Set<string>();
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
      all_keys.add(metadata.sqKey);
      all_keys.add(metadata.ruleSpecification);
      titles.add(metadata.title);
      types.add(metadata.type);
      severities.add(metadata.defaultSeverity as Severity);
      statuses.push((metadata.status ?? 'default') as Status);
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
      if (lang in allLangs) {
        allLangs[lang] += 1;
      } else {
        allLangs[lang] = 1;
      }
      tags.forEach((tag) => {
        if (tag in allTags) {
          allTags[tag] += 1;
        } else {
          allTags[tag] = 1;
        }
      });
    });
    qualityProfiles.forEach((qualityProfile) => {
      if (qualityProfile in allQualityProfiles) {
        allQualityProfiles[qualityProfile] += 1;
      } else {
        allQualityProfiles[qualityProfile] = 1;
      }
    });

    if (allLanguages.length < 1) {
      logger.error(`No languages found for rule ${ruleDir}, at least 1 is required`);
      return null;
    }
    if (types.size !== 1) {
      logger.error(`${types.size} type(s) found for rule ${ruleDir}, 1 is required: ${JSON.stringify(types)}`);
      return null;
    }
    if (severities.size < 1) {
      logger.error(`No severity found for rule ${ruleDir}, at least 1 is required`);
      return null;
    }

    const indexedRecord: IndexedRuleWithDescription = {
      id: ruleDir,
      languages: allLanguages.sort(),
      type: types.values().next().value,
      severities: Array.from(severities).sort(),
      all_keys: Array.from(all_keys).sort(),
      titles: Array.from(titles).sort(),
      tags: Array.from(tags).sort(),
      qualityProfiles: Array.from(qualityProfiles).sort(),
      descriptions: Array.from(descriptions).sort(),
      statuses: statuses,
      prUrl
    }

    return [ruleDir, indexedRecord];
  });

  const filteredRecords = indexedRecords.filter((value) => value !== null) as [string, IndexedRuleWithDescription][];

  return [Object.fromEntries(filteredRecords),
          {langs: allLangs, tags: allTags, qualityProfiles: allQualityProfiles}];
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
    if (fields.includes('all_keys') || fields.includes('titles') || fields.includes('descriptions') ) {
      // We don't use the stopword filter to allow words such as "do", "while", "for"
      const trimmed = lunr.trimmer(token);
      return lunr.stemmer(trimmed);
    }
    return token;
  }

  lunr.Pipeline.registerFunction(selectivePipeline, 'selectivePipeline');

  var ruleIndex = lunr(function () {
      // Set our own token processing pipeline
      this.pipeline.reset();
      this.pipeline.add(selectivePipeline);

      this.ref('id');
      this.field('titles');
      this.field('type');
      this.field('languages');
      this.field('defaultSeverity');
      this.field('tags');
      this.field('qualityProfiles');
      this.field('descriptions');
      this.field('all_keys');

      for (const searchRecord of Object.values(ruleIndexStore)) {
          const transformedRecord: any = { ...searchRecord };
          transformedRecord.titles = searchRecord.titles.join('\n');
          this.add(transformedRecord);
      }
  })

  return ruleIndex;
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
  const indexStoreJson = JSON.stringify(indexStore, null, 2);
  const indexStorePath = path.join(rulesPath, "rule-index-store.json")
  fs.writeFileSync(indexStorePath, indexStoreJson, {encoding: 'utf8', flag: 'w'});

  const aggregatesJson = JSON.stringify(indexAggregates);
  const aggregatesPath = path.join(rulesPath, "rule-index-aggregates.json");
  fs.writeFileSync(aggregatesPath, aggregatesJson, {encoding: 'utf8', flag: 'w'});
}
