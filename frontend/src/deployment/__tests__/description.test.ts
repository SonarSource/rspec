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
          '',
          '* See S101',
          '* See RSPEC-101',
        ].join('\n'),

        'S101/rule.adoc': 'Generic content',
        'S101/java/rule.adoc': [
          'include::../rule.adoc[]',
          'Specific content',
          'See S100.'
        ].join('\n'),

        'S501/rule.adoc': 'Generic content, no active language',
      });

      return withTestDir(async (dstPath) => {
        generateRulesDescription(srcPath, dstPath);

        const s100Java = path.join(dstPath, 'S100', 'java-description.html');
        expect(fs.existsSync(s100Java)).toBeTruthy();
        const htmlS100Java = fs.readFileSync(s100Java);
        expect(htmlS100Java.toString()).toMatchInlineSnapshot(`
"<div class=\\"sect1\\">
<h2 id=\\"_description\\">Description</h2>
<div class=\\"sectionbody\\">
<div class=\\"paragraph\\">
<p>Generic content
Specific content</p>
</div>
<div class=\\"ulist\\">
<ul>
<li>
<p>See <a data-rspec-id=\\"S101\\" class=\\"rspec-auto-link\\">S101</a></p>
</li>
<li>
<p>See <a data-rspec-id=\\"S101\\" class=\\"rspec-auto-link\\">RSPEC-101</a></p>
</li>
</ul>
</div>
</div>
</div>"
`);

        const s101Java = path.join(dstPath, 'S101', 'java-description.html');
        expect(fs.existsSync(s101Java)).toBeTruthy();
        const htmlS101Java = fs.readFileSync(s101Java);
        expect(htmlS101Java.toString()).toMatchInlineSnapshot(`
"<div class=\\"sect1\\">
<h2 id=\\"_description\\">Description</h2>
<div class=\\"sectionbody\\">
<div class=\\"paragraph\\">
<p>Generic content
Specific content
See <a data-rspec-id=\\"S100\\" class=\\"rspec-auto-link\\">S100</a>.</p>
</div>
</div>
</div>"
`);

        const s501Default = path.join(dstPath, 'S501', 'default-description.html');
        expect(fs.existsSync(s501Default)).toBeTruthy();
        const htmlS501Default = fs.readFileSync(s501Default);
        expect(htmlS501Default.toString()).toMatchInlineSnapshot(`
"<div class=\\"sect1\\">
<h2 id=\\"_description\\">Description</h2>
<div class=\\"sectionbody\\">
<div class=\\"paragraph\\">
<p>Generic content, no active language</p>
</div>
</div>
</div>"
`);
      });
    });
  });
});
