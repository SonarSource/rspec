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
 * @param srcDir directory containing the original rule metadata and description.
 * @param dstDir directory where the generated rules metadata and description will be written.
 */
export function generateOneRuleDescription(srcDir: string, dstDir: string) {
  fs.mkdirSync(dstDir, { recursive: true });
  const languages = listSupportedLanguages(srcDir);
  let default_descr_wanted = true;
  for (const language of languages) {
    const html = generateRuleDescription(srcDir, language);
    const dstFile = path.join(dstDir, language + '-description.html');
    fs.writeFileSync(dstFile, html, {encoding: 'utf8'});
    if (default_descr_wanted) {
      const defFile = path.join(dstDir, 'default-description.html');
      fs.writeFileSync(defFile, html, {encoding: 'utf8'});
      default_descr_wanted = false;
    }
  }
}

/**
 * Generate rules descriptions and write them in the destination directory.
 * @param srcPath directory containing the original rules metadata and description.
 * @param dstPath directory where the generated rules metadata and description will be written.
 * @param rules an optional list of rules to list. Other rules won't be generated.
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
