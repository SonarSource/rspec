import fs from 'fs';
import path from 'path';

import { getRulesDirectories, listSupportedLanguages } from './utils';

/**
 * Generate rule metadata (for all relevant languages) and write it in the destination directory.
 * @param srcDir directory containing the original rule metadata and description.
 * @param dstDir directory where the generated metadata and description will be written.
 * @param branch the branch containing the given version of the rule. Typically 'master' but can be different for not merged rules.
 * @param prUrl optional link to the PR adding the rule. absent for merged rules.
 */
export function generateOneRuleMetadata(srcDir: string, dstDir: string,
                                           branch: string, prUrl?: string) {
  fs.mkdirSync(dstDir, { recursive: true });
  const allLanguages = listSupportedLanguages(srcDir);
  const allMetadata = allLanguages.map((language) => {
    const metadata = generateRuleMetadata(srcDir, language.name);
    return {language, metadata};
  });

  // Update language status for all
  allMetadata.forEach(m => {
    allLanguages.find(l => l === m.language)!.status = m.metadata.status ?? 'default';
  });

  // Merge all sqKeys in an array so that we can use it later to check rule coverage.
  const allKeys = allMetadata
    .reduce((set, {metadata}) => {
      set.add(metadata.sqKey);
      metadata.extra?.legacyKeys?.forEach((key: string) => set.add(key));
      return set;
    }, new Set<string>());
  const allKeysArray = Array.from(allKeys);
  allMetadata.forEach(({metadata}) => {
    metadata.allKeys = allKeysArray;
    if (prUrl) {
      metadata.prUrl = prUrl;
    }
    metadata.branch = branch;
    metadata.languages_support = allLanguages;
  });

  let default_metadata_wanted = true;
  for (const { language, metadata } of allMetadata) {
    const dstJsonFile = path.join(dstDir, language.name + '-metadata.json');
    fs.writeFileSync(dstJsonFile, JSON.stringify(metadata, null, 2), { encoding: 'utf8' })
    if (default_metadata_wanted) {
      const dstFile = path.join(dstDir, 'default-metadata.json');
      fs.writeFileSync(dstFile, JSON.stringify(metadata, null, 2), { encoding: 'utf8' });
      default_metadata_wanted = false;
    }
  }
}

/**
 * Generate rules metadata and write them in the destination directory.
 * @param srcPath directory containing the original rules metadata and description.
 * @param dstPath directory where the generated rules metadata and description will be written.
 * @param rules an optional list of rules to list. Other rules won't be generated.
 */
export function generateRulesMetadata(srcPath: string, dstPath: string, rules?: string[]) {
  for (const { srcDir, dstDir } of getRulesDirectories(srcPath, dstPath, rules)) {
    generateOneRuleMetadata(srcDir, dstDir, 'master');
  }
}

/**
 * Generate the metadata corresponding to one rule and one language.
 * @param srcDir rule's source directory.
 * @param language language for which the metadata should be generated
 */
function generateRuleMetadata(srcDir: string, language: string) {
  let parentFile = path.join(srcDir, language, 'metadata.json');
  const parentJson = fs.existsSync(parentFile) ? JSON.parse(fs.readFileSync(parentFile, 'utf8')) : {};
  let childFile = path.join(srcDir, 'metadata.json');
  const childJson = fs.existsSync(childFile) ? JSON.parse(fs.readFileSync(childFile, 'utf8')) : {};
  const mergedJson = {...childJson, ...parentJson};
  return mergedJson;
}
