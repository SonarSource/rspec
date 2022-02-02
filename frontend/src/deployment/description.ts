import fs from 'fs';
import path from 'path';
import asciidoctor from 'asciidoctor';

import { getRulesDirectories, listSupportedLanguages } from './utils';
import { logger } from './deploymentLogger';

const asciidoc = asciidoctor();

function generateAutoRspecLinks(html: string) {
  // Insert placeholder links for SXXX or RSPEC-XXX to the appropriate description page.
  //
  // The web application is responsible for providing the target link.
  // The link will depend on whether the default page is viewed, and in that case it will
  // point to the default page for the target rules, or whether a language-specific page
  // is viewed.
  // The distinction cannot be made when generating the HTML description because the description
  // for the first language is also used as the default description.
  return html.replace(
    /(S|RSPEC-)(\d{3,})/g,
    '<a data-rspec-id="S$2" class="rspec-auto-link">$1$2</a>'
  );
}

const winstonLogger = asciidoc.LoggerManager.newLogger('WinstonLogger', {
  postConstruct: function () {
    this.logger = logger
  },
  add: function (severity: any, _: any, message: any) {
    const level = severity >= 3 ? 'error' : 'warning';
    const location = message.getSourceLocation();
    this.logger.log({
      level: level,
      message: message.getText(),
      source: path.basename(__filename),
      file: location.getFile(),
      line: location.getLineNumber()
    })
  }
});
asciidoc.LoggerManager.setLogger(winstonLogger);

/**
 * Save the given HTML description to disk.
 */
function writeRuleDescription(dstDir: string, filename: string, html: string) {
  const file = path.join(dstDir, filename);
  fs.writeFileSync(file, html, { encoding: 'utf8' });
}

/**
 * Generate the default description for a rule without any language-specific data.
 */
function generateGenericDescription(srcDir: string, dstDir: string) {
  const adocFile = getRuleAdoc(srcDir);
  const html = generateRuleDescription(adocFile);
  writeRuleDescription(dstDir, 'default-description.html', html);
}

/**
 * Generate rule descriptions (for all relevant languages) and write it in the destination directory.
 * @param srcDir directory containing the original rule's metadata and description.
 * @param dstDir directory where the generated rule's description will be written.
 */
export function generateOneRuleDescription(srcDir: string, dstDir: string) {
  fs.mkdirSync(dstDir, { recursive: true });
  const languages = listSupportedLanguages(srcDir);
  if (languages.length === 0) {
    generateGenericDescription(srcDir, dstDir);
    return;
  }

  let isFirstLanguage = true;
  for (const language of languages) {
    const adocFile = getRuleAdoc(srcDir, language);
    const html = generateRuleDescription(adocFile);
    writeRuleDescription(dstDir, language + '-description.html', html);

    if (isFirstLanguage) {
      // Use the first language as the default description.
      writeRuleDescription(dstDir, 'default-description.html', html);
      isFirstLanguage = false;
    }
  }
}

/**
 * Generate one directory per rule with its HTML description.
 * @param srcPath directory containing all the rules subdirectories, with the metadata and descriptions.
 * @param dstPath directory where rule directories should be created.
 * @param rules an optional list of rules to process. Other rules won't be generated.
 */
export function generateRulesDescription(srcPath: string, dstPath: string, rules?: string[]) {
  for (const { srcDir, dstDir } of getRulesDirectories(srcPath, dstPath, rules)) {
    generateOneRuleDescription(srcDir, dstDir);
  }
}

/**
 * Retrieve the path to the rule.adoc file for the given rule and optional language.
 * @param srcDir rule's source directory.
 * @param language language for which the metadata should be generated, when provided.
 */
function getRuleAdoc(srcDir: string, language?: string) {
  let ruleSrcFile = language ? path.join(srcDir, language, 'rule.adoc') : undefined;
  if (!ruleSrcFile || !fs.existsSync(ruleSrcFile)) {
    ruleSrcFile = path.join(srcDir, 'rule.adoc');
  }

  if (!fs.existsSync(ruleSrcFile)) {
    throw new Error(`Missing file 'rule.adoc' for language ${language} in ${srcDir}`);
  }

  return ruleSrcFile;
}

/**
 * Generate the HTML for the rule description.
 */
function generateRuleDescription(ruleAdocFile: string) {
  const baseDir = path.resolve(path.dirname(ruleAdocFile));
  const opts = {
    attributes: {
      'rspecator-view': '',
      docfile: ruleAdocFile,
    },
    safe: 'unsafe',
    base_dir: baseDir,
    backend: 'xhtml5',
    to_file: false
  };

  // Every rule documentation has an implicit level-1 "Description" header.
  const fileData = fs.readFileSync(ruleAdocFile);
  const data = '== Description\n\n' + fileData;
  const html = asciidoc.convert(data, opts) as string;
  return generateAutoRspecLinks(html);
}
