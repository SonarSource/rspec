import fs from 'fs';
import path from 'path';
import { Octokit } from '@octokit/rest';
import Git from 'nodegit';
import { logger as rootLogger } from './deploymentLogger';

const logger = rootLogger.child({ source: path.basename(__filename) })

export interface PullRequest {
  rspec_id: string,
  url: string,
  branch: string,
  pull_id: number
}

/**
 * Fetch all the open pull requests that add new rules (start with "Create rule Sxxx").
 * Call the "process" callback for each such rule.
 * @param tmpRepoDir Path to the temporary directory with a throw-away clone of the rspec repository.
 *                   if the repository does not exist, it will clone it first.
 * @param callback A callback to process each rule. Takes two arguments:
 *                srcDir - the path to the incomplete rule found in the corresponding PR.
 *                pr - the pull request attributes that might be useful to process the rule.
 */
export async function process_incomplete_rspecs(tmpRepoDir: string,
                                                callback: (srcDir: string, pr: PullRequest)=>void) {
  const octokit = process.env.GITHUB_TOKEN ?
    new Octokit({userAgent: 'rspec-tools', auth: process.env.GITHUB_TOKEN}):
    new Octokit({userAgent: 'rspec-tools'});
  const { data } = await octokit.rest.pulls.list({owner:'SonarSource', repo:'rspec', state:'open'});
  let pulls = [];
  for (const pull of data) {
    const found = pull.title.match('^Create rule (S[0-9]+)($|[^0-9])');
    if (found) {
      pulls.push({rspec_id: found[1],
                  url: pull.html_url,
                  branch: pull.head.ref,
                  pull_id: pull.number});
    }
  }
  const repo = await (() => {
    if (!fs.existsSync(path.join(tmpRepoDir, '.git'))) {
      if (process.env.GITHUB_TOKEN) {
        return Git.Clone.clone('https://' + process.env.GITHUB_TOKEN + '@github.com/SonarSource/rspec/', tmpRepoDir);
      } else {
        return Git.Clone.clone('https://github.com/SonarSource/rspec/', tmpRepoDir);
	logger.error(`Token is missing`);
      }
    } else {
      return Git.Repository.open(tmpRepoDir);
    }
  })();
  const config = await repo.config();
  await config.setString('remote.origin.fetch', '+refs/pull/*/head:refs/remotes/origin/pr/*');
  await repo.fetch('origin');
  for (const pull of pulls) {
    const ref = await repo.getBranch('refs/remotes/origin/pr/' + pull.pull_id);
    await repo.checkoutRef(ref);
    logger.error(`Processing PR ${pull.pull_id} (${pull.url}`)
    const ruleDir = path.join(tmpRepoDir, 'rules', pull.rspec_id);
    if (fs.existsSync(ruleDir)) {
      try {
        callback(ruleDir, pull);
      } catch (e) {
        logger.error(`Failed to process PR (${pull.url}), it will be skipped (${e})`);
      }
    } else {
      logger.error(`No rule dir rules/${pull.rspec_id} is found for the PR#${pull.pull_id}: ${pull.url}`);
    }
  }
}
