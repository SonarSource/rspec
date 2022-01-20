import fs from 'fs';
import path from 'path';

import { LanguageSupport } from '../types/RuleMetadata';
import { getRulesDirectories, listSupportedLanguages } from './utils';

/**
 * Save the given metadata to disk.
 */
function writeRuleMetadata(dstDir: string, filename: string, metadata: any) {
  const file = path.join(dstDir, filename);
  fs.writeFileSync(file, JSON.stringify(metadata), { encoding: 'utf8' });
}

/**
 * Merge all sqKeys in an array to check rule coverage.
 */
function getAllKeys(allMetadata: { metadata: any }[]) {
  const keys = allMetadata.reduce((set, { metadata }) => {
    set.add(metadata.sqKey);
    metadata.extra?.legacyKeys?.forEach((key: string) => set.add(key));
    return set;
  }, new Set<string>());
  return Array.from(keys);
}

/**
 * Generate the default metadata for a rule without any language-specific data.
 */
function generateGenericMetadata(srcDir: string, dstDir: string, branch: string, prUrl?: string) {
  const metadata = getRuleMetadata(srcDir);
  metadata.languagesSupport = [];
  metadata.allKeys = getAllKeys([{ metadata }]);
  if (prUrl) {
    metadata.prUrl = prUrl;
  }
  metadata.branch = branch;

  writeRuleMetadata(dstDir, 'default-metadata.json', metadata);
}

/**
 * Generate rule metadata (for all relevant languages) and write it in the destination directory.
 * @param srcDir directory containing the original rule's metadata and description.
 * @param dstDir directory where the generated metadata will be written.
 * @param branch the branch containing the given version of the rule.
 *               Typically 'master' but can be different for not merged rules.
 * @param prUrl optional link to the PR adding the rule. Absent for merged rules.
 */
export function generateOneRuleMetadata(srcDir: string, dstDir: string, branch: string, prUrl?: string) {
  fs.mkdirSync(dstDir, { recursive: true });
  const allLanguages = listSupportedLanguages(srcDir);
  if (allLanguages.length === 0) {
    generateGenericMetadata(srcDir, dstDir, branch, prUrl);
    return;
  }

  const allMetadata = allLanguages.map((language) => {
    const metadata = getRuleMetadata(srcDir, language);
    return { language, metadata };
  });

  // Update language status for all
  const languageSupports =
    allMetadata.map(m => ({ name: m.language, status: m.metadata.status } as LanguageSupport));

  const allKeys = getAllKeys(allMetadata);
  allMetadata.forEach(({ metadata }) => {
    metadata.allKeys = allKeys;
    if (prUrl) {
      metadata.prUrl = prUrl;
    }
    metadata.branch = branch;
    metadata.languagesSupport = languageSupports;
  });

  let isFirstLanguage = true;
  for (const { language, metadata } of allMetadata) {
    writeRuleMetadata(dstDir, language + '-metadata.json', metadata);

    if (isFirstLanguage) {
      // Use the first language as the default metadata.
      writeRuleMetadata(dstDir, 'default-metadata.json', metadata);
      isFirstLanguage = false;
    }
  }
}

/**
 * Generate one directory per rule with its JSON metadata.
 * @param srcPath directory containing all the rules subdirectories, with the metadata and descriptions.
 * @param dstPath directory where rule directories should be created.
 * @param rules an optional list of rules to process. Other rules won't be generated.
 */
export function generateRulesMetadata(srcPath: string, dstPath: string, rules?: string[]) {
  for (const { srcDir, dstDir } of getRulesDirectories(srcPath, dstPath, rules)) {
    generateOneRuleMetadata(srcDir, dstDir, 'master');
  }
}

/**
 * Generate the metadata corresponding to one rule and one language.
 * @param srcDir rule's source directory.
 * @param language language for which the metadata should be generated (or none)
 */
function getRuleMetadata(srcDir: string, language?: string) {
  const parentJson = (() => {
    if (!language) {
      return {};
    }
    const parentFile = path.join(srcDir, language, 'metadata.json');
    if (fs.existsSync(parentFile)) {
      return JSON.parse(fs.readFileSync(parentFile, 'utf8'));
    }
    return {};
  })();
  const childFile = path.join(srcDir, 'metadata.json');
  const childJson = fs.existsSync(childFile) ? JSON.parse(fs.readFileSync(childFile, 'utf8')) : {};
  return { ...childJson, ...parentJson };
}
