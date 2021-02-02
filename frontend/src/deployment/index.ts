#!/usr/bin/env ts-node

import yargs from 'yargs/yargs';

import { clean_rules } from './clean';
import { generate_rules_metadata } from './metadata';
import { generate_rules_description } from './description';
import { createIndexFiles } from './searchIndex';

import { RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY } from './paths';

// eslint-disable-next-line @typescript-eslint/no-unused-expressions
yargs(process.argv.slice(2))

.command('clean', 'clean the rules', () => {}, clean_rules)

.command('gen-metadata', 'generate metadata',
(yargs) => {
  yargs.array<string>('rules')
},
(argv: any) => generate_rules_metadata(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY, argv.rules))

.command('gen-description', 'generate description',
(yargs) => {
  yargs.array<string>('rules')
},
(argv: any) => generate_rules_description(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY, argv.rules))

.command('gen-index', 'generate search index',
() => {},
(argv: any) => createIndexFiles(RULE_DST_DIRECTORY))

.command('*', 'generate rules metadata, description and index',
() => {},
(argv: any) => {
  generate_rules_metadata(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY);
  generate_rules_description(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY);
  createIndexFiles(RULE_DST_DIRECTORY);
})

.argv;
