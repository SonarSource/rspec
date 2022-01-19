import fs from 'fs';
import path from 'path';
import asciidoctor from 'asciidoctor';

import { getRulesDirectories, listSupportedLanguages } from './utils';
import { logger } from './deploymentLogger';

const asciidoc = asciidoctor();

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
 * Generate rule descriptions (for all relevant languages) and write it in the destination directory.
 * @param srcDir directory containing the original rule's metadata and description.
 * @param dstDir directory where the generated rule's description will be written.
 */
export function generateOneRuleDescription(srcDir: string, dstDir: string) {
  fs.mkdirSync(dstDir, { recursive: true });
  const languages = listSupportedLanguages(srcDir);
  let isFirstLanguage = true;
  for (const language of languages) {
    const html = generateRuleDescription(srcDir, language);
    const dstFile = path.join(dstDir, language + '-description.html');
    fs.writeFileSync(dstFile, html, {encoding: 'utf8'});

    if (isFirstLanguage) {
      // Use the first language as the default description.
      const defFile = path.join(dstDir, 'default-description.html');
      fs.writeFileSync(defFile, html, {encoding: 'utf8'});
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
 * Generate the description corresponding to one rule and one language.
 * @param srcDir rule's source directory.
 * @param language language for which the metadata should be generated
 */
function generateRuleDescription(srcDir: string, language: string) {
    let ruleSrcFile = path.join(srcDir, language, 'rule.adoc');
    if (!fs.existsSync(ruleSrcFile)) {
        ruleSrcFile = path.join(srcDir, 'rule.adoc');
        if (!fs.existsSync(ruleSrcFile)) {
            throw new Error(`Missing file 'rule.adoc' for language ${language} in ${srcDir}`);
        }
    }
    const baseDir = path.resolve(path.dirname(ruleSrcFile));
    const opts = {
        attributes: {
          'rspecator-view': '',
          docfile: ruleSrcFile,
        },
        safe: 'unsafe',
        base_dir: baseDir,
        backend: 'xhtml5',
        to_file: false
    };

    // Every rule documentation has an implicit level-1 "Description" header.
    const fileData = fs.readFileSync(ruleSrcFile);
    const data = '== Description\n\n' + fileData;
    return asciidoc.convert(data, opts);
}
