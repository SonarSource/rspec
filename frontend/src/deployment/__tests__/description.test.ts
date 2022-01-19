import fs from 'fs';
import path from 'path';

import { generateRulesDescription } from '../description';
import { withTestDir, createFiles } from '../testutils';

describe('description generation', () => {
test('generates html from asciidoc', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/rule.adoc': 'Generic content',
        'S100/java/rule.adoc': [
          'include::../rule.adoc[]',
          'Specific content',
        ].join('\n'),

        'S501/rule.adoc': 'Generic content, no active language',
      });

      return withTestDir(async (dstPath) => {
        generateRulesDescription(srcPath, dstPath);

        const s100Java = path.join(dstPath, 'S100', 'java-description.html');
        expect(fs.existsSync(s100Java)).toBeTruthy();
        const htmlS100Java = fs.readFileSync(s100Java);
        expect(htmlS100Java.toString()).toEqual([
          '<div class="sect1">',
          '<h2 id="_description">Description</h2>',
          '<div class="sectionbody">',
          '<div class="paragraph">',
          '<p>Generic content',
          'Specific content</p>',
          '</div>',
          '</div>',
          '</div>',
        ].join('\n'));

        const s501Default = path.join(dstPath, 'S501', 'default-description.html');
        expect(fs.existsSync(s501Default)).toBeTruthy();
        const htmlS501Default = fs.readFileSync(s501Default);
        expect(htmlS501Default.toString()).toEqual([
          '<div class="sect1">',
          '<h2 id="_description">Description</h2>',
          '<div class="sectionbody">',
          '<div class="paragraph">',
          '<p>Generic content, no active language</p>',
          '</div>',
          '</div>',
          '</div>',
        ].join('\n'));
      });
    });
  });
});