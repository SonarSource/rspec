import fs from 'fs';
import path from 'path';

import { generateOneRuleMetadata, generateRulesMetadata } from '../metadata';
import { withTestDir, createFiles } from '../testutils';

describe('metadata generation', () => {

  test('language specific metadata overrides generic metadata', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/metadata.json': JSON.stringify({
          title: 'Rule S100',
          tags: ['confusing']
        }),
        'S100/java/metadata.json': JSON.stringify({
          title: 'Java Rule S100'
        }),
        'S100/python/metadata.json': JSON.stringify({
          tags: ['pep8']
        }),
      });
      return withTestDir(async (dstPath) => {
        generateRulesMetadata(srcPath, dstPath);
        const javaStrMetadata = fs.readFileSync(`${dstPath}/S100/java-metadata.json`);
        const javaMetadata = JSON.parse(javaStrMetadata.toString());
        expect(javaMetadata).toMatchObject({
          title: 'Java Rule S100',
          tags: ['confusing']
        });
  
        const pythonStrMetadata = fs.readFileSync(`${dstPath}/S100/python-metadata.json`);
        const pythonMetadata = JSON.parse(pythonStrMetadata.toString());
        expect(pythonMetadata).toMatchObject({
          title: 'Rule S100',
          tags: ['pep8']
        });
      });
    });
  });

  test('check default status', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/metadata.json': JSON.stringify({
        }),
        'S100/java/metadata.json': JSON.stringify({
        }),
      });
      return withTestDir(async (dstPath) => {
        generateRulesMetadata(srcPath, dstPath);
        const javaStrMetadata = fs.readFileSync(`${dstPath}/S100/java-metadata.json`);
        const javaMetadata = JSON.parse(javaStrMetadata.toString());
        expect(javaMetadata).toMatchObject({
          languagesSupport: [
            {name: 'java', status: 'default'}
          ]
        });
      });
    });
  });

  test('check status computation', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/metadata.json': JSON.stringify({
          title: 'Rule S100',
          status: 'ready'
        }),
        'S100/java/metadata.json': JSON.stringify({
          title: 'Java Rule S100'
        }),
        'S100/python/metadata.json': JSON.stringify({
          status: 'closed'
        }),
      });
      return withTestDir(async (dstPath) => {
        generateRulesMetadata(srcPath, dstPath);
        const javaStrMetadata = fs.readFileSync(`${dstPath}/S100/java-metadata.json`);
        const pythonStrMetadata = fs.readFileSync(`${dstPath}/S100/python-metadata.json`);
        const javaMetadata = JSON.parse(javaStrMetadata.toString());
        const pythonMetadata = JSON.parse(pythonStrMetadata.toString());
        expect(pythonMetadata).toMatchObject({
          title: 'Rule S100',
          languagesSupport: [
            {name: 'java', status: 'ready'},
            {name: 'python', status: 'closed'}
          ]
        });

        expect(javaMetadata.languagesSupport).toStrictEqual(pythonMetadata.languagesSupport);
      });
    });
  });

  test('generates only requested rules if a list of rule is provided', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/java/metadata.json': JSON.stringify({
          title: 'Rule S100'
        }),
        'S200/java/metadata.json': JSON.stringify({
          title: 'Rule S200'
        }),
      });
      return withTestDir(async (dstPath) => {
        generateRulesMetadata(srcPath, dstPath, ['S100']);

        const s100Exists = fs.existsSync(`${dstPath}/S100/java-metadata.json`);
        expect(s100Exists).toBeTruthy();
    
        const s200Exists = fs.existsSync(`${dstPath}/S200/java-metadata.json`);
        expect(s200Exists).toBeFalsy();
      });
    });
  });

  test('forwards the pr url when provided', () => {
    return withTestDir((srcPath) => {
      createFiles(srcPath, {
        'S100/java/metadata.json': JSON.stringify({
          title: 'Rule S100'
        }),
        'S200/java/metadata.json': JSON.stringify({
          title: 'Rule S200'
        }),
      });
      return withTestDir(async (dstPath) => {
        generateOneRuleMetadata(path.join(srcPath, 'S100'), path.join(dstPath, 'S100'), 'master');

        const s100StrMetadata = fs.readFileSync(`${dstPath}/S100/java-metadata.json`);
        const s100Metadata = JSON.parse(s100StrMetadata.toString());
        expect(Object.keys(s100Metadata)).toContain('branch');
        expect(s100Metadata.branch).toEqual('master');
        expect(Object.keys(s100Metadata)).not.toContain('prUrl');

        generateOneRuleMetadata(path.join(srcPath, 'S200'), path.join(dstPath, 'S200'), 'add-my-rule', 'https://some.pr/url');


        const s200StrMetadata = fs.readFileSync(`${dstPath}/S200/java-metadata.json`);
        const s200Metadata = JSON.parse(s200StrMetadata.toString());
        expect(Object.keys(s200Metadata)).toContain('prUrl');
        expect(s200Metadata.branch).toEqual('add-my-rule');
        expect(s200Metadata.prUrl).toEqual('https://some.pr/url');
      });
    });
  });

  test('generate test metadata', () => {
    return withTestDir(async (dstPath) => {
      generateRulesMetadata(path.join(__dirname, 'resources', 'rules'), dstPath);
      const rules = fs.readdirSync(dstPath);
      expect(rules.length).toEqual(3);
      rules.forEach(ruleDir => {
        const languages = fs.readdirSync(`${dstPath}/${ruleDir}`);
        expect(languages.length).toBeGreaterThanOrEqual(1);
        languages.forEach(file => {
          const actual = JSON.parse(fs.readFileSync(`${dstPath}/${ruleDir}/${file}`).toString());
          const expectedPath = path.join(__dirname, 'resources', 'metadata', ruleDir, file);
          const expected = JSON.parse(fs.readFileSync(expectedPath).toString());
          expect(actual).toStrictEqual(expected);
        })
      });
    });
  });
});
