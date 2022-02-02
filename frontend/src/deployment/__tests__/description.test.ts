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

  expect.extend({
    toBeSameAsFile(received, expected, expectedPath) {
      if (expected.replaceAll('\r\n', '\n') === received.replaceAll('\r\n', '\n')) {
        return {
          message: () => `Identity check failed on ${expectedPath}.\nExpected:\n${expected}\n\nReceived:\n${received}`,
          pass: true
        };
      } else {
        const receivedPath = path.join(path.dirname(expectedPath), 'received-' + path.basename(expectedPath));
        fs.writeFileSync(receivedPath, received);
        return {
          message: () => `Identity check failed on ${expectedPath}.\nReceived file saved in ${receivedPath}`,
          pass: false
        };
      }
    }
  });
  test('generates description for active rules', () => {
    return withTestDir(async (dstPath) => {
      generateRulesDescription(path.join(__dirname, 'resources', 'rules'), dstPath);
      const rules = fs.readdirSync(dstPath);
      expect(rules.length).toEqual(4);
      let treated = 0;
      rules.forEach(ruleDir => {
        const languages = fs.readdirSync(`${dstPath}/${ruleDir}`);
        expect(languages.length).toBeGreaterThanOrEqual(1);
        languages.forEach(file => {
          const actual = fs.readFileSync(`${dstPath}/${ruleDir}/${file}`).toString();
          const expectedPath = path.join(__dirname, 'resources', 'metadata', ruleDir, file);
          const expected = fs.readFileSync(expectedPath).toString();
          expect(expected).not.toBeNull();
          expect(actual).toBeSameAsFile(expected, expectedPath);
          treated++;
        })
      });
      expect(treated).toBe(11);
    });
  });
});