import fs from 'fs';
import path from 'path';

import { generateRulesDescription } from '../description';
import { withTestDir, createFiles } from '../testutils';

describe('description generation', () => {
test('generates html from asciidoc', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/description.adoc': 'Generic content',
        'S100/java/rule.adoc':
          ['include::../description.adoc[]',
          'Specific content'].join('\n')
      });
      return withTestDir(async (dstPath) => {
        generateRulesDescription(srcPath, dstPath);

        const ruleHtml = fs.readFileSync(path.join(dstPath, 'S100', 'java-description.html'));
        expect(ruleHtml.toString()).toEqual(
          [
            '<div class="sect1">',
            '<h2 id="_description">Description</h2>',
            '<div class="sectionbody">',
            '<div class="paragraph">',
            '<p>Generic content',
            'Specific content</p>',
            '</div>',
            '</div>',
            '</div>'
          ].join('\n')
        );
      });
    });
  });
});