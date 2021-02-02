import fs from 'fs';

import { generate_rules_metadata } from '../metadata';
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
        generate_rules_metadata(srcPath, dstPath);
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
        generate_rules_metadata(srcPath, dstPath, ['S100']);

        const s100Exists = fs.existsSync(`${dstPath}/S100/java-metadata.json`);
        expect(s100Exists).toBeTruthy();
    
        const s200Exists = fs.existsSync(`${dstPath}/S200/java-metadata.json`);
        expect(s200Exists).toBeFalsy();
      });
    });
  });
});