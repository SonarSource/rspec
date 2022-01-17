
import fs from 'fs';
import path from 'path';

/**
 * Get the list of source and destination directories for each rule.
 * Destination directories will be created if they don't already exist.
 * @param srcPath directory containing the original rules metadata and description.
 * @param dstPath directory where the generated rules metadata and description will be written.
 * @param rules an optional list of rules to list. Other rules won't be listed.
 */
export function getRulesDirectories(srcPath: string, dstPath: string, rules?: string[]) {
  let ruleDirs = fs.readdirSync(srcPath);
  if (rules) {
    ruleDirs = ruleDirs.filter(fileName => rules.includes(fileName));
  }

  return ruleDirs.map(function (fileName) {
    const srcDir = path.join(srcPath, fileName);
    const dstDir = path.join(dstPath, fileName);
    fs.mkdirSync(dstDir, { recursive: true });
    return { srcDir, dstDir };
  });
}

/**
 * List every language for which a rule has a specialization, i.e. a sub-directory.
 * @param ruleDirectory the rule's source directory
 */
export function listSupportedLanguages(ruleDirectory: string): string[] {
  return fs.readdirSync(ruleDirectory)
    .filter(fileName => fs.lstatSync(path.join(ruleDirectory, fileName)).isDirectory())
    .sort();
}