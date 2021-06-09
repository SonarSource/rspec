#!/usr/bin/env ts-node

import yargs from 'yargs/yargs';

import path from 'path';

import { clean_rules } from './clean';
import { generate_one_rule_metadata, generate_rules_metadata } from './metadata';
import { generate_one_rule_description, generate_rules_description, } from './description';
import { createIndexFiles } from './searchIndex';
import { process_incomplete_rspecs, PullRequest } from './pullRequestIndexing';

import { PR_DIRECTORY, RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY } from './paths';

process.on('unhandledRejection', up => { throw up })

// eslint-disable-next-line @typescript-eslint/no-unused-expressions
yargs(process.argv.slice(2))

.command('clean', 'clean the rules', () => {}, clean_rules)

.command('gen-metadata', 'generate metadata',
         (yargs) => {
             yargs.array<string>('rules')
         },
         (argv: any) => {
             generate_rules_metadata(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY, argv.rules)
             process_incomplete_rspecs(PR_DIRECTORY, function (srcDir: string, pr: PullRequest) {
                 const dstDir = path.join(RULE_DST_DIRECTORY, pr.rspec_id);
                 generate_one_rule_metadata(srcDir, dstDir, pr.branch, pr.url);
             })
         })

.command('gen-description', 'generate description',
         (yargs) => {
             yargs.array<string>('rules')
         },
         (argv: any) => {
             generate_rules_description(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY, argv.rules)
             process_incomplete_rspecs(PR_DIRECTORY, function (srcDir: string, pr: PullRequest) {
                 const dstDir = path.join(RULE_DST_DIRECTORY, pr.rspec_id);
                 generate_one_rule_description(srcDir, dstDir);
             })
         })

.command('gen-index', 'generate search index',
() => {},
(argv: any) => createIndexFiles(RULE_DST_DIRECTORY))

.command('*', 'generate rules metadata, description and index',
() => {},
(argv: any) => {
  generate_rules_metadata(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY);
  generate_rules_description(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY);
  process_incomplete_rspecs(PR_DIRECTORY, function (srcDir: string, pr: PullRequest) {
    const dstDir = path.join(RULE_DST_DIRECTORY, pr.rspec_id);
    generate_one_rule_metadata(srcDir, dstDir, pr.branch, pr.url);
    generate_one_rule_description(srcDir, dstDir);
  }).then(function() {
    createIndexFiles(RULE_DST_DIRECTORY);
  });
})

.argv;
