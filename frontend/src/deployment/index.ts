import yargs from 'yargs/yargs';

import path from 'path';

import { clean_rules } from './clean';
import { generateOneRuleMetadata, generateRulesMetadata } from './metadata';
import { generateOneRuleDescription, generateRulesDescription, } from './description';
import { createIndexFiles } from './searchIndex';
import { process_incomplete_rspecs, PullRequest } from './pullRequestIndexing';

import { PR_DIRECTORY, RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY } from './paths';

process.on('unhandledRejection', up => {
  throw up;
});

function noArgumentBuilder() {
  // Nothing to do.
}

yargs(process.argv.slice(2))
  .command('clean', 'clean the rules', noArgumentBuilder, clean_rules)
  .command('gen-metadata [rules..]', 'generate metadata',
    (argBuilder) => {
      argBuilder.array<string>('rules');
    },
    (argv: { rules: string[] }) => {
      generateRulesMetadata(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY, argv.rules);
      process_incomplete_rspecs(PR_DIRECTORY, function (srcDir: string, pr: PullRequest) {
        const dstDir = path.join(RULE_DST_DIRECTORY, pr.rspec_id);
        generateOneRuleMetadata(srcDir, dstDir, pr.branch, pr.url);
      });
    })
  .command('gen-description [rules..]', 'generate description',
    (argBuilder) => {
      argBuilder.array<string>('rules');
    },
    (argv: { rules: string[] }) => {
      generateRulesDescription(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY, argv.rules);
      process_incomplete_rspecs(PR_DIRECTORY, function (srcDir: string, pr: PullRequest) {
        const dstDir = path.join(RULE_DST_DIRECTORY, pr.rspec_id);
        generateOneRuleDescription(srcDir, dstDir);
      });
    })
  .command('gen-index', 'generate search index',
    noArgumentBuilder,
    _ => createIndexFiles(RULE_DST_DIRECTORY))
  .command('*', 'generate rules metadata, description and index',
    noArgumentBuilder,
    _ => {
      generateRulesMetadata(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY);
      generateRulesDescription(RULE_SRC_DIRECTORY, RULE_DST_DIRECTORY);
      process_incomplete_rspecs(PR_DIRECTORY, function (srcDir: string, pr: PullRequest) {
        const dstDir = path.join(RULE_DST_DIRECTORY, pr.rspec_id);
        generateOneRuleMetadata(srcDir, dstDir, pr.branch, pr.url);
        generateOneRuleDescription(srcDir, dstDir);
      }).then(function () {
        createIndexFiles(RULE_DST_DIRECTORY);
      });
    })
  .parse();
