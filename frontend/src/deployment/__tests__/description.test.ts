import fs from 'fs';
import path from 'path';

import { generateRulesDescription } from '../description';
import { withTestDir, createFiles } from '../testutils';

describe('description generation', () => {
  test('generates html from asciidoc', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/rule.adoc': 'Generic content',
        'S100/java/rule.adoc': `
include::../rule.adoc[]
Specific content

== Test various forms of auto-link for RSPEC. S100

* See S100, S101,S102.
* See RSPEC-101
* But not S103badref.
* This is a code literal \`+S234+\` but this isn't S567.

\\https://sonarsource.github.io/rspec/#/rspec/S100

https://sonarsource.github.io/rspec/#/rspec/S100/cfamily

https://sonarsource.github.io/rspec/#/rspec/S100/cfamily[]

[source,cpp]
----
int foo() {
  // No auto-links in code!
  auto S100 = 100;
  auto U100 = 100u;
  return S100 + U100;
}
----

After snippet, See S100.

[source,cpp]
----
int goo() {
  // No auto-links in code!
  // S100
}
----

more ref: RSPEC-200.
`,

        'S101/rule.adoc': 'Generic content',
        'S101/java/rule.adoc': `
include::../rule.adoc[]
Specific content
See S100.
`,

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
</div>
</div>
<div class=\\"sect1\\">
<h2 id=\\"_test_various_forms_of_auto_link_for_rspec_s100\\">Test various forms of auto-link for RSPEC. <a data-rspec-id=\\"S100\\" class=\\"rspec-auto-link\\">S100</a></h2>
<div class=\\"sectionbody\\">
<div class=\\"ulist\\">
<ul>
<li>
<p>See <a data-rspec-id=\\"S100\\" class=\\"rspec-auto-link\\">S100</a>, <a data-rspec-id=\\"S101\\" class=\\"rspec-auto-link\\">S101</a>,<a data-rspec-id=\\"S102\\" class=\\"rspec-auto-link\\">S102</a>.</p>
</li>
<li>
<p>See <a data-rspec-id=\\"S101\\" class=\\"rspec-auto-link\\">RSPEC-101</a></p>
</li>
<li>
<p>But not S103badref.</p>
</li>
<li>
<p>This is a code literal <code>S234</code> but this isn&#8217;t <a data-rspec-id=\\"S567\\" class=\\"rspec-auto-link\\">S567</a>.</p>
</li>
</ul>
</div>
<div class=\\"paragraph\\">
<p>https://sonarsource.github.io/rspec/#/rspec/S100</p>
</div>
<div class=\\"paragraph\\">
<p><a href=\\"https://sonarsource.github.io/rspec/#/rspec/S100/cfamily\\" class=\\"bare\\">https://sonarsource.github.io/rspec/#/rspec/S100/cfamily</a></p>
</div>
<div class=\\"paragraph\\">
<p><a href=\\"https://sonarsource.github.io/rspec/#/rspec/S100/cfamily\\" class=\\"bare\\">https://sonarsource.github.io/rspec/#/rspec/S100/cfamily</a></p>
</div>
<div class=\\"listingblock\\">
<div class=\\"content\\">
<pre class=\\"highlight\\"><code class=\\"language-cpp\\" data-lang=\\"cpp\\">int foo() {
  // No auto-links in code!
  auto S100 = 100;
  auto U100 = 100u;
  return S100 + U100;
}</code></pre>
</div>
</div>
<div class=\\"paragraph\\">
<p>After snippet, See <a data-rspec-id=\\"S100\\" class=\\"rspec-auto-link\\">S100</a>.</p>
</div>
<div class=\\"listingblock\\">
<div class=\\"content\\">
<pre class=\\"highlight\\"><code class=\\"language-cpp\\" data-lang=\\"cpp\\">int goo() {
  // No auto-links in code!
  // S100
}</code></pre>
</div>
</div>
<div class=\\"paragraph\\">
<p>more ref: <a data-rspec-id=\\"S200\\" class=\\"rspec-auto-link\\">RSPEC-200</a>.</p>
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

  function normalizeString(str: string) {
    // Ignore \n\r vs \n differences, and ignore extra whitespace.
    return str.replace(/\r\n/g, '\n').trimEnd();
  }

  expect.extend({
    toBeSameAsFile(received: string, expectedPath: string) {
      if (!fs.existsSync(expectedPath)) {
        return {
          message: () => `File ${expectedPath} was not found.`,
          pass: false
        };
      }
      const expected = fs.readFileSync(expectedPath).toString();
      if (normalizeString(expected) === normalizeString(received)) {
        return {
          // This message is used in case of test negation `expect(a).not.toBeSameAsFile(f)`
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
          expect(actual).toBeSameAsFile(expectedPath);
          treated++;
        });
      });
      expect(treated).toBe(11);
    });
  });
});
